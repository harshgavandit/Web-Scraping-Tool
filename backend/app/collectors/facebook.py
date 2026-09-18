import httpx
from datetime import datetime
from typing import List
from app.collectors.base import BaseCollector, RawPost
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
        Collect public Facebook Page posts via the permitted Graph API.
        An unconfigured collector returns no records; it never fabricates data.
        """
        if not self.is_enabled():
            logger.info("Facebook collector skipped because its access token is not configured or it is disabled.")
            return []

        results: List[RawPost] = []
        try:
            # Using permitted public Graph API page feed endpoint
            # e.g., https://graph.facebook.com/v19.0/{page-id}/feed
            api_url = "https://graph.facebook.com/v19.0/nike/feed"
            params = {
                "fields": "id,message,permalink_url,created_time,shares,comments.summary(true),likes.summary(true)",
                "access_token": settings.FACEBOOK_ACCESS_TOKEN,
                "limit": min(limit, 100),
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    for item in data:
                        created_time_str = item.get("created_time")
                        pub_date = datetime.fromisoformat(created_time_str.replace("Z", "+00:00")).replace(tzinfo=None) if created_time_str else utc_now()
                        likes = item.get("likes", {}).get("summary", {}).get("total_count", 0)
                        comments = item.get("comments", {}).get("summary", {}).get("total_count", 0)
                        shares = item.get("shares", {}).get("count", 0)

                        message = item.get("message", "")
                        permalink = item.get("permalink_url")
                        if message and permalink:
                            results.append(
                                RawPost(
                                    source="facebook",
                                    external_id=item.get("id"),
                                    url=permalink,
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
                raise RuntimeError(f"Facebook Graph API request failed with status {resp.status_code}")
        except Exception as e:
            logger.error(f"Facebook collection error: {e}")
            raise
