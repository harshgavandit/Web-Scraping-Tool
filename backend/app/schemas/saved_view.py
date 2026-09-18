from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class SavedViewBase(BaseModel):
    name: str
    description: Optional[str] = None
    team: str = "brand"
    filters: Dict[str, Any] = {}
    is_default: bool = False


class SavedViewCreate(SavedViewBase):
    brand_id: int = 1


class SavedViewUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    team: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


class SavedViewResponse(SavedViewBase):
    id: int
    brand_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
