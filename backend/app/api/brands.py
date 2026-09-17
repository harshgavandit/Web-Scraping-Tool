from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.brand import Brand
from app.models.competitor import Competitor
from app.models.tracked_keyword import TrackedKeyword
from app.models.organization import Organization
from app.schemas.brand import BrandResponse, BrandCreate, BrandDetailResponse
from app.schemas.competitor import CompetitorCreate, CompetitorResponse
from app.schemas.tracked_keyword import TrackedKeywordCreate, TrackedKeywordResponse

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("", response_model=List[BrandResponse])
def list_brands(db: Session = Depends(get_db)):
    """List all configured brands."""
    return db.query(Brand).all()


@router.post("", response_model=BrandDetailResponse)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    """Create a new brand along with initial competitors and keywords."""
    # Ensure organization exists
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Default Marketing Organization")
        db.add(org)
        db.commit()
        db.refresh(org)

    brand = Brand(
        organization_id=org.id,
        name=payload.name,
        description=payload.description
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)

    # Add competitors
    for comp_name in payload.competitors or []:
        db.add(Competitor(brand_id=brand.id, name=comp_name))

    # Add keywords
    for kw in payload.keywords or []:
        db.add(TrackedKeyword(brand_id=brand.id, keyword=kw, category="general"))

    db.commit()
    db.refresh(brand)
    return brand


@router.get("/{brand_id}", response_model=BrandDetailResponse)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    """Retrieve brand details including competitors and tracked keywords."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.post("/{brand_id}/keywords", response_model=TrackedKeywordResponse)
def add_keyword(brand_id: int, payload: TrackedKeywordCreate, db: Session = Depends(get_db)):
    """Add a new tracked keyword or product name to a brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    keyword = TrackedKeyword(
        brand_id=brand_id,
        keyword=payload.keyword,
        category=payload.category,
        active=payload.active
    )
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.post("/{brand_id}/competitors", response_model=CompetitorResponse)
def add_competitor(brand_id: int, payload: CompetitorCreate, db: Session = Depends(get_db)):
    """Add a competitor to track alongside the brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    competitor = Competitor(brand_id=brand_id, name=payload.name)
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor
