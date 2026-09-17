import httpx
from datetime import datetime, timezone
from typing import List
from app.collectors.base import BaseCollector, RawPost
from app.collectors.mock import MockCollector
from app.core.config import settings
from app.core.logging import logger
from app.utils.datetime_utils import utc_now


class RedditCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "reddit"

    def is_enabled(self) -> bool:
        return bool(settings.REDDIT_ENABLED and settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET)

    def collect(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        limit: int = 50
    ) -> List[RawPost]:
        """
        Collect public Reddit submissions.
        If credentials are not present, fallback cleanly to high-fidelity mock data.
        """
        if not self.is_enabled():
            logger.info("Reddit credentials not configured or disabled: using mock Reddit data fallback.")
            mock_collector = MockCollector()
            all_mock = mock_collector.collect(brand_name, keywords, competitors, limit=50)
            return [p for p in all_mock if p.source == "reddit"][:limit]

        # When credentials are provided, use Reddit OAuth public endpoint
        results: List[RawPost] = []
        try:
            auth = (settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET)
            headers = {"User-Agent": settings.REDDIT_USER_AGENT or "BrandChatter/1.0"}

            # Request app-only access token
            token_url = "https://www.reddit.com/api/v1/access_token"
            with httpx.Client(timeout=10.0) as client:
                token_resp = client.post(
                    token_url,
                    auth=auth,
                    data={"grant_type": "client_credentials"},
                    headers=headers
                )

                if token_resp.status_code != 200:
                    logger.warning(f"Reddit OAuth token failed ({token_resp.status_code}), falling back to mock.")
                    mock_collector = MockCollector()
                    return [p for p in mock_collector.collect(brand_name, keywords, competitors, limit=limit) if p.source == "reddit"]

                token = token_resp.json().get("access_token")
                api_headers = {
                    "Authorization": f"bearer {token}",
                    "User-Agent": settings.REDDIT_USER_AGENT
                }

                # Search submissions for brand query
                search_query = f"{brand_name} (shoes OR running OR sneaker OR comfort OR price)"
                search_url = f"https://oauth.reddit.com/search?q={search_query}&sort=relevance&t=week&limit={min(limit, 50)}"
                search_resp = client.get(search_url, headers=api_headers)

                if search_resp.status_code == 200:
                    data = search_resp.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        post_data = child.get("data", {})
                        created_utc = post_data.get("created_utc")
                        pub_date = datetime.fromtimestamp(created_utc, timezone.utc).replace(tzinfo=None) if created_utc else utc_now()

                        results.append(
                            RawPost(
                                source="reddit",
                                external_id=post_data.get("id"),
                                url=f"https://reddit.com{post_data.get('permalink')}",
                                author=post_data.get("author"),
                                title=post_data.get("title"),
                                content=f"{post_data.get('title', '')}\n\n{post_data.get('selftext', '')}".strip(),
                                published_at=pub_date,
                                likes=post_data.get("ups", 0),
                                comments=post_data.get("num_comments", 0),
                                shares=0,
                                raw_metadata={
                                    "subreddit": post_data.get("subreddit"),
                                    "upvote_ratio": post_data.get("upvote_ratio")
                                }
                            )
                        )
                    logger.info(f"Reddit collector fetched {len(results)} live posts.")
                    return results
                else:
                    logger.warning(f"Reddit search failed ({search_resp.status_code}).")

        except Exception as e:
            logger.error(f"Reddit collection error: {e}")

        # Fallback if any network / API failure occurs
        mock_collector = MockCollector()
        return [p for p in mock_collector.collect(brand_name, keywords, competitors, limit=limit) if p.source == "reddit"]
