from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.session import get_db, SessionLocal
from app.models.collection_run import CollectionRun
from app.schemas.collection_run import CollectionRunResponse, CollectionRunTrigger
from app.services.collection_service import collection_service

router = APIRouter(prefix="/collection", tags=["Collection"])


def _run_bg_collection(brand_id: int, source: str):
    db = SessionLocal()
    try:
        collection_service.run_pipeline(db=db, brand_id=brand_id, source=source)
    finally:
        db.close()


@router.post("/run", response_model=List[CollectionRunResponse])
def trigger_collection(
    payload: Optional[CollectionRunTrigger] = None,
    background_tasks: BackgroundTasks = None,
    sync: bool = Query(True, description="Execute synchronously to return newly added count"),
    db: Session = Depends(get_db)
):
    """
    Trigger brand data collection across enabled sources (Reddit, Facebook, RSS, Web, Mock).
    """
    brand_id = payload.brand_id if payload else 1
    source = payload.source if payload else "all"

    if sync:
        runs = collection_service.run_pipeline(db=db, brand_id=brand_id, source=source)
        return runs
    else:
        background_tasks.add_task(_run_bg_collection, brand_id=brand_id, source=source)
        return []


@router.get("/runs", response_model=List[CollectionRunResponse])
def get_collection_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve history of collection runs with status and metrics."""
    return db.query(CollectionRun).order_by(desc(CollectionRun.started_at)).limit(limit).all()
