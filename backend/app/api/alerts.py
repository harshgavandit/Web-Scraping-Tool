from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse, AlertUpdate
from app.utils.datetime_utils import utc_now


router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    brand_id: int = Query(1, ge=1),
    status: str | None = Query(None, pattern="^(open|acknowledged|resolved)$"),
    db: Session = Depends(get_db),
):
    query = db.query(Alert).filter(Alert.brand_id == brand_id)
    if status:
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.created_at.desc()).all()


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = payload.status
    alert.acknowledged_at = utc_now() if payload.status == "acknowledged" else None
    alert.resolved_at = utc_now() if payload.status == "resolved" else None
    alert.updated_at = utc_now()
    db.commit()
    db.refresh(alert)
    return alert
