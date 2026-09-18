from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.saved_view import SavedView
from app.schemas.saved_view import SavedViewCreate, SavedViewResponse, SavedViewUpdate
from app.utils.datetime_utils import utc_now


router = APIRouter(prefix="/saved-views", tags=["Saved Views"])


@router.get("", response_model=List[SavedViewResponse])
def list_saved_views(
    brand_id: int = Query(1, ge=1),
    team: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(SavedView).filter(SavedView.brand_id == brand_id)
    if team:
        query = query.filter(SavedView.team == team)
    return query.order_by(SavedView.is_default.desc(), SavedView.name.asc()).all()


@router.post("", response_model=SavedViewResponse, status_code=status.HTTP_201_CREATED)
def create_saved_view(
    payload: SavedViewCreate,
    db: Session = Depends(get_db),
):
    # If set to default, clear previous defaults for the brand
    if payload.is_default:
        db.query(SavedView).filter(SavedView.brand_id == payload.brand_id, SavedView.is_default.is_(True)).update(
            {"is_default": False}, synchronize_session=False
        )

    saved_view = SavedView(
        brand_id=payload.brand_id,
        name=payload.name,
        description=payload.description,
        team=payload.team,
        filters=payload.filters or {},
        is_default=payload.is_default,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(saved_view)
    db.commit()
    db.refresh(saved_view)
    return saved_view


@router.get("/{view_id}", response_model=SavedViewResponse)
def get_saved_view(view_id: int, db: Session = Depends(get_db)):
    saved_view = db.get(SavedView, view_id)
    if not saved_view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    return saved_view


@router.patch("/{view_id}", response_model=SavedViewResponse)
def update_saved_view(view_id: int, payload: SavedViewUpdate, db: Session = Depends(get_db)):
    saved_view = db.get(SavedView, view_id)
    if not saved_view:
        raise HTTPException(status_code=404, detail="Saved view not found")

    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("is_default"):
        db.query(SavedView).filter(
            SavedView.brand_id == saved_view.brand_id,
            SavedView.id != saved_view.id,
            SavedView.is_default.is_(True),
        ).update({"is_default": False}, synchronize_session=False)

    for key, value in update_data.items():
        setattr(saved_view, key, value)
    saved_view.updated_at = utc_now()

    db.commit()
    db.refresh(saved_view)
    return saved_view


@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_view(view_id: int, db: Session = Depends(get_db)):
    saved_view = db.get(SavedView, view_id)
    if not saved_view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    db.delete(saved_view)
    db.commit()
    return None
