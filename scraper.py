#!/usr/bin/env python3
"""
TrendPulse :: Automation Engine
--------------------------------
Zero-dependency scraper (Python 3 standard library only) that pulls the live
Google Trends RSS stream, extracts the top trending titles and writes a clean,
indented `trends.json` to the project root.

Design goals:
  * No pip installs  -> runs on any bare GitHub Actions / Vercel / cloud runner.
  * Never crashes    -> any network/parse failure writes a hardcoded fallback.
  * Idempotent       -> always overwrites trends.json with valid structure.
"""

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

# Browser-ish UA: Google rejects the default python-urllib agent.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 20          # seconds
MAX_ITEMS = 9                 # top 9 trending items
DEFAULT_CATEGORY = "General Viral"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trends.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(title: str) -> str:
    """Turn 'Real Madrid vs. Barca!' -> 'realmadridvsbarca' for hashtag use."""
    cleaned = "".join(ch for ch in title if ch.isalnum() or ch.isspace())
    return "".join(cleaned.lower().split()) or "trendpulse"


def short_slug(title: str) -> str:
    """First two words of the title, slugified -> secondary hashtag variation."""
    words = [w for w in title.split() if w.strip()]
    return slugify(" ".join(words[:2])) if words else "trendpulse"


def build_hashtags(title: str) -> list:
    """Generate a deterministic 4-item hashtag array for a topic."""
    primary = slugify(title)
    secondary = short_slug(title)
    tags = [primary, secondary, "viral", "trending"]

    # De-duplicate while preserving order, then pad back up to exactly 4 items.
    unique = []
    for tag in tags:
        if tag not in unique:
            unique.append(tag)

    for filler in ("fyp", "explorepage", "trendpulse", "news"):
        if len(unique) >= 4:
            break
        if filler not in unique:
            unique.append(filler)

    return unique[:4]


def fetch_rss(url: str) -> bytes:
    """Fetch raw RSS bytes with an explicit timeout and browser user-agent."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return response.read()


def parse_titles(raw_xml: bytes) -> list:
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
        raise ValueError("RSS feed parsed but contained zero usable <item><title> nodes.")

    return titles


def build_trend_objects(titles: list) -> list:
    """Format raw titles into the frontend card contract."""
    trends = []
    for index, title in enumerate(titles, start=1):
        trends.append(
            {
                "id": index,
                "category": DEFAULT_CATEGORY,
                "topic": title,
                "tags": build_hashtags(title),
            }
        )
    return trends


def fallback_trends() -> list:
    """Hardcoded, structurally identical payload used when the network fails."""
    seeds = [
        ("Artificial Intelligence", ["artificialintelligence", "ai", "viral", "trending"]),
        ("Premier League", ["premierleague", "football", "viral", "trending"]),
        ("Crypto Market", ["cryptomarket", "crypto", "viral", "trending"]),
        ("Box Office Weekend", ["boxofficeweekend", "movies", "viral", "trending"]),
        ("Tech Layoffs", ["techlayoffs", "tech", "viral", "trending"]),
        ("Space Launch", ["spacelaunch", "space", "viral", "trending"]),
        ("Fitness Challenge", ["fitnesschallenge", "fitness", "viral", "trending"]),
        ("Street Food Tour", ["streetfoodtour", "foodie", "viral", "trending"]),
        ("Travel Deals", ["traveldeals", "travel", "viral", "trending"]),
    ]
    return [
        {"id": i, "category": DEFAULT_CATEGORY, "topic": topic, "tags": tags}
        for i, (topic, tags) in enumerate(seeds, start=1)
    ]


def write_output(trends: list, source: str) -> None:
    """Overwrite trends.json with a clean, indented document."""
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "count": len(trends),
        "trends": trends,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print("[TrendPulse] Wrote %d trends to %s (source=%s)" % (len(trends), OUTPUT_FILE, source))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    try:
        print("[TrendPulse] Fetching %s" % TRENDS_RSS_URL)
        raw_xml = fetch_rss(TRENDS_RSS_URL)
        titles = parse_titles(raw_xml)
        trends = build_trend_objects(titles)
        write_output(trends, source="google-trends-rss")
    except Exception as error:  # network timeout, HTTP error, XML parse error, etc.
        print("[TrendPulse] WARNING: live scrape failed (%s: %s)" % (type(error).__name__, error))
        print("[TrendPulse] Falling back to hardcoded dataset so the pipeline never breaks.")
        write_output(fallback_trends(), source="fallback")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
