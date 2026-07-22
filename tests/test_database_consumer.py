from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consumers.database.main import store_article
from shared.models import NewsEvent


@pytest.fixture
def sample_event() -> NewsEvent:
    return NewsEvent(
        id="test-db-001",
        title="Test Article",
        content="Test content",
        source="Reuters",
        timestamp=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_store_article_executes_sql(mock_session, sample_event):
    await store_article(mock_session, sample_event)
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_article_uses_correct_table(mock_session, sample_event):
    await store_article(mock_session, sample_event)
    statement = mock_session.execute.await_args.args[0]
    assert "INSERT INTO articles" in str(statement)


@pytest.mark.asyncio
async def test_store_article_maps_all_fields(mock_session, sample_event):
    await store_article(mock_session, sample_event)
    params = mock_session.execute.await_args.args[1]
    assert {"id", "title", "content", "source", "timestamp", "received_at"}.issubset(params.keys())
    assert params["id"] == sample_event.id
    assert params["title"] == sample_event.title
    assert params["content"] == sample_event.content
    assert params["source"] == sample_event.source
    assert params["timestamp"] == sample_event.timestamp
    assert params["received_at"] == sample_event.received_at