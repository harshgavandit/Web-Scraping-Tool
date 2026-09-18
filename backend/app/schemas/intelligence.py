from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProductInsight(BaseModel):
    product: str
    mention_count: int
    positive_count: int
    negative_count: int
    top_praise: Optional[str] = None
    top_complaint: Optional[str] = None
    average_attention: float


class RiskInsight(BaseModel):
    id: int
    title: str
    product: Optional[str] = None
    aspect: str
    mention_count: int
    unique_sources: int
    growth_pct: float
    attention_score: float
    risk_score: float
    risk_level: str
    confidence: float
    last_seen_at: Optional[datetime] = None


class PraiseInsight(BaseModel):
    product: Optional[str] = None
    aspect: str
    mention_count: int
    top_quote: Optional[str] = None
    average_attention: float = 0.0


class CompetitorInsight(BaseModel):
    competitor: str
    mention_count: int
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    top_topics: List[str] = Field(default_factory=list)
    average_attention: float = 0.0


class IntelligenceOverview(BaseModel):
    products: List[ProductInsight] = Field(default_factory=list)
    risks: List[RiskInsight] = Field(default_factory=list)
    praises: List[PraiseInsight] = Field(default_factory=list)
    competitors: List[CompetitorInsight] = Field(default_factory=list)
