# Plan — Daily Reader

Current strategy for reaching goal.md. Freely rewritten as we learn.

## Phase 0 — Scaffold and roster hardening

- Scaffold project folder (project-kit) with the five state files.
- Resolve truncated Substack names (Data Engineering..., Secure Trajectori...,
  Strange Loop C..., The Roots of Pr..., Oana) against Substack.
- Collect and verify a working feed URL for every roster entry (Substack
  /feed, YouTube channel_id RSS). Record fetch status per entry in roster.md.
- Exit: every roster line has a verified feed URL or an explicit "unresolved"
  flag.

## Phase 1 — Poller and state

- Cycle script: read roster.md, fetch all feeds, diff against stored state
  (last-seen item IDs per feed), emit new items.
- Creator-level dedupe map for multi-outlet creators.
- Exit: two consecutive manual runs produce correct new-item diffs and no
  repeats.

## Phase 2 — Summarize and render

- Articles: one-bullet generation from feed-carried text (Claude API, cheap
  model). Videos: creator + title only, no API.
- Digest artifact: dated markdown per cycle in digest\; ephemeral rendered
  view generated from it. Links to sources. Empty-cycle rendering.
- Exit: a real mixed cycle (articles + at least one video) renders correctly.

## Phase 2.5 — Backtest replay (goal.md backtest verifier)

- Freeze all roster feeds to fixtures\ with capture timestamp.
- Replay trailing 14 days (or feed depth) into 3-hour cycle buckets; generate
  the retroactive digest series; run coverage + dedupe checks. Cache
  summaries per item ID. (Video transcript summaries cut from v1 2026-07-27
  — videos are creator + title only; Shorts excluded entirely 2026-07-27.)
- Write the backtest report. Fixtures become the permanent regression set —
  all later pipeline/prompt/render changes re-run and diff against them first.
- Exit: backtest verifier in goal.md passes.

## Phase 3 — Schedule and surface

- Task Scheduler job: every 3h, 07:00-22:00. Windows toast EVERY cycle (break
  clock; empty cycles labeled); click opens the rendered rolling view (most
  recent 15, NEW markers), closing leaves no state.
- Cycle output (incl. per-cycle API cost line) teed to state\cycle.log —
  stdout vanishes under Task Scheduler; the cost log is the local half of the
  owner's consumption-pattern experiment (Console per-key usage = other half;
  key is exclusive to this project, so Console curve = daily-reader).
- Digest archive: dated markdown per cycle in digest\; rolling view assembled
  from the archive tail.
- Exit: unattended cycles fire on schedule for a full day.

## Phase 4 — Verifier window

- Run the goal.md primary verifier over 48 hours, including the roster
  hot-edit test. Fix what fails, append evidence to worklog.md, write
  result.md when it passes.

## Future goals (not this goal.md)

- Video summarize-on-demand: click a video item -> transcribe pipeline ->
  paragraph summary. Cut from v1 on 2026-07-27 (creator + title is the gate).
- Reddit top-N digests. Aggregator source-mining (Data Elixir cutout).
- Per-source yield tracking to drive prune/breed decisions.
- Notification channel experiments (phone text, email). Audio/TTS digest.
- Spotify-only podcast creators.
