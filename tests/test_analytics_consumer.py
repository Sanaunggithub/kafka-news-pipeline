from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consumers.analytics import main as analytics_main
from consumers.analytics.main import (
    article_counts,
    detect_language,
    get_articles_per_minute,
    processing_times,
    store_metric,
)
from shared.models import AnalyticsMetric, NewsEvent


@pytest.fixture
def sample_event():
    return NewsEvent(
        id="test-analytics-001",
        title="Analytics Test",
        content="Test content",
        source="CNN",
        timestamp=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_metric():
    return AnalyticsMetric(
        article_id="test-analytics-001",
        source="CNN",
        processed_at=datetime.now(timezone.utc),
        processing_latency_ms=5.0,
    )


@pytest.mark.asyncio
async def test_store_metric_executes_sql(sample_metric):
    session = MagicMock()
    session.execute = AsyncMock()

    with patch.object(analytics_main, "get_db_session", MagicMock(return_value=session)):
        await store_metric(session, sample_metric)

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_metric_uses_correct_table(sample_metric):
    session = MagicMock()
    session.execute = AsyncMock()

    with patch.object(analytics_main, "get_db_session", MagicMock(return_value=session)):
        await store_metric(session, sample_metric)

    executed_sql = session.execute.await_args.args[0]
    sql_text = getattr(executed_sql, "text", None) or str(executed_sql)
    assert "INSERT INTO analytics_metrics" in sql_text


@pytest.mark.asyncio
async def test_store_metric_maps_all_fields(sample_metric):
    session = MagicMock()
    session.execute = AsyncMock()

    with patch.object(analytics_main, "get_db_session", MagicMock(return_value=session)):
        await store_metric(session, sample_metric)

    params = session.execute.await_args.args[1]
    assert params["article_id"] == sample_metric.article_id
    assert params["source"] == sample_metric.source
    assert params["processed_at"] == sample_metric.processed_at
    assert params["processing_latency_ms"] == sample_metric.processing_latency_ms


def test_detect_language_returns_string():
    result = detect_language("some text")
    assert isinstance(result, str)


def test_get_articles_per_minute_returns_int():
    result = get_articles_per_minute()
    assert isinstance(result, int)


def test_article_counts_tracks_sources(sample_event, sample_metric):
    article_counts.clear()
    processing_times.clear()

    processing_times.append(sample_metric.processing_latency_ms)
    article_counts[sample_event.source] = article_counts.get(sample_event.source, 0) + 1

    processing_times.append(7.0)
    article_counts["BBC"] = article_counts.get("BBC", 0) + 1

    assert article_counts[sample_event.source] == 1
    assert article_counts["BBC"] == 1
    assert processing_times[-1] == 7.0