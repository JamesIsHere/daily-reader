r"""Backtest verifier (goal.md): freeze fixtures, replay, check, report.

Usage:
    python backtest.py --freeze    capture every roster feed's raw XML into
                                   fixtures\ with a manifest (one-shot; the
                                   corpus is the permanent regression set —
                                   never refresh casually, a refresh
                                   invalidates every prior diff baseline)
    python backtest.py             replay trailing 14 days from fixtures into
                                   3-hour cycle buckets, render the
                                   retroactive digest series, run coverage /
                                   dedupe / forms checks, write the report

Replay reuses production code on purpose: item extraction from poller.py,
rendering and summarization from digest.py. Live pipeline state (seen.json,
items.jsonl, digested.json) is never touched; the only shared state is the
summaries.json cache, so replays never re-spend API on a summarized article.

Outputs:
    fixtures\<nn>-<slug>.xml + fixtures\manifest.json     (--freeze)
    backtest\digests\YYYY-MM-DD-HHMM.md                   (replay series)
    backtest\report.md                                    (verifier evidence)
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

import digest as dg
import poller as pl

ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"
MANIFEST = FIXTURES / "manifest.json"
BT_DIR = ROOT / "backtest"
BT_DIGESTS = BT_DIR / "digests"
REPORT = BT_DIR / "report.md"

WINDOW_DAYS = 14
CYCLE_HOURS = [7, 10, 13, 16, 19, 22]  # local schedule, goal.md cadence


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def freeze():
    """Capture every roster feed raw. All-or-nothing: a corpus with holes
    would silently narrow coverage (forbidden), so any failure aborts."""
    sources = pl.parse_roster()
    if len(sources) == 0:
        sys.exit("ERROR: no active sources in roster.md")
    if MANIFEST.exists():
        sys.exit("ERROR: fixtures already frozen. Refreshing invalidates all "
                 "prior diff baselines — delete fixtures\\ manually first if "
                 "that is really intended.")
    FIXTURES.mkdir(exist_ok=True)

    captured, manifest = [], []
    for n, src in enumerate(sources, 1):
        try:
            resp = requests.get(src["feed"], headers=pl.UA, timeout=pl.TIMEOUT)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
            if parsed.bozo and not parsed.entries:
                raise ValueError(f"unparseable: {parsed.bozo_exception}")
        except Exception as e:
            for f in captured:
                f.unlink()
            sys.exit(f"ERROR: {src['creator']} failed ({e}) — freeze aborted, "
                     f"partial captures removed. Fix the feed and rerun.")
        fname = f"{n:02d}-{slugify(src['creator'])}.xml"
        (FIXTURES / fname).write_bytes(resp.content)
        captured.append(FIXTURES / fname)
        manifest.append({
            "creator": src["creator"], "kind": src["kind"], "feed": src["feed"],
            "file": fname, "bytes": len(resp.content),
            "entries": len(parsed.entries),
        })
        print(f"  frozen {fname}: {len(parsed.entries)} entries, "
              f"{len(resp.content)} bytes")

    capture_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    MANIFEST.write_text(json.dumps(
        {"capture_utc": capture_utc, "sources": manifest},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"FROZEN: {len(manifest)} feeds at {capture_utc} -> fixtures\\")


def fixture_items(manifest):
    """Extract items from frozen XML via the same rules poller.py applies
    live (id, published, body, Shorts exclusion)."""
    items, shorts = [], 0
    for src in manifest["sources"]:
        parsed = feedparser.parse((FIXTURES / src["file"]).read_bytes())
        for e in parsed.entries:
            if src["kind"] == "video" and "/shorts/" in e.get("link", ""):
                shorts += 1
                continue
            items.append({
                "id": pl.entry_id(e),
                "creator": src["creator"], "kind": src["kind"],
                "title": e.get("title", "(untitled)"),
                "link": e.get("link", ""),
                "published": pl.entry_published(e),
                "body": pl.entry_body(e)[:8000] if src["kind"] == "article" else "",
            })
    return items, shorts


def cycle_for(pub_local):
    """First scheduled cycle at or after publication (next-day 07:00 for
    anything after the 22:00 cycle — overnight items ride the morning ding)."""
    for h in CYCLE_HOURS:
        c = pub_local.replace(hour=h, minute=0, second=0, microsecond=0)
        if c >= pub_local:
            return c
    return (pub_local + timedelta(days=1)).replace(
        hour=CYCLE_HOURS[0], minute=0, second=0, microsecond=0)


def replay():
    if not MANIFEST.exists():
        sys.exit("ERROR: no fixtures. Run: python backtest.py --freeze")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    capture = datetime.strptime(
        manifest["capture_utc"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc).astimezone()
    win_start = capture - timedelta(days=WINDOW_DAYS)

    all_items, shorts_excluded = fixture_items(manifest)

    # Per-source span: how far back the feed's exposed depth actually reaches
    # (goal.md known limit — log it, don't hide it).
    spans = {}
    for src in manifest["sources"]:
        pubs = sorted(i["published"] for i in all_items
                      if i["creator"] == src["creator"] and i["published"])
        spans[src["creator"]] = {
            "entries": src["entries"],
            "earliest": pubs[0] if pubs else None,
            "latest": pubs[-1] if pubs else None,
            "depth_limited": bool(pubs) and pubs[0] > win_start.astimezone(
                timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    undated = [i for i in all_items if not i["published"]]
    dated = [i for i in all_items if i["published"]]
    windowed = []
    for i in dated:
        pub = datetime.strptime(i["published"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc).astimezone()
        if win_start <= pub <= capture:
            i["_pub_local"] = pub
            windowed.append(i)

    # Bucket into the cycle each item would have landed in.
    buckets = {}
    for i in windowed:
        buckets.setdefault(cycle_for(i["_pub_local"]), []).append(i)

    # Summaries: cache first, API only for uncached windowed articles.
    summaries = dg.load_json(dg.SUMMARIES, {})
    need = [i for i in windowed
            if i["kind"] == "article" and i["id"] not in summaries]
    print(f"window: {len(windowed)} items ({len(need)} articles need bullets, "
          f"{sum(1 for i in windowed if i['kind'] == 'article') - len(need)} cached)")
    in_tok = out_tok = calls = 0
    if need:
        client = dg.get_client()
        for it in need:
            result = dg.make_bullet(client, it)
            if result is None:
                continue  # no feed body -> title-only form, never fabricated
            bullet, (ti, to) = result
            if bullet:
                summaries[it["id"]] = bullet
            calls, in_tok, out_tok = calls + 1, in_tok + ti, out_tok + to
        dg.SUMMARIES.write_text(
            json.dumps(summaries, ensure_ascii=False, indent=1),
            encoding="utf-8")
    cost = in_tok / 1e6 * 1.00 + out_tok / 1e6 * 5.00

    # Render the FULL retroactive series — every scheduled cycle in the
    # window, empty ones included (that is what live would have produced).
    BT_DIGESTS.mkdir(parents=True, exist_ok=True)
    for old in BT_DIGESTS.glob("*.md"):
        old.unlink()  # regenerated, never hand-edited
    first_cycle = cycle_for(win_start)
    cycles, c = [], first_cycle
    while c <= capture:
        cycles.append(c)
        idx = CYCLE_HOURS.index(c.hour)
        c = (c + timedelta(days=1)).replace(hour=CYCLE_HOURS[0]) \
            if idx == len(CYCLE_HOURS) - 1 \
            else c.replace(hour=CYCLE_HOURS[idx + 1])
    for c in cycles:
        cycle_items = sorted(buckets.get(c, []),
                             key=lambda i: i["published"], reverse=True)
        stamp = c.strftime("%Y-%m-%d %H:%M")
        (BT_DIGESTS / c.strftime("%Y-%m-%d-%H%M.md")).write_text(
            dg.render_archive(cycle_items, summaries, stamp),
            encoding="utf-8")

    checks = run_checks(windowed, buckets, cycles, summaries, manifest)
    write_report(manifest, capture, win_start, spans, all_items, windowed,
                 undated, shorts_excluded, buckets, cycles, checks,
                 calls, in_tok, out_tok, cost)

    status = "PASS" if all(ok for ok, _ in checks.values()) else "FAIL"
    print(f"BACKTEST {status}: {len(windowed)} items -> {len(cycles)} cycles "
          f"({sum(1 for c in cycles if buckets.get(c))} non-empty), "
          f"{calls} API calls, ~${cost:.4f}")
    for name, (ok, detail) in checks.items():
        print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    print(f"report: {REPORT.relative_to(ROOT)}")
    return status == "PASS"


def run_checks(windowed, buckets, cycles, summaries, manifest):
    """goal.md backtest verifier step 3, plus format law and output hygiene."""
    checks = {}

    # Coverage + dedupe: every windowed item in exactly one digest. Digest
    # files identify items by link (ids are not rendered), so verify link
    # uniqueness first — the count check is only sound if links are keys.
    links = [i["link"] for i in windowed]
    dup_links = len(links) - len(set(links))
    text_by_file = {p.name: p.read_text(encoding="utf-8")
                    for p in sorted(BT_DIGESTS.glob("*.md"))}
    all_text = "\n".join(text_by_file.values())
    appearances = {i["id"]: all_text.count(f"({i['link']})") for i in windowed}
    missing = [i for i in windowed if appearances[i["id"]] == 0]
    repeated = [i for i in windowed if appearances[i["id"]] > 1]
    checks["coverage"] = (
        not missing and dup_links == 0,
        f"{len(windowed) - len(missing)}/{len(windowed)} items appear; "
        f"{len(missing)} missing; {dup_links} duplicate links")
    checks["dedupe"] = (
        not repeated,
        f"{len(repeated)} items appear in more than one digest")

    # Cross-platform: verifiable only if some creator has two outlets.
    creators = {}
    for s in manifest["sources"]:
        creators.setdefault(dg.creator_short({"creator": s["creator"]}),
                            set()).add(s["kind"])
    multi = [c for c, kinds in creators.items() if len(kinds) > 1]
    checks["cross-platform"] = (
        True,
        f"N/A — no multi-outlet creators on roster ({len(creators)} creators, "
        f"all single-outlet); rule specified, untestable until one exists"
        if not multi else f"testable: {multi}")

    # Forms: article = title + exactly one bullet line; video = bare line.
    form_bad = []
    for fname, text in text_by_file.items():
        lines = text.splitlines()
        for j, line in enumerate(lines):
            nxt = lines[j + 1] if j + 1 < len(lines) else ""
            if line.startswith("- [ART] "):
                extra = lines[j + 2] if j + 2 < len(lines) else ""
                if not nxt.startswith("  - ") or extra.startswith("  - "):
                    form_bad.append(f"{fname}:{j+1} article bullet count != 1")
            elif line.startswith("- [VID] ") and nxt.startswith("  - "):
                form_bad.append(f"{fname}:{j+1} video has a bullet")
    checks["forms"] = (not form_bad,
                       f"{len(form_bad)} violations" +
                       (f" e.g. {form_bad[0]}" if form_bad else ""))

    # Output hygiene: no emoji anywhere (goal.md), no Shorts links (red-pen).
    emoji_hits = dg.EMOJI.findall(all_text)
    checks["no-emoji"] = (not emoji_hits,
                          f"{len(emoji_hits)} emoji chars in rendered output")
    checks["no-shorts"] = ("/shorts/" not in all_text,
                           f"{all_text.count('/shorts/')} Shorts links")
    return checks


def write_report(manifest, capture, win_start, spans, all_items, windowed,
                 undated, shorts_excluded, buckets, cycles, checks,
                 calls, in_tok, out_tok, cost):
    L = ["# Backtest report — daily-reader", "",
         f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by "
         f"backtest.py (regenerated, never hand-edited).", "",
         "## Corpus", "",
         f"- Frozen {manifest['capture_utc']} — {len(manifest['sources'])} "
         f"feeds, {sum(s['bytes'] for s in manifest['sources'])} bytes, "
         f"{sum(s['entries'] for s in manifest['sources'])} raw entries.",
         f"- Replay window: {win_start.strftime('%Y-%m-%d %H:%M')} -> "
         f"{capture.strftime('%Y-%m-%d %H:%M')} local ({WINDOW_DAYS} days).",
         f"- Items extracted: {len(all_items)} (+{shorts_excluded} Shorts "
         f"excluded by policy, red-pen 2026-07-27); {len(undated)} undated "
         f"items excluded from window (cannot be bucketed).",
         f"- In window: {len(windowed)} items "
         f"({sum(1 for i in windowed if i['kind'] == 'article')} articles, "
         f"{sum(1 for i in windowed if i['kind'] == 'video')} videos).",
         f"- API this replay: {calls} calls, {in_tok}/{out_tok} tokens, "
         f"~${cost:.4f} (cache absorbed the rest).", "",
         "## Verifier checks", ""]
    for name, (ok, detail) in checks.items():
        L.append(f"- {'PASS' if ok else 'FAIL'} — {name}: {detail}")
    L += ["", "## Cycle series", "",
          f"- {len(cycles)} scheduled cycles in window, "
          f"{sum(1 for c in cycles if buckets.get(c))} with items, "
          f"{sum(1 for c in cycles if not buckets.get(c))} empty (rendered "
          f"and labeled, as live would).", ""]
    for c in cycles:
        if buckets.get(c):
            L.append(f"- {c.strftime('%Y-%m-%d %H:%M')}: "
                     f"{len(buckets[c])} items")
    L += ["", "## Per-source span (feed depth vs window)", "",
          "| Source | Entries | Earliest | Latest | Window coverage |",
          "| --- | --- | --- | --- | --- |"]
    for creator, s in spans.items():
        cov = ("full 14d" if s["earliest"] and not s["depth_limited"]
               else "depth-limited" if s["earliest"] else "no dated items")
        L.append(f"| {creator} | {s['entries']} | "
                 f"{(s['earliest'] or '-')[:10]} | "
                 f"{(s['latest'] or '-')[:10]} | {cov} |")
    L += ["", "Known limit (goal.md): feed depth caps how far back prolific",
          "sources reach; notification timing is not backtestable, only",
          "cycle bucketing.", ""]
    BT_DIR.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    args = ap.parse_args()
    if args.freeze:
        freeze()
    else:
        sys.exit(0 if replay() else 1)
