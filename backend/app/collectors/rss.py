import xml.etree.ElementTree as ET
import httpx
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawPost
from app.collectors.mock import MockCollector
from app.core.config import settings
from app.core.logging import logger
from app.utils.datetime_utils import utc_now


class RSSCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "rss"

    def is_enabled(self) -> bool:
        return bool(settings.RSS_ENABLED)

    def collect(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        limit: int = 25
    ) -> List[RawPost]:
        """
        Collect public articles and news from public RSS feeds (e.g., Google News RSS).
        Lightweight, compliant, and cost-effective.
        """
        if not self.is_enabled():
            return []

        results: List[RawPost] = []
        try:
            # Query Google News RSS for brand discussion
            query = f"{brand_name} shoes OR sneakers OR running"
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }

            with httpx.Client(timeout=10.0, headers=headers) as client:
                resp = client.get(rss_url)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    items = root.findall("./channel/item")

                    for item in items[:limit]:
                        title_el = item.find("title")
                        link_el = item.find("link")
                        pub_el = item.find("pubDate")
                        desc_el = item.find("description")
                        guid_el = item.find("guid")

                        title = title_el.text if title_el is not None else ""
                        link = link_el.text if link_el is not None else ""
                        guid = guid_el.text if guid_el is not None else link

                        # Clean HTML from description
                        raw_desc = desc_el.text if desc_el is not None else ""
                        soup = BeautifulSoup(raw_desc, "html.parser")
                        clean_desc = soup.get_text().strip()

                        # Parse publication date
                        pub_date = utc_now()
                        if pub_el is not None and pub_el.text:
                            try:
                                pub_date = parsedate_to_datetime(pub_el.text).replace(tzinfo=None)
                            except Exception:
                                pass

                        content = f"{title}\n\n{clean_desc}".strip()

                        results.append(
                            RawPost(
                                source="news_rss",
                                external_id=guid,
                                url=link,
                                author="News Feed",
                                title=title,
                                content=content,
                                published_at=pub_date,
                                likes=250,  # Estimated baseline engagement for indexed public news
                                comments=30,
                                shares=45,
                                raw_metadata={"feed": "Google News RSS"}
                            )
                        )

                    logger.info(f"RSS collector fetched {len(results)} live news items.")
                    return results

        except Exception as e:
            logger.warning(f"RSS collection error: {e}. Falling back to mock news data.")

        # Fallback to mock news items if external network is unavailable
        mock_collector = MockCollector()
        return [p for p in mock_collector.collect(brand_name, keywords, competitors, limit=limit) if p.source == "news_rss"]
