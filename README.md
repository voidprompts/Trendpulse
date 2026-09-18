# TrendPulse

Automated, zero-cost, AdSense-ready social-media tag generator.

Two data layers:
- **Micro trends (live)** — client-side **JSONP** against YouTube's search
  autocomplete service. The endpoint sends no CORS headers, so `fetch()` is
  blocked; `client=youtube` + a custom `jsonp=` callback makes script-tag
  injection work. No proxy, no API key, no server to IP-ban.
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

Source: `suggestqueries.google.com/complete/search` (mirror:
`clients1.google.com`), params `client=youtube&ds=yt&hl=en&gs_ri=youtube&jsonp=<cb>&q=<kw>`.
Response is a JSONP envelope: `cb(["kw",[["suggestion",0,[433]],...],{...}])`.

| Timeframe | Velocity modifiers injected |
|---|---|
| Hourly | `#shorts #reels #viral #trendingnow #breaking` |
| Daily | `#shorts #reels #viral #trendingtoday #fyp` |
| Weekly | `#trendingthisweek #weeklytrends` |
| Monthly | `#trending #evergreen` |

Instagram/Facebook/All emit camelCase hashtags (`#TrendingAudioMeme`);
YouTube emits comma-separated phrases capped at 480 chars (Studio's limit is 500).
Leading/trailing stop words are stripped ("how to do the griddy" -> `#Griddy`).

Two mirrors are tried in order; if both fail or time out (6s each), the
generator emits structured viral fields and labels the output "offline mode".

## Before requesting AdSense review

- [ ] Replace every `trendpulse.vercel.app` reference (`template.html`, `privacy.html`, `robots.txt`, `scraper.py` → `SITE_URL`) with your real domain.
- [ ] Set a real contact address in `privacy.html` §11 and update the "Last updated" date.
- [ ] Uncomment the AdSense `<script>` in `template.html` `<head>` and insert your `ca-pub-` ID.
- [ ] Paste real `<ins class="adsbygoogle">` units into the two `.adsense-slot` divs.
- [ ] Submit the domain in Google Search Console and the sitemap at `/sitemap.xml`.
- [ ] Let the cron run several days first — AdSense rejects sites that look thin or brand new.
