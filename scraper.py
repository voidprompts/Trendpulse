#!/usr/bin/env python3
"""
TrendPulse :: SEO Pre-Render Engine
-----------------------------------
Zero-dependency static site generator (Python 3 standard library only).

Pipeline:
  1. Fetch the live Google Trends RSS stream.
  2. Safely parse the XML tree for the top 9 trending titles.
  3. Compile each title into a semantic, crawlable HTML dashboard card.
  4. Read template.html, substitute <!-- TREND_CARDS_PLACEHOLDER -->,
     and write a production-ready index.html to the project root.
  5. Emit a matching sitemap.xml with a fresh <lastmod>.

Why pre-render instead of client-side fetch? Google AdSense and search
crawlers must see real text in the delivered HTML source. Baking the cards
into index.html guarantees that with zero JavaScript execution.

No pip installs required -> runs on any bare cloud runner.
Never raises -> any failure falls back to a hardcoded topic list.
"""

import html
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Google Trends live RSS stream (daily trending searches feed).
TRENDS_RSS_URL = "https://trends.google.com/trending/rss?geo=US"

# Google rejects the default python-urllib user agent.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

SITE_URL = "https://trendpulse.vercel.app"
REQUEST_TIMEOUT = 20            # seconds
MAX_ITEMS = 9                   # top 9 trending items
DEFAULT_CATEGORY = "General Viral"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(BASE_DIR, "template.html")
OUTPUT_FILE = os.path.join(BASE_DIR, "index.html")
SITEMAP_FILE = os.path.join(BASE_DIR, "sitemap.xml")
DATA_FILE = os.path.join(BASE_DIR, "trends.json")

PLACEHOLDER = "<!-- TREND_CARDS_PLACEHOLDER -->"

# Button class strings must match the BTN_IDLE constant in template.html.
BTN_IDLE_CLASS = (
    "mt-5 w-full rounded-xl px-4 py-2.5 text-sm font-bold transition-all duration-200 "
    "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 "
    "bg-indigo-600 text-white shadow-lg shadow-indigo-900/40 hover:bg-indigo-500 focus:ring-indigo-400"
)

# Fallback topics used when the network or the feed is unavailable.
FALLBACK_TITLES = [
    "Artificial Intelligence",
    "Premier League",
    "Crypto Market",
    "Box Office Weekend",
    "Tech Layoffs",
    "Space Launch",
    "Fitness Challenge",
    "Street Food Tour",
    "Travel Deals",
]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def slugify(title):
    """'Real Madrid vs. Barca!' -> 'realmadridvsbarca' (hashtag-safe)."""
    cleaned = "".join(ch for ch in title if ch.isalnum() or ch.isspace())
    return "".join(cleaned.lower().split()) or "trendpulse"


def short_slug(title):
    """First two words, slugified -> a shorter secondary hashtag."""
    words = [w for w in title.split() if w.strip()]
    return slugify(" ".join(words[:2])) if words else "trendpulse"


def build_hashtags(title):
    """Deterministic 4-item hashtag array for a topic."""
    candidates = [slugify(title), short_slug(title), "viral", "trending"]

    unique = []
    for tag in candidates:
        if tag and tag not in unique:
            unique.append(tag)

    # Pad back to exactly four if de-duplication shortened the list.
    for filler in ("fyp", "explorepage", "trendpulse", "news"):
        if len(unique) >= 4:
            break
        if filler not in unique:
            unique.append(filler)

    return unique[:4]


def hashtag_string(tags):
    """['a','b'] -> '#a #b'"""
    return " ".join("#" + tag for tag in tags)


def esc(value):
    """Escape for HTML text nodes and double-quoted attributes."""
    return html.escape(str(value), quote=True)


def esc_js(value):
    """Escape for a single-quoted inline JS string inside an HTML attribute."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", " ")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ---------------------------------------------------------------------------
# Network + parsing
# ---------------------------------------------------------------------------

def fetch_rss(url):
    """Fetch raw RSS bytes with an explicit timeout and browser user-agent."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return response.read()


def parse_titles(raw_xml):
    """Walk the XML tree and safely extract up to MAX_ITEMS <item><title> values."""
    root = ET.fromstring(raw_xml)
    titles = []

    for item in root.iter("item"):
        node = item.find("title")
        if node is None:
            continue
        text = (node.text or "").strip()
        if not text or text in titles:
            continue
        titles.append(text)
        if len(titles) >= MAX_ITEMS:
            break

    if not titles:
        raise ValueError("Feed parsed but contained no usable <item><title> nodes.")

    return titles


def collect_titles():
    """Return (titles, source). Never raises."""
    try:
        print("[TrendPulse] Fetching %s" % TRENDS_RSS_URL)
        titles = parse_titles(fetch_rss(TRENDS_RSS_URL))
        print("[TrendPulse] Parsed %d live titles." % len(titles))
        return titles, "google-trends-rss"
    except Exception as error:
        print("[TrendPulse] WARNING: live scrape failed (%s: %s)"
              % (type(error).__name__, error))
        print("[TrendPulse] Using hardcoded fallback list; pipeline continues.")
        return list(FALLBACK_TITLES), "fallback"


# ---------------------------------------------------------------------------
# HTML card rendering
# ---------------------------------------------------------------------------

def render_card(index, title, tags):
    """Compile one semantic, crawlable trend card."""
    rank = str(index + 1).zfill(2)
    tag_line = hashtag_string(tags)

    badges = "\n".join(
        '          <li class="rounded-full border border-indigo-400/25 bg-indigo-500/10 '
        'px-3 py-1 text-xs font-semibold text-indigo-300">#%s</li>' % esc(tag)
        for tag in tags
    )

    return """      <article class="group flex flex-col rounded-3xl border border-white/5 bg-slate-900/60 p-6 shadow-xl shadow-slate-950/40 backdrop-blur transition duration-300 hover:-translate-y-1 hover:border-indigo-400/40 hover:shadow-indigo-950/50">
        <div class="flex items-center justify-between gap-3">
          <span class="rounded-full bg-indigo-500/15 px-3 py-1 text-[11px] font-bold uppercase tracking-widest text-indigo-300">%(category)s</span>
          <span class="font-mono text-xs text-slate-600">#%(rank)s</span>
        </div>

        <h2 class="mt-4 text-xl font-bold leading-snug text-white transition group-hover:text-indigo-200">%(title)s</h2>

        <p class="mt-2 text-sm leading-relaxed text-slate-400">
          Trending right now. Use the hashtag set below to join the conversation around
          &ldquo;%(title)s&rdquo; on Instagram, TikTok, X and YouTube.
        </p>

        <ul class="mt-4 flex flex-wrap gap-2" aria-label="Suggested hashtags for %(title)s">
%(badges)s
        </ul>

        <div class="mt-auto">
          <button type="button"
                  class="%(btn)s"
                  data-label="Copy Hashtag String"
                  aria-label="Copy hashtags for %(title)s"
                  onclick="copyTags(this, '%(js_tags)s')">Copy Hashtag String</button>
        </div>
      </article>""" % {
        "category": esc(DEFAULT_CATEGORY),
        "rank": rank,
        "title": esc(title),
        "badges": badges,
        "btn": BTN_IDLE_CLASS,
        "js_tags": esc_js(tag_line),
    }


def render_all_cards(titles):
    """Compile the full card block string."""
    return "\n\n".join(
        render_card(i, title, build_hashtags(title))
        for i, title in enumerate(titles)
    )


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_index(cards_html, generated_at):
    """Read the template, inject cards + timestamps, write index.html."""
    if not os.path.exists(TEMPLATE_FILE):
        raise SystemExit("[TrendPulse] FATAL: template.html not found at %s" % TEMPLATE_FILE)

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as handle:
        template = handle.read()

    if PLACEHOLDER not in template:
        raise SystemExit("[TrendPulse] FATAL: placeholder %s missing from template.html" % PLACEHOLDER)

    human = generated_at.strftime("%d %B %Y, %H:%M UTC")
    iso = generated_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    output = template.replace(PLACEHOLDER, cards_html)
    output = output.replace("<!-- UPDATED_ISO -->", iso)
    output = output.replace("<!-- UPDATED_HUMAN -->", human)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        handle.write(output)

    print("[TrendPulse] Wrote %s (%d bytes)" % (OUTPUT_FILE, len(output)))


def write_sitemap(generated_at):
    """Emit a minimal two-URL sitemap with a fresh lastmod date."""
    lastmod = generated_at.strftime("%Y-%m-%d")
    pages = [("/", "daily", "1.0"), ("/privacy.html", "yearly", "0.3")]

    entries = "\n".join(
        "  <url>\n"
        "    <loc>%s%s</loc>\n"
        "    <lastmod>%s</lastmod>\n"
        "    <changefreq>%s</changefreq>\n"
        "    <priority>%s</priority>\n"
        "  </url>" % (SITE_URL, path, lastmod, freq, priority)
        for path, freq, priority in pages
    )

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "%s\n"
        "</urlset>\n" % entries
    )

    with open(SITEMAP_FILE, "w", encoding="utf-8") as handle:
        handle.write(sitemap)

    print("[TrendPulse] Wrote %s" % SITEMAP_FILE)


def write_data(titles, source, generated_at):
    """Optional machine-readable mirror of the rendered data."""
    payload = {
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "count": len(titles),
        "trends": [
            {
                "id": i,
                "category": DEFAULT_CATEGORY,
                "topic": title,
                "tags": build_hashtags(title),
            }
            for i, title in enumerate(titles, start=1)
        ],
    }

    with open(DATA_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print("[TrendPulse] Wrote %s" % DATA_FILE)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    generated_at = datetime.now(timezone.utc)

    titles, source = collect_titles()
    cards_html = render_all_cards(titles)

    write_index(cards_html, generated_at)
    write_sitemap(generated_at)
    write_data(titles, source, generated_at)

    print("[TrendPulse] Build complete — %d cards (source=%s)." % (len(titles), source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
