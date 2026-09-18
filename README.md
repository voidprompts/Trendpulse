# TrendPulse

Automated, zero-cost, AdSense-ready social-media tag generator.

Two data layers:
- **Micro trends (live)** — client-side JS queries the public Wikimedia search +
  pageviews APIs with `origin=*`, ranks topics by real traffic, and emits
  platform-compliant tag strings. No server, so nothing to time out or IP-ban.
- **Macro trends (daily)** — Python pre-renders the top 9 global searches into
  static HTML so crawlers receive finished text, not a JavaScript shell.

## Architecture

| File | Role |
|---|---|
| `template.html` | Base layout + SEO/OG meta + interactive generator + live data engine + `copyTags()`. Contains `<!-- TREND_CARDS_PLACEHOLDER -->`. **Edit this, never `index.html`.** |
| `scraper.py` | Stdlib-only engine: fetch RSS → build cards → render `index.html`, `sitemap.xml`, `trends.json`. |
| `index.html` | **Generated.** Overwritten on every build. |
| `privacy.html` | AdSense-mandatory privacy policy with cookie/opt-out clauses. |
| `robots.txt` | Allows `Mediapartners-Google`, `AdsBot-Google`, all search bots. Links the sitemap. |
| `sitemap.xml` | **Generated.** Fresh `<lastmod>` each run. |
| `.github/workflows/scrape.yml` | Daily cron → regenerate → commit → Vercel rebuild. |

## Deploy

1. Push to GitHub.
2. Import on Vercel as a **static** project: no build command, output directory = root.
3. The Action runs at `34 0 * * *` UTC, commits without `[skip ci]`, Vercel auto-deploys.

Manual run: **Actions → TrendPulse Daily Pre-Render → Run workflow**. Locally:

```bash
python scraper.py
python -m http.server 8000   # http://localhost:8000
```

## Live generator

| Timeframe | Pageview window | Velocity amplifiers |
|---|---|---|
| Right now | 48 hours | `#trendingnow #breaking #happeningnow` |
| Today | 7 days | `#trendingtoday #todaystrend #viral` |
| This week | 30 days | `#trendingthisweek #weeklytrends` |
| This month | 90 days | `#trendingnow #monthlyroundup` |

Instagram/Facebook/TikTok/X return `#hashtags`; YouTube returns comma-separated
phrases capped at 480 chars (Studio's field limit is 500). Queries end 2 days
back because Wikimedia publishes pageviews with a 24-48h lag.

If the API throttles or fails, the generator falls back to structured
keyword-derived fields and labels the output "offline mode".

## Before requesting AdSense review

- [ ] Replace every `trendpulse.vercel.app` reference (`template.html`, `privacy.html`, `robots.txt`, `scraper.py` → `SITE_URL`) with your real domain.
- [ ] Set a real contact address in `privacy.html` §11 and update the "Last updated" date.
- [ ] Uncomment the AdSense `<script>` in `template.html` `<head>` and insert your `ca-pub-` ID.
- [ ] Paste real `<ins class="adsbygoogle">` units into the two `.adsense-slot` divs.
- [ ] Submit the domain in Google Search Console and the sitemap at `/sitemap.xml`.
- [ ] Let the cron run several days first — AdSense rejects sites that look thin or brand new.
