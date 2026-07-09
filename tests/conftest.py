import pytest
from datetime import datetime, timezone

from shared.models import AnalysisResult, NewsArticle, NewsEvent


@pytest.fixture(scope="function")
def sample_article():
    return NewsArticle(
        id="test-001",
        title="Test Article About Technology",
        content="This is a test article about AI and technology companies like Google.",
        source="Reuters",
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture(scope="function")
def sample_news_event():
    return NewsEvent(
        id="test-001",
        title="Test Article About Technology",
        content="This is a test article about AI and technology companies like Google.",
        source="Reuters",
        timestamp=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )


@pytest.fixture(scope="function")
def sample_analysis_result():
    return AnalysisResult(
        article_id="test-001",
        summary="Test summary.",
        sentiment="positive",
        keywords=["test", "article"],
        categories=["technology"],
        companies=["google"],
        countries=[],
        importance_score=0.3,
        urgency="normal",
    )