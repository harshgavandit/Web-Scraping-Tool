import xml.etree.ElementTree as ET
import httpx
from datetime import datetime
from email.utils import parsedate_to_datetime
from math import ceil
from typing import List, Optional
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawPost
from app.core.config import settings
from app.core.logging import logger
from app.services.deduplication_service import canonicalize_url
from app.utils.datetime_utils import utc_now
from app.discovery.query_planner import GoogleQuerySpec


def build_google_news_queries(
    brand_name: str,
    keywords: List[str],
    competitors: List[str],
) -> List[tuple[str, str]]:
    """Build focused Google News searches from the configured brand portfolio."""
    brand = brand_name.strip()
    queries = [
        ("overall_presence", f'"{brand}" (brand OR products OR company) when:30d'),
        ("customer_feedback", f'"{brand}" (review OR reviews OR complaint OR complaints OR "customer feedback" OR quality OR comfort) when:90d'),
        ("viral_trending", f'"{brand}" (viral OR trending OR "social media" OR campaign) when:30d'),
        ("articles_blogs", f'"{brand}" (article OR analysis OR blog OR review) when:90d'),
    ]

    cleaned_competitors = list(dict.fromkeys(
        item.strip() for item in competitors if item and item.strip()
    ))[:6]
    for rival in cleaned_competitors:
        queries.append((
            "competitor_comparison",
            f'"{brand}" "{rival}" (versus OR vs OR comparison OR compared OR review) when:90d',
        ))

    seen_topics = {brand.casefold()}
    for keyword in keywords:
        topic = keyword.strip()
        if not topic or topic.casefold() in seen_topics:
            continue
        seen_topics.add(topic.casefold())
        queries.append((
            "tracked_topic",
            f'"{brand}" "{topic}" (review OR feedback OR launch OR performance) when:90d',
        ))
        if len(seen_topics) >= 9:
            break

    return queries


class RSSCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "rss"

    def is_enabled(self) -> bool:
        return bool(settings.RSS_ENABLED)

    def build_queries(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
    ) -> List[GoogleQuerySpec]:
        return [
            GoogleQuerySpec(category=category, query=query)
            for category, query in build_google_news_queries(brand_name, keywords, competitors)
        ]

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
        seen_ids = set()
        successful_queries = 0
        queries = [(spec.category, spec.query) for spec in self.build_queries(brand_name, keywords, competitors)]
        per_query_limit = max(3, min(8, ceil(limit / max(len(queries), 1)) + 1))
        rss_url = "https://news.google.com/rss/search"
        headers = {
            "User-Agent": "BrandChatter/1.0 (+public Google News RSS discovery)"
        }

        try:
            with httpx.Client(timeout=12.0, headers=headers) as client:
                for category, query in queries:
                    resp = client.get(
                        rss_url,
                        params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
                    )
                    if resp.status_code != 200:
                        logger.warning(
                            f"Google News query '{category}' failed with status {resp.status_code}."
                        )
                        continue

                    successful_queries += 1
                    root = ET.fromstring(resp.content)
                    for item in root.findall("./channel/item")[:per_query_limit]:
                        title_el = item.find("title")
                        link_el = item.find("link")
                        pub_el = item.find("pubDate")
                        desc_el = item.find("description")
                        guid_el = item.find("guid")
                        source_el = item.find("source")

                        title = (title_el.text if title_el is not None else "").strip()
                        link = (link_el.text if link_el is not None else "").strip()
                        guid = (guid_el.text if guid_el is not None else link).strip()
                        dedupe_key = guid or link
                        if not link or not dedupe_key or dedupe_key in seen_ids:
                            continue
                        seen_ids.add(dedupe_key)

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

                        publisher = (
                            source_el.text.strip()
                            if source_el is not None and source_el.text
                            else "Google News publisher"
                        )
                        publisher_url = source_el.get("url") if source_el is not None else None

                        results.append(RawPost(
                            source="news_rss",
                            external_id=guid,
                            url=link,
                            author=publisher,
                            title=title,
                            content=content,
                            published_at=pub_date,
                            likes=0,
                            comments=0,
                            shares=0,
                            raw_metadata={
                                "feed": "Google News RSS",
                                "discovery_category": category,
                                "google_query": query,
                                "publisher": publisher,
                                "publisher_url": publisher_url,
                                "engagement_available": False,
                            },
                        ))

            if successful_queries == 0:
                raise RuntimeError("Every Google News RSS query failed")

            results.sort(key=lambda post: post.published_at or utc_now(), reverse=True)
            limited_results = results[:limit]
            logger.info(
                f"RSS collector fetched {len(limited_results)} unique live news items "
                f"across {successful_queries} Google discovery queries."
            )
            return limited_results

        except Exception as e:
            logger.error(f"RSS collection error: {e}")
            raise


# Broad public feeds are allowlisted here. A record is kept only when its title
# or body explicitly mentions the active brand, so publisher ownership never
# becomes a substitute for actual Nike relevance.
DEFAULT_NIKE_PUBLISHER_FEEDS = (
    ("Footwear News", "https://wwd.com/footwear-news/feed/"),
    ("Hypebeast", "https://hypebeast.com/feed"),
    ("Sneaker News", "https://sneakernews.com/feed/"),
    ("Nice Kicks", "https://www.nicekicks.com/feed/"),
)


def configured_publisher_feeds() -> List[tuple[str, str]]:
    """Read configured publisher feeds, or the curated Nike allowlist."""
    configured = (settings.PUBLISHER_RSS_FEEDS or "").strip()
    if not configured:
        return list(DEFAULT_NIKE_PUBLISHER_FEEDS)

    feeds: List[tuple[str, str]] = []
    for raw_line in configured.splitlines():
        name, separator, url = raw_line.partition("|")
        if separator and name.strip() and canonicalize_url(url.strip()):
            feeds.append((name.strip(), url.strip()))
        elif raw_line.strip():
            logger.warning("Ignoring malformed PUBLISHER_RSS_FEEDS entry.")
    return feeds


def _entry_text(element: Optional[ET.Element], tag: str) -> str:
    child = element.find(tag) if element is not None else None
    return (child.text or "").strip() if child is not None else ""


def _parse_feed_datetime(value: str) -> datetime:
    if value:
        try:
            return parsedate_to_datetime(value).replace(tzinfo=None)
        except (TypeError, ValueError, IndexError):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                pass
    return utc_now()


class PublisherRSSCollector(BaseCollector):
    """Collect explicit Nike mentions from curated publisher RSS and Atom feeds."""

    @property
    def source_name(self) -> str:
        return "publisher_rss"

    def is_enabled(self) -> bool:
        return bool(settings.PUBLISHER_RSS_ENABLED and configured_publisher_feeds())

    @staticmethod
    def _metadata(feed_name: str, feed_url: str, original_feed_url: str, feed_format: str) -> dict:
        return {
            "feed_name": feed_name,
            "feed_url": feed_url,
            "original_feed_url": original_feed_url,
            "feed_format": feed_format,
            "engagement_available": False,
        }

    def _rss_posts(self, feed_name: str, feed_url: str, root: ET.Element, brand_name: str) -> List[RawPost]:
        posts: List[RawPost] = []
        brand_marker = brand_name.casefold()
        for item in root.findall("./channel/item"):
            title = _entry_text(item, "title")
            original_feed_url = _entry_text(item, "link")
            summary = BeautifulSoup(_entry_text(item, "description"), "html.parser").get_text(" ", strip=True)
            content = f"{title}\n\n{summary}".strip()
            if not original_feed_url or brand_marker not in content.casefold():
                continue
            article_url = canonicalize_url(original_feed_url)
            if not article_url:
                continue
            posts.append(RawPost(
                source=self.source_name,
                external_id=_entry_text(item, "guid") or article_url,
                url=article_url,
                author=feed_name,
                title=title,
                content=content,
                published_at=_parse_feed_datetime(_entry_text(item, "pubDate")),
                raw_metadata=self._metadata(feed_name, feed_url, original_feed_url, "rss"),
            ))
        return posts

    def _atom_posts(self, feed_name: str, feed_url: str, root: ET.Element, brand_name: str) -> List[RawPost]:
        posts: List[RawPost] = []
        namespace = "{http://www.w3.org/2005/Atom}"
        brand_marker = brand_name.casefold()
        for entry in root.findall(f"{namespace}entry"):
            title = _entry_text(entry, f"{namespace}title")
            summary_html = _entry_text(entry, f"{namespace}content") or _entry_text(entry, f"{namespace}summary")
            summary = BeautifulSoup(summary_html, "html.parser").get_text(" ", strip=True)
            content = f"{title}\n\n{summary}".strip()
            if brand_marker not in content.casefold():
                continue
            links = entry.findall(f"{namespace}link")
            original_feed_url = next((link.get("href") for link in links if link.get("rel", "alternate") == "alternate"), None)
            original_feed_url = original_feed_url or next((link.get("href") for link in links if link.get("href")), "")
            article_url = canonicalize_url(original_feed_url)
            if not article_url:
                continue
            posts.append(RawPost(
                source=self.source_name,
                external_id=_entry_text(entry, f"{namespace}id") or article_url,
                url=article_url,
                author=feed_name,
                title=title,
                content=content,
                published_at=_parse_feed_datetime(_entry_text(entry, f"{namespace}published") or _entry_text(entry, f"{namespace}updated")),
                raw_metadata=self._metadata(feed_name, feed_url, original_feed_url, "atom"),
            ))
        return posts

    def collect(self, brand_name: str, keywords: List[str], competitors: List[str], limit: int = 25) -> List[RawPost]:
        if not self.is_enabled():
            return []

        results: List[RawPost] = []
        headers = {"User-Agent": "BrandChatter/1.0 (+public publisher RSS discovery)"}
        with httpx.Client(timeout=12.0, headers=headers, follow_redirects=True) as client:
            for feed_name, feed_url in configured_publisher_feeds():
                try:
                    response = client.get(feed_url)
                    if response.status_code != 200:
                        logger.warning(f"Publisher feed '{feed_name}' failed with status {response.status_code}.")
                        continue
                    root = ET.fromstring(response.content)
                    if root.tag.endswith("feed"):
                        results.extend(self._atom_posts(feed_name, feed_url, root, brand_name))
                    else:
                        results.extend(self._rss_posts(feed_name, feed_url, root, brand_name))
                except (ET.ParseError, httpx.HTTPError) as exc:
                    logger.warning(f"Publisher feed '{feed_name}' could not be read: {exc}")

        unique_posts: List[RawPost] = []
        seen_urls = set()
        for post in results:
            if post.url in seen_urls:
                continue
            seen_urls.add(post.url)
            unique_posts.append(post)
        unique_posts.sort(key=lambda post: post.published_at or utc_now(), reverse=True)
        logger.info(f"Publisher RSS collector fetched {len(unique_posts[:limit])} live Nike items.")
        return unique_posts[:limit]
