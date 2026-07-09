import pytest
from datetime import datetime
from pydantic import ValidationError

from shared.models import (
    AnalyticsMetric,
    AnalysisResult,
    NewsArticle,
    NewsEvent,
)


def test_news_article_valid(sample_article):
    assert sample_article.id == "test-001"
    assert sample_article.title == "Test Article About Technology"
    assert (
        sample_article.content
        == "This is a test article about AI and technology companies like Google."
    )
    assert sample_article.source == "Reuters"
    assert isinstance(sample_article.timestamp, datetime)


def test_news_article_default_timestamp():
    article = NewsArticle(
        id="test-002",
        title="Test Article",
        content="Some content",
        source="AP",
    )
    assert isinstance(article.timestamp, datetime)


def test_news_article_missing_required_fields():
    with pytest.raises(ValidationError):
        NewsArticle()


def test_news_event_inherits_article(sample_news_event):
    assert isinstance(sample_news_event, NewsArticle)
    assert sample_news_event.id == "test-001"
    assert sample_news_event.title == "Test Article About Technology"
    assert (
        sample_news_event.content
        == "This is a test article about AI and technology companies like Google."
    )
    assert sample_news_event.source == "Reuters"
    assert isinstance(sample_news_event.timestamp, datetime)
    assert isinstance(sample_news_event.received_at, datetime)


def test_analysis_result_defaults():
    result = AnalysisResult(article_id="test-001")

    assert result.article_id == "test-001"
    assert result.summary is None
    assert result.sentiment is None
    assert result.keywords == []
    assert result.categories == []
    assert result.companies == []
    assert result.countries == []
    assert result.importance_score is None
    assert result.urgency is None


@pytest.mark.parametrize("urgency_value", ["normal", "high", "urgent"])
def test_analysis_result_urgency_field(urgency_value):
    result = AnalysisResult(article_id="test-001", urgency=urgency_value)
    assert result.urgency == urgency_value


def test_analytics_metric_defaults():
    metric = AnalyticsMetric(article_id="test-001", source="Reuters")
    assert metric.article_id == "test-001"
    assert metric.source == "Reuters"
    assert isinstance(metric.processed_at, datetime)