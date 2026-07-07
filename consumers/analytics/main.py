import asyncio
import time
from sqlalchemy import text
from shared.database import get_db_session
from shared.kafka import get_consumer
from shared.logger import get_logger
from shared.models import AnalyticsMetric, NewsEvent
from shared.utils import utcnow

logger = get_logger("AnalyticsConsumer")


async def store_metric(session, metric: AnalyticsMetric) -> None:
    await session.execute(
        text("""
            INSERT INTO analytics_metrics
                (article_id, source, processed_at, processing_latency_ms)
            VALUES
                (:article_id, :source, :processed_at, :processing_latency_ms)
        """),
        {
            "article_id": metric.article_id,
            "source": metric.source,
            "processed_at": metric.processed_at,
            "processing_latency_ms": metric.processing_latency_ms,
        },
    )


async def consume() -> None:
    consumer = await get_consumer(
        topic="news.raw",
        group_id="analytics-consumer-group",
    )
    try:
        async for message in consumer:
            try:
                start_time = time.time()
                event = NewsEvent.model_validate(message.value)
                processing_latency_ms = (time.time() - start_time) * 1000
                metric = AnalyticsMetric(
                    article_id=event.id,
                    source=event.source,
                    processed_at=utcnow(),
                    processing_latency_ms=processing_latency_ms,
                )
                async with get_db_session() as session:
                    await store_metric(session, metric)
                logger.info("[AnalyticsConsumer] Recorded metrics for article %s", event.id)
            except Exception as exc:
                logger.exception("Error processing message: %s", exc)
    finally:
        await consumer.stop()
        logger.info("[AnalyticsConsumer] Shutting down")


if __name__ == "__main__":
    asyncio.run(consume())