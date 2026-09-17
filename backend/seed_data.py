import sys
import os
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.session import SessionLocal, Base, engine
from app.models.organization import Organization
from app.models.brand import Brand
from app.models.competitor import Competitor
from app.models.tracked_keyword import TrackedKeyword
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.services.deduplication_service import compute_content_hash
from app.services.sentiment_service import analyze_local_sentiment
from app.services.virality_service import calculate_engagement_and_virality
from app.services.openai_service import heuristic_fallback_analyze
from app.utils.datetime_utils import utc_now

SEED_POSTS = [
    # --- VIRAL & HIGH IMPACT (Mixed, Negative, and Positive) ---
    {
        "source": "reddit",
        "external_id": "seed_reddit_01",
        "url": "https://reddit.com/r/RunningShoeGeeks/comments/nike_pegasus_41_honest_review",
        "author": "u/MarathonChaser",
        "title": "Nike Pegasus 41 honest review after 250 miles: great daily trainer, but is $145 becoming too steep?",
        "content": "Nike Pegasus is probably the most comfortable running shoe I've owned, but it's becoming too expensive. The ReactX foam is noticeably springier than the 40, but retail prices keep climbing while competitors like New Balance offer comparable cushion for less.",
        "likes": 8420,
        "comments": 1250,
        "shares": 430,
        "hours_ago": 2,
        "topic": "Running Shoes / Pricing",
        "product": "Pegasus",
        "competitor": "New Balance",
        "sentiment": "Mixed",
        "sentiment_score": 0.28,
        "summary": "Users strongly appreciate Nike Pegasus comfort but are increasingly concerned about pricing.",
        "key_positive": "Comfort and ReactX foam energy return for daily training",
        "key_negative": "Steep retail price increases compared to competitors",
        "recommendation": "Highlight comfort and performance while strengthening value-for-money messaging."
    },
    {
        "source": "reddit",
        "external_id": "seed_reddit_02",
        "url": "https://reddit.com/r/Sneakers/comments/snkrs_app_completely_broken",
        "author": "u/SoleCollector99",
        "title": "The SNKRS app is completely broken for real sneakerheads",
        "content": "Tried to get the Military Blue Air Jordan 4 release this morning. App froze at 10:00:01 AM, pending for 25 minutes, then hit with 'Error: Out of Stock'. Meanwhile resellers on StockX already have 50 pairs listed. Nike customer service just told me 'better luck next drop'. Fix your bot protection!",
        "likes": 12500,
        "comments": 2400,
        "shares": 890,
        "hours_ago": 4,
        "topic": "Customer Experience / Drops",
        "product": "Air Jordan",
        "competitor": None,
        "sentiment": "Negative",
        "sentiment_score": -0.72,
        "summary": "Sneaker enthusiasts express severe anger over SNKRS app server freezes and bot reseller dominance during Jordan drops.",
        "key_positive": None,
        "key_negative": "App crashes, bot infiltration, and dismissive customer service",
        "recommendation": "Overhaul SNKRS queue verification algorithms and publish transparent anti-bot accountability updates."
    },
    {
        "source": "twitter",
        "external_id": "seed_twitter_03",
        "url": "https://twitter.com/kicksdaily/status/17892019283",
        "author": "@KicksDaily",
        "title": "Adidas vs Nike pricing dilemma",
        "content": "Nike shoes are noticeably more comfortable for long-distance training, but Adidas has drastically better pricing and sales right now. Hard to justify $180 on Nike Air Max when Ultraboosts are regularly on sale for $110.",
        "likes": 6400,
        "comments": 820,
        "shares": 950,
        "hours_ago": 3,
        "topic": "Comfort / Pricing Comparison",
        "product": "Air Max",
        "competitor": "Adidas",
        "sentiment": "Mixed",
        "sentiment_score": 0.15,
        "summary": "Users prefer Nike for comfort but consider Adidas more competitive on price.",
        "key_positive": "Superior long-distance cushioning and comfort",
        "key_negative": "High retail prices relative to frequent Adidas promotional discounting",
        "recommendation": "Strengthen Nike's value messaging without weakening premium positioning."
    },
    {
        "source": "reddit",
        "external_id": "seed_reddit_04",
        "url": "https://reddit.com/r/running/comments/alphafly_3_marathon_pr",
        "author": "u/Sub3Runner",
        "title": "Nike Alphafly 3 carried me to a sub-3 marathon PR in Boston!",
        "content": "Just crossed the line in 2:58:14 wearing the Nike Alphafly 3. The propulsion and ZoomX foam absorb so much road chatter that my quads felt fresh through Heartbreak Hill. Nike Running remains unmatched at the marathon distance!",
        "likes": 5600,
        "comments": 410,
        "shares": 280,
        "hours_ago": 6,
        "topic": "Running & Performance",
        "product": "Nike Running",
        "competitor": None,
        "sentiment": "Positive",
        "sentiment_score": 0.88,
        "summary": "Marathoners enthusiastically celebrate massive PR achievements enabled by Nike Alphafly 3 ZoomX propulsion.",
        "key_positive": "Elite energy return, quad fatigue reduction, and carbon plate propulsion",
        "key_negative": None,
        "recommendation": "Feature real everyday marathoners in organic social storytelling to cement marathon authority."
    },
    {
        "source": "reddit",
        "external_id": "seed_reddit_05",
        "url": "https://reddit.com/r/streetwear/comments/new_balance_taking_over",
        "author": "u/StreetStyleTrends",
        "title": "Why New Balance is taking over Nike's lifestyle market",
        "content": "Nike used to dominate every lifestyle category with Dunks and Air Force 1s, but market fatigue has set in. New Balance 9060 and 1906R offer superior materials and all-day comfort without squeaking or creasing in 2 days. Nike needs fresh silhouettes, not another colorway of the Panda Dunk.",
        "likes": 7800,
        "comments": 940,
        "shares": 310,
        "hours_ago": 5,
        "topic": "Lifestyle Market / Fatigue",
        "product": "Air Max",
        "competitor": "New Balance",
        "sentiment": "Negative",
        "sentiment_score": -0.38,
        "summary": "Fashion community highlights silhouette fatigue with Nike retro re-releases while New Balance captures lifestyle mindshare with better comfort.",
        "key_positive": None,
        "key_negative": "Over-saturation of Dunks and material quality complaints",
        "recommendation": "Accelerate innovation in everyday lifestyle comfort silhouettes and moderate legacy retro release cadences."
    },
    {
        "source": "news_rss",
        "external_id": "seed_news_06",
        "url": "https://reuters.com/sports/nike-unveils-olympic-marathon-innovations",
        "author": "Reuters Sports",
        "title": "Nike Unveils Next-Generation Olympic Marathon Footwear Innovation Ahead of Summer Games",
        "content": "Nike today unveiled its flagship Olympic competition lineup featuring upgraded ZoomX cushioning and carbon composite flyplates. Elite marathoners praise the responsive energy return, positioning Nike Running ahead of rivals Adidas and Puma ahead of Paris competition.",
        "likes": 1800,
        "comments": 220,
        "shares": 610,
        "hours_ago": 8,
        "topic": "Olympic Innovation & Media",
        "product": "Nike Running",
        "competitor": "Adidas",
        "sentiment": "Positive",
        "sentiment_score": 0.65,
        "summary": "Global sports press highlights Nike's cutting-edge Olympic marathon footwear innovation.",
        "key_positive": "Technological leadership and elite athlete endorsements",
        "key_negative": None,
        "recommendation": "Capitalize on Olympic media buzz with localized commercial running footwear campaigns."
    },

    # --- COMPLAINTS, DURABILITY & CUSTOMER SERVICE ---
    {
        "source": "reddit",
        "external_id": "seed_reddit_07",
        "url": "https://reddit.com/r/Sneakers/comments/air_max_270_popped_bubble",
        "author": "u/UrbanWalker",
        "title": "Air Max 270 bubble popped after just 3 months of normal walking",
        "content": "Bought a fresh pair of Air Max 270 directly from Nike.com. Walking to work today and heard a hiss, air unit completely deflated. Contacted Nike customer support and they claimed it's 'wear and tear' not covered under warranty. Anyone else experiencing terrible durability lately?",
        "likes": 3200,
        "comments": 610,
        "shares": 85,
        "hours_ago": 12,
        "topic": "Build Quality & Durability",
        "product": "Air Max",
        "competitor": None,
        "sentiment": "Negative",
        "sentiment_score": -0.65,
        "summary": "Customer reports Air Max 270 air cushion popped prematurely and was denied warranty coverage by customer support.",
        "key_positive": None,
        "key_negative": "Air unit deflation failure and unhelpful warranty policy",
        "recommendation": "Review Air Max outsole puncture resistance and train support representatives on warranty goodwill."
    },
    {
        "source": "facebook",
        "external_id": "seed_fb_08",
        "url": "https://facebook.com/groups/runnersnetwork/posts/991203",
        "author": "Sarah Jenkins",
        "title": "Nike customer service refund headache",
        "content": "Returned a pair of Nike Pegasus trail shoes three weeks ago with tracking showing delivered. Still no refund or email confirmation. Spent 45 minutes waiting on customer service live chat only to get disconnected. Very disappointing experience from such a large brand.",
        "likes": 420,
        "comments": 95,
        "shares": 14,
        "hours_ago": 18,
        "topic": "Customer Service & Returns",
        "product": "Pegasus",
        "competitor": None,
        "sentiment": "Negative",
        "sentiment_score": -0.78,
        "summary": "Customer voices deep frustration over delayed return refunds and dropped customer support chat sessions.",
        "key_positive": None,
        "key_negative": "Unresolved returns backlog and unresponsive chat queue",
        "recommendation": "Audit return fulfillment workflows and implement automated tracking status notifications for customer returns."
    },
    {
        "source": "reddit",
        "external_id": "seed_reddit_09",
        "url": "https://reddit.com/r/football/comments/nike_cleat_durability",
        "author": "u/GridironPrep",
        "title": "Nike Football Cleats - stud shearing issue on turf",
        "content": "Second pair of Nike Vapor Edge cleats this season where the corner stud cracked on artificial turf. Love the lightweight lockdown and traction, but the plastic soleplate durability is unacceptable for a $200 football cleat.",
        "likes": 890,
        "comments": 142,
        "shares": 33,
        "hours_ago": 22,
        "topic": "Product Durability / Cleats",
        "product": "Nike Football",
        "competitor": None,
        "sentiment": "Negative",
        "sentiment_score": -0.42,
        "summary": "Football players report repeated cracked studs on turf soleplates despite praising fit and traction.",
        "key_positive": "Lightweight lockdown and explosive traction",
        "key_negative": "Brittle stud durability on modern turf fields",
        "recommendation": "Reinforce turf plate polymer formulations and offer specialized warranty replacements for student athletes."
    },
    {
        "source": "twitter",
        "external_id": "seed_tw_10",
        "url": "https://twitter.com/sizingguru/status/178923091",
        "author": "@SneakerSizingGuru",
        "title": "Nike sizing inconsistency is driving me crazy",
        "content": "Why is Nike sizing so inconsistent between models? I am a size 10 in Nike Pegasus, a 10.5 in Air Jordan 1s, and an 11 in Nike Invincible. Having to return and re-order multiple sizes every single time is such an unnecessary hassle.",
        "likes": 2100,
        "comments": 340,
        "shares": 180,
        "hours_ago": 14,
        "topic": "Sizing & Fit Inconsistency",
        "product": "Pegasus",
        "competitor": None,
        "sentiment": "Negative",
        "sentiment_score": -0.52,
        "summary": "Sneaker buyers vent frustration over erratic size variations across different Nike silhouettes.",
        "key_positive": None,
        "key_negative": "Sizing discrepancies causing repeated returns",
        "recommendation": "Introduce interactive 3D fit recommendations and standardized true-to-size guide widgets on product pages."
    },

    # --- PRAISE, COMFORT & INNOVATION ---
    {
        "source": "facebook",
        "external_id": "seed_fb_11",
        "url": "https://facebook.com/groups/crossfitandrunning/posts/102938",
        "author": "Mike Davenport",
        "title": "Nike Pegasus 40 still the king of gym trainers",
        "content": "Picked up a pair of Nike Pegasus on sale last week. Did 5 miles on the treadmill and heavy squats. Cushioned yet stable. For under $100 on discount, nothing beats it.",
        "likes": 310,
        "comments": 42,
        "shares": 8,
        "hours_ago": 26,
        "topic": "Gym Training & Comfort",
        "product": "Pegasus",
        "competitor": None,
        "sentiment": "Positive",
        "sentiment_score": 0.74,
        "summary": "Fitness enthusiasts endorse Nike Pegasus as a reliable all-around trainer for cardio and lifting.",
        "key_positive": "Versatile cushioning, stability, and great discount value",
        "key_negative": None,
        "recommendation": "Target cross-training gym demographics highlighting versatile cross-discipline utility."
    },
    {
        "source": "reddit",
        "external_id": "seed_reddit_12",
        "url": "https://reddit.com/r/Jordans/comments/jordan_3_white_cement_quality",
        "author": "u/OG_Kicks88",
        "title": "Air Jordan 3 White Cement reimagined quality exceeded expectations",
        "content": "Finally got my hands on the reimagined Jordan 3s. The tumbled leather is super soft, elephant print looks authentic, and the pre-aged midsole is executed perfectly. Nike nailed this retro release!",
        "likes": 3800,
        "comments": 290,
        "shares": 65,
        "hours_ago": 30,
        "topic": "Heritage & Craftsmanship",
        "product": "Air Jordan",
        "competitor": None,
        "sentiment": "Positive",
        "sentiment_score": 0.86,
        "summary": "Sneaker collectors praise the craftsmanship, premium leather, and authentic styling of recent Jordan 3 retro releases.",
        "key_positive": "Superior tumbled leather, accurate shape, and vintage aesthetics",
        "key_negative": None,
        "recommendation": "Maintain premium material quality standards across retro Jordan heritage collections."
    },
    {
        "source": "web",
        "external_id": "seed_web_13",
        "url": "https://greenbiz.com/article/nike-move-to-zero-annual-progress",
        "author": "GreenBusinessReview",
        "title": "Nike's Move to Zero sustainability initiative shows measurable carbon reduction",
        "content": "Nike has published its latest environmental impact report demonstrating that over 75% of Nike footwear and apparel products now incorporate recycled polyester and Flyknit scrap waste, setting a benchmark for sustainable athletic wear.",
        "likes": 650,
        "comments": 38,
        "shares": 190,
        "hours_ago": 36,
        "topic": "Sustainability & Materials",
        "product": "Nike Running",
        "competitor": None,
        "sentiment": "Positive",
        "sentiment_score": 0.59,
        "summary": "Corporate and environmental media praise Nike's Move to Zero program for measurable circular manufacturing progress.",
        "key_positive": "75%+ recycled material adoption and circular manufacturing leadership",
        "key_negative": None,
        "recommendation": "Promote eco-conscious product features to attract younger Gen-Z eco-minded consumers."
    },

    # --- COMPETITOR COMPARISONS ---
    {
        "source": "reddit",
        "external_id": "seed_reddit_14",
        "url": "https://reddit.com/r/RunningShoeGeeks/comments/puma_nitro_vs_nike_zoomx",
        "author": "u/WetWeatherRunner",
        "title": "Puma Nitro foam vs Nike ZoomX for daily mileage",
        "content": "I've been a die-hard Nike runner for 8 years, but Puma Velocity Nitro 3 has made me question my loyalty. The grip on wet asphalt blows Nike away and the price is $50 lower. Nike needs better wet-surface outsoles.",
        "likes": 1850,
        "comments": 260,
        "shares": 45,
        "hours_ago": 16,
        "topic": "Wet Traction / Price vs Puma",
        "product": "Nike Running",
        "competitor": "Puma",
        "sentiment": "Mixed",
        "sentiment_score": 0.05,
        "summary": "Runners note Puma offers superior wet-surface outsole rubber grip at a lower price point than Nike.",
        "key_positive": "Nike ZoomX foam springiness",
        "key_negative": "Slippery wet-weather traction compared to Puma Pumagrip",
        "recommendation": "Upgrade wet-traction compound testing on daily road running shoes."
    },
    {
        "source": "twitter",
        "external_id": "seed_tw_15",
        "url": "https://twitter.com/youthsports/status/17894921",
        "author": "@YouthSportsBiz",
        "title": "Under Armour vs Nike Football kit deal",
        "content": "Under Armour is quietly offering grassroots football academies much better sponsorship terms than Nike. Several premier youth clubs in Texas are switching kits this season citing better availability and turnaround time.",
        "likes": 890,
        "comments": 110,
        "shares": 75,
        "hours_ago": 24,
        "topic": "Grassroots Sponsorships",
        "product": "Nike Football",
        "competitor": "Under Armour",
        "sentiment": "Negative",
        "sentiment_score": -0.22,
        "summary": "Youth football leagues report switching kit providers from Nike to Under Armour due to supply delivery turnaround.",
        "key_positive": None,
        "key_negative": "Delivery delays and inflexible academy sponsorship tiers",
        "recommendation": "Streamline direct-to-club fulfillment for scholastic and club football programs."
    },
    {
        "source": "reddit",
        "external_id": "seed_reddit_16",
        "url": "https://reddit.com/r/Sneakers/comments/air_max_pulse_vs_nb_990v6",
        "author": "u/NurseOnDuty",
        "title": "Nike Air Max Pulse vs New Balance 990v6: which is better for standing 8 hours?",
        "content": "Need recommendation for hospital shifts. Tried Air Max Pulse and heels were cushioned but forefoot cramped up after hour 4. New Balance 990v6 provides wider toe box and balanced arch support. Nike really needs to offer wide sizes across all Air Max models.",
        "likes": 2400,
        "comments": 410,
        "shares": 92,
        "hours_ago": 10,
        "topic": "All-Day Standing Comfort",
        "product": "Air Max",
        "competitor": "New Balance",
        "sentiment": "Mixed",
        "sentiment_score": 0.12,
        "summary": "Healthcare professionals compare Air Max against New Balance 990v6, highlighting need for wider toe box comfort.",
        "key_positive": "Good heel cushioning",
        "key_negative": "Narrow forefoot causing foot fatigue during prolonged shifts",
        "recommendation": "Expand wide-width (2E/4E) availability in Air Max comfort styles for standing professions."
    },

    # --- MORE DIVERSE POSTS TO REACH 50+ REALISTIC SEEDED RECORDS ---
]

# Generate additional realistic variations to exceed 60+ records
EXTRA_THEMES = [
    ("reddit", "u/SoleSearcher", "Nike Vomero 17 vs Pegasus 41 comparison", "The Vomero 17 dual foam setup is vastly superior to the Pegasus 41 for easy days. Well worth the extra $20.", 950, 110, 25, 32, "Product Comparison", "Pegasus", None, "Positive", 0.62, "Vomero praised over Pegasus for recovery miles.", "Dual-density cushion", None, "Highlight Vomero as the premium recovery companion."),
    ("twitter", "@SneakerCop", "Air Jordan 4 Bred Reimagined restock rumors", "Nike just loaded style codes for a potential Jordan 4 Bred restock next month. Get SNKRS app ready.", 1450, 230, 410, 15, "Product Restock & Hype", "Air Jordan", None, "Positive", 0.35, "Speculation over Air Jordan 4 Bred restock gains traction.", "High consumer anticipation", None, "Prepare server scalability to prevent drop crashes."),
    ("facebook", "Marcus Vance", "Nike Air Max 90 classic durability check", "Wearing my Air Max 90s for 4 years straight and they still look amazing with zero sole cracks. Timeless shoe.", 280, 31, 5, 42, "Durability & Heritage", "Air Max", None, "Positive", 0.81, "Customers praise longevity of Air Max 90 retro releases.", "Excellent multi-year durability", None, "Emphasize enduring heritage and longevity in lifestyle creative."),
    ("reddit", "u/TrackCoachSam", "Nike Running spike plates breaking in colder weather", "Had two athletes snap their Superfly spike plates during an early spring meet in 40 degree weather. Is the plastic becoming more brittle?", 620, 89, 18, 55, "Track Spikes / Cold Weather", "Nike Running", None, "Negative", -0.45, "Track coaches report spike plate brittleness in low temperatures.", None, "Plate snapping in cold weather", "Review cold-temperature polymer resilience for competition spikes."),
    ("web", "SneakerFreaker", "Adidas Samba boom slows as Nike Field General returns", "With Adidas Samba mania cooling down, Nike's revival of the 1982 Field General offers a strong retro contender in the low-profile casual market.", 820, 74, 140, 28, "Retro Low-Profile Trend", "Nike Running", "Adidas", "Positive", 0.48, "Market analysts note Nike Field General is challenging Adidas Samba dominance.", "Strong retro low-profile positioning", None, "Ramp up influencer styling around Field General casual silhouettes."),
    ("reddit", "u/TrailBlazerDan", "Nike Pegasus Trail 4 GORE-TEX is the best winter commuter shoe ever made", "Waterproof, warm, super grippy on icy pavement, and doesn't look like an ugly hiking boot. Nike knocked it out of the park with this model.", 1920, 240, 85, 38, "Winter Footwear & Weatherproofing", "Pegasus", None, "Positive", 0.89, "Commuters celebrate Pegasus Trail GORE-TEX for winter functionality and aesthetics.", "Waterproof membrane and sleek styling", None, "Promote Pegasus Trail GORE-TEX aggressively ahead of winter rainy seasons."),
    ("twitter", "@KicksAlert", "Nike customer service queue times hit 60 mins today", "Multiple followers reporting customer service phone lines and live chat completely backed up today following the weekend drop.", 1100, 310, 190, 7, "Customer Service Delay", None, None, "Negative", -0.68, "Social media accounts complain about extended customer support hold times.", None, "Customer service wait times", "Implement automated callback options during peak drop days."),
    ("reddit", "u/UltraDistance", "Nike ZoomX Streakfly durability after 100km", "Streakfly is super fast for 5k and 10k, but the exposed ZoomX under the midfoot is completely chewed up on road gravel. Expected better wear for $160.", 750, 130, 22, 65, "Race Day Durability", "Nike Running", None, "Mixed", -0.15, "Racers love Streakfly speed but criticize midfoot outsole gravel wear.", "Ultra-lightweight feel and responsiveness", "Rapid outsole abrasion on rough surfaces", "Add full-length thin rubber coverage to prevent premature foam shredding."),
    ("facebook", "Rachel Adams", "Under Armour youth soccer cleats vs Nike", "Bought Nike Jr Mercurials and the laces ripped through the eyelet on day two. Exchanged for Under Armour and the stitching is much tougher.", 195, 28, 4, 72, "Youth Footwear Durability", "Nike Football", "Under Armour", "Negative", -0.58, "Parents compare youth soccer durability favorably toward Under Armour.", None, "Torn eyelets on junior football boots", "Strengthen eyelet reinforcement on youth football footwear."),
    ("reddit", "u/SneakerTherapy", "Puma making serious moves with LaMelo signature line against Nike Basketball", "Nike used to own 90% of high school basketball courts. Now half the kids are rocking Puma MB series because the colorways are wilder and price is lower.", 2150, 340, 110, 19, "Basketball Market Competition", "Air Jordan", "Puma", "Mixed", 0.22, "Youth basketball observers note Puma is capturing share from Nike with bold designs.", "Nike heritage prestige", "Puma winning on bold styling and accessible price", "Inject more expressive color blocking into non-signature basketball tiers.")
]


def seed_database():
    print("Beginning database seed...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Ensure Organization
        org = db.query(Organization).first()
        if not org:
            org = Organization(name="Nike Global Brand Marketing")
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"Created organization: {org.name}")

        # 2. Ensure Nike Brand
        brand = db.query(Brand).filter(Brand.name == "Nike").first()
        if not brand:
            brand = Brand(
                organization_id=org.id,
                name="Nike",
                description="Global leader in athletic footwear, apparel, equipment, and sports culture."
            )
            db.add(brand)
            db.commit()
            db.refresh(brand)
            print(f"Created brand: {brand.name}")

        # 3. Add Competitors
        competitors_to_add = ["Adidas", "Puma", "New Balance", "Under Armour"]
        existing_comps = {c.name for c in db.query(Competitor).filter(Competitor.brand_id == brand.id).all()}
        for comp_name in competitors_to_add:
            if comp_name not in existing_comps:
                db.add(Competitor(brand_id=brand.id, name=comp_name))
        db.commit()

        # 4. Add Tracked Keywords and Products
        tracked_items = [
            ("Nike", "brand"),
            ("Nike shoes", "brand"),
            ("Nike pricing", "brand"),
            ("Nike customer service", "brand"),
            ("Nike quality", "brand"),
            ("Nike vs Adidas", "brand"),
            ("Air Max", "product"),
            ("Air Jordan", "product"),
            ("Pegasus", "product"),
            ("Nike Running", "product"),
            ("Nike Football", "product"),
            ("ZoomX", "product"),
            ("SNKRS", "campaign"),
        ]
        existing_keywords = {k.keyword for k in db.query(TrackedKeyword).filter(TrackedKeyword.brand_id == brand.id).all()}
        for kw, cat in tracked_items:
            if kw not in existing_keywords:
                db.add(TrackedKeyword(brand_id=brand.id, keyword=kw, category=cat, active=True))
        db.commit()

        # 5. Populate Seed Posts and Analysis
        now = utc_now()
        all_posts_data = list(SEED_POSTS)

        # Append extra themes with timestamp adjustments
        for idx, item in enumerate(EXTRA_THEMES):
            src, auth, title, content, likes, comms, shares, h_ago, top, prod, comp, sent, sent_sc, summ, pos, neg, rec = item
            all_posts_data.append({
                "source": src,
                "external_id": f"seed_extra_{idx}_{src}",
                "url": f"https://social.example.com/{src}/{idx}",
                "author": auth,
                "title": title,
                "content": content,
                "likes": likes,
                "comments": comms,
                "shares": shares,
                "hours_ago": h_ago,
                "topic": top,
                "product": prod,
                "competitor": comp,
                "sentiment": sent,
                "sentiment_score": sent_sc,
                "summary": summ,
                "key_positive": pos,
                "key_negative": neg,
                "recommendation": rec
            })

        # Generate additional realistic variations to exceed 70+ records
        for i in range(1, 55):
            base_ref = SEED_POSTS[i % len(SEED_POSTS)]
            hours = 12 + (i * 3)
            all_posts_data.append({
                "source": base_ref["source"],
                "external_id": f"seed_extended_{i}_{base_ref['source']}",
                "url": f"{base_ref['url']}_ext_{i}",
                "author": f"{base_ref['author']}_{i}",
                "title": f"[Community Thread] {base_ref['title']}",
                "content": f"{base_ref['content']} (Follow-up discussion #{i})",
                "likes": max(15, int(base_ref["likes"] * (0.2 + (i % 5) * 0.15))),
                "comments": max(5, int(base_ref["comments"] * (0.2 + (i % 5) * 0.12))),
                "shares": max(2, int(base_ref["shares"] * (0.2 + (i % 4) * 0.1))),
                "hours_ago": hours,
                "topic": base_ref["topic"],
                "product": base_ref["product"],
                "competitor": base_ref["competitor"],
                "sentiment": base_ref["sentiment"],
                "sentiment_score": base_ref["sentiment_score"],
                "summary": base_ref["summary"],
                "key_positive": base_ref["key_positive"],
                "key_negative": base_ref["key_negative"],
                "recommendation": base_ref["recommendation"],
            })

        inserted_count = 0
        for p_data in all_posts_data:
            # Check existing by external_id
            ext_id = p_data["external_id"]
            existing = db.query(Post).filter(Post.source == p_data["source"], Post.external_id == ext_id).first()
            if existing:
                continue

            pub_date = now - timedelta(hours=p_data["hours_ago"])
            c_hash = compute_content_hash(p_data["content"])

            eng_count, velocity, vir_score, vir_level, is_viral = calculate_engagement_and_virality(
                likes=p_data["likes"],
                comments=p_data["comments"],
                shares=p_data["shares"],
                published_at=pub_date,
                source=p_data["source"]
            )

            post = Post(
                brand_id=brand.id,
                source=p_data["source"],
                external_id=ext_id,
                url=p_data["url"],
                author=p_data["author"],
                title=p_data["title"],
                content=p_data["content"],
                published_at=pub_date,
                likes=p_data["likes"],
                comments=p_data["comments"],
                shares=p_data["shares"],
                engagement_count=eng_count,
                engagement_velocity=velocity,
                raw_metadata={"is_demo": True, "seed": True},
                content_hash=c_hash
            )
            db.add(post)
            db.flush()

            analysis = PostAnalysis(
                post_id=post.id,
                sentiment=p_data["sentiment"],
                sentiment_score=p_data["sentiment_score"],
                topic=p_data["topic"],
                product=p_data["product"],
                competitor=p_data["competitor"],
                key_positive=p_data["key_positive"],
                key_negative=p_data["key_negative"],
                summary=p_data["summary"],
                recommendation=p_data["recommendation"],
                virality_score=vir_score,
                virality_level=vir_level,
                is_viral=is_viral,
                analyzed_at=now,
                analysis_version="1.0",
                model_used="demo_seed_vader"
            )
            db.add(analysis)
            inserted_count += 1

        db.commit()
        print(f"Successfully seeded {inserted_count} posts and analyses into database.")

    except Exception as e:
        db.rollback()
        print(f"Seeding error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
