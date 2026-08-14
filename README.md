# daily-reader

A release calendar for a hand-curated roster of creators (Substack,
YouTube, and feedless static pages), run locally on Windows. Polls the
roster's RSS feeds, detects new releases, and produces an all-text
digest every ~3 waking hours: articles get a title plus exactly one
bullet; videos get creator plus title only. A Vercel mirror serves the
rolling view to an iPhone home-screen icon, and an SMTP newsletter
mails the rolling window.

Start with [CLAUDE.md](CLAUDE.md) -- it is the operating manual: every
command, the state layout, and the gotchas. The project is also a trial
of the goal/plan/state/worklog method; those four files plus
worklog.md are the method record, kept honest at each wind-down.

Requires Python 3.x, a `.env` with `ANTHROPIC_API_KEY` (bullets via
claude-haiku-4-5), and optionally the Vercel CLI (mirror) and
`.env.smtp` (newsletter). Runtime state, digests, and deploy artifacts
are gitignored and regenerate from the scripts.
