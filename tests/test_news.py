from __future__ import annotations

from jarvis.news.feeds import parse_rss
from jarvis.security.gate import PermissionGate
from jarvis.tools.catalog import default_registry

_SAMPLE = """
<rss><channel>
  <item><title>Budget vote</title><link>https://example.test/a</link></item>
  <item><title>Cyclone watch</title><link>https://example.test/b</link></item>
</channel></rss>
"""


def test_parse_rss_titles() -> None:
    items = parse_rss(_SAMPLE, section="National", limit=10)
    assert [i.title for i in items] == ["Budget vote", "Cyclone watch"]


def test_news_digest_tool_uses_stub(db_session) -> None:
    gate = PermissionGate(db_session, default_registry())
    outcome = gate.invoke("news.digest", {}, agent="news")
    assert outcome.status == "ok"
    assert "India story" in outcome.message
    assert "World story" in outcome.message
    assert "Daily news" in outcome.message
