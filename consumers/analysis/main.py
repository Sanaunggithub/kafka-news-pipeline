import asyncio
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import text
from transformers import pipeline
from shared.database import get_db_session
from shared.kafka import get_consumer, get_producer
from shared.logger import get_logger
from shared.models import AnalysisResult, NewsEvent

logger = get_logger("AnalysisConsumer")
executor = ThreadPoolExecutor(max_workers=2)

_sentiment_analyzer = None

def get_sentiment_analyzer():
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment"
        )
    return _sentiment_analyzer

SENTIMENT_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive"
}

CATEGORY_KEYWORDS = {
    "technology": ["ai", "tech", "software", "hardware", "digital", "cyber", "robot"],
    "business": ["market", "stock", "economy", "company", "revenue", "profit"],
    "health": ["medical", "health", "disease", "vaccine", "hospital", "doctor"],
    "politics": ["government", "election", "president", "policy", "law", "senate"],
}

COMPANY_KEYWORDS = ["apple", "google", "microsoft", "tesla", "amazon", "openai", "meta"]
COUNTRY_KEYWORDS = ["usa", "china", "uk", "india", "russia", "germany", "france", "japan"]


async def extract_sentiment_async(text: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        lambda: SENTIMENT_MAP.get(
            get_sentiment_analyzer()(text[:500])[0].get("label", "LABEL_1"),
            "neutral"
        )
    )


def extract_keywords(text: str) -> list[str]:
    stopwords = {"this", "that", "with", "from", "have", "will", "been", "they", "were"}
    words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
    filtered = [w for w in words if len(w) >= 4 and w not in stopwords]
    counts = Counter(filtered)
    return [w for w, _ in counts.most_common(10)]


def extract_categories(text: str) -> list[str]:
    lower = text.lower()
    return [
        category for category, keywords in CATEGORY_KEYWORDS.items()
        if any(kw in lower for kw in keywords)
    ]


def extract_companies(text: str) -> list[str]:
    lower = text.lower()
    return [c for c in COMPANY_KEYWORDS if c in lower]


def extract_countries(text: str) -> list[str]:
    lower = text.lower()
    return [c for c in COUNTRY_KEYWORDS if c in lower]


def extract_urgency(text: str) -> str:
    lower = text.lower()
    urgent_keywords = ["breaking", "urgent", "emergency", "critical", "immediate", "crisis", "alert"]
    high_keywords = ["major", "significant", "important", "serious", "severe"]

    if any(keyword in lower for keyword in urgent_keywords):
        return "urgent"
    if any(keyword in lower for keyword in high_keywords):
        return "high"
    return "normal"


def extract_summary(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:2]).strip()


async def analyze_article(event: NewsEvent) -> AnalysisResult:
    combined = f"{event.title}. {event.content}"
    sentiment = await extract_sentiment_async(combined)
    return AnalysisResult(
        article_id=event.id,
        summary=extract_summary(combined),
        sentiment=sentiment,
        keywords=extract_keywords(combined),
        categories=extract_categories(combined),
        companies=extract_companies(combined),
        countries=extract_countries(combined),
        importance_score=min(1.0, 0.2 * len(extract_companies(combined)) + 0.1 * len(extract_categories(combined))),
        urgency=extract_urgency(combined),
    )


async def store_analysis(session, result: AnalysisResult) -> None:
    await session.execute(
        text("""
            INSERT INTO analysis_results
                (article_id, summary, sentiment, keywords, categories,
                 companies, countries, importance_score, urgency)
            VALUES
                (:article_id, :summary, :sentiment, :keywords, :categories,
                 :companies, :countries, :importance_score, :urgency)
        """),
        {
            "article_id": result.article_id,
            "summary": result.summary,
            "sentiment": result.sentiment,
            "keywords": result.keywords,
            "categories": result.categories,
            "companies": result.companies,
            "countries": result.countries,
            "importance_score": result.importance_score,
            "urgency": result.urgency,
        },
    )


async def consume() -> None:
    producer = await get_producer()
    consumer = await get_consumer(topic="news.raw", group_id="analysis-consumer-group")
    try:
        async for message in consumer:
            try:
                event = NewsEvent.model_validate(message.value)
                result = await analyze_article(event)

                # Retry up to 3 times waiting for database consumer to store article first
                for attempt in range(3):
                    try:
                        async with get_db_session() as session:
                            await store_analysis(session, result)
                        break
                    except Exception as exc:
                        if "ForeignKeyViolation" in str(exc) and attempt < 2:
                            logger.warning(
                                "Article %s not in DB yet, retrying in 3s (attempt %d/3)",
                                event.id, attempt + 1
                            )
                            await asyncio.sleep(3)
                        else:
                            raise

                await producer.send_and_wait(
                    "news.analysis",
                    value=result.model_dump(mode="json"),
                    key=result.article_id.encode("utf-8"),
                )
                logger.info("[AnalysisConsumer] Analyzed article %s", event.id)
            except Exception as exc:
                logger.exception("Error processing message: %s", exc)
    finally:
        await producer.stop()
        await consumer.stop()
        logger.info("[AnalysisConsumer] Shutting down")


if __name__ == "__main__":
    asyncio.run(consume())