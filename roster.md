# Roster — who I follow

Source of truth. Hand-edit freely; the system re-reads this every cycle.
Quick add: `python add.py @Handle-or-URL` resolves the feed, verifies it,
appends the row, and baselines it so only future releases appear
(`--backfill N` lets the N newest items through; `--dry-run` previews).
Hand-adding a full row also works, but YouTube rows need the UC... channel
ID filled in — rows without one are skipped, not resolved.

`creator` ties outlets together for dedupe (same creator, multiple outlets ->
same creator name). Status: active | resolve (identity unconfirmed) |
degraded (feed failing).

Admission rule (ratified 2026-08-01): a row requires a trusted selector
upstream — a person, or a single editorial voice choosing what gets
released. Distribution channels don't qualify, however on-topic: if nobody
upstream is exercising judgment (unfiltered conference dumps, corporate
firehoses), the filtering lands here at read time, which is the system
doing the opposite of its job. Dormant people are fine — a silent feed is
a zero-cost tripwire. Burstiness alone is not disqualifying; voicelessness
is.

## Substack

Feed titles verified by fetch 2026-07-27. Despite the section name, any
http feed URL works here (the poller reads URL + status only) — non-
Substack feeds live in this table too; do NOT rename the section, poller
matches it literally. Dan Luu's feed is valid but untitled by design.

| Publication                               | Feed URL                                     | Verified title                         | Status |
| ----------------------------------------- | -------------------------------------------- | -------------------------------------- | ------ |
| Agentic AI (Ken Huang)                    | https://kenhuangus.substack.com/feed         | Agentic AI                             | active |
| Data Ground Up                            | https://datagroundup.substack.com/feed       | Data Ground Up                         | active |
| DataPulse Weekly                          | https://datapulseweekly.substack.com/feed    | DataPulse Weekly                       | active |
| Dramatic Analyst                          | https://dramaticanalyst.substack.com/feed    | Dramatic Analyst                       | active |
| Exponential View (Azeem Azhar)            | https://www.exponentialview.co/feed          | Exponential View                       | active |
| Granted (Adam Grant)                      | https://adamgrant.substack.com/feed          | Granted                                | active |
| Ground Truths (Eric Topol)                | https://erictopol.substack.com/feed          | Ground Truths                          | active |
| Import AI (Jack Clark)                    | https://importai.substack.com/feed           | Import AI                              | active |
| Interconnects AI (Nathan Lambert)         | https://www.interconnects.ai/feed            | Interconnects AI                       | active |
| Latent.Space                              | https://www.latent.space/feed                | Latent.Space                           | active |
| One Useful Thing (Ethan Mollick)          | https://www.oneusefulthing.org/feed          | One Useful Thing                       | active |
| Resilient Cyber                           | https://www.resilientcyber.io/feed           | Resilient Cyber                        | active |
| Secure Trajectories by Sondera            | https://securetrajectories.substack.com/feed | Secure Trajectories by Sondera         | active |
| Simon Willison's Newsletter               | https://simonw.substack.com/feed             | Simon Willison's Newsletter            | active |
| Steel and Silicon                         | https://steelandsilicon.substack.com/feed    | Steel and Silicon                      | active |
| Strange Loop Canon (Rohit Krishnan)       | https://www.strangeloopcanon.com/feed        | Strange Loop Canon                     | active |
| The AiEdge Newsletter (Damien Benveniste) | https://newsletter.theaiedge.io/feed         | The AiEdge Newsletter                  | active |
| The Roots of Progress (Jason Crawford)    | https://newsletter.rootsofprogress.org/feed  | The Roots of Progress                  | active |
| Think Like A Game Designer (Justin Gary)  | https://justingarydesign.substack.com/feed   | Think Like A Game Designer             | active |
| Patrick Collison (Substack)               | https://patrickcollison.substack.com/feed    | Patrick Collison                       | active |
| Dan Luu                                   | https://danluu.com/atom.xml                  | (untitled feed — danluu.com)           | active |
| antirez (Salvatore Sanfilippo)            | https://antirez.com/rss                      | <antirez>                              | active |
| Bret Victor                               | https://worrydream.com/feed.xml              | Bret Victor's website                  | active |
| Sergey Brin (too blog)                    | https://too.blogspot.com/feeds/posts/default | too                                    | active |
| Thinking Machines Lab                     | https://thinkingmachines.ai/blog/index.xml   | Connectionism on Thinking Machines Lab | active |
| Quanta Magazine                           | https://www.quantamagazine.org/feed          | Quanta Magazine                        | active |
| Farid Zakaria                             | https://fzakaria.com/feed                    | Farid Zakaria’s Blog                   | active |
| Colin Scott                               | https://colin-scott.github.io/atom.xml       | site_title                             | active |
| Brian Krebs (Krebs on Security)           | https://krebsonsecurity.com/feed             | Krebs on Security                      | active |

## YouTube

Channel IDs resolved from handles and feed titles verified by fetch
2026-07-27. Feed URL pattern:
https://www.youtube.com/feeds/videos.xml?channel_id=<ID>

| Creator / Channel                       | Handle                     | Channel ID               | Verified title                           | Notes                                                                     | Status |
| --------------------------------------- | -------------------------- | ------------------------ | ---------------------------------------- | ------------------------------------------------------------------------- | ------ |
| Peter Yang                              | @peteryangyt               | UCnpBg7yqNauHtlNSpOl5-cg | Peter Yang                               | also Substack: creatoreconomy.so (not subscribed there — dedupe if added) | active |
| Nate B Jones (AI News & Strategy Daily) | @NateBJones                | UC0C-17n9iuUQPylguM1d-lQ | AI News & Strategy Daily / Nate B Jones  | also natesnewsletter.substack.com — dedupe                                | active |
| Lenny's Podcast                         | @LennysPodcast             | UC6t1O76G0jYXOAoYCm153dA | Lenny's Podcast                          | also lennysnewsletter.com — dedupe                                        | active |
| AI Engineer                             | @aiDotEngineer             | UCLKPca3kwwd-B59HNr-_lvA | AI Engineer                              | bursty (conference talks)                                                 | active |
| Machine Learning Street Talk            | @MachineLearningStreetTalk | UCMLtBahI5DMrt0NPvDSoIRQ | Machine Learning Street Talk             | technical long-form                                                       | active |
| Every                                   | @EveryInc                  | UCjIMtrzxYc0lblGhmOgC_CA | Every                                    | also every.to — dedupe                                                    | active |
| Unsupervised Learning (Jacob Effron)    | @RedpointAI                | UCUl-s_Vp-Kkk_XVyDylNwLA | Unsupervised Learning: With Jacob Effron | podcast                                                                   | active |
| LangChain                               | @LangChain                 | UCC-lyoTfSrcJzA1ab3APAgw | LangChain                                | Shorts-heavy (5 of 15 feed entries); added 2026-07-29, baselined at add   | active |

## Page watch

Feedless static pages watched for edits by watch.py (fetch, hash the content
div, diff, emit the added text). New rows auto-baseline on first sight: add a
row, nothing fires until the next real edit. patrickcollison.com verified
feedless 2026-08-01 (8 feed paths probed, no feed links, openrss 404).
paulgraham.com: the Aaron Swartz scraped feed (aaronsw.com pgessays.rss)
verified STALE 2026-08-01 — newest item Superlinear Returns (Oct 2023),
page has many newer; page-watch of articles.html is the live path (no
content div there: watch.py falls back to whole-document text).

| Creator           | Page       | URL                                                                                                              | Status |
| ----------------- | ---------- | ---------------------------------------------------------------------------------------------------------------- | ------ |
| Patrick Collison  | About      | https://patrickcollison.com/about                                                                                | active |
| Patrick Collison  | Advice     | https://patrickcollison.com/advice                                                                               | active |
| Patrick Collison  | Bookshelf  | https://patrickcollison.com/bookshelf                                                                            | active |
| Patrick Collison  | Culture    | https://patrickcollison.com/culture                                                                              | active |
| Patrick Collison  | Dispatches | https://patrickcollison.com/dispatches                                                                           | active |
| Patrick Collison  | Fast       | https://patrickcollison.com/fast                                                                                 | active |
| Patrick Collison  | Growth     | https://patrickcollison.com/growth                                                                               | active |
| Patrick Collison  | Labs       | https://patrickcollison.com/labs                                                                                 | active |
| Patrick Collison  | Links      | https://patrickcollison.com/links                                                                                | active |
| Patrick Collison  | Pollution  | https://patrickcollison.com/pollution                                                                            | active |
| Patrick Collison  | Progress   | https://patrickcollison.com/progress                                                                             | active |
| Patrick Collison  | Questions  | https://patrickcollison.com/questions                                                                            | active |
| Patrick Collison  | Solar      | https://patrickcollison.com/solar                                                                                | active |
| Patrick Collison  | SV history | https://patrickcollison.com/svhistory                                                                            | active |
| Patrick Collison  | Travel     | https://patrickcollison.com/travel                                                                               | active |
| Paul Graham       | Essays     | https://paulgraham.com/articles.html                                                                             | active |
| Peter Norvig      | Home       | https://norvig.com/                                                                                              | active |
| Fabrice Bellard   | Home       | https://bellard.org/                                                                                             | active |
| Moxie Marlinspike | Home       | https://moxie.org/                                                                                               | active |
| Nassim Taleb      | Home       | https://fooledbyrandomness.com/                                                                                  | active |
| Gwern             | Changelog  | https://gwern.net/changelog                                                                                      | active |

## Email newsletters / aggregators (transport TBD, mining = future goal)

| Name        | Cadence      | Note                                                             |
| ----------- | ------------ | ---------------------------------------------------------------- |
| Data Elixir | monthly-ish? | aggregator; future: mine issues for recurring underlying sources |

## Deferred mediums (future goals)

- Reddit: top 5/10 per subreddit per period digest. Not in v1.
- Spotify-only podcasts: same creator logic when one appears.

## Context (not system inputs)

Read directly, not part of this system: The Economist, WSJ, WaPo, NYT,
Institutional Investor, Foreign Affairs.
