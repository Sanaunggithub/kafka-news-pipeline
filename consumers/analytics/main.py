import asyncio
import time
from sqlalchemy import text
from shared.database import get_db_session
from shared.kafka import get_consumer
from shared.logger import get_logger
from shared.models import AnalyticsMetric, NewsEvent
from shared.utils import utcnow

logger = get_logger("AnalyticsConsumer")

article_counts: dict[str, int] = {}
processing_times: list[float] = []


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


def get_articles_per_minute() -> int:
    return len(processing_times)


def detect_language(text: str) -> str:
    # This can be replaced with langdetect library later
    return "en"


async def consume() -> None:
    consumer = await get_consumer(
        topic="news.raw",
        group_id="analytics-consumer-group",
    )
    processed_count = 0
    try:
        async for message in consumer:
            try:
                start_time = time.time()
                event = NewsEvent.model_validate(message.value)
                processing_latency_ms = (time.time() - start_time) * 1000

                article_counts[event.source] = article_counts.get(event.source, 0) + 1
                processing_times.append(processing_latency_ms)
                if len(processing_times) > 100:
                    processing_times.pop(0)

                detected_language = detect_language(f"{event.title}. {event.content}")

                metric = AnalyticsMetric(
                    article_id=event.id,
                    source=event.source,
                    processed_at=utcnow(),
                    processing_latency_ms=processing_latency_ms,
                )
                async with get_db_session() as session:
                    await store_metric(session, metric)

                processed_count += 1
                logger.info(
                    "[AnalyticsConsumer] Recorded metrics for article %s (language=%s)",
                    event.id,
                    detected_language,
                )

                if processed_count % 5 == 0:
                    logger.info(
                        "[AnalyticsConsumer] Articles per minute approx: %s",
                        get_articles_per_minute(),
                    )
            except Exception as exc:
                logger.exception("Error processing message: %s", exc)
    finally:
        await consumer.stop()
        logger.info("[AnalyticsConsumer] Shutting down")


if __name__ == "__main__":
    asyncio.run(consume())