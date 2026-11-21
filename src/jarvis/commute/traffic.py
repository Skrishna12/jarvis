from __future__ import annotations

from urllib.parse import quote_plus

from jarvis.commute.schedule import resolve_city
from jarvis.config import load_settings
from jarvis.news.feeds import NewsSection, fetch_feed, format_digest


def traffic_feed_url(city: str) -> str:
    query = f"{city} traffic" if city else "India traffic delay"
    return (
        "https://news.google.com/rss/search?q="
        + quote_plus(query)
        + "&hl=en-IN&gl=IN&ceid=IN:en"
    )


def fetch_traffic(*, session=None, limit: int = 6) -> NewsSection:
    city = resolve_city(session, load_settings())
    label = f"Traffic ({city})" if city else "Traffic (India)"
    return fetch_feed(traffic_feed_url(city), section=label, limit=limit)


def format_traffic(section: NewsSection) -> str:
    return format_digest([section])
