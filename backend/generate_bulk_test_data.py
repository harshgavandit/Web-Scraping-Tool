import sys
import os
import random
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.session import SessionLocal, engine, Base
from app.models.brand import Brand
from app.models.post import Post
from app.models.post_analysis import PostAnalysis
from app.services.deduplication_service import compute_content_hash
from app.services.virality_service import calculate_engagement_and_virality
from app.utils.datetime_utils import utc_now

SOURCES = ["reddit", "twitter", "facebook", "news_rss", "web"]
PRODUCTS = ["Pegasus", "Air Max", "Air Jordan", "Nike Running", "Nike Football", "Vomero", "Invincible"]
COMPETITORS = ["Adidas", "Puma", "New Balance", "Under Armour", None, None]
SENTIMENTS = ["Positive", "Negative", "Neutral", "Mixed"]
TOPICS = [
    "Running Shoes / Pricing", "Customer Service / Drops", "Build Quality & Durability",
    "Product Comfort & Fit", "Heritage & Craftsmanship", "All-Day Standing Comfort",
    "Sustainability & Materials", "Wet Traction / Grip", "Lifestyle Silhouette Fatigue"
]


def generate_bulk_records(total_count: int = 10000, batch_size: int = 1000):
    print(f"Generating {total_count} realistic social chatter records in batches of {batch_size}...")
    start_time = time.time()
    db = SessionLocal()

    try:
        brand = db.query(Brand).filter(Brand.name == "Nike").first()
        if not brand:
            print("Please run seed_data.py first to create the Nike brand.")
            return

        now = utc_now()
        inserted_total = 0

        for batch_idx in range(0, total_count, batch_size):
            posts_batch = []
            analyses_batch = []

            for i in range(batch_size):
                idx = batch_idx + i
                src = random.choice(SOURCES)
                prod = random.choice(PRODUCTS)
                comp = random.choice(COMPETITORS)
                sentiment = random.choice(SENTIMENTS)
                topic = random.choice(TOPICS)

                likes = int(random.expovariate(1 / 400)) + random.randint(5, 500)
                comments = int(likes * random.uniform(0.05, 0.45))
                shares = int(likes * random.uniform(0.01, 0.2))
                hours_ago = random.randint(1, 720)  # up to 30 days
                pub_date = now - timedelta(hours=hours_ago)

                content = (
                    f"Discussion regarding {prod} performance and features. "
                    f"Comparing against market alternatives like {comp or 'standard trainers'}. "
                    f"Sentiment around this discussion is generally {sentiment.lower()}."
                )
                title = f"Thoughts on {prod} vs {comp or 'alternatives'} #{idx}"
                c_hash = compute_content_hash(f"{content}_{idx}_{src}")

                eng_count, velocity, vir_score, vir_level, is_viral = calculate_engagement_and_virality(
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    published_at=pub_date,
                    source=src
                )

                sent_score = 0.6 if sentiment == "Positive" else (-0.6 if sentiment == "Negative" else (0.1 if sentiment == "Mixed" else 0.0))

                post = Post(
                    brand_id=brand.id,
                    source=src,
                    external_id=f"bulk_{idx}_{src}",
                    url=f"https://social.example.com/{src}/bulk_{idx}",
                    author=f"user_{idx}",
                    title=title,
                    content=content,
                    published_at=pub_date,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    engagement_count=eng_count,
                    engagement_velocity=velocity,
                    raw_metadata={"is_demo": True, "bulk_test": True},
                    content_hash=c_hash
                )
                db.add(post)
                db.flush()

                analysis = PostAnalysis(
                    post_id=post.id,
                    sentiment=sentiment,
                    sentiment_score=sent_score,
                    topic=topic,
                    product=prod,
                    competitor=comp,
                    key_positive=f"Strong reception for {prod}" if sentiment in ("Positive", "Mixed") else None,
                    key_negative=f"Pricing concerns on {prod}" if sentiment in ("Negative", "Mixed") else None,
                    summary=f"Users evaluate {prod} in comparison to competitors.",
                    recommendation=f"Maintain consistent product positioning for {prod}.",
                    virality_score=vir_score,
                    virality_level=vir_level,
                    is_viral=is_viral,
                    analyzed_at=now,
                    analysis_version="1.0",
                    model_used="bulk_generator"
                )
                db.add(analysis)

            db.commit()
            inserted_total += batch_size
            print(f"Inserted {inserted_total}/{total_count} records ({time.time() - start_time:.2f}s elapsed)...")

        total_time = time.time() - start_time
        print(f"Done! Inserted {inserted_total} records in {total_time:.2f} seconds.")

    except Exception as e:
        db.rollback()
        print(f"Error during bulk generation: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    generate_bulk_records(count)
