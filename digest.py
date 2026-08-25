"""Turn newly polled items into a digest: bullets, dated archive, rolling view.

Usage:
    python digest.py                 digest all undigested items
    python digest.py --max-items N   digest only the N newest undigested items
                                     (older ones stay undigested for later)
    python digest.py --baseline      mark all undigested items digested without
                                     rendering or summarizing (arming)

Consumes state/items.jsonl (written by poller.py). Tracks what has already
appeared in a digest via state/digested.json. Caches one-bullet summaries per
item id in state/summaries.json so replays and re-renders never re-spend API.

Outputs:
    digest/YYYY-MM-DD-HHMM.md   dated archive file per run (the memory)
    digest/latest.html          ephemeral rolling view (30 most recent per
                                kind, Articles/Videos toggle defaulting to
                                Articles, NEW markers for this run's items)
"""

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent
STATE_DIR = ROOT / "state"
ITEMS = STATE_DIR / "items.jsonl"
DIGESTED = STATE_DIR / "digested.json"
SUMMARIES = STATE_DIR / "summaries.json"
DIGEST_DIR = ROOT / "digest"
ROLLING_COUNT = 30

BULLET_MODEL = "claude-haiku-4-5"  # goal.md: cheapest adequate model for bullets
BULLET_PROMPT = (
    "Write exactly one bullet point (max 25 words, plain text, no emoji, no "
    "leading dash) stating what this article is about. Be concrete and "
    "factual; name the specific subject, not the genre.\n\n"
    "Title: {title}\n\nArticle text:\n{body}"
)


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


# Title junk stripping (red-pen 2026-07-27). Display-only: items.jsonl keeps
# the raw feed title. Hashtag rule needs a pile of 2+ letter-initial tags so
# issue numbers like "#594" survive; emoji class includes VS-16 and ZWJ so
# compound emoji strip fully.
EMOJI = re.compile("[\U0001F000-\U0001FBFF☀-➿⬀-⯿️‍]")


def clean_title(title):
    title = re.sub(r"(\s+#[A-Za-z]\w*){2,}\s*$", "", title)
    return re.sub(r"\s+", " ", EMOJI.sub("", title)).strip()


def get_client():
    key = (ROOT / ".env").read_text(encoding="utf-8").strip().split("=", 1)[1]
    return anthropic.Anthropic(api_key=key)


def make_bullet(client, item):
    body = strip_html(item.get("body", ""))[:4000]
    if not body:
        return None  # title-only per goal.md: never fabricate
    resp = client.messages.create(
        model=BULLET_MODEL,
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": BULLET_PROMPT.format(title=item["title"], body=body),
        }],
    )
    text = next((b.text for b in resp.content if b.type == "text"), "").strip()
    usage = resp.usage.input_tokens, resp.usage.output_tokens
    return (text or None), usage


def creator_short(item):
    return item["creator"].split(" (")[0].strip()


# Max window slots per creator (added 2026-08-01, James's call: "we can
# always remove it"). Observed failure: one AI Engineer conference batch
# held 9 of 15 slots under pure recency. Archive files stay uncapped —
# the cap is window-representation policy, not memory policy.
CREATOR_CAP = 3


def rolling_window(items, count=ROLLING_COUNT, cap=CREATOR_CAP):
    """Strict recency, then per-creator cap: newest first, items beyond a
    creator's `cap` are skipped, window fills to `count`."""
    per, out = {}, []
    for it in sorted((i for i in items if i.get("published")),
                     key=lambda i: i["published"], reverse=True):
        c = creator_short(it)
        if per.get(c, 0) >= cap:
            continue
        per[c] = per.get(c, 0) + 1
        out.append(it)
        if len(out) >= count:
            break
    return out


def render_archive(cycle_items, summaries, stamp):
    lines = [f"# Daily Reader digest — {stamp}", ""]
    if not cycle_items:
        lines.append("Nothing new this cycle. Go stretch.")
    for it in cycle_items:
        pub = (it.get("published") or "")[:10]
        title = clean_title(it["title"])
        if it["kind"] == "video":
            lines.append(f"- [VID] {creator_short(it)} — [{title}]({it['link']}) ({pub})")
        else:
            lines.append(f"- [ART] {creator_short(it)} — [{title}]({it['link']}) ({pub})")
            b = summaries.get(it["id"])
            lines.append(f"  - {b}" if b else "  - (no article text in feed — title only)")
    lines.append("")
    return "\n".join(lines)


def added_local(it):
    """Fetched timestamp (stored UTC) as local-time 'mm-dd hh:mm'."""
    f = it.get("fetched")
    if not f:
        return ""
    t = datetime.fromisoformat(f.replace("Z", "+00:00")).astimezone()
    return t.strftime("%m-%d %H:%M")


def render_rolling(all_items, summaries, new_ids, stamp):
    # One full window per kind (not a filtered mixed window): each toggle
    # state shows ROLLING_COUNT items of that kind. Default view is Articles.
    def row(it):
        new = '<span class="new">NEW</span> ' if it["id"] in new_ids else ""
        kind_label = "Video" if it["kind"] == "video" else "Article"
        kind_class = "kind-video" if it["kind"] == "video" else "kind-article"
        pub = (it.get("published") or "")[:10]
        added = added_local(it)
        added_html = f" &middot; added {added}" if added else ""
        bullet = summaries.get(it["id"], "")
        bullet_html = f'<div class="bullet">{html.escape(bullet)}</div>' if bullet else ""
        return (
            f'<div class="item">{new}'
            f'<span class="creator">{html.escape(creator_short(it))}</span> '
            f'<span class="date">{pub}{added_html}</span><br>'
            f'<a href="{html.escape(it["link"])}">{html.escape(clean_title(it["title"]))}</a> '
            f'<span class="kind {kind_class}">{kind_label}</span>'
            f'{bullet_html}</div>'
        )

    art_rows = "".join(row(i) for i in
                       rolling_window([i for i in all_items if i["kind"] != "video"]))
    vid_rows = "".join(row(i) for i in
                       rolling_window([i for i in all_items if i["kind"] == "video"]))
    return f"""<!doctype html><meta charset="utf-8">
<title>Daily Reader</title>
<style>
body {{ font-family: Segoe UI, sans-serif; max-width: 720px; margin: 2rem auto;
       line-height: 1.5; padding: 0 1rem; }}
.item {{ margin-bottom: 1.1rem; }}
.creator {{ font-weight: 600; }}
.date {{ color: #888; font-size: 0.85em; }}
.new {{ background: #1a5276; color: #fff; font-size: 0.75em; padding: 1px 5px;
        border-radius: 3px; font-family: Consolas, monospace; }}
.kind {{ font-family: Consolas, monospace; font-size: 0.75em; padding: 1px 6px;
        border-radius: 3px; margin-left: 4px; display: inline-block; vertical-align: middle; }}
.kind-video {{ background: #c53030; color: #ffffff; font-weight: bold; }}
.kind-article {{ background: #e2e8f0; color: #2d3748; font-weight: 500; }}
.bullet {{ color: #333; font-size: 0.95em; margin-top: 2px; }}
a {{ color: #1a5276; text-decoration: none; }}
.stamp {{ color: #888; font-size: 0.85em; }}
.toggle {{ margin: 0 0 1.2rem; }}
.toggle button {{ font-family: Segoe UI, sans-serif; font-size: 0.9em;
        padding: 4px 14px; border: 1px solid #1a5276; background: #fff;
        color: #1a5276; cursor: pointer; }}
.toggle button:first-child {{ border-radius: 4px 0 0 4px; border-right: none; }}
.toggle button:last-child {{ border-radius: 0 4px 4px 0; }}
.toggle button.active {{ background: #1a5276; color: #fff; }}
</style>
<p class="stamp">Refreshed {stamp[:10]} at {stamp[11:]} US Eastern</p>
<div class="toggle">
<button id="btn-articles" class="active" onclick="show('articles')">Articles</button>
<button id="btn-videos" onclick="show('videos')">Videos</button>
</div>
<div id="articles">{art_rows}</div>
<div id="videos" style="display:none">{vid_rows}</div>
<script>
function show(which) {{
  document.getElementById('articles').style.display = which === 'articles' ? 'block' : 'none';
  document.getElementById('videos').style.display = which === 'videos' ? 'block' : 'none';
  document.getElementById('btn-articles').classList.toggle('active', which === 'articles');
  document.getElementById('btn-videos').classList.toggle('active', which === 'videos');
}}
</script>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-items", type=int, default=None)
    ap.add_argument("--baseline", action="store_true")
    args = ap.parse_args()

    all_items = [json.loads(l) for l in ITEMS.read_text(encoding="utf-8").splitlines()] \
        if ITEMS.exists() else []
    # Shorts excluded by policy (red-pen 2026-07-27). Poller no longer emits
    # them; this filter also retires the ones already in the append-only store.
    all_items = [i for i in all_items if "/shorts/" not in i.get("link", "")]
    digested = set(load_json(DIGESTED, []))
    summaries = load_json(SUMMARIES, {})

    undigested = [i for i in all_items if i["id"] not in digested]
    undigested.sort(key=lambda i: i.get("published") or "", reverse=True)

    if args.baseline:
        digested.update(i["id"] for i in undigested)
        DIGESTED.write_text(json.dumps(sorted(digested)), encoding="utf-8")
        print(f"BASELINE: marked {len(undigested)} items digested without rendering")
        return

    cycle_items = undigested[: args.max_items] if args.max_items else undigested

    in_tok = out_tok = calls = 0
    if any(i["kind"] == "article" and i["id"] not in summaries for i in cycle_items):
        client = get_client()
        for it in cycle_items:
            if it["kind"] != "article" or it["id"] in summaries:
                continue
            result = make_bullet(client, it)
            if result is None:
                continue
            bullet, (ti, to) = result
            if bullet:
                summaries[it["id"]] = bullet
            calls += 1
            in_tok += ti
            out_tok += to
        SUMMARIES.write_text(
            json.dumps(summaries, ensure_ascii=False, indent=1), encoding="utf-8")

    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")
    DIGEST_DIR.mkdir(exist_ok=True)
    archive_path = DIGEST_DIR / now.strftime("%Y-%m-%d-%H%M.md")
    archive_path.write_text(
        render_archive(cycle_items, summaries, stamp), encoding="utf-8")

    digested.update(i["id"] for i in cycle_items)
    DIGESTED.write_text(json.dumps(sorted(digested)), encoding="utf-8")

    new_ids = {i["id"] for i in cycle_items}
    shown = [i for i in all_items if i["id"] in digested]
    (DIGEST_DIR / "latest.html").write_text(
        render_rolling(shown, summaries, new_ids, stamp), encoding="utf-8")

    cost = in_tok / 1e6 * 1.00 + out_tok / 1e6 * 5.00  # haiku-4-5 $1/$5 per MTok
    print(f"CYCLE {stamp}: {len(cycle_items)} items digested "
          f"({sum(1 for i in cycle_items if i['kind'] == 'article')} articles, "
          f"{sum(1 for i in cycle_items if i['kind'] == 'video')} videos), "
          f"{calls} API calls, {in_tok}/{out_tok} tokens, ~${cost:.4f}")
    print(f"archive: {archive_path.name}  |  view: digest/latest.html")


if __name__ == "__main__":
    main()
