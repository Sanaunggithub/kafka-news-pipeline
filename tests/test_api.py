import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from api.main import app


@pytest.fixture
def mock_producer():
    producer = MagicMock()
    producer.send_and_wait = AsyncMock()
    return producer


@pytest_asyncio.fixture
async def test_app(mock_producer):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        app.state.producer = mock_producer
        yield client


@pytest.mark.asyncio
async def test_health_endpoint(test_app):
    response = await test_app.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_publish_news_valid(test_app, mock_producer):
    article = {
        "id": "article-123",
        "title": "Test Article",
        "content": "This is a test article.",
        "source": "Reuters",
    }

    response = await test_app.post("/news", json=article)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "published"
    assert payload["article_id"] == article["id"]


@pytest.mark.asyncio
async def test_publish_news_missing_fields(test_app):
    response = await test_app.post("/news", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_publish_news_missing_title(test_app):
    response = await test_app.post(
        "/news",
        json={"content": "This is content", "source": "Reuters"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_publish_news_missing_content(test_app):
    response = await test_app.post(
        "/news",
        json={"title": "Test Article", "source": "Reuters"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_publish_news_calls_kafka(test_app, mock_producer):
    article = {
        "id": "article-456",
        "title": "Kafka Test",
        "content": "This should be published.",
        "source": "Reuters",
    }

    await test_app.post("/news", json=article)

    mock_producer.send_and_wait.assert_awaited_once()
    assert mock_producer.send_and_wait.await_args.args[0] == "news.raw"


@pytest.mark.asyncio
async def test_publish_news_invalid_json(test_app):
    response = await test_app.post("/news", content="not-json")

    assert response.status_code == 422