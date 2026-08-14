"""Quick-add a source to roster.md: resolve, verify, append, baseline.

Usage:
    python add.py @LangChain                    YouTube handle
    python add.py https://www.youtube.com/@X    YouTube URL
    python add.py https://foo.substack.com      Substack URL or bare domain
    python add.py @X --backfill 3               let the 3 most recent items
                                                through to the next digest
    python add.py @X --dry-run                  resolve + verify + print the
                                                row, write nothing
    python add.py @X --name "Display Name"      override the creator column
                                                (default: verified feed title)

What it does, in order:
    1. Resolve the input to a feed URL. YouTube: fetch the channel page and
       read the canonical channel ID (UC...) from <link rel="canonical">;
       the RSS endpoint only accepts channel IDs, never handles. Substack:
       normalize to https://<domain>/feed.
    2. Verify the feed actually fetches and parses; capture its title.
    3. Refuse duplicates (feed URL or channel ID already in roster.md).
    4. Baseline: seed state/seen.json with the feed's current entry ids so
       the next cycle emits only future releases, not the backlog.
       --backfill N leaves the N newest non-Shorts entries unseeded.
    5. Append the row to the matching roster.md table.

New file by design: the live pipeline (poller/digest/cycle) is untouched.
Hand-editing roster.md still works exactly as before.
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import feedparser
import requests

ROOT = Path(__file__).parent
ROSTER = ROOT / "roster.md"
SEEN = ROOT / "state" / "seen.json"

YT_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
PAGE_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
FEED_UA = {"User-Agent": "daily-reader/0.1 (personal feed poller)"}
TIMEOUT = 20


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def resolve_youtube(target):
    """Handle or channel URL -> (handle, channel_id, feed_url)."""
    m = re.search(r"@([\w.\-]+)", target)
    if not m:
        fail(f"could not find an @handle in {target!r}")
    handle = "@" + m.group(1)
    page = requests.get(f"https://www.youtube.com/{handle}",
                        headers=PAGE_UA, timeout=TIMEOUT)
    page.raise_for_status()
    # The page mentions many channel IDs (related channels, shelves); only
    # the canonical link identifies THIS channel.
    m = re.search(r'<link rel="canonical" '
                  r'href="https://www\.youtube\.com/channel/'
                  r'(UC[A-Za-z0-9_-]{22})"', page.text)
    if not m:
        fail(f"no canonical channel ID on the page for {handle} "
             "(page layout changed, or not a channel page)")
    cid = m.group(1)
    return handle, cid, YT_FEED.format(cid=cid)


def resolve_substack(target):
    """URL or bare domain -> feed_url."""
    if re.search(r"\.(xml|rss|atom)($|\?)", target):
        return target
    domain = re.sub(r"^https?://", "", target).strip("/")
    domain = domain.removesuffix("/feed")
    return f"https://{domain}/feed"


def verify_feed(feed_url):
    """Fetch + parse; return (title, entries) or die."""
    resp = requests.get(feed_url, headers=FEED_UA, timeout=TIMEOUT)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)
    if parsed.bozo and not parsed.entries:
        fail(f"feed fetched but unparseable: {parsed.bozo_exception}")
    title = parsed.feed.get("title")
    if not title:
        fail("feed parsed but has no title")
    return title, parsed.entries


def entry_id(entry):
    return entry.get("id") or entry.get("link") or entry.get("title", "?")


def baseline(feed_url, entries, backfill):
    """Seed seen.json; skip the `backfill` newest non-Shorts entries."""
    seen = json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else {}
    ids, spared = set(seen.get(feed_url, [])), 0
    for e in entries:
        is_short = "/shorts/" in e.get("link", "")
        if not is_short and spared < backfill:
            spared += 1
            continue
        ids.add(entry_id(e))
    seen[feed_url] = sorted(ids)
    SEEN.write_text(json.dumps(seen, indent=1), encoding="utf-8")
    return len(ids), spared


def append_row(section, row):
    """Insert row after the last table line of the given ## section."""
    lines = ROSTER.read_text(encoding="utf-8").splitlines()
    start = next((i for i, l in enumerate(lines)
                  if l.strip().lower() == f"## {section}"), None)
    if start is None:
        fail(f"no '## {section}' section in roster.md")
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("## ")), len(lines))
    last = max(i for i in range(start, end) if lines[i].startswith("|"))
    lines.insert(last + 1, row)
    ROSTER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="@handle, YouTube URL, or Substack URL")
    ap.add_argument("--name", help="creator column override")
    ap.add_argument("--backfill", type=int, default=0,
                    help="let the N newest items through (default 0)")
    ap.add_argument("--dry-run", action="store_true",
                    help="resolve and verify only; write nothing")
    args = ap.parse_args()

    t = args.target
    is_yt = t.startswith("@") or "youtube.com" in t
    if not is_yt and "." not in t:
        fail(f"{t!r} is neither an @handle, a YouTube URL, nor a domain")

    roster_text = ROSTER.read_text(encoding="utf-8")
    today = date.today().isoformat()

    if is_yt:
        handle, cid, feed_url = resolve_youtube(t)
        if cid in roster_text:
            fail(f"channel ID {cid} is already in roster.md")
        title, entries = verify_feed(feed_url)
        name = args.name or title
        shorts = sum(1 for e in entries if "/shorts/" in e.get("link", ""))
        note = f"added {today} via add.py"
        if shorts:
            note += f"; Shorts-heavy ({shorts} of {len(entries)} feed entries)"
        row = f"| {name} | {handle} | {cid} | {title} | {note} | active |"
        section = "youtube"
        print(f"resolved: {handle} -> {cid}")
    else:
        feed_url = resolve_substack(t)
        if feed_url in roster_text:
            fail(f"{feed_url} is already in roster.md")
        title, entries = verify_feed(feed_url)
        name = args.name or title
        row = f"| {name} | {feed_url} | {title} | active |"
        section = "substack"
        print(f"resolved: {t} -> {feed_url}")

    print(f"verified: feed title {title!r}, {len(entries)} entries")
    print(f"row:      {row}")
    if args.dry_run:
        print("DRY RUN: nothing written")
        return

    seeded, spared = baseline(feed_url, entries, args.backfill)
    append_row(section, row)
    print(f"baselined: {seeded} entries marked seen"
          + (f", {spared} left for next digest" if spared else ""))
    print(f"DONE: {name} added to roster.md; next cycle picks it up")


if __name__ == "__main__":
    main()
