"""Weekly newsletter: email the rolling window (last 30 digested items).

Usage:
    python newsletter.py --dry-run     render to digest/newsletter-preview.html
                                       and print the text part; no send, no
                                       credentials needed
    python newsletter.py               render and send to every TO recipient
    python newsletter.py --to a@b.c    override recipients (test sends)

Ship-the-product distribution (ruled 2026-08-01): one runner (this machine),
N readers, nothing to install on theirs. Item selection: digested items with
a published date, newest first, top 30, articles and videos mixed. Since
2026-08-24 latest.html renders per-kind windows behind an Articles/Videos
toggle, so the email is the union view, not a literal mirror of the page.

Credentials live in .env.smtp (gitignored), NOT .env: digest.py reads .env
as a single-line file and a second line would break get_client. Format,
one KEY=VALUE per line:

    SMTP_HOST=smtp.mail.yahoo.com
    SMTP_PORT=465
    SMTP_USER=you@yahoo.com
    SMTP_PASS=<app password, not the account password>
    MAIL_FROM=you@yahoo.com
    MAIL_TO=brother@example.com,you@yahoo.com

Deliberately ugly: plain text + one minimal HTML part, no images, no
tracking, no unsubscribe theater. The digest law holds: title + the cached
one-bullet summary; videos are creator + title only. Sends re-read only
state files — the live pipeline is untouched (add.py philosophy).
"""

import argparse
import html
import json
import smtplib
import ssl
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import digest as dg

ROOT = Path(__file__).parent
STATE_DIR = ROOT / "state"
ITEMS = STATE_DIR / "items.jsonl"
DIGESTED = STATE_DIR / "digested.json"
SUMMARIES = STATE_DIR / "summaries.json"
SMTP_ENV = ROOT / ".env.smtp"
PREVIEW = ROOT / "digest" / "newsletter-preview.html"
SEND_LOG = STATE_DIR / "newsletter.log"
COUNT = 30


def load_config():
    if not SMTP_ENV.exists():
        sys.exit("ERROR: .env.smtp missing (see module docstring for format)")
    cfg = {}
    for line in SMTP_ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            cfg[k.strip()] = v.strip()
    missing = [k for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS",
                           "MAIL_FROM", "MAIL_TO") if not cfg.get(k)]
    if missing:
        sys.exit(f"ERROR: .env.smtp missing keys: {', '.join(missing)}")
    return cfg


def window_items():
    """The rolling view's exact selection, via digest.rolling_window (strict
    recency + per-creator cap) so the two surfaces can never drift."""
    if not ITEMS.exists():
        sys.exit("ERROR: no items store yet")
    all_items = [json.loads(l)
                 for l in ITEMS.read_text(encoding="utf-8").splitlines()]
    all_items = [i for i in all_items if "/shorts/" not in i.get("link", "")]
    digested = set(dg.load_json(DIGESTED, []))
    shown = [i for i in all_items if i["id"] in digested]
    return dg.rolling_window(shown, count=COUNT), dg.load_json(SUMMARIES, {})


def render_text(items, summaries, stamp):
    lines = [f"Daily Reader — week of {stamp}",
             f"Most recent {len(items)} releases", ""]
    for it in items:
        kind = "VID" if it["kind"] == "video" else "ART"
        pub = (it.get("published") or "")[:10]
        lines.append(f"[{kind}] {dg.creator_short(it)} — "
                     f"{dg.clean_title(it['title'])} ({pub})")
        b = summaries.get(it["id"])
        if b:
            lines.append(f"      {b}")
        lines.append(f"      {it['link']}")
        lines.append("")
    lines.append("-- sent by daily-reader, one ugly cron email a week")
    return "\n".join(lines)


def render_html(items, summaries, stamp):
    rows = []
    for it in items:
        kind = "VID" if it["kind"] == "video" else "ART"
        pub = (it.get("published") or "")[:10]
        b = summaries.get(it["id"])
        bullet = (f'<div style="color:#333;margin-top:2px">{html.escape(b)}</div>'
                  if b else "")
        rows.append(
            f'<div style="margin-bottom:14px">'
            f'<span style="font-family:monospace;color:#888">[{kind}]</span> '
            f'<b>{html.escape(dg.creator_short(it))}</b> '
            f'<span style="color:#888;font-size:0.85em">{pub}</span><br>'
            f'<a href="{html.escape(it["link"])}" style="color:#1a5276">'
            f'{html.escape(dg.clean_title(it["title"]))}</a>{bullet}</div>')
    return (f'<div style="font-family:Segoe UI,sans-serif;max-width:720px;'
            f'line-height:1.5">'
            f'<h2 style="font-size:1.15em">Daily Reader — week of {stamp}</h2>'
            f'<p style="color:#888;font-size:0.85em">most recent {len(items)} '
            f'releases</p>{"".join(rows)}</div>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="render preview + print text part; no send")
    ap.add_argument("--to", help="comma-separated recipient override")
    args = ap.parse_args()

    items, summaries = window_items()
    if not items:
        sys.exit("ERROR: rolling window is empty — nothing to send")
    stamp = datetime.now().strftime("%Y-%m-%d")
    text = render_text(items, summaries, stamp)
    body_html = render_html(items, summaries, stamp)

    if args.dry_run:
        PREVIEW.parent.mkdir(exist_ok=True)
        PREVIEW.write_text(body_html, encoding="utf-8")
        print(text)
        print(f"\nDRY RUN: nothing sent; HTML preview at {PREVIEW}")
        return

    cfg = load_config()
    recipients = [r.strip() for r in
                  (args.to or cfg["MAIL_TO"]).split(",") if r.strip()]
    msg = EmailMessage()
    msg["Subject"] = f"Daily Reader — week of {stamp}"
    msg["From"] = cfg["MAIL_FROM"]
    msg["To"] = ", ".join(recipients)
    msg.set_content(text)
    msg.add_alternative(body_html, subtype="html")

    with smtplib.SMTP_SSL(cfg["SMTP_HOST"], int(cfg["SMTP_PORT"]),
                          context=ssl.create_default_context()) as s:
        s.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
        s.send_message(msg)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with SEND_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{now} | sent {len(items)} items to {len(recipients)} "
                f"recipient(s): {', '.join(recipients)}\n")
    print(f"SENT: {len(items)} items to {', '.join(recipients)}")


if __name__ == "__main__":
    main()
