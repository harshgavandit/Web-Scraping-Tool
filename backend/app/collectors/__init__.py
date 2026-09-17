from typing import List
from app.collectors.base import BaseCollector, RawPost
from app.collectors.reddit import RedditCollector
from app.collectors.facebook import FacebookCollector
from app.collectors.rss import RSSCollector
from app.collectors.generic_web import GenericWebCollector
from app.collectors.mock import MockCollector

ALL_COLLECTORS = [
    RedditCollector(),
    FacebookCollector(),
    RSSCollector(),
    GenericWebCollector(),
    MockCollector(),
]


def get_collectors(source: str = "all") -> List[BaseCollector]:
    """Retrieve requested collectors or all active collectors."""
    if source == "all":
        return ALL_COLLECTORS
    matched = [c for c in ALL_COLLECTORS if c.source_name.lower() == source.lower()]
    return matched if matched else [MockCollector()]


__all__ = [
    "BaseCollector",
    "RawPost",
    "RedditCollector",
    "FacebookCollector",
    "RSSCollector",
    "GenericWebCollector",
    "MockCollector",
    "get_collectors",
    "ALL_COLLECTORS",
]
