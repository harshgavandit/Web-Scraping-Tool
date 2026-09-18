from typing import List
from app.collectors.base import BaseCollector, RawPost
from app.collectors.rss import RSSCollector, PublisherRSSCollector
from app.collectors.google_search import GoogleSearchCollector

ALL_COLLECTORS = [
    RSSCollector(),
    PublisherRSSCollector(),
    GoogleSearchCollector(),
]


def get_collectors(source: str = "all") -> List[BaseCollector]:
    """Retrieve requested collectors or all active collectors."""
    if source == "all":
        return [collector for collector in ALL_COLLECTORS if collector.is_enabled()]
    return [collector for collector in ALL_COLLECTORS if collector.source_name.lower() == source.lower()]


__all__ = [
    "BaseCollector",
    "RawPost",
    "RSSCollector",
    "PublisherRSSCollector",
    "GoogleSearchCollector",
    "get_collectors",
    "ALL_COLLECTORS",
]
