from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class DocumentSnapshotResponse(BaseModel):
    id: int
    content_text: str
    extracted_data: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: int
    canonical_url: Optional[str] = None
    domain: Optional[str] = None
    source_type: str
    content_status: str
    robots_allowed: Optional[bool] = None
    http_status: Optional[int] = None
    language: Optional[str] = None
    publisher: Optional[str] = None
    author: Optional[str] = None
    fetched_at: datetime
    error_message: Optional[str] = None
    snapshots: list[DocumentSnapshotResponse] = []

    model_config = ConfigDict(from_attributes=True)
