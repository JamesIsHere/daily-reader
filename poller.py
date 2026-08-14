"""Poll roster feeds, diff against seen state, append new items to the store.

Usage:
    python poller.py               one cycle: fetch, diff, record, report
    python poller.py --baseline    mark everything currently in feeds as seen
                                   without emitting items (first-run arming)

Files (all relative to this script's directory):
    roster.md          hand-edited source of truth (re-read every cycle)
    state/seen.json    per-feed set of item ids already processed
    state/items.jsonl  append-only store of emitted items (digest reads this)
    state/poll.log     one line per feed per cycle: fetch status
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

ROOT = Path(__file__).parent
ROSTER = ROOT / "roster.md"
STATE_DIR = ROOT / "state"
SEEN = STATE_DIR / "seen.json"
ITEMS = STATE_DIR / "items.jsonl"
POLL_LOG = STATE_DIR / "poll.log"

YT_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
UA = {"User-Agent": "daily-reader/0.1 (personal feed poller)"}
TIMEOUT = 20


def parse_roster():
    """Extract active sources from roster.md's Substack and YouTube tables."""
    sources = []
    section = None
    for line in ROSTER.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        if not line.startswith("|") or set(line) <= {"|", "-", " "}:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if section == "substack" and len(cells) >= 4:
            name, url, _, status = cells[0], cells[1], cells[2], cells[3]
            if status == "active" and url.startswith("http"):
                sources.append({"creator": name, "kind": "article", "feed": url})
        elif section == "youtube" and len(cells) >= 6:
            name, _, cid, _, _, status = cells[:6]
            if status == "active" and cid.startswith("UC"):
                sources.append({"creator": name, "kind": "video",
                                "feed": YT_FEED.format(cid=cid)})
    return sources


def entry_id(entry):
    return entry.get("id") or entry.get("link") or entry.get("title", "?")


def entry_published(entry):
    for key in ("published_parsed", "updated_parsed"):
        if entry.get(key):
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", entry[key])
    return None


def entry_body(entry):
    """Best available text for later summarization (articles)."""
    if entry.get("content"):
        return entry["content"][0].get("value", "")
    return entry.get("summary", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true",
                    help="mark current feed contents seen without emitting")
    args = ap.parse_args()

    STATE_DIR.mkdir(exist_ok=True)
    seen = json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else {}
    sources = parse_roster()
    if not sources:
        print("ERROR: no active sources parsed from roster.md", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_items, log_lines = [], []

    for src in sources:
        try:
            resp = requests.get(src["feed"], headers=UA, timeout=TIMEOUT)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
            if parsed.bozo and not parsed.entries:
                raise ValueError(f"unparseable feed: {parsed.bozo_exception}")
            status = f"OK {len(parsed.entries)} entries"
        except Exception as e:
            log_lines.append(f"{now} | {src['creator']} | DEGRADED: {e}")
            continue

        feed_seen = set(seen.get(src["feed"], []))
        fresh = [e for e in parsed.entries if entry_id(e) not in feed_seen]
        shorts_skipped = 0
        for e in fresh:
            feed_seen.add(entry_id(e))
            # Shorts excluded by policy (red-pen 2026-07-27): engagement chaff
            # crowding the calendar. YouTube RSS carries no duration; the
            # /shorts/ link is the only feed-carried signal.
            if src["kind"] == "video" and "/shorts/" in e.get("link", ""):
                shorts_skipped += 1
                continue
            if not args.baseline:
                new_items.append({
                    "id": entry_id(e),
                    "creator": src["creator"],
                    "kind": src["kind"],
                    "title": e.get("title", "(untitled)"),
                    "link": e.get("link", ""),
                    "published": entry_published(e),
                    "fetched": now,
                    "body": entry_body(e)[:8000] if src["kind"] == "article" else "",
                })
        seen[src["feed"]] = sorted(feed_seen)
        skipped = f", {shorts_skipped} shorts skipped" if shorts_skipped else ""
        log_lines.append(f"{now} | {src['creator']} | {status} | {len(fresh)} new{skipped}")

    SEEN.write_text(json.dumps(seen, indent=1), encoding="utf-8")
    with POLL_LOG.open("a", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
    if new_items:
        with ITEMS.open("a", encoding="utf-8") as f:
            for it in new_items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")

    degraded = sum(1 for l in log_lines if "DEGRADED" in l)
    mode = "BASELINE" if args.baseline else "CYCLE"
    print(f"{mode}: {len(sources)} sources polled, "
          f"{degraded} degraded, {len(new_items)} new items emitted")
    for it in new_items:
        print(f"  NEW [{it['kind']}] {it['creator']}: {it['title']}")


if __name__ == "__main__":
    main()
