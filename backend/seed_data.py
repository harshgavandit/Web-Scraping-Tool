"""Initialize brand configuration without creating conversation records."""

from app.database.session import Base, SessionLocal, engine
from app.models.brand import Brand
from app.models.competitor import Competitor
from app.models.organization import Organization
from app.models.tracked_keyword import TrackedKeyword


COMPETITORS = ("Adidas", "Puma", "New Balance", "Under Armour")
KEYWORDS = (
    ("Nike", "brand"),
    ("Nike shoes", "brand"),
    ("Pegasus", "product"),
    ("Air Max", "product"),
    ("Air Jordan", "product"),
    ("Nike Running", "product"),
)


def seed_database() -> None:
    """Create the default Nike workspace; never generate posts or analysis."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        organization = db.query(Organization).filter(Organization.name == "Evidently AEO").first()
        if organization is None:
            organization = Organization(name="Evidently AEO")
            db.add(organization)
            db.flush()

        brand = db.query(Brand).filter(Brand.name == "Nike").first()
        if brand is None:
            brand = Brand(
                organization_id=organization.id,
                name="Nike",
                description="Nike brand intelligence from verified public web sources.",
            )
            db.add(brand)
            db.flush()

        existing_competitors = {item.name.casefold() for item in brand.competitors}
        for name in COMPETITORS:
            if name.casefold() not in existing_competitors:
                db.add(Competitor(brand_id=brand.id, name=name))

        existing_keywords = {item.keyword.casefold() for item in brand.keywords}
        for keyword, category in KEYWORDS:
            if keyword.casefold() not in existing_keywords:
                db.add(TrackedKeyword(
                    brand_id=brand.id,
                    keyword=keyword,
                    category=category,
                    active=True,
                ))

        db.commit()
        print("Brand configuration is ready. No conversation data was generated.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
