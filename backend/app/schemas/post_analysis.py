from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class PostAnalysisBase(BaseModel):
    sentiment: str = "Neutral"
    sentiment_score: float = 0.0
    topic: Optional[str] = None
    product: Optional[str] = None
    competitor: Optional[str] = None
    key_positive: Optional[str] = None
    key_negative: Optional[str] = None
    summary: Optional[str] = None
    recommendation: Optional[str] = None
    virality_score: float = 0.0
    virality_level: str = "Low"
    is_viral: bool = False
    analysis_version: str = "1.0"
    model_used: str = "vader_local"


class PostAnalysisCreate(PostAnalysisBase):
    post_id: int


class PostAnalysisResponse(PostAnalysisBase):
    id: int
    post_id: int
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIAnalysisItem(BaseModel):
    post_id: int
    sentiment: Literal["Positive", "Negative", "Neutral", "Mixed"] = Field(
        description="One of: Positive, Negative, Neutral, Mixed"
    )
    topic: Optional[str] = Field(default=None, description="Topic of discussion e.g. Running Shoes / Pricing, Quality, Customer Service")
    product: Optional[str] = Field(default=None, description="Brand product discussed if any, e.g. Pegasus, Air Max, Air Jordan")
    competitor: Optional[str] = Field(default=None, description="Competitor discussed if any, e.g. Adidas, Puma, New Balance, Under Armour")
    summary: str = Field(description="Concise 1-2 sentence summary of user sentiment and discussion")
    key_positive: Optional[str] = Field(default=None, description="Key positive aspect mentioned")
    key_negative: Optional[str] = Field(default=None, description="Key negative aspect or complaint mentioned")
    recommendation: str = Field(description="1-2 sentence actionable marketing/business recommendation")

    model_config = ConfigDict(extra="forbid")


class AIBatchResult(BaseModel):
    items: list[AIAnalysisItem] = Field(default_factory=list)
