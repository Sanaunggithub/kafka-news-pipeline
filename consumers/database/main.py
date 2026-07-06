import asyncio
from sqlalchemy import text
from shared.kafka import get_consumer
from shared.logger import get_logger
from shared.database import get_db_session
from shared.models import NewsEvent

logger = get_logger("DatabaseConsumer")


async def store_article(session, event: NewsEvent) -> None:
    query = """
        INSERT INTO articles (id, title, content, source, timestamp, received_at)
        VALUES (:id, :title, :content, :source, :timestamp, :received_at)
        ON CONFLICT (id) DO NOTHING
    """
    await session.execute(
        text(query),
        {
            "id": event.id,
            "title": event.title,
            "content": event.content,
            "source": event.source,
            "timestamp": event.timestamp,
            "received_at": event.received_at,
        },
    )


async def consume() -> None:
    consumer = await get_consumer(
        topic="news.raw",
        group_id="database-consumer-group"
    )

    try:
        async for message in consumer:
            try:
                event = NewsEvent.model_validate(message.value)
                async with get_db_session() as session:
                    await store_article(session, event)
                logger.info("[DatabaseConsumer] Stored article %s", event.id)
            except Exception as exc:
                logger.exception("[DatabaseConsumer] Error processing message: %s", exc)
    finally:
        logger.info("[DatabaseConsumer] Shutting down")
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(consume())