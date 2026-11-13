# State -- Daily Reader

Cache for cold resume. Overwritten each wind-down; never the authority.

## Status

COMPLETE 2026-11-13 (result.md written, s9). In plain English:
- Done: the reader is built and live. Every night at midnight, Task Scheduler
  ("daily-reader", pythonw cycle.py, runs at next logon if midnight is missed)
  polls the roster's feeds and watched pages, writes Haiku bullets for new
  articles, archives a dated digest, rebuilds digest\latest.html
  (Articles/Videos toggle, 30 per kind, max 3 per creator) and publishes it to
  the Vercel mirror. No notification (removed 2026-11-13).
- Verifier: the backtest (python backtest.py) is the only one. The live test
  window was deleted 2026-11-13.
- Remaining: nothing owed to the goal. The method retro is deferred (trigger
  in worklog s9). The newsletter is built but parked.
- Final goal (met): a hand-editable roster turned into a daily text digest
  with no registration step.

## Next actions

- None required. The reader runs unattended.
- If James picks it up again, the stated reason he stopped is too little
  variety, which is a roster problem (curation), not a pipeline problem.

## Watch items and caveats

- Thinking Machines Lab feed (https://thinkingmachines.ai/blog/index.xml)
  404 since 2026-11-13 20:53Z after OK at 15:00Z; the blog page loads but
  links no feed. If it persists, the fallback is a '## Page watch' row for
  /blog/ (a roster call for James).
- Patrick Collison Substack: verified feed, 0 posts (dormant tripwire). If a
  first post sounds wrong, re-check identity before trusting it.
- The video window tops out at 24, not 30: 8 YouTube creators x CREATOR_CAP 3.
- Three Stanford CodeX "Projects page updated" items stay in the article
  window until newer items push them out (store is append-only).
- Credentials: .env ANTHROPIC_API_KEY is the Console key "daily-reader"
  (Default workspace, no expiry, created 2026-08-24). A revoked key fails
  only the digest step; publish keeps re-deploying a stale page (the
  2026-08-15 to 08-24 outage). Check cycle.log for digest 401s if the
  mirror looks frozen.
- Manual runs: schtasks /Run /TN daily-reader (the real path, pythonw);
  Ctrl+Alt+D or the desktop "Daily Reader" shortcut opens the local view.

## Open decisions

- Newsletter (parked since 2026-08-01): needs a Yahoo app password in
  .env.smtp (not .env) and the brother's email address; then a test send
  --to self and a weekly task ("daily-reader-weekly", Sun 08:00, pythonw
  newsletter.py). No rulings.md in this project (pre-dates the ledger).
