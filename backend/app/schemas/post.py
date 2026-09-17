from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.post_analysis import PostAnalysisResponse


class PostBase(BaseModel):
    brand_id: int
    source: str
    external_id: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    content: str
    published_at: Optional[datetime] = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_count: int = 0
    engagement_velocity: float = 0.0
    raw_metadata: Dict[str, Any] = {}
    content_hash: str


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    id: int
    collected_at: datetime
    analysis: Optional[PostAnalysisResponse] = None

    model_config = ConfigDict(from_attributes=True)
