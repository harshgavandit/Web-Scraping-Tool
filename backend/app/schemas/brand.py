from datetime import datetime
from typing import Annotated, List, Optional
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from app.schemas.competitor import CompetitorResponse
from app.schemas.tracked_keyword import TrackedKeywordResponse


BrandName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
BrandDescription = Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)]


class BrandBase(BaseModel):
    name: BrandName
    description: Optional[BrandDescription] = None


class BrandCreate(BrandBase):
    organization_id: int = Field(default=1, ge=1)
    competitors: List[BrandName] = Field(default_factory=list, max_length=50)
    keywords: List[BrandName] = Field(default_factory=list, max_length=100)


class BrandResponse(BrandBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrandDetailResponse(BrandResponse):
    competitors: List[CompetitorResponse] = Field(default_factory=list)
    keywords: List[TrackedKeywordResponse] = Field(default_factory=list)
