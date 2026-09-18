import hashlib
from datetime import datetime
from typing import List, Optional

import httpx

from app.collectors.base import BaseCollector, RawPost
from app.core.config import settings
from app.core.logging import logger
from app.discovery.query_planner import GoogleQuerySpec, build_google_query_specs


def _parse_published_at(item: dict) -> Optional[datetime]:
    pagemap = item.get("pagemap") or {}
    metatags = pagemap.get("metatags") or []
    if not metatags:
        return None
    value = metatags[0].get("article:published_time") or metatags[0].get("date")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


class GoogleSearchCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "google_search"

    def is_enabled(self) -> bool:
        return bool(
            settings.GOOGLE_SEARCH_ENABLED
            and settings.GOOGLE_SEARCH_API_KEY
            and settings.GOOGLE_SEARCH_ENGINE_ID
        )

    def build_queries(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
    ) -> List[GoogleQuerySpec]:
        return build_google_query_specs(brand_name, keywords, competitors)

    def collect(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        limit: int = 50,
    ) -> List[RawPost]:
        if not self.is_enabled():
            return []

        results: List[RawPost] = []
        seen_urls = set()
        specs = self.build_queries(brand_name, keywords, competitors)
        per_query = max(1, min(10, (limit + len(specs) - 1) // max(len(specs), 1)))

        with httpx.Client(timeout=20.0, headers={"User-Agent": "BrandChatter/2.0"}) as client:
            for spec in specs:
                response = client.get(
                    settings.GOOGLE_SEARCH_ENDPOINT,
                    params={
                        "key": settings.GOOGLE_SEARCH_API_KEY,
                        "cx": settings.GOOGLE_SEARCH_ENGINE_ID,
                        "q": spec.query,
                        "num": per_query,
                        "gl": settings.GOOGLE_SEARCH_COUNTRY.lower(),
                        "lr": f"lang_{settings.GOOGLE_SEARCH_LANGUAGE}",
                    },
                )
                if response.status_code != 200:
                    logger.warning(
                        f"Google Search query '{spec.category}' failed with status {response.status_code}."
                    )
                    continue

                for position, item in enumerate(response.json().get("items") or [], start=1):
                    url = (item.get("link") or "").strip()
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    title = (item.get("title") or "").strip()
                    snippet = (item.get("snippet") or "").strip()
                    external_id = item.get("cacheId") or hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
                    results.append(RawPost(
                        source="google_search",
                        external_id=f"google-{external_id}",
                        url=url,
                        author=item.get("displayLink") or None,
                        title=title,
                        content=f"{title}\n\n{snippet}".strip(),
                        published_at=_parse_published_at(item),
                        raw_metadata={
                            "provider": "google",
                            "discovery_category": spec.category,
                            "google_query": spec.query,
                            "product": spec.product,
                            "competitor": spec.competitor,
                            "display_domain": item.get("displayLink"),
                            "search_position": position,
                            "country": settings.GOOGLE_SEARCH_COUNTRY,
                            "language": settings.GOOGLE_SEARCH_LANGUAGE,
                            "engagement_available": False,
                        },
                    ))
                    if len(results) >= limit:
                        return results

        return results
