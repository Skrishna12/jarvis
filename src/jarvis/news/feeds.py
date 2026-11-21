"""Public RSS headlines. No news API key — Google News and BBC feeds."""

from __future__ import annotations

import html
from dataclasses import dataclass
from xml.etree import ElementTree

import httpx

from jarvis.config import Settings, load_settings
from jarvis.memory.errors import ValidationError

_UA = "jarvis-cli/0.1 (personal assistant; RSS reader)"
_TIMEOUT = 20.0

_TOPIC_FEEDS: tuple[tuple[str, str], ...] = (
    (
        "Business",
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Technology",
        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Sports",
        "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Science",
        "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Health",
        "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Entertainment",
        "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-IN&gl=IN&ceid=IN:en",
    ),
)


@dataclass(frozen=True)
class Headline:
    title: str
    link: str
    section: str


@dataclass(frozen=True)
class NewsSection:
    name: str
    headlines: list[Headline]
    error: str | None = None


def parse_rss(xml_text: str, *, section: str, limit: int) -> list[Headline]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise ValidationError(f"News feed was not valid XML: {exc}.") from exc
    items: list[Headline] = []
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag != "item" and tag != "entry":
            continue
        title = _child_text(node, "title")
        link = _child_text(node, "link")
        if not link:
            href = _child_attr(node, "link", "href")
            link = href
        if not title:
            continue
        items.append(Headline(title=html.unescape(title).strip(), link=link, section=section))
        if len(items) >= limit:
            break
    return items


def fetch_feed(
    url: str,
    *,
    section: str,
    limit: int,
    client: httpx.Client | None = None,
) -> NewsSection:
    own = client is None
    http = client or httpx.Client(timeout=_TIMEOUT, follow_redirects=True)
    try:
        try:
            response = http.get(url, headers={"User-Agent": _UA, "Accept": "application/rss+xml, application/xml, text/xml"})
        except httpx.RequestError as exc:
            return NewsSection(section, [], error=f"Could not reach news ({exc}).")
        if response.status_code >= 400:
            return NewsSection(
                section,
                [],
                error=f"News feed failed (HTTP {response.status_code}).",
            )
        try:
            headlines = parse_rss(response.text, section=section, limit=limit)
        except ValidationError as exc:
            return NewsSection(section, [], error=str(exc))
        if not headlines:
            return NewsSection(section, [], error="News feed had no headlines.")
        return NewsSection(section, headlines)
    finally:
        if own:
            http.close()


def fetch_digest(
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    per_section: int | None = None,
    include_topics: bool = True,
) -> list[NewsSection]:
    cfg = settings or load_settings()
    limit = per_section or cfg.news_per_section
    topic_limit = max(2, min(limit, 3))
    own = client is None
    http = client or httpx.Client(timeout=_TIMEOUT, follow_redirects=True)
    try:
        sections = [
            fetch_feed(cfg.news_national_feed, section="National", limit=limit, client=http),
            fetch_feed(cfg.news_world_feed, section="International", limit=limit, client=http),
        ]
        if include_topics:
            for name, url in _TOPIC_FEEDS:
                sections.append(fetch_feed(url, section=name, limit=topic_limit, client=http))
        return sections
    finally:
        if own:
            http.close()


def format_digest(sections: list[NewsSection]) -> str:
    lines: list[str] = ["Daily news"]
    for section in sections:
        lines.append(f"{section.name}:")
        if section.error:
            lines.append(f"  ({section.error})")
            continue
        for item in section.headlines:
            lines.append(f"  - {item.title}")
    return "\n".join(lines)


def _child_text(node: ElementTree.Element, name: str) -> str:
    for child in list(node):
        if child.tag.rsplit("}", 1)[-1] == name:
            if child.text:
                return child.text.strip()
            return ""
    return ""


def _child_attr(node: ElementTree.Element, name: str, attr: str) -> str:
    for child in list(node):
        if child.tag.rsplit("}", 1)[-1] == name:
            return (child.get(attr) or "").strip()
    return ""
