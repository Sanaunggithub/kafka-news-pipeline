import pytest
from datetime import datetime, timezone

from shared.models import AnalysisResult, NewsArticle, NewsEvent

import sys
from unittest.mock import MagicMock, patch, AsyncMock

mock_engine = MagicMock()
mock_session = MagicMock()
mock_session.execute = AsyncMock()
mock_session.commit = AsyncMock()
mock_session.rollback = AsyncMock()
mock_session.close = AsyncMock()

@pytest.fixture(autouse=True, scope="session")
def mock_database():
    with patch("shared.database.create_async_engine", return_value=mock_engine), \
         patch("shared.database.async_sessionmaker", return_value=MagicMock()), \
         patch("shared.database._get_connect_args", return_value={}):
        yield


@pytest.fixture(autouse=True, scope="session")
def mock_sentiment_pipeline():
    def smart_mock(text):
        if any(word in text.lower() for word in ["terrible", "awful", "bad"]):
            return [{"label": "LABEL_0", "score": 0.9}]
        return [{"label": "LABEL_2", "score": 0.9}]
    
    mock = MagicMock(side_effect=smart_mock)
    with patch("consumers.analysis.main.get_sentiment_analyzer", return_value=mock):
        yield mock


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