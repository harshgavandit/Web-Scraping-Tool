from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class AlertUpdate(BaseModel):
    status: Literal["open", "acknowledged", "resolved"]


class AlertResponse(BaseModel):
    id: int
    brand_id: int
    issue_cluster_id: int
    alert_type: str
    severity: str
    title: str
    message: str
    status: str
    evidence_count: int
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    email_status: str = "pending"
    email_recipients: list[str] = []
    email_sent_at: Optional[datetime] = None
    email_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
