from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from consumers.embedding import main as embedding_main
from consumers.embedding.main import store_embedding
from shared.models import NewsEvent


@pytest.fixture
def sample_event():
    return NewsEvent(
        id="test-emb-001",
        title="Embedding Test",
        content="Test content for embedding",
        source="BBC",
        timestamp=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_store_embedding_generates_vector(sample_event):
    generate_mock = MagicMock(return_value=[0.0] * 384)
    client_mock = MagicMock()
    embedding_service_mock = MagicMock()
    embedding_service_mock.generate = generate_mock

    with patch.object(embedding_main, "client", client_mock), \
         patch.object(embedding_main, "embedding_service", embedding_service_mock):
        await store_embedding(sample_event)

    generate_mock.assert_called_once()
    text = generate_mock.call_args.args[0]
    assert sample_event.title in text


@pytest.mark.asyncio
async def test_store_embedding_calls_qdrant_upsert(sample_event):
    generate_mock = MagicMock(return_value=[0.1] * 384)
    client_mock = MagicMock()
    embedding_service_mock = MagicMock()
    embedding_service_mock.generate = generate_mock

    with patch.object(embedding_main, "client", client_mock), \
         patch.object(embedding_main, "embedding_service", embedding_service_mock):
        await store_embedding(sample_event)

    client_mock.upsert.assert_called_once()
    assert client_mock.upsert.call_args.kwargs["collection_name"] == "news_articles"


@pytest.mark.asyncio
async def test_store_embedding_text_combines_title_and_content(sample_event):
    generate_mock = MagicMock(return_value=[0.2] * 384)
    client_mock = MagicMock()
    embedding_service_mock = MagicMock()
    embedding_service_mock.generate = generate_mock

    with patch.object(embedding_main, "client", client_mock), \
         patch.object(embedding_main, "embedding_service", embedding_service_mock):
        await store_embedding(sample_event)

    text = generate_mock.call_args.args[0]
    assert sample_event.title in text
    assert sample_event.content in text


@pytest.mark.asyncio
async def test_point_id_is_positive_integer(sample_event):
    generate_mock = MagicMock(return_value=[0.3] * 384)
    client_mock = MagicMock()
    embedding_service_mock = MagicMock()
    embedding_service_mock.generate = generate_mock

    with patch.object(embedding_main, "client", client_mock), \
         patch.object(embedding_main, "embedding_service", embedding_service_mock):
        await store_embedding(sample_event)

    call_args = client_mock.upsert.call_args
    points = call_args.kwargs.get("points") or (call_args.args[1] if len(call_args.args) > 1 else None)
    assert points is not None
    point = points[0]
    point_id = getattr(point, "id", None) or (point.get("id") if isinstance(point, dict) else None)
    assert isinstance(point_id, int)
    assert point_id > 0