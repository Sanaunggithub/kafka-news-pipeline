from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, Field

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class NewsArticle(BaseModel):
    id: str
    title: str
    content: str
    source: str
    timestamp: datetime = Field(default_factory=utcnow)


class NewsEvent(NewsArticle):
    received_at: datetime = Field(default_factory=utcnow)


class AnalysisResult(BaseModel):
    article_id: str
    summary: str | None = None
    sentiment: str | None = None
    keywords: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    importance_score: float | None = None
    urgency: str | None = None


class AnalyticsMetric(BaseModel):
    article_id: str
    source: str
    processed_at: datetime = Field(default_factory=utcnow)
    processing_latency_ms: float | None = None