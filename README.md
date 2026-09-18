# TrendPulse

Automated, zero-cost, AdSense-ready social-media trend tracker. Statically
pre-rendered — crawlers receive finished HTML, not a JavaScript shell.

## Architecture

| File | Role |
|---|---|
| `template.html` | Base layout + SEO/OG meta + global `copyTags()` helper. Contains `<!-- TREND_CARDS_PLACEHOLDER -->`. **Edit this, never `index.html`.** |
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

## Before requesting AdSense review

- [ ] Replace every `trendpulse.vercel.app` reference (`template.html`, `privacy.html`, `robots.txt`, `scraper.py` → `SITE_URL`) with your real domain.
- [ ] Set a real contact address in `privacy.html` §11 and update the "Last updated" date.
- [ ] Uncomment the AdSense `<script>` in `template.html` `<head>` and insert your `ca-pub-` ID.
- [ ] Paste real `<ins class="adsbygoogle">` units into the two `.adsense-slot` divs.
- [ ] Submit the domain in Google Search Console and the sitemap at `/sitemap.xml`.
- [ ] Let the cron run several days first — AdSense rejects sites that look thin or brand new.
