from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class CollectionRunBase(BaseModel):
    source: str


class CollectionRunResponse(CollectionRunBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_found: int = 0
    records_added: int = 0
    records_skipped: int = 0
    status: str
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionRunTrigger(BaseModel):
    source: Literal["all", "rss", "publisher_rss", "google_search"] = "all"
    brand_id: int = Field(default=1, ge=1)
