import random
from datetime import datetime, timedelta
from typing import List
from app.collectors.base import BaseCollector, RawPost
from app.utils.datetime_utils import utc_now

MOCK_SOCIAL_POSTS = [
    # --- VIRAL & HIGH IMPACT DISCUSSIONS ---
    {
        "source": "reddit",
        "title": "Nike Pegasus 41 honest review after 250 miles: great daily trainer, but is $145 becoming too steep?",
        "content": "Nike Pegasus is probably the most comfortable running shoe I've owned, but it's becoming too expensive. The ReactX foam is noticeably springier than the 40, but retail prices keep climbing while competitors like New Balance offer comparable cushion for less.",
        "author": "u/MarathonChaser",
        "url": "https://reddit.com/r/RunningShoeGeeks/comments/nike_pegasus_41_honest_review",
        "likes": 8420,
        "comments": 1250,
        "shares": 430,
        "hours_ago": 2,
    },
    {
        "source": "reddit",
        "title": "The SNKRS app is completely broken for real sneakerheads",
        "content": "Tried to get the Military Blue Air Jordan 4 release this morning. App froze at 10:00:01 AM, pending for 25 minutes, then hit with 'Error: Out of Stock'. Meanwhile resellers on StockX already have 50 pairs listed. Nike customer service just told me 'better luck next drop'. Fix your bot protection!",
        "author": "u/SoleCollector99",
        "url": "https://reddit.com/r/Sneakers/comments/snkrs_app_completely_broken",
        "likes": 12500,
        "comments": 2400,
        "shares": 890,
        "hours_ago": 4,
    },
    {
        "source": "twitter",
        "title": "Adidas vs Nike pricing dilemma",
        "content": "Nike shoes are noticeably more comfortable for long-distance training, but Adidas has drastically better pricing and sales right now. Hard to justify $180 on Nike Air Max when Ultraboosts are regularly on sale for $110.",
        "author": "@KicksDaily",
        "url": "https://twitter.com/kicksdaily/status/17892019283",
        "likes": 6400,
        "comments": 820,
        "shares": 950,
        "hours_ago": 3,
    },
    {
        "source": "reddit",
        "title": "Why New Balance is taking over Nike's lifestyle market",
        "content": "Nike used to dominate every lifestyle category with Dunks and Air Force 1s, but market fatigue has set in. New Balance 9060 and 1906R offer superior materials and all-day comfort without squeaking or creasing in 2 days. Nike needs fresh silhouettes, not another colorway of the Panda Dunk.",
        "author": "u/StreetwearObserver",
        "url": "https://reddit.com/r/streetwear/comments/new_balance_taking_over_nike",
        "likes": 7800,
        "comments": 940,
        "shares": 310,
        "hours_ago": 5,
    },
    {
        "source": "news_rss",
        "title": "Nike Unveils Next-Generation Olympic Marathon Footwear Innovation",
        "content": "Nike today unveiled its Olympic performance lineup featuring upgraded ZoomX cushioning and carbon composite flyplates. Elite marathoners praise the responsive energy return, positioning Nike Running ahead of rivals Adidas and Puma ahead of Paris competition.",
        "author": "Reuters Sports",
        "url": "https://reuters.com/sports/nike-unveils-olympic-marathon-footwear",
        "likes": 1400,
        "comments": 180,
        "shares": 520,
        "hours_ago": 8,
    },

    # --- PRODUCT COMPLAINTS & QUALITY ISSUES ---
    {
        "source": "reddit",
        "title": "Air Max 270 bubble popped after just 3 months of normal walking",
        "content": "Bought a fresh pair of Air Max 270 directly from Nike.com. Walking to work today and heard a hiss, air unit completely deflated. Contacted Nike customer support and they claimed it's 'wear and tear' not covered under warranty. Anyone else experiencing terrible durability lately?",
        "author": "u/UrbanWalker",
        "url": "https://reddit.com/r/Sneakers/comments/air_max_270_bubble_popped",
        "likes": 3200,
        "comments": 610,
        "shares": 85,
        "hours_ago": 12,
    },
    {
        "source": "facebook",
        "title": "Nike customer service refund headache",
        "content": "Returned a pair of Nike Pegasus trail shoes three weeks ago with tracking showing delivered. Still no refund or email confirmation. Spent 45 minutes waiting on customer service live chat only to get disconnected. Very disappointing experience from such a large brand.",
        "author": "Sarah Jenkins",
        "url": "https://facebook.com/groups/runnersnetwork/posts/991203",
        "likes": 420,
        "comments": 95,
        "shares": 14,
        "hours_ago": 18,
    },
    {
        "source": "reddit",
        "title": "Nike Football Cleats - stud shearing issue on turf",
        "content": "Second pair of Nike Vapor Edge cleats this season where the corner stud cracked on artificial turf. Love the lightweight lockdown and traction, but the plastic soleplate durability is unacceptable for a $200 football cleat.",
        "author": "u/GridironPrep",
        "url": "https://reddit.com/r/football/comments/nike_cleat_durability_issues",
        "likes": 890,
        "comments": 142,
        "shares": 33,
        "hours_ago": 22,
    },
    {
        "source": "twitter",
        "title": "Nike sizing inconsistency is driving me crazy",
        "content": "Why is Nike sizing so inconsistent between models? I am a size 10 in Nike Pegasus, a 10.5 in Air Jordan 1s, and an 11 in Nike Invincible. Having to return and re-order multiple sizes every single time is such an unnecessary hassle.",
        "author": "@SneakerSizingGuru",
        "url": "https://twitter.com/sizingguru/status/178923091",
        "likes": 2100,
        "comments": 340,
        "shares": 180,
        "hours_ago": 14,
    },

    # --- HIGH POSITIVE & PRAISE POSTS ---
    {
        "source": "reddit",
        "title": "Nike Alphafly 3 carried me to a 15-minute Marathon PR!",
        "content": "Just completed the Berlin Marathon in the Alphafly 3. The energy return in the final 10k was unbelievable. Absolutely zero foot fatigue or blisters. Nike Running engineering is legitimately years ahead of the competition.",
        "author": "u/Sub3Hopeful",
        "url": "https://reddit.com/r/running/comments/nike_alphafly_3_marathon_pr",
        "likes": 4500,
        "comments": 380,
        "shares": 140,
        "hours_ago": 20,
    },
    {
        "source": "facebook",
        "title": "Nike Pegasus 40 still the king of gym trainers",
        "content": "Picked up a pair of Nike Pegasus on sale last week. Did 5 miles on the treadmill and heavy squats. Cushioned yet stable. For under $100 on discount, nothing beats it.",
        "author": "Mike Davenport",
        "url": "https://facebook.com/groups/crossfitandrunning/posts/102938",
        "likes": 310,
        "comments": 42,
        "shares": 8,
        "hours_ago": 26,
    },
    {
        "source": "reddit",
        "title": "Air Jordan 3 White Cement reimagined quality exceeded expectations",
        "content": "Finally got my hands on the reimagined Jordan 3s. The tumbled leather is super soft, elephant print looks authentic, and the pre-aged midsole is executed perfectly. Nike nailed this retro release!",
        "author": "u/OG_Kicks88",
        "url": "https://reddit.com/r/Jordans/comments/jordan_3_white_cement_quality",
        "likes": 3800,
        "comments": 290,
        "shares": 65,
        "hours_ago": 30,
    },
    {
        "source": "web",
        "title": "Nike's Move to Zero sustainability initiative shows measurable carbon reduction",
        "content": "Nike has published its latest environmental impact report demonstrating that over 75% of Nike footwear and apparel products now incorporate recycled polyester and Flyknit scrap waste, setting a benchmark for sustainable athletic wear.",
        "author": "GreenBusinessReview",
        "url": "https://greenbiz.com/article/nike-move-to-zero-annual-progress",
        "likes": 650,
        "comments": 38,
        "shares": 190,
        "hours_ago": 36,
    },

    # --- COMPETITOR COMPARISONS ---
    {
        "source": "reddit",
        "title": "Puma Nitro foam vs Nike ZoomX for daily mileage",
        "content": "I've been a die-hard Nike runner for 8 years, but Puma Velocity Nitro 3 has made me question my loyalty. The grip on wet asphalt blows Nike away and the price is $50 lower. Nike needs better wet-surface outsoles.",
        "author": "u/WetWeatherRunner",
        "url": "https://reddit.com/r/RunningShoeGeeks/comments/puma_nitro_vs_nike_zoomx",
        "likes": 1850,
        "comments": 260,
        "shares": 45,
        "hours_ago": 16,
    },
    {
        "source": "twitter",
        "title": "Under Armour vs Nike Football kit deal",
        "content": "Under Armour is quietly offering grassroots football academies much better sponsorship terms than Nike. Several premier youth clubs in Texas are switching kits this season citing better availability and turnaround time.",
        "author": "@YouthSportsBiz",
        "url": "https://twitter.com/youthsports/status/17894921",
        "likes": 890,
        "comments": 110,
        "shares": 75,
        "hours_ago": 24,
    },
    {
        "source": "reddit",
        "title": "Nike Air Max Pulse vs New Balance 990v6: which is better for standing 8 hours?",
        "content": "Need recommendation for hospital shifts. Tried Air Max Pulse and heels were cushioned but forefoot cramped up after hour 4. New Balance 990v6 provides wider toe box and balanced arch support. Nike really needs to offer wide sizes across all Air Max models.",
        "author": "u/NurseOnDuty",
        "url": "https://reddit.com/r/Sneakers/comments/air_max_pulse_vs_nb_990v6",
        "likes": 2400,
        "comments": 410,
        "shares": 92,
        "hours_ago": 10,
    },

    # --- STEADY & LOW-ENGAGEMENT REVIEWS ---
    {
        "source": "reddit",
        "title": "Nike Invincible 3 squeak after rain",
        "content": "Does anyone else have an annoying squeak in their Nike Invincible 3 after getting them wet? Cushion is great, but walking into the office sounds like a duck.",
        "author": "u/RainyDayCommuter",
        "url": "https://reddit.com/r/RunningShoeGeeks/comments/nike_invincible_squeak",
        "likes": 140,
        "comments": 45,
        "shares": 2,
        "hours_ago": 48,
    },
    {
        "source": "facebook",
        "title": "Local 10k prep with Nike Running Club app",
        "content": "Loving the audio-guided runs on the Nike Run Club app. Coach Bennett's tips helped me pace my 10k training without burning out early.",
        "author": "David Miller",
        "url": "https://facebook.com/groups/runnerscorner/posts/449102",
        "likes": 85,
        "comments": 12,
        "shares": 3,
        "hours_ago": 52,
    },
    {
        "source": "web",
        "title": "Nike reveals new Air Jordan 1 Low Golf colorways for summer season",
        "content": "Nike expands its golf footwear category with the Air Jordan 1 Low Golf in classic university blue. The silhouette combines iconic basketball heritage with spiked turf traction for golf enthusiasts.",
        "author": "GolfGearDigest",
        "url": "https://golfdigest.com/equipment/jordan-1-low-golf-summer",
        "likes": 320,
        "comments": 22,
        "shares": 65,
        "hours_ago": 60,
    },
]


class MockCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "mock"

    def is_enabled(self) -> bool:
        return True

    def collect(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        limit: int = 50
    ) -> List[RawPost]:
        """Returns realistic mock posts with dynamically adjusted timestamps."""
        now = utc_now()
        results: List[RawPost] = []

        # Repeat and vary items if limit > len(MOCK_SOCIAL_POSTS)
        items_to_generate = []
        multiplier = (limit // len(MOCK_SOCIAL_POSTS)) + 1
        for m in range(multiplier):
            for i, p in enumerate(MOCK_SOCIAL_POSTS):
                item = p.copy()
                item["external_id"] = f"mock_{item['source']}_{i}_{m}"
                # Slight variation in engagement and time
                item["hours_ago"] = p["hours_ago"] + (m * 24)
                item["likes"] = int(p["likes"] * (1.0 + (random.uniform(-0.1, 0.1) if m > 0 else 0)))
                item["comments"] = int(p["comments"] * (1.0 + (random.uniform(-0.1, 0.1) if m > 0 else 0)))
                item["shares"] = int(p["shares"] * (1.0 + (random.uniform(-0.1, 0.1) if m > 0 else 0)))
                items_to_generate.append(item)

        items_to_generate = items_to_generate[:limit]

        for p in items_to_generate:
            pub_date = now - timedelta(hours=p["hours_ago"])
            results.append(
                RawPost(
                    source=p["source"],
                    external_id=p["external_id"],
                    url=p["url"],
                    author=p["author"],
                    title=p["title"],
                    content=p["content"],
                    published_at=pub_date,
                    likes=p["likes"],
                    comments=p["comments"],
                    shares=p["shares"],
                    raw_metadata={"is_demo": True, "source_category": "social_discussion"}
                )
            )

        return results
