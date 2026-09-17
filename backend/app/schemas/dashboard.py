from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class DashboardKPIs(BaseModel):
    total_mentions: int = 0
    positive_pct: float = 0.0
    negative_pct: float = 0.0
    neutral_pct: float = 0.0
    mixed_pct: float = 0.0
    viral_posts_count: int = 0
    top_trending_topic: Optional[str] = "N/A"
    top_complaint: Optional[str] = "N/A"
    top_positive_topic: Optional[str] = "N/A"


class ExecutiveSummary(BaseModel):
    overall_sentiment: str
    positive_pct: float
    negative_pct: float
    neutral_mixed_pct: float
    top_positive_topic: str
    top_negative_topic: str
    fastest_growing_topic: str
    most_viral_discussion: str
    key_insight: str
    recommended_action: str
    generated_at: datetime
    data_version: str


class DashboardSummaryResponse(BaseModel):
    kpis: DashboardKPIs
    executive_summary: ExecutiveSummary


class TopicTrendItem(BaseModel):
    topic: str
    current_count: int
    previous_count: int
    pct_change: float
    sentiment: str
    avg_virality: float
    trend_direction: str  # Rising, Falling, Steady
