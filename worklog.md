# Worklog — Daily Reader

Append-only. Newest at bottom.

## 2026-07-27 — Session 1 (planning interview)

- Reviewed Jason Liu Codex-method source material: goal-file anatomy from
  snaps (drum-transcription example), method details from transcript.
  Key adoptions: goal = verification not tasks; agent drafts goal, human
  edits; goal.md editable mid-run for scope changes; plan/state/worklog split
  by mutation rules.
- Reframed project: creator-centric follow-list, not email triage. Two jobs:
  release calendar for trusted roster; aggregators as discovery engines
  (mining deferred).
- Gmail scanning declined — email dropped as transport entirely. RSS chosen
  for both mediums.
- Roster collected via screenshots + dictation: 21 Substacks, 7 YouTube
  channels. Reddit deferred by user ("we've got enough to work with").
- User constraints captured: easy-to-edit beats done-right (roster = plain
  markdown); digest every ~3 waking hours (doubles as break reminder);
  all-text, title + exactly one bullet; paragraph middle layer gates video;
  desktop icon access; notification channel = iterate over time, toast first.
- Drafted goal.md, plan.md, state.md, worklog.md, roster.md for review.
- User direction pre-review: verification must support backtesting and fast
  iteration. Added backtest verifier to goal.md (replay trailing 14 days from
  feed-carried history into 3h cycle buckets; frozen feed fixtures become the
  permanent regression set; summaries cached per item ID) and Phase 2.5 to
  plan.md. Live 48h window remains the final proof; backtest gates it.

## 2026-07-27 — Session 1 (continued): red-pen round 1

- Location decided: Desktop\workshop\daily-reader. Scaffolded via project-kit
  (CLAUDE.md), state files moved in from scratchpad.
- Red-pen correction from goal review: killed the desktop-icon/permanent-
  fixture model. Reading surface must be ephemeral (ding -> scan -> close,
  no unread state, no save/star/read-later); durable half is a passive
  archive of dated markdown digests on disk, greppable later. Distinction
  recorded: email rejected as INTAKE transport, still a candidate DELIVERY
  channel experiment. goal.md and plan.md updated accordingly.

## 2026-07-27 — Session 1 (continued): red-pen round 2

- Cut the video paragraph-summary layer from v1 entirely. Videos = creator +
  title, no generated summary, no API spend, no transcribe-pipeline
  dependency. Rationale: roster membership already encodes trust; name +
  title gates the watch decision. Summarize-on-demand parked in plan.md
  future goals. goal.md, plan.md, CLAUDE.md updated.

## 2026-07-27 — Session 1 (continued): red-pen round 3

- Verifier sections reviewed and liked. Surfacing mechanics decided: toast
  ding fires EVERY cycle (break clock), not just on new items. Rendered view
  changed from cycle-report to rolling window: most recent 15 items, newest
  first, NEW markers for this cycle — skipped dings never strand items,
  quiet cycles still offer backlog. Archive stays per-cycle. goal.md and
  plan.md updated.

## 2026-07-27 — Session 1 (continued): approval + Phase 0

- goal.md APPROVED by James after round 3.
- Phase 0 roster hardening executed:
  - YouTube: all 7 handles resolved to channel IDs, every RSS feed fetched
    and title-verified. Two initial mis-resolutions caught BY the title check
    (petergyang guess hit "Harry Patrick"; MLST first grab hit "Yannic
    Kilcher" via a related-channel link) — canonical-link extraction fixed
    MLST; web search fixed Peter Yang (real handle @peteryangyt).
  - Substack: 19 of 21 publications feed-verified with matching titles.
    Truncated names resolved: Secure Trajectories by Sondera, Strange Loop
    Canon, The Roots of Progress, Agentic AI (kenhuangus), Think Like A Game
    Designer (justingarydesign, via web search).
  - Open confirms for James: Data Engineering Weekly vs Central (both exist);
    Oana (unidentifiable from first name alone).
  - Tooling notes: Git Bash grep -P unusable (locale); Substack titles are
    CDATA-wrapped — parse with Python regex. Substack serves plain curl fine.
- roster.md rewritten with verified feed URLs, titles, and dated status.

## 2026-07-27 — Session 1 (continued): gaps dropped

- Per James: all unresolved roster entries dropped rather than chased —
  Data Engineering (Weekly/Central ambiguity), Oana, and both maybes
  (@OpenAIDevs, @jxnlcol). Rationale: roster churn is expected and constant
  over the coming weeks; gaps get re-added by the owner, not researched by
  the system. Roster now 26 entries, 100% feed-verified.

## 2026-07-27 — Session 1 (continued): method extracted, Phase 1 start

- METHOD: framework extracted to workshop\_status\templates\goal-method.md
  per James — the trial stays in this project, the reusable anatomy lives
  with the other workshop templates. Convention adopted: method observations
  in this worklog get a METHOD: prefix for later retro-grep.
- METHOD: observation from Phase 0 — the "verify titles, not HTTP 200s"
  check caught two silent wrong-channel resolutions immediately. Verifiers
  that compare content beat verifiers that check existence.
- Phase 1 (poller + state) started.

## 2026-07-27 — Session 1 (continued): Phase 1 complete

- poller.py built: parses roster.md tables (active rows only), fetches all
  feeds (requests + feedparser, 20s timeout, custom UA), diffs per-feed seen
  sets (state/seen.json), appends emissions to state/items.jsonl, logs every
  fetch to state/poll.log. --baseline flag arms without emitting. Degraded
  feeds logged and skipped, never fatal (goal blocker rule).
- Phase 1 exit test PASSED: run 1 = 26/26 sources OK, 0 degraded, 464 items
  emitted (359 articles, 105 videos, published 2023-07-17 -> 2026-07-27,
  capped ~20/feed by feed depth). Run 2 = 0 new, 0 repeats.
- Judgment call flagged, not baked in: cross-platform creator dedupe is
  specified in goal.md but NOT yet implemented — currently impossible to
  trigger because every roster creator has exactly one outlet listed (Nate/
  Lenny/Every are YouTube-only on the roster; their newsletters are not
  subscribed). Implement when a second outlet actually appears, test then.
- Next: Phase 2 (summarize + render).

## 2026-07-27 — Session 1 (continued): Phase 2 complete

- API key: found in archived/glean-health/.env, verified live via free
  count_tokens call, copied to project .env (gitignored by convention).
- digest.py built: consumes items.jsonl, tracks digested ids, generates
  article one-bullets via claude-haiku-4-5 (goal's cheapest-adequate default,
  $1/$5 per MTok per claude-api skill), caches per item id in
  state/summaries.json, writes dated markdown archive per run in digest\,
  renders rolling latest.html (recent 15, NEW markers). --baseline arms
  without rendering; --max-items caps a run.
- Phase 2 exit test PASSED: real mixed cycle of 15 items (2 articles + 13
  videos) rendered correctly with real bullets. Evidence: 2 API calls,
  1973 in / 67 out tokens, ~$0.0023. Remaining 449 items baselined.
- Note: first digest included the Jason Liu video this project came from
  (via Peter Yang's channel).
- Next: Phase 2.5 (backtest replay + fixtures), then Phase 3 (Task
  Scheduler + toast).

## 2026-07-27 — Session 1 wind-down (context clear)

- Session paused deliberately (context ~50%). Clean state: Phases 0-2
  complete and verified; no half-finished work in flight.
- Decisions this session (all in goal.md/plan.md): API stays for bullets
  (robustness of unattended credential beats pennies; consumption experiment:
  state\cycle.log vs Console per-key curve, key exclusive to this project).
- METHOD: first cold-resume test of the four-file method is the NEXT session.
  Judge it by: can a fresh session read CLAUDE.md -> state.md -> plan.md and
  start Phase 2.5 without re-reading this worklog or re-asking James anything?
- RESUME POINT: Phase 2.5 — freeze all 26 roster feeds as raw XML fixtures
  in fixtures\ with capture timestamp, replay trailing 14 days into 3h cycle
  buckets, generate retroactive digest series, run goal.md backtest verifier
  (coverage, dedupe, forms). Summaries cache means replay only pays for
  articles not already in state\summaries.json. Then Phase 3 (Task Scheduler
  6x daily 07-22, toast EVERY cycle, tee output to state\cycle.log), then
  Phase 4 (48h live verifier incl. roster hot-edit test), then result.md.

## 2026-07-27 — Session 2: digest red-pen round 1 (Shorts killed)

- METHOD: cold-resume test result, honest score: state.md + plan.md + CLAUDE.md
  were sufficient to know WHAT to do next (Phase 2.5), but plan.md carried a
  stale instruction — Phase 2.5 still said "summarize at least three real
  videos from transcripts," which predates the round-2 video-summary cut.
  Detectable only via worklog or goal.md. Lesson: a scope cut must sweep ALL
  phase sections of plan.md, not just the phase it lands in. (Stale line
  still in plan.md; fix queued behind red-pen.)
- Red-pen decision (James): YouTube Shorts eliminated entirely — "they're
  trying to game our feed." Evidence supported it: 43 of 105 stored videos
  (41%) were Shorts (Every 13, Lenny 12, Peter Yang 10, Nate 8).
- Implementation: poller.py skips /shorts/ links at emit (still marks them
  seen; logs "N shorts skipped" per feed); digest.py filters /shorts/ out of
  the store on load, retiring the 43 already ingested. Detection is the
  /shorts/ URL — YouTube RSS carries no duration field, so a Short served
  under a watch?v= link would slip through (accepted limitation, none
  observed in the 105-video corpus).
- Verified this session: poll cycle 26/26 OK, 0 degraded, 0 new (nothing
  fresh since yesterday). latest.html re-rendered from the digested set:
  421 non-short items, 9 of yesterday's 15 cycle items survive with NEW
  markers, 0 /shorts/ links in output.
- Red-pen continues one item at a time; Shorts was item one. Fixtures NOT
  yet frozen — format still cheap to change.

## 2026-07-27 — Session 2: red-pen round 2 (title junk stripped)

- Evidence sweep before writing the regex: of 421 non-short items, 0 had
  trailing hashtag piles (all were on the killed Shorts) and 41 had emoji
  (Exponential View 20 — house-style leading 🔮; DataPulse Weekly 19 —
  trailing 📊 etc.; Latent.Space 2).
- clean_title() added to digest.py, display-only (items.jsonl keeps raw
  titles; transform stays cheap to retune pre-freeze). Two rules: strip a
  trailing pile of 2+ letter-initial hashtags (digit-start tags like EV's
  "#594" issue numbers survive; rule kept despite 0 current hits as a guard
  for future videos); strip emoji incl. VS-16/ZWJ so compound emoji (🕵️‍♂️)
  go fully. Applied in both render_archive and render_rolling.
- Verified: all 41 emoji titles clean correctly (spot-checked list), #594
  preserved, hashtag pile test case strips, re-rendered latest.html has 0
  emoji chars. Existing dated archive 2026-07-27-0745.md left as-is —
  faithful record of cycle 1; the backtest replay regenerates the canonical
  series later anyway.
- Red-pen item 3 (steady-state NEW preview) satisfied incidentally: the
  re-rendered view already shows the mixed state (9 NEW, 6 unmarked).
  Next open item: creator grouping vs strict recency (owner's call).

## 2026-07-27 — Session 2: red-pen rounds 4-5, format FINAL

- Round 4 (James): strict recency only, no creator grouping — "we're not
  trying to embed too much information." Matches existing behavior; no code
  change. Recorded as a format ruling, not just a default.
- Round 5 closed under the same minimal-information principle: day-only
  dates stay; ordering already carries sequence.
- Stale plan.md Phase 2.5 line fixed (transcript-summary instruction removed;
  predates the 2026-07-27 video-summary cut).
- Digest format is now FINAL for v1: strict recency, 15-item rolling window,
  NEW markers, [ART]/[VID] kinds, day-only dates, clean_title junk stripping,
  no Shorts, articles = title + one bullet, videos = creator + title.
  This is the format the fixtures regression baseline will freeze.

## 2026-07-27 — Session 2: Phase 2.5 COMPLETE, backtest verifier PASS

- Freeze approved by James after format finalized. backtest.py built: one
  file, two modes. --freeze captures raw feed XML to fixtures\ with
  manifest.json (all-or-nothing; aborts and removes partial captures on any
  failure; refuses to run if manifest exists — refresh must be a deliberate
  manual delete). Replay mode imports poller.py extraction and digest.py
  rendering/summarization so the backtest exercises PRODUCTION code paths;
  live state (seen/items/digested) untouched, only summaries.json shared.
- Frozen: 26/26 feeds at 2026-07-27T12:13:51Z, 464 raw entries, ~12.4 MB.
- Replay run 1: 74 items in the 14-day window (43 articles, 31 videos)
  bucketed into 84 scheduled cycles (43 non-empty, 41 empty rendered and
  labeled). 41 uncached article bullets generated: 41 calls, 35904/1507
  tokens, ~$0.0434. ALL SIX CHECKS PASS: coverage 74/74 exactly once,
  dedupe 0 repeats, cross-platform N/A (26 creators all single-outlet —
  recorded, untestable until a second outlet exists), forms 0 violations,
  0 emoji, 0 Shorts links. Spot-checked 2026-07-24-1300.md visually:
  article has exactly one bullet, five videos bare.
- Replay run 2 (regression-loop proof): identical PASS, 0 API calls, $0.
- Honest depth limits logged in report: AI Engineer, Nate B Jones, and
  Every are depth-limited (Every's 15 entries reach back only 1 day —
  13 of 15 were Shorts). Report: backtest\report.md.
- Session hygiene: earlier entries this session were misdated 2026-07-28
  (today is 2026-07-27; morning and afternoon were the same day). Swept and
  corrected across worklog/state/plan/CLAUDE.md/code comments before the
  wrong date fossilized. Caught by reading the generated report's dates
  against the manifest — generated artifacts audit the author.
- Next: Phase 3 — Task Scheduler 6x daily 07-22, toast EVERY cycle,
  tee cycle output incl. per-cycle cost line to state\cycle.log.

## 2026-07-27 — Session 2: Phase 3 built and registered

- cycle.py built: runs poller then digest as subprocesses, tees both outputs
  (incl. digest's per-cycle cost line) to state\cycle.log, fires a toast
  EVERY cycle — named items (max 3 + "+N more", cleaned titles) or "Quiet
  cycle. Go stretch." Click opens digest\latest.html via protocol
  activation. Toast failure is logged, never fatal.
- toast.ps1: zero-dependency WinRT toast on PS 5.1, ASCII-only file; the
  XML payload is written by Python to state\toast.xml as UTF-8 and loaded
  from disk, so unicode titles never cross a PS 5.1 command line (JAMESTOWN
  encoding trap). Displays under PowerShell's AppId for v1 — channel
  identity is an iterate-over-time question per goal.md.
- Task Scheduler: "daily-reader" registered — daily 07:00, repeat every
  180 min for 15h = fires 07/10/13/16/19/22, interactive-only as james
  (required for toasts), pythonw.exe so no console flash. Gotcha hit and
  noted: Git Bash mangles schtasks /flags into paths — MSYS_NO_PATHCONV=1.
- Verified this session: direct run (exit 0, cycle.log block 08:20, toast
  rc=0) AND scheduler-fired run (schtasks /Run -> Last Result 0, cycle.log
  block 08:21, empty cycle archived + labeled, toast rc=0). Both cycles
  were quiet — 26/26 polled, 0 new.
- NOT yet verified (needs James's eyes / elapsed time): toast visually
  appeared and ding sounded; click opens latest.html in browser; Phase 3
  exit = unattended cycles fire on schedule a full day. Next natural fire:
  today 10:00. The 48h Phase 4 verifier window can ride on the same clock
  once Phase 3 exit is observed.

## 2026-07-27 — Session 2: live toast test with James watching

- Confirmed by James: toast appears; click opens latest.html and he likes
  what he sees. NOT confirmed: the ding — no sound despite the audio
  element in the toast XML. Parked as a known issue in state.md (suspects:
  per-app notification sound for the PowerShell AppId, or Focus Assist).
  James: fine to worry about later.
- James observation on the rolling view: mostly videos, AI Engineer
  dominating. Investigated with receipts — see state.md observation note:
  AI Engineer uploaded 15 talks in 7 days (conference-batch cadence), and
  under strict recency the top-15 window spans only ~1.9 days, so the
  fastest publisher holds 9 of 15 slots. Roster-wide 7-day mix is actually
  balanced: 24 videos / 23 articles. Structural consequence of the strict-
  recency ruling, recorded without action; levers listed in state.md.

## 2026-07-27 — Session 2: out-of-cycle peek shortcut

- Per James ("cheat a little... just want to quickly pull it up"): desktop
  shortcut "Daily Reader.lnk" with global hotkey Ctrl+Alt+D -> opens
  digest\latest.html in the browser. Verified created, hotkey registered.
- Method-file honesty note: red-pen round 1 killed the desktop icon AS A
  READING FIXTURE (persistent surface, unread state). This shortcut is a
  LAUNCHER — the surface it opens is still ephemeral, still holds no state.
  The distinction is deliberate, not a scope reversal.
- Second gear if wanted (already exists, nothing built): a full out-of-cycle
  run incl. fresh poll and real ding = schtasks /Run /TN daily-reader
  (~1 min to fire).

## 2026-07-27 — Session 2 wind-down: BUILD COMPLETE, verifier clock running

- James's verdict: "a well-done project... closure with some notes but a
  full product." Agreed on the build; per goal.md's own bar, result.md
  waits for the 48h primary verifier, which now runs passively — nothing
  left to build, only elapsed time plus one human act (hot-edit test:
  James hand-adds a creator line to roster.md mid-window).
- v1 shipped totals: 2 sessions, 2 context windows, ~$0.09 API spend
  (bullets incl. backtest), 26 sources, scheduled 6x daily, backtest
  verifier PASS, fixtures frozen as permanent regression set.
- Remaining for result.md: Phase 3 exit (one full unattended day — today),
  Phase 4 48h window checks 1-5 (coverage/links/hot-edit/cross-platform
  [N/A unless roster changes]/every-cycle archive+toast), ding known-issue
  triage (parked), then write result.md quoting cycle.log evidence.
- METHOD: retro at wind-down, James's verdict on the trial: "worked really
  well." Observations worth carrying to the template:
  - Goal-as-verifier caught real bugs twice (title-vs-200 check in Phase 0;
    forms/coverage checks in backtest). Verify content, not existence.
  - Backtest-before-live inverted the usual wait: 14 days of confidence in
    one morning, and fixtures + summary cache made rerunning free ($0 run 2).
  - Red-pen rounds (one kill per round) produced sharp scope cuts with no
    relitigating: Shorts, junk titles, grouping, dates — four rulings in
    under an hour, each recorded with rationale.
  - Cold-resume test: 3 files sufficed for WHAT next; stale plan.md line
    showed scope cuts must sweep the whole plan. Method survives context
    clears — this entire session ran without replaying session 1.
  - Generated artifacts audit the author: the backtest report's dates
    exposed my own misdating of the session.
- System is LIVE and autonomous from here. Next session: read the evidence,
  close the goal.
- METHOD: retro distilled into workshop\_status\templates\goal-method.md
  per James ("worried I'm not capturing the magic"): red-pen protocol
  (provenance + 5 mechanisms), honest-boundary section with confounds, and
  the next falsification test (a fuzzy-goal project). The magic is now on
  paper where forgetting can't reach it.

## 2026-07-27 — Session 3: mid-window fix — cp1252 crash in captured child stdout

- Symptom (found reading cycle.log): the 13:00 cycle logged WARN poller=1
  with UnicodeEncodeError — an emoji (U+1F4C8) in an item title crashed
  poller.py's report print. Data was intact (seen.json + items.jsonl are
  written BEFORE the report loop; the 2 items digested fine), but the toast
  parses the NEW lines from stdout, so the 13:00 toast wrongly said
  "nothing new" while 2 items shipped.
- Root cause: cycle.py captures children through a pipe; on Windows a piped
  child stdout defaults to cp1252, which can't encode emoji. Direct console
  runs never hit it (console is UTF-8), which is why manual testing missed it.
- Fix (minimum edit, cycle.py only): run_step now sets
  PYTHONIOENCODING=utf-8 in the child env, matching the UTF-8 decode already
  on the parent side. poller.py and digest.py untouched.
- Evidence: scratchpad repro of the exact mechanism — child printing U+1F4C8
  through a captured pipe: rc=1 with the identical UnicodeEncodeError
  without the env var, rc=0 with it. Backtest replay after the change:
  PASS, all 6 checks OK, 0 API calls (summary cache). Live end-to-end:
  manual cycle 2026-07-27 22:54 exit=0, archive + view + toast all fired.
- NOTE for the evidence read: the 22:54:32 cycle.log entry is this session's
  manual verification run, not a scheduled fire. The 13:00 WARN in the log
  is this bug — diagnosed and fixed, cosmetic-print only, no data loss.
- Observation (no action, watch at 07:00): the 22:54 cycle showed all 7
  YouTube feeds DEGRADED (six 404, one 500) after all were OK at 22:00.
  Probed directly: 404 regardless of user agent — YouTube's RSS endpoint
  flaking server-side, not our change. Degraded path behaves as designed
  (skip, don't mark seen, catch up on recovery). If still 404 across
  several cycles tomorrow, investigate; one flaky hour is noise.

## 2026-07-29 — Session 4: quick-add tooling (add.py) + LangChain added

- James's ask: adding a source required spinning up a Claude session just to
  resolve a YouTube channel ID. Root cause found: roster.md's header promised
  blank-URL resolution ("the system resolves and fills it") but poller.py
  never implemented it — blank rows are silently skipped. Header over-promised
  since 2026-07-27.
- LangChain added by hand this session (canonical ID UCC-lyoTfSrcJzA1ab3APAgw
  via <link rel="canonical"> on the channel page; feed title "LangChain"
  verified by fetch, 15 entries, 5 Shorts). seen.json seeded BEFORE the
  roster row landed so a scheduled cycle could not race a backlog dump into
  the digest. 27 active sources now. This add doubles as the roster
  hot-edit evidence for the 48h close-out read.
- Fix chosen (James picked from three options): add.py, a NEW file — the
  live pipeline is untouched mid-verification-window. resolve -> verify ->
  dupe-check -> baseline -> append. Baseline-by-default is the release-
  calendar semantic (no backlog dump); --backfill N is the escape hatch.
  In-cycle stub resolver NOT built; roster.md header corrected to match
  reality instead.
- Evidence: dupe guard exits 1 on @LangChain and @MachineLearningStreetTalk
  (both already rostered); dry-runs resolve @OpenAI -> UCXZCJLdBC09xxGZ6gcdrc6A
  and stratechery.com -> /feed with verified titles, nothing written.
  No backtest run — no pipeline/prompt/render change (backtest law applies
  to those only; add.py edits inputs, not the pipeline).
- NOTE: resolve_substack accepts any domain and pattern-matches /feed —
  stratechery.com (WordPress) verified fine but would land in the Substack
  table. Cosmetic mislabel, acceptable; rename the section if it grates.

## 2026-08-01 — Session 5: Patrick Collison (Substack tripwire + watch.py page watcher)

- James's ask: follow Patrick Collison. Recon found no feedable output:
  his Substack (patrickcollison.substack.com, "Mostly financial
  infrastructure, sometimes science funding") exists but has ZERO posts;
  patrickcollison.com is ~15 static topical pages behind a catch-all
  router (every path returns the same shell; /dispatches etc. serve full
  static HTML at their real paths). No YouTube. Feedless verified: 8
  common feed paths probed (all catch-all), no rel=alternate links,
  openrss.org 404. James ruled: watch both Substack and site; skip YT.
- Substack added via add.py (--name "Patrick Collison (Substack)"): feed
  verified, title 'Patrick Collison', 0 entries, baselined 0. A dormant
  tripwire — fires only if he ever posts. Identity caveat on record: an
  empty Substack with a plausible description is what a squatter looks
  like; nothing to verify against until a first post. add.py hardcodes
  status active; left as-is per James's call.
- watch.py built (NEW file, add.py philosophy): '## Page watch' roster
  section (Creator | Page | URL | Status, 15 rows, hand-editable, new
  rows auto-baseline on first sight), fetch -> extract content div
  (stdlib HTMLParser, div-depth tracked, script/style skipped) -> sha256
  -> diff vs state\pages\<slug>.txt snapshot -> emit ADDED text as the
  body of a kind-"article" item in poller's exact schema. Downstream
  (digest bullets, toast regex, rolling view) needed zero changes —
  deliberate: item carries published= so the rolling view keeps it, and
  the "  NEW [article] " print matches cycle.py's toast parse.
- cycle.py touched (the only live-pipeline change): run watch.py between
  poll and digest, merge watch_out into poll_out for the toast, include
  rc_watch in WARN + exit. Deletion-only edits emit with empty body ->
  digest's title-only fallback (never fabricate).
- Evidence: first run baselined 15/15, 0 degraded; snapshots are clean
  prose (advice.txt starts with the real page text, dispatches 113KB).
  Tamper test: rewound advice snapshot by 2 lines + recomputed stored
  hash -> --dry-run reported "1 changed" + NEW line, diff body was
  exactly the 2 lines, items.jsonl untouched (grep '"page:' count 0).
  --baseline re-armed; next run "0 changed". backtest.py PASS post-change
  (74 items, 0 API calls, all checks OK). Manual cycle 02:14 exit=0:
  28 sources polled (new Substack "OK 0 entries"), WATCH line in
  cycle.log, digest 2 items, toast rc=0.
- Watch item still live: 3 YouTube feeds 404 this cycle (Peter Yang,
  AI Engineer, LangChain) — same intermittent server-side flake as
  2026-07-27 (AI Engineer emitted fine at 22:00 yesterday). No action.
- METHOD: recon before design paid off twice — the "add Collison" ask
  looked like a one-liner but the Substack is empty and the site is
  feedless; probing first turned a wrong-tool answer (add.py alone) into
  a right-sized build (tripwire + watcher).

## 2026-08-01 — Session 5 (cont.): newsletter.py — ship the product

- Distribution question resolved by reframe: James asked for a frozen
  binary so his brother could run the system; the real blockers were the
  API key (only secret, only per-user cost) and unsigned-exe SmartScreen
  friction. Map shown (embeddable-python zip as the local-instance play,
  hosted output as the 80%) — James collapsed it himself: "I just need a
  simple newsletter." One runner, N readers, zero install on theirs.
- newsletter.py built (NEW file, pipeline untouched): re-reads state
  (items.jsonl + digested.json + summaries.json), selects the rolling
  view's exact window (digested, dated, newest 15, Shorts filtered),
  renders plain text + minimal inline-styled HTML (multipart), sends via
  smtplib SSL. Reuses digest.py's clean_title/creator_short/load_json so
  display law can't drift. Deliberately ugly by request.
- .env trap caught before it fired: digest.py get_client reads .env as a
  SINGLE-LINE file (split("=",1) on whole text) — adding SMTP lines there
  would break the live pipeline. Creds go in .env.smtp instead (KEY=VALUE
  per line, parsed properly). Documented in both files' docstrings.
- Also: workshop root is NOT a git repo despite the session snapshot
  claiming so (disk is the authority) — no gitignore work needed for
  .env.smtp; it is a local secret like .env.
- Evidence: --dry-run against live state rendered all 15 window items,
  format law holds (ART title + cached bullet, VID creator + title only),
  preview at digest\newsletter-preview.html, nothing sent.
- BLOCKED (only James can unblock): app password for the sending account
  (Yahoo app password path documented in state.md), brother's email
  address. Then: test send --to self, verify receipt, register weekly
  task "daily-reader-weekly" (schtasks, Sun 08:00, pythonw). Weekly task
  deliberately NOT registered before a verified send.

## 2026-08-01 — Session 5 (cont.): Paul Graham page-watched

- James's ask: monitor paulgraham.com too. Recon: the canonical PG RSS
  (Aaron Swartz's scraped pgessays.rss on aaronsw.com) is ALIVE but STALE
  — newest item Superlinear Returns (Oct 2023); articles.html has ~12
  newer essays (Founder Mode, The Origins of Wokeness, How to Earn a
  Billion Dollars...). Stale feed rejected; page-watch is the live path.
- watch.py generalized for table-era HTML (two changes): (1) whole-doc
  extraction fallback when no <div id="content"> exists — PG's nav is
  images, so whole-page text is essentially the essay list; (2) block
  tags (br/p/tr/td/li/table/h*) now emit line breaks, else PG's list
  collapses into one mega-line and a new essay diffs as "everything
  changed" with an 8000-char body. Snapshot shape changed -> all 16
  pages re-baselined (--baseline emits nothing; no false fires).
- Roster row added by hand: Paul Graham | Essays | articles.html.
  Provenance note in roster '## Page watch' header (stale-feed ruling).
- Evidence: baseline 16/16, second run "0 changed" twice (page is
  static, no dynamic churn); essays.txt is one title per line (239
  lines); Collison snapshots unaffected (advice.txt prose intact).
  Tamper test — removed "How to Earn a Billion Dollars" from snapshot,
  recomputed hash: dry-run "1 changed" + NEW line, and added_lines
  returned exactly 'How to Earn a Billion Dollars'. A future PG essay
  will hit the digest carrying its own title. Re-baselined, quiet.
- No backtest run: watch.py is outside the fixture replay path and
  poller/digest/cycle untouched this pass (backtest law applies to
  pipeline/prompt/render changes; extractor is upstream of the store).

## 2026-08-01 — Session 5 (cont.): the feedless-by-choice cohort (8 adds)

- James: "add them all, they're easy to remove." Eight candidates from the
  exploratory sweep, all verified by probe before rostering — which caught
  two more zombie feeds: Gwern's rss.xml AND his Substack both died June
  2021 (newsletter discontinued; the site lives on), so Gwern is
  page-watched via gwern.net/changelog, not feed-polled. Dan Luu's
  atom.xml is valid but has an EMPTY title — add.py's verify_feed would
  refuse it; poller doesn't care (never reads titles). Noted in roster.
- Feeds added (hand-rows in the Substack table; section preamble now
  documents that any http feed URL belongs there and the section name is
  load-bearing for parse_roster — never rename): Dan Luu (128 entries),
  antirez (100), Bret Victor (11). All baselined via add.baseline BEFORE
  the roster rows landed (LangChain race-avoidance precedent).
- Pages added: Norvig, Bellard, Moxie, Taleb (homepages), Gwern
  (changelog). BUG caught in verification: snapshot filenames were
  slugged from the page LABEL — four rows named "Home" shared one
  snapshot file, so diff bodies would compare against the wrong site
  (hash detection was unaffected; pages.json is URL-keyed). Fixed: slug
  from URL. All snapshots rebuilt under URL slugs, re-baselined.
- Evidence: baseline 21/21, 0 degraded; second run "0 changed" (no
  dynamic-content false-fire on any of the five new sites); per-site
  snapshots verified (norvig-com.txt = Norvig bio, bellard-org.txt =
  release news list — the intended tripwire). parse_roster: 31 feed
  sources (23 article, 8 video); parse_watchlist: 21 pages.
- Roster is now: 23 article feeds, 8 YouTube, 21 watched pages across
  8 creators' properties. Removal = flip status or delete row.

## 2026-08-01 — Session 5 (cont.): per-creator window cap

- James ruled: per-creator cap, "we can always remove it." Root itch from
  the author-click discussion: fast channels drown slow authors in the
  window (observed 2026-07-27: AI Engineer conference batch held 9/15
  slots). Author-click browse surface rejected (portal, not calendar);
  backfill ritual noted as the free add-time introduction (--backfill 3
  for essayist-cadence adds).
- Implemented as dg.rolling_window(items, count, cap): strict recency,
  skip items past a creator's cap (CREATOR_CAP=3, editable constant),
  fill to count. render_rolling and newsletter.window_items both call it
  — one function, two surfaces, no drift. Archives stay UNCAPPED (cap is
  window-representation policy, not memory policy). Creator counted via
  creator_short so outlet suffixes merge.
- Evidence: live-state comparison — uncapped window {AI Engineer: 8, 7
  others x1}; capped {AI Engineer: 3, Latent.Space 2, Agentic AI 2,
  Resilient Cyber 2, 6 others x1} = 8 -> 10 creators represented.
  backtest.py PASS post-change (74/74 coverage — archive path uncapped,
  unaffected). Newsletter dry-run regenerated: freed slots surfaced
  Resilient Cyber #108, Slopdemic, Think Like A Game Designer #108.
- Format law amended: strict recency + per-creator cap 3 (was: pure
  strict recency).

## 2026-08-03 — Thinking Machines Lab added

- James asked to add https://thinkingmachines.ai/blog/. The page advertises
  canonical RSS at https://thinkingmachines.ai/blog/index.xml; fetched 200
  application/xml, feedparser reported bozo=False, title "Connectionism on
  Thinking Machines Lab", and 7 entries.
- Added the feed as active in roster.md and the person-level ledger, then
  baselined all 7 current entry IDs in state/seen.json so only future posts
  emit. Roster now parses as 32 feeds: 24 article, 8 video.
- Correction from the post-edit parser check: the pre-existing state count
  was stale. The authoritative roster total is 33 feeds: 25 article, 8 video.

## 2026-08-05 — Quanta Magazine, Farid Zakaria, and Colin Scott added

- User requested adding https://www.quantamagazine.org/ to daily reader.
- `python add.py https://www.quantamagazine.org/` resolved URL to feed `https://www.quantamagazine.org/feed`, verified title 'Quanta Magazine' with 5 entries, appended active row to roster.md under ## Substack, and baselined all 5 current entries in state/seen.json.
- User requested adding http://fzakaria.com/ to daily reader.
- `python add.py http://fzakaria.com/ --name "Farid Zakaria"` resolved URL to feed `https://fzakaria.com/feed`, verified title 'Farid Zakaria’s Blog' with 10 entries, appended active row to roster.md under ## Substack, and baselined all 10 current entries in state/seen.json.
- User requested adding https://colin-scott.github.io/ to daily reader. Probed HTML for feed links (`<link rel="alternate" href="/atom.xml">`). Updated `add.py` `resolve_substack` to preserve explicit `.xml` feed URLs.
- `python add.py https://colin-scott.github.io/atom.xml --name "Colin Scott"` resolved to feed `https://colin-scott.github.io/atom.xml`, verified title 'site_title' with 14 entries, appended active row to roster.md under ## Substack, and baselined all 14 current entries in state/seen.json.
- Recorded additions in roster-history.md under ## Following.
- Executed `python poller.py`: 36 sources polled cleanly, 0 degraded, 0 new items emitted.
- Executed `python backtest.py`: PASS (74 items -> 84 cycles, 0 API calls).

## 2026-08-06 — Brian Krebs (Krebs on Security) added

- User requested adding Brian Krebs Bot from krebsonsecurity.com to daily reader.
- `python add.py https://krebsonsecurity.com --name "Brian Krebs (Krebs on Security)"` resolved URL to `https://krebsonsecurity.com/feed`, verified title 'Krebs on Security' with 10 entries, appended active row to `roster.md` under `## Substack`, and baselined all 10 current entries in `state/seen.json`.
- Formatted markdown tables in `roster.md` and `roster-history.md` with vertically aligned columns per layout guidelines.
- Recorded addition in `roster-history.md` under `## Following`.
- Updated coarse state table in `CLAUDE.md` and fine-grained snapshot in `state.md` (37 feeds: 29 article, 8 YouTube + 21 watched pages).

## 2026-08-08 — Stanford CodeX Projects added

- User requested adding `https://law.stanford.edu/codex-the-stanford-center-for-legal-informatics/codex-projects/#slsnav-current-projects` to daily reader.
- Verified target page has no RSS/Atom feed; website feed `https://law.stanford.edu/feed` is site-wide Stanford Law School news rather than CodeX project updates.
- Added static page watch row to `roster.md` under `## Page watch` for `Stanford CodeX` (Projects page).
- Formatted markdown tables in `roster.md` and `roster-history.md` with vertically aligned columns per layout guidelines.
- Recorded addition in `roster-history.md` under `## Following`.
- Ran `python watch.py`: checked 22 pages (0 degraded, 1 baselined, 0 changed). Stanford CodeX Projects snapshot written to `state/pages/`.
- Executed `python backtest.py`: PASS (74 items -> 84 cycles, 0 API calls).
- Updated state tables in `CLAUDE.md` and `state.md` (37 feeds + 22 watched pages).


