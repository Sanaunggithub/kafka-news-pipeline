import asyncio
from qdrant_client import QdrantClient, models
from shared.config import settings
from shared.embeddings import embedding_service
from shared.kafka import get_consumer, get_producer
from shared.logger import get_logger
from shared.models import NewsEvent

logger = get_logger("EmbeddingConsumer")
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
COLLECTION_NAME = "news_articles"


async def ensure_collection() -> None:
    if not client.collection_exists(collection_name=COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection: %s", COLLECTION_NAME)


async def store_embedding(event: NewsEvent) -> None:
    text = f"{event.title}. {event.content}"
    embedding = embedding_service.generate(text)
    point_id = abs(hash(event.id)) % (2**63)
    payload = {
        "article_id": str(event.id),
        "title": str(event.title),
        "source": str(event.source),
        "timestamp": str(event.timestamp),
    }
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )
        ],
    )
    logger.info("[EmbeddingConsumer] Stored embedding for article %s", event.id)


async def consume() -> None:
    await ensure_collection()
    producer = await get_producer()
    consumer = await get_consumer(
        topic="news.raw",
        group_id="embedding-consumer-group",
    )
    try:
        async for message in consumer:
            try:
                event = NewsEvent.model_validate(message.value)
                await store_embedding(event)
                await producer.send_and_wait(
                    "news.embedded",
                    value={**event.model_dump(mode="json"), "embedding_stored": True},
                    key=event.id.encode("utf-8"),
                )
                logger.info("[EmbeddingConsumer] Published to news.embedded for article %s", event.id)
            except Exception as exc:
                logger.exception("Error processing message: %s", exc)
    finally:
        await producer.stop()
        await consumer.stop()
        logger.info("[EmbeddingConsumer] Shutting down")


if __name__ == "__main__":
    asyncio.run(consume())