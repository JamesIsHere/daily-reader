"""Watch feedless static pages for edits: fetch, extract, hash, diff, emit.

Usage:
    python watch.py                one cycle: fetch watched pages, diff each
                                   against its stored snapshot, emit an item
                                   per changed page
    python watch.py --baseline     re-arm every page: store current text,
                                   emit nothing
    python watch.py --dry-run      detect and report; write no state, no items

Covers sources with no feed in any form (patrickcollison.com: static topical
pages behind a catch-all router — the pages get edited, not posted to).
Reads the '## Page watch' roster.md section:

    | Creator | Page | URL | Status |

Rows with status 'active' are watched. A page not yet in state is baselined
silently on first sight, so hand-adding a row stays a one-line edit and never
dumps a backlog — same law as feeds.

Emitted items use kind "article" and the poller's exact schema, so digest
and the rolling view treat them natively; the body is the text ADDED
since the last snapshot, so the digest bullet can say what changed. A
deletion-only edit emits with an empty body and falls back to title-only
(never fabricate).

State: state/pages.json (url -> hash + timestamps) and one full-text snapshot
per page in state/pages/<slug>.txt (kept for diffing, human-inspectable).
New file by design: poller/digest/backtest are untouched; cycle.py runs this
between poll and digest.
"""

import argparse
import difflib
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import requests

ROOT = Path(__file__).parent
ROSTER = ROOT / "roster.md"
STATE_DIR = ROOT / "state"
PAGES = STATE_DIR / "pages.json"
SNAP_DIR = STATE_DIR / "pages"
ITEMS = STATE_DIR / "items.jsonl"
POLL_LOG = STATE_DIR / "poll.log"

UA = {"User-Agent": "daily-reader/0.1 (personal page watcher)"}
TIMEOUT = 20
BODY_CAP = 8000  # same cap as poller article bodies


class ContentExtractor(HTMLParser):
    """Collect text inside <div id="content">, tracking div nesting.

    whole_doc=True collects all text instead (script/style still skipped) —
    the fallback for pages with no content div (paulgraham.com is table-era
    HTML; its nav is images, so whole-document text is the essay list).
    """

    # Block boundaries become line breaks so diffs stay line-granular even
    # in table-era HTML whose source has no newlines between cells (else a
    # new PG essay diffs as "the whole one-line list changed").
    BREAKS = {"br", "p", "tr", "td", "li", "table", "ul", "ol",
              "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self, whole_doc=False):
        super().__init__()
        self.depth = 1 if whole_doc else 0  # div depth inside content div
        self.whole_doc = whole_doc
        self.skip = 0         # script/style nesting
        self.chunks = []

    def _break(self, tag):
        if self.depth and not self.skip and tag in self.BREAKS:
            self.chunks.append("\n")

    def handle_starttag(self, tag, attrs):
        if tag == "div" and not self.whole_doc:
            if self.depth:
                self.depth += 1
            elif dict(attrs).get("id") == "content":
                self.depth = 1
        elif self.depth and tag in ("script", "style"):
            self.skip += 1
        self._break(tag)

    def handle_endtag(self, tag):
        if tag == "div" and not self.whole_doc and self.depth:
            self.depth -= 1
        elif tag in ("script", "style") and self.skip:
            self.skip -= 1
        self._break(tag)

    def handle_data(self, data):
        if self.depth and not self.skip:
            self.chunks.append(data)


def extract_text(html):
    """Content-div text (whole-document fallback) as normalized lines."""
    p = ContentExtractor()
    p.feed(html)
    if not "".join(p.chunks).strip():
        p = ContentExtractor(whole_doc=True)
        p.feed(html)
    lines = [re.sub(r"\s+", " ", l).strip()
             for l in "".join(p.chunks).splitlines()]
    return "\n".join(l for l in lines if l)


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def parse_watchlist():
    rows, section = [], None
    for line in ROSTER.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        if section != "page watch" or not line.startswith("|") \
                or set(line) <= {"|", "-", " "}:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 4 and cells[3] == "active" \
                and cells[2].startswith("http") and cells[0] != "Creator":
            rows.append({"creator": cells[0], "page": cells[1], "url": cells[2]})
    return rows


def added_lines(old_text, new_text):
    diff = difflib.ndiff(old_text.splitlines(), new_text.splitlines())
    return "\n".join(l[2:] for l in diff if l.startswith("+ "))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true",
                    help="store current page text without emitting")
    ap.add_argument("--dry-run", action="store_true",
                    help="detect and report; write nothing")
    args = ap.parse_args()

    pages = parse_watchlist()
    if not pages:
        print("WATCH: no active rows in '## Page watch' — nothing to do")
        return

    STATE_DIR.mkdir(exist_ok=True)
    SNAP_DIR.mkdir(exist_ok=True)
    state = json.loads(PAGES.read_text(encoding="utf-8")) if PAGES.exists() else {}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_items, log_lines = [], []
    degraded = changed = armed = 0

    for pg in pages:
        label = f"page:{pg['page']}"
        try:
            resp = requests.get(pg["url"], headers=UA, timeout=TIMEOUT)
            resp.raise_for_status()
            text = extract_text(resp.text)
            if not text:
                raise ValueError("content div empty or missing")
        except Exception as e:
            degraded += 1
            log_lines.append(f"{now} | {label} | DEGRADED: {e}")
            continue

        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        # Slug from URL, not page label — labels collide (four rows named
        # "Home") and a shared snapshot file diffs against the wrong site.
        snap = SNAP_DIR / f"{slugify(re.sub(r'^https?://', '', pg['url']))}.txt"
        known = state.get(pg["url"])

        if known is None or args.baseline:
            armed += 1
            log_lines.append(f"{now} | {label} | OK | baselined")
        elif digest != known["hash"]:
            changed += 1
            old_text = snap.read_text(encoding="utf-8") if snap.exists() else ""
            body = added_lines(old_text, text)[:BODY_CAP]
            new_items.append({
                "id": f"page:{pg['url']}@{digest[:12]}",
                "creator": pg["creator"],
                "kind": "article",
                "title": f"{pg['page']} page updated",
                "link": pg["url"],
                "published": now,
                "fetched": now,
                "body": body,
            })
            log_lines.append(f"{now} | {label} | OK | changed "
                             f"({len(body)} chars added)")
        else:
            log_lines.append(f"{now} | {label} | OK | unchanged")

        if not args.dry_run:
            state[pg["url"]] = {"hash": digest, "checked": now}
            snap.write_text(text, encoding="utf-8")

    if not args.dry_run:
        PAGES.write_text(json.dumps(state, indent=1), encoding="utf-8")
        with POLL_LOG.open("a", encoding="utf-8") as f:
            f.write("\n".join(log_lines) + "\n")
        if new_items:
            with ITEMS.open("a", encoding="utf-8") as f:
                for it in new_items:
                    f.write(json.dumps(it, ensure_ascii=False) + "\n")

    mode = "DRY RUN" if args.dry_run else \
           "BASELINE" if args.baseline else "WATCH"
    print(f"{mode}: {len(pages)} pages checked, {degraded} degraded, "
          f"{armed} baselined, {changed} changed")
    for it in new_items:
        # exact poller NEW format (cycle.log readers rely on it)
        print(f"  NEW [{it['kind']}] {it['creator']}: {it['title']}")

    if degraded == len(pages):
        sys.exit(1)


if __name__ == "__main__":
    main()
