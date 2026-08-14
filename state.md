# State — Daily Reader

Snapshot of where things stand. Overwritten as state changes.

- Status: BUILD COMPLETE 2026-07-27, LIVE on Task Scheduler ("daily-reader",
  07/10/13/16/19/22 daily). goal.md APPROVED; phases 0-3 done; backtest
  verifier PASS (backtest\report.md). The 48h primary verifier is running
  PASSIVELY now — evidence accrues in state\cycle.log and digest\ with no
  further build work. result.md is NOT yet earned.
- To close the goal (next session, ~2026-07-29): verify Phase 3 exit (full
  unattended day of cycles in cycle.log), run Phase 4 checks 1-5 over the
  48h window, confirm the hot-edit test (DONE 2026-07-29: LangChain row
  added mid-window — verify a scheduled cycle polls it, 27 sources), then
  write result.md quoting evidence.
- Surfaces: toast every cycle (click opens view; confirmed working);
  Ctrl+Alt+D / desktop "Daily Reader" shortcut = out-of-cycle peek;
  schtasks /Run /TN daily-reader = full out-of-cycle run with fresh poll.
- Built: poller.py, digest.py (Haiku-4-5 bullets, cached), backtest.py
  (fixtures frozen 2026-07-27T12:13:51Z — permanent regression set, NEVER
  refresh casually; replay is free), cycle.py + toast.ps1 (scheduled cycle).
  Format for v1 (amended 2026-08-01): strict recency + per-creator cap
  (dg.CREATOR_CAP=3; archives uncapped), 15-item window, NEW markers,
  day-only dates, clean_title stripping, Shorts excluded.
- Known issues (parked): toast fires but does NOT ding — audio element is
  in the XML; suspects: per-app sound for the PowerShell AppId, Focus
  Assist. Triage after the window.
- FIXED mid-window (2026-07-27 session 3): 13:00 cycle WARN poller=1 was a
  cp1252 UnicodeEncodeError on an emoji title in the captured-pipe report
  print — no data loss, but the 13:00 toast wrongly said "nothing new".
  run_step in cycle.py now sets PYTHONIOENCODING=utf-8 for children.
  Verified: repro (rc 1 -> 0), backtest PASS post-change, manual cycle
  22:54 exit=0. The 22:54 cycle.log entry is that manual run, not a
  scheduled fire. Details in worklog session 3.
- Watch (check at 07:00 cycle): all 7 YouTube feeds DEGRADED (404/500) at
  22:54 after being OK at 22:00 — YouTube RSS endpoint flaking server-side
  (probed: 404 with any UA). Degraded path handled it correctly; only
  investigate if it persists across several cycles.
- Observation (no action): AI Engineer's conference-batch uploads hold 9 of
  15 window slots under strict recency (roster-wide 7d mix is balanced,
  24 vid / 23 art). Levers if it grates: per-creator window cap, window
  count (editable per goal.md), roster call. First data point for the
  parked per-source yield-tracking goal.
- Credentials: .env ANTHROPIC_API_KEY, exclusive to this project; Console
  per-key curve = project consumption. Spend to date ~$0.09.
- Roster: 37 feed entries (29 article-table, 8 YouTube) + 22 watched
  pages. 2026-08-01 cohort add (James: "add them all, easy to remove"):
  feeds Dan Luu (atom.xml, UNTITLED by design — add.py would refuse it,
  poller doesn't care), antirez, Bret Victor; page-watch Norvig, Bellard,
  Moxie, Taleb (homepages) + Gwern (changelog — BOTH his feeds died June
  2021) + Paul Graham articles.html (Swartz pgessays.rss STALE since Oct
  2023). Zombie-feed pattern is now 3-for-3 among feedless-by-choice
  authors: probe freshness before trusting any feed. watch.py: whole-doc
  extractor fallback, block-tag line breaks, snapshot slugs from URL not
  page label (label collision bug caught in verification — four "Home"
  rows shared one snapshot file). All 21 snapshots stable across
  double-run (no dynamic-content false fires).
  LangChain added 2026-07-29 (hot-edit test), baselined at add. Patrick
  Collison Substack added 2026-08-01 via add.py — feed verified but has 0
  posts (dormant tripwire; identity unconfirmable until he posts — if a
  first post sounds wrong, re-check before trusting). Cross-platform
  dedupe still N/A (all single-outlet). Thinking Machines Lab's
  Connectionism RSS added 2026-08-03 and baselined at 7 entries.
  Quanta Magazine RSS added 2026-08-05 and baselined at 5 entries.
  Farid Zakaria RSS added 2026-08-05 and baselined at 10 entries.
  Colin Scott Atom feed added 2026-08-05 and baselined at 14 entries.
  Brian Krebs RSS (krebsonsecurity.com/feed) added 2026-08-06 and baselined at 10 entries.
  Stanford CodeX Projects page (law.stanford.edu/codex-the-stanford-center-for-legal-informatics/codex-projects/#slsnav-current-projects) added 2026-08-08 as watched page and baselined.
- New tool (2026-08-01 session 5): watch.py — feedless-page watcher for
  patrickcollison.com (site verified feedless: catch-all router, 8 feed
  paths probed, no feed links, openrss 404; pages are static topical HTML
  that gets edited, not posted to). Reads '## Page watch' roster section
  (15 pages), hashes each page's content div, diffs against
  state\pages\<slug>.txt snapshots, emits added text as kind-"article"
  items in the poller's exact schema — digest/toast/rolling view need no
  changes. New rows auto-baseline on first sight (no backlog dump).
  cycle.py touched (only live-pipeline change): watch step between poll
  and digest, NEW lines merged into the toast parse, rc in exit/WARN.
  Verified: 15 pages baselined; tamper test detected a rewound snapshot
  (dry-run, 1 changed, correct diff body, nothing written); backtest PASS
  post-change; manual cycle 2026-08-01 02:14 exit=0 with WATCH line in
  cycle.log and toast rc=0.
- New tool (2026-07-29 session 4): add.py — quick-add without a Claude
  session (resolve -> verify -> dupe-check -> baseline -> append;
  --backfill N / --dry-run / --name). New file; pipeline untouched.
  roster.md header corrected: blank-URL resolution was promised but never
  built — rows without a channel ID are skipped, not resolved.
- Method trial: James's verdict "worked really well" — retro observations
  in worklog wind-down entry, tagged METHOD: for retro-grep.
- Newsletter (2026-08-01 session 5, BUILT, NOT YET LIVE): ship-the-product
  distribution ruled over frozen-binary after James's pivot — one runner,
  N readers, nothing installed on theirs. newsletter.py renders the
  rolling window's exact selection (digested + dated, newest 15) as plain
  text + minimal HTML email via smtplib. Dry-run verified against live
  state (15 items, format law holds). BLOCKED on: (1) .env.smtp creds —
  James must generate an app password (Yahoo: account security -> app
  passwords); NOT .env, digest.py reads .env as a single-line file;
  (2) brother's email (not in addresses.md); (3) verified test send to
  self, then weekly Task Scheduler registration (e.g. schtasks weekly Sun
  08:00, task "daily-reader-weekly", pythonw newsletter.py).
- Open decisions: newsletter send account + recipient (above). Otherwise
  the clock is the only dependency.
