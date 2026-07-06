from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.kafka import get_producer
from shared.logger import get_logger
from shared.models import NewsArticle

logger = get_logger("Producer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up News Pipeline API")
    producer = await get_producer()
    app.state.producer = producer
    yield
    logger.info("Shutting down News Pipeline API")
    await app.state.producer.stop()


app = FastAPI(title="News Pipeline API", lifespan=lifespan)


@app.post("/news")
async def publish_news(article: NewsArticle):
    await app.state.producer.send_and_wait(
        "news.raw",
        value=article.model_dump(mode="json"),
        key=article.id.encode("utf-8"),
    )
    logger.info("[Producer] Published article %s", article.id)
    return {"status": "published", "article_id": article.id}


@app.get("/health")
async def health():
    return {"status": "ok"}