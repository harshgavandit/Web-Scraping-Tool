from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy import desc, distinct, func
from sqlalchemy.orm import Session

from app.database.session import get_db, SessionLocal
from app.models.collection_run import CollectionRun
from app.models.search_discovery import SearchQuery, SearchRun, SearchResult
from app.schemas.collection_run import CollectionRunResponse, CollectionRunTrigger
from app.schemas.discovery import DiscoveryHealthResponse
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
    background_tasks: BackgroundTasks,
    payload: Optional[CollectionRunTrigger] = None,
    sync: bool = Query(True, description="Execute synchronously to return newly added count"),
    db: Session = Depends(get_db)
):
    """
    Trigger collection across enabled Google Search and Google News sources.
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


@router.get("/health", response_model=DiscoveryHealthResponse)
def get_discovery_health(
    brand_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    query_ids = db.query(SearchQuery.id).filter(SearchQuery.brand_id == brand_id)
    configured_queries = query_ids.count()
    query_id_select = query_ids.subquery()
    run_filter = SearchRun.query_id.in_(db.query(query_id_select.c.id))
    result_filter = SearchResult.query_id.in_(db.query(query_id_select.c.id))
    last_successful = db.query(func.max(SearchRun.completed_at)).filter(
        run_filter,
        SearchRun.status == "completed",
    ).scalar()
    return DiscoveryHealthResponse(
        brand_id=brand_id,
        configured_queries=configured_queries,
        successful_query_runs=db.query(SearchRun).filter(run_filter, SearchRun.status == "completed").count(),
        failed_query_runs=db.query(SearchRun).filter(run_filter, SearchRun.status == "failed").count(),
        discovered_results=db.query(SearchResult).filter(result_filter).count(),
        unique_domains=db.query(func.count(distinct(SearchResult.display_domain))).filter(result_filter).scalar() or 0,
        last_successful_discovery=last_successful,
    )
