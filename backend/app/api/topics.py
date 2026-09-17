from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.dashboard import TopicTrendItem
from app.analytics.trends import compute_trending_topics

router = APIRouter(prefix="/topics", tags=["Topics"])


@router.get("", response_model=List[TopicTrendItem])
def get_trending_topics(
    brand_id: int = Query(1, description="Brand ID"),
    days: int = Query(7, ge=1, le=90, description="Window in days for trending delta"),
    db: Session = Depends(get_db)
):
    """
    Retrieve list of trending topics with volume, growth delta (%), sentiment, and virality.
    """
    return compute_trending_topics(db=db, brand_id=brand_id, days=days)
