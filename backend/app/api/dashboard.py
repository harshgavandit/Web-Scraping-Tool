from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.analytics.summary_generator import generate_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    brand_id: int = Query(1, description="Brand ID"),
    days: int = Query(30, ge=1, le=365, description="Historical days window"),
    refresh: bool = Query(False, description="Force regenerate summary bypassing cache"),
    db: Session = Depends(get_db)
):
    """
    Retrieve aggregated KPIs and executive AI brand health summary.
    Lightweight, cached, and cost-effective.
    """
    return generate_dashboard_summary(
        db=db,
        brand_id=brand_id,
        days=days,
        force_refresh=refresh
    )
