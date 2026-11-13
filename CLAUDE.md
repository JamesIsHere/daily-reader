# daily-reader

## Purpose

A release calendar for a hand-curated roster of creators (Substack + YouTube +
feedless static pages via watch.py), run locally. Polls the roster's RSS feeds, detects new releases, and produces
an all-text digest every ~3 waking hours (articles: title + exactly one
bullet; videos: creator + title only). "Working" means the goal.md verifiers pass: backtest replay over
the trailing two weeks, then a live 48-hour window. The project is also a
trial of the goal/plan/state/worklog method (Jason Liu, Codex) — judge the
method by how this project goes.

## State

| Field        | Value                                                                                              |
| ------------ | -------------------------------------------------------------------------------------------------- |
| Status       | LIVE, once a day at midnight (James, 2026-11-13; was 6 a day), healthy (611 runs logged; 4 WARNs since 10-14, all publish/watch, none fatal)  |
| Last session | 2026-11-13 — review; Stanford CodeX page-watch removed (251 of 256 fires were the page flipping)   |
| Next action  | pop-up fix (cause CONFIRMED 2026-11-13): CREATE_NO_WINDOW on the toast powershell call (cycle.py) and vercel.CMD call (publish.py); re-run the window recording during a manual run and expect zero new windows |

state.md is the fine-grained snapshot; this table is the coarse one. Keep both
honest at wind-down. (state.md not yet rewritten for the 2026-11-13 session.)

Open decisions (need James; he asked to take these one at a time after the pop-up fix):
- Toast every run even when nothing is new: with one run at midnight, the toast fires at midnight;
  keep it, cut it, or move it.
- Window ordering: interleave sources so one source never sits in a block.
- Teaser-only bodies (88 of 275 articles in 30 days under 300 chars): fetch full pages for bullets?
- Older parked: restart of the 48h verifier window; newsletter send account and recipient.

Unsure about:
- Pop-up cause no longer inferred: a window recording during the manual run at 2026-11-13 15:53
  caught two Windows Terminal windows, "cmd.exe" at 15:54:22 (vercel.CMD from publish.py) and
  "powershell.exe" at 15:54:27 (toast from cycle.py). The recorder script was session scratch;
  rebuild it if needed (EnumWindows every 100 ms, log handles not in the starting set).
- The 3 existing CodeX items stay in the article window until newer items push them out; the
  append-only store was not edited.

## How to run

From the project root, in order:

    python cycle.py              one full scheduled cycle: poll + digest +
                                 cycle.log + toast (what Task Scheduler runs
                                 as "daily-reader", once daily at 00:00
                                 since 2026-11-13; was 6x daily 07-22;
                                 runs at next logon if midnight is missed)
    python poller.py             one poll cycle (fetch, diff, emit new items)
    python digest.py             digest undigested items: bullets + archive +
                                 rolling view (--max-items N caps; --baseline
                                 arms without rendering)
    python add.py @Handle        quick-add a source: resolve (YouTube handle
                                 -> channel ID, or Substack URL -> /feed),
                                 verify the feed, append the roster row,
                                 baseline so no backlog dump (--backfill N,
                                 --dry-run, --name)
    python watch.py              one page-watch cycle: fetch '## Page watch'
                                 roster pages, hash the content div, diff
                                 against state\pages\ snapshots, emit changed
                                 pages as items (--baseline re-arms all;
                                 --dry-run detects without writing; new rows
                                 auto-baseline on first sight)
    python publish.py            mirror digest\latest.html (+ explore\
                                 corpus.html) to the Vercel mirror (URL =
                                 https://<projectName>.vercel.app, projectName
                                 in publish\.vercel\project.json, gitignored)
                                 for the iPhone home-screen icon:
                                 inject mobile/PWA head tags on the COPY
                                 (digest.py untouched), deploy publish\
                                 (--dry-run builds without deploying); runs
                                 automatically at the end of every cycle,
                                 guarded on publish\.vercel\project.json,
                                 failure logged but never fatal
    python newsletter.py         email the rolling window (last 15 digested
                                 items) to MAIL_TO; creds in .env.smtp — NOT
                                 .env, digest.py reads .env as a single-line
                                 file (--dry-run renders digest\newsletter-
                                 preview.html + prints text, sends nothing;
                                 --to overrides recipients for test sends)
    python backtest.py           replay fixtures through the 14-day backtest
                                 verifier; run after ANY pipeline/prompt/render
                                 change, before touching live (--freeze is
                                 one-shot, already done 2026-07-27; it refuses
                                 to overwrite an existing corpus)

State in state\ (seen.json, items.jsonl, digested.json, summaries.json,
poll.log). Digests in digest\ (dated .md archive + latest.html view).
Requires .env with ANTHROPIC_API_KEY (bullets via claude-haiku-4-5).

## explore/

Free exploratory and research area (declared 2026-08-01). Anything goes
here: pull data, chart it, follow curiosity. Two boundaries only:

- Read-only toward the live pipeline: explore/ scripts may read roster.md
  and state\, but write nothing outside explore\.
- Descriptive, not normative: findings here do not become rules, roster
  edits, or pipeline changes by themselves — those route through James.

Current contents: pull_history.py (per-source publication history to
explore\data\, Substack archive API + feeds, 24-month window, raw pulls
cached in data\raw\ behind a REFRESH flag) and corpus_dashboard.py
(-> corpus.html, tabbed self-contained HTML per the dashboard skill).
Rebuild: python pull_history.py && python corpus_dashboard.py.

## rollout/

Recipient-facing docs for sharing the Vercel mirror: phone-setup
(add-to-home-screen directions) and sources (human-readable roster
snapshot, dated — refresh it when the roster changes meaningfully).
Each is .md source + .pdf; PDFs regenerate via one-off scripts (session
scratchpad), not by hand-editing.

## Method files

| File       | Mutation rule                                              |
| ---------- | ---------------------------------------------------------- |
| goal.md    | edited rarely and deliberately — scope changes only        |
| plan.md    | current strategy, freely rewritten                         |
| state.md   | current snapshot, overwritten each session                 |
| worklog.md | append-only, never rewritten                               |
| roster.md  | hand-editable source of truth; adding a creator = one line |
| roster-history.md | person-level ledger: follows + cuts with dates and short reasons; every roster.md creator add/remove gets a dated line here, same session; not rendered anywhere yet (future: newsletter footer) |
| result.md  | created only after goal.md completion proof is met         |

## Gotchas

- roster.md is the source of truth and must stay trivially hand-editable —
  any design that adds a registration step beyond editing the file violates
  goal.md.
- Digest format law: title + exactly ONE bullet per item. Not three.
- Email is not a transport (deliberate — Gmail access declined). RSS only.
- Cross-platform creators (Nate B Jones, Lenny, Every) must dedupe at the
  creator level or the same piece appears twice.
- YouTube Shorts are excluded by policy (red-pen 2026-07-27): poller skips
  /shorts/ links at emit, digest filters them from the store on load. Feed
  entry counts will exceed emit counts for Shorts-heavy channels — that is
  the filter working, not a bug.
- fixtures\ (once created) is a frozen regression corpus — never refresh it
  casually; a refresh invalidates every prior diff baseline.
- ../transcribe is NOT a v1 dependency (video summaries were cut 2026-07-27);
  it is reserved for the future summarize-on-demand goal. Never modify that
  project from here.

## Rules for agents

- Do not report success, sync, or completion unless you have run the
  relevant command this session and are quoting its output.
- Generated files (digests, fixtures, backtest reports) are regenerated,
  never hand-edited.
- Judgment calls get flagged (`confirm`-style), not silently baked in.
- When sources disagree, record the disagreement — both values, with
  provenance.
- Secrets live in `.env` (gitignored); never in tracked files.
- The Vercel mirror is public-but-obscure by accepted trade-off
  (2026-08-01): anyone with the URL can read the digest. To keep the
  obscure half intact, the URL itself never appears in tracked files
  (ruled 2026-08-13, at GitHub publication) — it lives only in
  publish\.vercel\project.json (gitignored): https://<projectName>
  .vercel.app. Auth lives in the Vercel CLI's user login; no token in
  the repo.
