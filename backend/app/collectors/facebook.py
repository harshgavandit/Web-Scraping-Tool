import httpx
from datetime import datetime
from typing import List
from app.collectors.base import BaseCollector, RawPost
from app.collectors.mock import MockCollector
from app.core.config import settings
from app.core.logging import logger
from app.utils.datetime_utils import utc_now


class FacebookCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "facebook"

    def is_enabled(self) -> bool:
        return bool(settings.FACEBOOK_ENABLED and settings.FACEBOOK_ACCESS_TOKEN)

    def collect(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        limit: int = 50
    ) -> List[RawPost]:
        """
        Collect public Facebook Page posts or discussions via Graph API.
        If credentials/token not configured, fallback gracefully to mock Facebook data.
        """
        if not self.is_enabled():
            logger.info("Facebook API access token not configured or disabled: using mock Facebook data fallback.")
            mock_collector = MockCollector()
            all_mock = mock_collector.collect(brand_name, keywords, competitors, limit=50)
            return [p for p in all_mock if p.source == "facebook"][:limit]

        results: List[RawPost] = []
        try:
            # Using permitted public Graph API page feed endpoint
            # e.g., https://graph.facebook.com/v19.0/{page-id}/feed
            api_url = f"https://graph.facebook.com/v19.0/nike/feed?fields=id,message,created_time,shares,comments.summary(true),likes.summary(true)&access_token={settings.FACEBOOK_ACCESS_TOKEN}"
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(api_url)
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    for item in data:
                        created_time_str = item.get("created_time")
                        pub_date = datetime.fromisoformat(created_time_str.replace("Z", "+00:00")).replace(tzinfo=None) if created_time_str else utc_now()
                        likes = item.get("likes", {}).get("summary", {}).get("total_count", 0)
                        comments = item.get("comments", {}).get("summary", {}).get("total_count", 0)
                        shares = item.get("shares", {}).get("count", 0)

                        message = item.get("message", "")
                        if message:
                            results.append(
                                RawPost(
                                    source="facebook",
                                    external_id=item.get("id"),
                                    url=f"https://facebook.com/{item.get('id')}",
                                    author="Nike Official Page",
                                    title=message[:60] + "...",
                                    content=message,
                                    published_at=pub_date,
                                    likes=likes,
                                    comments=comments,
                                    shares=shares,
                                    raw_metadata={"graph_api": True}
                                )
                            )
                    logger.info(f"Facebook collector fetched {len(results)} live posts.")
                    return results
                else:
                    logger.warning(f"Facebook Graph API request returned {resp.status_code}.")
        except Exception as e:
            logger.error(f"Facebook collection error: {e}")

        mock_collector = MockCollector()
        return [p for p in mock_collector.collect(brand_name, keywords, competitors, limit=limit) if p.source == "facebook"]
