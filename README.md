# TrendPulse

Automated, zero-cost social-media trend tracker.

| Layer | File | Role |
|---|---|---|
| Frontend | `index.html` | Static SPA (Tailwind CDN) that fetches `trends.json` |
| Engine | `scraper.py` | Stdlib-only Google Trends RSS scraper → `trends.json` |
| Scheduler | `.github/workflows/scrape.yml` | Daily cron → commit → Vercel rebuild |

## Deploy

1. Push this repo to GitHub.
2. Import it on Vercel as a **static** project (no build command, output dir = root).
3. Done. The Action runs at `34 0 * * *` UTC daily, commits `trends.json` with a
   normal message (no `[skip ci]`), and Vercel auto-deploys the push.

Manual run: **Actions → TrendPulse Daily Scrape → Run workflow**, or locally:

```bash
python scraper.py
python -m http.server 8000   # then open http://localhost:8000
```
