import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import List
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawPost
from app.core.logging import logger
from app.utils.datetime_utils import utc_now


def extract_original_url(url: str) -> str:
    """Return the original publisher URL embedded in a Bing News link."""
    parsed = urlparse(url)
    if parsed.netloc.lower().endswith("bing.com"):
        target = parse_qs(parsed.query).get("url", [""])[0]
        if urlparse(target).scheme in {"http", "https"}:
            return target
    return url


class GenericWebCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "web"

    def is_enabled(self) -> bool:
        return True

    def collect(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        limit: int = 15
    ) -> List[RawPost]:
        """
        Discover public review and feedback articles through Bing's public RSS
        index. Publisher pages are not scraped, and each record uses the direct
        publisher URL embedded in the feed.
        """
        query = f'"{brand_name}" (review OR complaint OR customer feedback)'
        headers = {"User-Agent": "BrandChatter/1.0 (+public RSS discovery)"}

        try:
            with httpx.Client(timeout=10.0, headers=headers) as client:
                response = client.get(
                    "https://www.bing.com/news/search",
                    params={"q": query, "format": "rss"},
                )

            if response.status_code != 200:
                raise RuntimeError(f"Bing News RSS request failed with status {response.status_code}")

            root = ET.fromstring(response.content)
            results: List[RawPost] = []
            for item in root.findall("./channel/item")[:limit]:
                title = (item.findtext("title") or "").strip()
                feed_url = (item.findtext("link") or "").strip()
                url = extract_original_url(feed_url)
                if urlparse(url).scheme not in {"http", "https"}:
                    continue

                description = BeautifulSoup(
                    item.findtext("description") or "", "html.parser"
                ).get_text(" ", strip=True)
                content = f"{title}\n\n{description}".strip()
                if not content:
                    continue

                published_at = utc_now()
                published_text = item.findtext("pubDate")
                if published_text:
                    try:
                        published_at = parsedate_to_datetime(published_text).replace(tzinfo=None)
                    except (TypeError, ValueError, OverflowError):
                        pass

                publisher = urlparse(url).netloc.removeprefix("www.") or "Public web"
                results.append(RawPost(
                    source="web",
                    external_id=(item.findtext("guid") or url).strip(),
                    url=url,
                    author=publisher,
                    title=title,
                    content=content,
                    published_at=published_at,
                    likes=0,
                    comments=0,
                    shares=0,
                    raw_metadata={
                        "feed": "Bing News RSS",
                        "publisher": publisher,
                        "engagement_available": False,
                    },
                ))

            logger.info(f"Web collector fetched {len(results)} live public items.")
            return results
        except Exception as exc:
            logger.error(f"Web collection error: {exc}")
            raise
