from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, StringConstraints

KeywordValue = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class TrackedKeywordBase(BaseModel):
    keyword: KeywordValue
    category: Literal["general", "brand", "product", "campaign"] = "general"
    active: bool = True


class TrackedKeywordCreate(TrackedKeywordBase):
    pass


class TrackedKeywordResponse(TrackedKeywordBase):
    id: int
    brand_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
