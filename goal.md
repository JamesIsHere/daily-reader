# Daily Reader

## Outcome

Build and verify a locally-run release calendar for a hand-curated roster of
creators (Substack publications and YouTube channels). The system polls the
roster's feeds on a fixed cycle, detects new releases, and produces an all-text
digest every ~3 waking hours. Articles are a title plus exactly one bullet.
Video items are creator plus title only — no generated summary; a roster
creator's name and title are the gate on watching. Transcript-derived
summaries (automatic or on-click via the transcribe pipeline) are a parked
future goal, added later by editing this file.

The reading surface is ephemeral: a ding, a scan, a close — no persistent
fixture, no unread state, nothing to maintain. The durable half is a passive
archive: every digest saved as a dated markdown file on disk, greppable later
when something half-remembered needs finding. Scanning is the mode; the
archive is the only memory.

The roster file is the source of truth and must remain trivially hand-editable:
adding a creator is adding a line, with no other registration step.

## Baseline

- roster.md exists: 21 Substack publications, 7 YouTube channels, 2 maybes.
  Several Substack names are truncated from a screenshot and need resolution;
  feed URLs are not yet collected.
- A working transcript pipeline exists at Desktop\workshop\transcribe
  (yt video -> cleaned transcript -> summary artifacts). NOT used in v1 —
  reserved for the future summarize-on-demand goal.
- Host: Windows 11 (JAMESTOWN), Python 3.14, PowerShell 5.1, Task Scheduler
  available for the 3-hour cycle.
- Gmail/email is NOT a transport — access declined by design. Substack is
  reached via per-publication RSS, YouTube via per-channel RSS. No platform
  API keys at baseline.
- Reddit, Spotify-only podcasts, and aggregator source-mining are out of scope
  for v1 (recorded as future goals in roster.md).

## Constraints and quality bar

- All-text digest. Articles: title + exactly one bullet — never more.
  Videos: creator + title, nothing else.
- Progressive disclosure: bullet/title -> source (click). No intermediate
  summary layers in v1.
- Dedupe at the creator level: a creator with multiple outlets (e.g. Nate B
  Jones on YouTube + Substack) appears once per piece of content, not once
  per feed.
- The cycle fires on schedule even when empty, and so does the ding — the
  pulse is also a break reminder. An empty cycle says so plainly; the view
  still shows the rolling recent window.
- If article text cannot be retrieved (feed error, empty feed body), the item
  appears as title-only with the failure noted. Never fabricate a summary for
  content that was not actually fetched.
- Only content the user's subscriptions legitimately expose. No paywall or
  DRM bypass; paid-post handling is deferred until it actually bites.
- No emojis anywhere in output. Plain-text markers only.
- No permanence in the reading surface: no save, star, or read-later features,
  no unread counts, no persistent window. The dated digest files on disk are
  the only memory; going back = reading the markdown history.

## Decision defaults

- Substack intake: name.substack.com/feed RSS. YouTube intake: per-channel RSS
  (no API key). Poll each cycle; new = published since last recorded state.
- Summaries: Claude API, article one-bullets only (feed-carried text as input;
  cheapest adequate model). Videos consume no API. Consult the claude-api
  skill at build time for current models/pricing; do not hardcode from memory.
- Digest artifact: a dated markdown file per cycle in digest\ (the archive,
  source of truth). A rendered ephemeral view (browser tab opened on demand,
  holding no state) is generated from it for scanning.
- Surfacing v1: Windows toast ding fires EVERY cycle — with new items it names
  them; with none it says so plainly (the ding is also the break clock).
  Clicking opens the rendered digest; closing it leaves nothing behind.
  AMENDED 2026-11-13 (James: "delete everything toast", too annoying): the
  toast is removed. No notification surface exists; the view, the Vercel
  mirror and the archive are the surfaces. Every ding/toast clause in this
  file (the empty-cycle pulse above, Phase 4 check 5's toast half, the
  toast deliverable) is void from this date.
  Email-to-self, phone text, and other channels are logged as future
  experiments — the channel question is explicitly iterate-over-time, not a
  v1 decision.
- Rendered view: a rolling window of the most recent 15 items (count
  editable), newest first, this cycle's arrivals marked NEW. Never an empty
  screen while the roster has any recent history — skipped cycles stay
  scannable, and a quiet cycle still offers the backlog.
- Cadence: every 3 hours, 07:00-22:00, via Task Scheduler.

## Allowed without asking

- Read public RSS feeds and public web pages for roster sources.
- Install Python packages per-user; create and update files inside the project
  directory and scratchpad.
- Register/modify the project's own scheduled task and toast notifications.
- Call the Claude API for summarization within a small per-cycle budget.

## Approval required

- Any outbound channel beyond a local toast (SMS, email, anything leaving the
  machine).
- Material API spend changes (new models, per-cycle cost growth).
- System-wide installs or writes outside the project directory.
- Dropping a roster source from coverage for implementation convenience.

## Forbidden

- Modifying unrelated user files, the transcribe pipeline's existing outputs,
  or other workshop projects.
- Bypassing paywalls, DRM, or access controls.
- Fabricating or padding summaries for unfetched content.
- Weakening the verifier or silently narrowing roster coverage to make the
  goal pass.

## Backtest verifier (must pass before the live window)

RSS feeds carry their own recent history (Substack ~20 latest posts, YouTube
~15 latest videos), so verification starts with a replay, not a wait:

1. Capture every roster feed once; store the raw XML on disk as a frozen
   fixture corpus with capture timestamp.
2. Replay the trailing 14 days (or the feed's full exposed depth if shorter,
   logging the actual span per source): bucket each item into the 3-hour
   cycle it would have landed in and generate the full digest series
   retroactively.
3. Coverage: every item in the window appears in exactly one digest in its
   correct form (article: title + one bullet; video: creator + title); a
   cross-platform release appears once.
4. The frozen corpus is the permanent regression set: any later change to
   pipeline, prompts, or rendering re-runs against fixtures and diffs the
   digest output before touching live. Summaries are cached per item ID so
   replays do not re-spend API.

Known limits, recorded rather than hidden: feed depth caps how far back the
replay reaches on prolific sources; notification timing cannot be backtested,
only cycle bucketing.

## Primary verifier (live)

Over a 48-hour test window with the scheduled task live:

1. Every item published by a roster feed during the window appears in the next
   digest after its publication, in its correct form (article: title + one
   bullet; video: creator + title).
2. Every digest item links correctly to its source (article page / video).
3. A hot-edit test passes: add a new creator line to roster.md mid-window with
   no other action; their next release appears in a subsequent digest.
4. A cross-platform creator releasing one piece appears once, not twice.
5. Every scheduled cycle in the window produced a dated digest file in the
   archive (empty cycles included and labeled) and fired a toast ding (empty
   cycles labeled as such); the ding's click opened the rendered rolling view
   (most recent 15, NEW markers correct); closing that view left no
   persistent state behind.

## Supporting checks

- Per-cycle poll log: every roster entry checked every cycle, with fetch
  status recorded.
- No item ever re-surfaces as new in a later digest (state dedupe holds).
- Digest renders as plain readable text with no broken click-throughs.
- Cycle runtime stays well under the 3-hour period; API cost per cycle logged.

## Completion proof

- Project directory containing roster.md (all truncated names resolved, feed
  URLs verified fetchable for every entry), the poller/summarizer/renderer
  code, and state files.
- fixtures\ directory with the frozen feed corpus and a backtest report
  showing the replayed digest series and coverage results per source.
- digest\ archive of dated markdown files covering at least one full day of
  real cycles, plus the rendered ephemeral view they generate.
- Registered Task Scheduler job and working toast notification.
- worklog.md recording the 48-hour verifier window, including the hot-edit
  test.
- result.md written only after the primary verifier passes.

## Iteration and recovery

For each phase: inspect current evidence, make one bounded change, run the
nearest check, record the result in worklog.md, update state.md. If a feed,
transcript, or model call fails, try a compatible alternative without reducing
roster coverage. Preserve failed-attempt evidence when it explains a fallback.

## Blocker rule

Difficulty, long processing time, model uncertainty, or a failed first attempt
are not blockers. An external blocker requires concrete evidence, no remaining
safe fallback, and the same blocking condition across three consecutive goal
turns. A single unreachable feed is never a blocker for the system — mark the
source degraded in the digest and continue.

## State files

- plan.md — current strategy, freely rewritten
- state.md — current state snapshot
- worklog.md — append-only history
- roster.md — hand-editable source of truth for who is followed
- result.md — created only after completion
