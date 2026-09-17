from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class RawPost:
    source: str
    content: str
    external_id: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    published_at: Optional[datetime] = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the source, e.g. 'reddit', 'facebook', 'rss'"""
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Returns True if collector is enabled and configured"""
        pass

    @abstractmethod
    def collect(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        limit: int = 50
    ) -> List[RawPost]:
        """Collect raw brand mentions adhering to safety rules."""
        pass
