from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, StringConstraints

CompetitorName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class CompetitorBase(BaseModel):
    name: CompetitorName


class CompetitorCreate(CompetitorBase):
    pass


class CompetitorResponse(CompetitorBase):
    id: int
    brand_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
