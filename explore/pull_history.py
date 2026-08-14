"""
daily-reader/explore :: publication-history puller
--------------------------------------------------
Pulls per-source publication history as deep as each source will freely give,
so the corpus dashboard has trends beyond the live window (items.jsonl starts
2026-07-27). Read-only with respect to the live pipeline: reads ../roster.md
and ../state/items.jsonl, writes only under explore/data/.

Depth per entry point (recorded as a first-class fact, never papered over):
  substack-api  archive API paginates well past the ~20-entry feed window;
                pulled back to CUTOFF
  blogspot      full history via ?max-results=500
  feed-only     whatever the feed carries (danluu atom = full history;
                most RSS = a recent window) -- truncation flagged
  youtube       feed serves exactly 15 entries, hard cap -- always truncated
  page-watch    no history exists; pages are edited, not posted

Usage:  python pull_history.py            (cached: skips sources already in
                                           data/raw/ unless REFRESH = True)
Output: data/history.jsonl   one row per published item
        data/sources.csv     one row per source with depth metadata
"""

import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

HERE = Path(__file__).parent
ROOT = HERE.parent
ROSTER = ROOT / "roster.md"
ITEMS = ROOT / "state" / "items.jsonl"
DATA = HERE / "data"
RAW = DATA / "raw"
DATA.mkdir(exist_ok=True)
RAW.mkdir(exist_ok=True)

CUTOFF = "2024-08-01"          # pull archives back to here (24 months)
REFRESH = False                # True forces re-download of cached raw pulls
UA = {"User-Agent": "daily-reader-explore/0.1 (personal corpus analysis)"}
TIMEOUT = 25
YT_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"


def log(msg):
    print(msg, flush=True)


def slug(url):
    return re.sub(r"[^A-Za-z0-9]+", "-", re.sub(r"^https?://", "", url)).strip("-")[:80]


# ---------------------------------------------------------------------------
# Roster parsing (same literal-section contract as poller.py)
# ---------------------------------------------------------------------------
def parse_roster():
    """Return (feeds, youtube, pages) lists of dicts from roster.md tables."""
    text = ROSTER.read_text(encoding="utf-8")
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections[current] = []
        elif current is not None and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and not set(cells[0]) <= set("-: ") and cells[0].lower() not in (
                    "publication", "creator / channel", "creator", "name"):
                sections[current].append(cells)

    feeds = [{"creator": r[0], "url": r[1], "status": r[3]}
             for r in sections.get("substack", []) if len(r) >= 4]
    youtube = [{"creator": r[0], "handle": r[1], "cid": r[2], "status": r[5]}
               for r in sections.get("youtube", []) if len(r) >= 6]
    pages = [{"creator": r[0], "page": r[1], "url": r[2], "status": r[3]}
             for r in sections.get("page watch", []) if len(r) >= 4]
    return feeds, youtube, pages


# ---------------------------------------------------------------------------
# Pullers -- each returns (platform, items, truncated) where items are
# {"title", "url", "published"} dicts, or raises for fail-soft handling
# ---------------------------------------------------------------------------
def try_substack_api(feed_url):
    """Paginate the Substack archive API back to CUTOFF; None if not Substack."""
    domain = re.sub(r"^https?://", "", feed_url).split("/")[0]
    base = f"https://{domain}/api/v1/archive"
    items, offset = [], 0
    while True:
        r = requests.get(base, params={"sort": "new", "search": "", "offset": offset,
                                       "limit": 50}, headers=UA, timeout=TIMEOUT)
        if r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
            return None
        batch = r.json()
        if not isinstance(batch, list):
            return None
        if not batch:
            break
        for p in batch:
            d = (p.get("post_date") or "")[:10]
            items.append({"title": p.get("title") or "?",
                          "url": p.get("canonical_url") or "",
                          "published": d})
        if items and items[-1]["published"] < CUTOFF:
            break
        offset += 50
        time.sleep(0.4)
    return [i for i in items if i["published"] >= CUTOFF]


def pull_feed(feed_url):
    """Parse a feed; return items with ISO dates. Blogspot gets full depth."""
    url = feed_url
    if "blogspot.com" in url:
        url += ("&" if "?" in url else "?") + "max-results=500"
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    parsed = feedparser.parse(r.content)
    items = []
    for e in parsed.entries:
        t = e.get("published_parsed") or e.get("updated_parsed")
        if not t:
            continue
        items.append({"title": e.get("title", "?"),
                      "url": e.get("link", ""),
                      "published": time.strftime("%Y-%m-%d", t)})
    return items


def cached(name, puller):
    """data/raw/<name>.json cache with REFRESH override; fail-soft."""
    path = RAW / f"{name}.json"
    if path.exists() and not REFRESH:
        return json.loads(path.read_text(encoding="utf-8"))
    result = puller()
    path.write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    feeds, youtube, pages = parse_roster()
    log(f"roster: {len(feeds)} feeds, {len(youtube)} youtube, {len(pages)} watched pages")

    history, sources = [], []

    def record(creator, entry_point, platform, source_url, items, truncated, note=""):
        pubs = sorted(i["published"] for i in items if i.get("published"))
        sources.append({
            "creator": creator, "entry_point": entry_point, "platform": platform,
            "source_url": source_url, "n_items": len(items),
            "earliest": pubs[0] if pubs else "", "latest": pubs[-1] if pubs else "",
            "truncated": truncated, "note": note,
        })
        for i in items:
            if i.get("published"):
                history.append({"creator": creator, "entry_point": entry_point,
                                "platform": platform, "title": i["title"],
                                "url": i["url"], "published": i["published"]})

    for f in feeds:
        name = slug(f["url"])
        try:
            api = cached(name + "-api", lambda u=f["url"]: try_substack_api(u)) \
                if "blogspot.com" not in f["url"] else None
            if api is not None:
                record(f["creator"], "feed", "substack-api", f["url"], api,
                       truncated=False, note=f"archive API to {CUTOFF}")
                log(f"  substack-api  {f['creator']}: {len(api)} items")
                continue
            items = cached(name + "-feed", lambda u=f["url"]: pull_feed(u))
            recent = [i for i in items if i["published"] >= CUTOFF]
            full_depth = bool(items) and min(i["published"] for i in items) < CUTOFF
            plat = "blogspot" if "blogspot.com" in f["url"] else "feed-only"
            record(f["creator"], "feed", plat, f["url"], recent,
                   truncated=not full_depth,
                   note=f"feed carries {len(items)} entries"
                        + ("; full history visible" if full_depth else "; window only"))
            log(f"  {plat:<13} {f['creator']}: {len(recent)} in window "
                f"({len(items)} in feed)")
        except Exception as e:
            record(f["creator"], "feed", "error", f["url"], [], True, str(e)[:80])
            log(f"  ERROR         {f['creator']}: {str(e)[:80]}")

    for y in youtube:
        url = YT_FEED.format(cid=y["cid"])
        try:
            items = cached("yt-" + y["cid"], lambda u=url: pull_feed(u))
            items = [i for i in items if "/shorts/" not in i["url"]]
            record(y["creator"], "youtube", "youtube", url, items, truncated=True,
                   note="feed caps at 15 entries (Shorts excluded here)")
            log(f"  youtube       {y['creator']}: {len(items)} non-Shorts entries")
        except Exception as e:
            record(y["creator"], "youtube", "error", url, [], True, str(e)[:80])
            log(f"  ERROR         {y['creator']}: {str(e)[:80]}")

    for p in pages:
        record(p["creator"], "page-watch", "page", p["url"], [], truncated=True,
               note=f"no history exists; watch began 2026-08-01 ({p['page']})")

    with open(DATA / "history.jsonl", "w", encoding="utf-8") as fh:
        for row in sorted(history, key=lambda r: r["published"]):
            fh.write(json.dumps(row) + "\n")
    with open(DATA / "sources.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sources[0].keys()))
        w.writeheader()
        w.writerows(sources)

    live = sum(1 for _ in open(ITEMS, encoding="utf-8"))
    log(f"\nDONE: {len(history)} historical items from {len(sources)} sources "
        f"-> data/history.jsonl; live items.jsonl has {live} rows (read-only)")


if __name__ == "__main__":
    main()
