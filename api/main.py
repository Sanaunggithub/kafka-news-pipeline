import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from shared.database import get_db_session
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

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/")
    async def dashboard():
        return FileResponse("static/dashboard.html")

    @app.get("/article/{article_id}")
    async def article_detail_page(article_id: str):
        return FileResponse("static/article_detail.html")

@app.get("/")
async def dashboard():
    return FileResponse("static/dashboard.html")

@app.post("/news")
async def publish_news(article: NewsArticle):
    await app.state.producer.send_and_wait(
        "news.raw",
        value=article.model_dump(mode="json"),
        key=article.id.encode("utf-8"),
    )
    logger.info("[Producer] Published article %s", article.id)
    return {"status": "published", "article_id": article.id}


@app.get("/dashboard/articles")
async def dashboard_articles():
    async with get_db_session() as session:
        result = await session.execute(
            text("""
                SELECT a.id, a.title, a.source, a.timestamp,
                       ar.sentiment, ar.urgency
                FROM articles a
                LEFT JOIN analysis_results ar ON ar.article_id = a.id
                ORDER BY a.timestamp DESC
                LIMIT 20
            """)
        )
        return [dict(row._mapping) for row in result.fetchall()]


@app.get("/dashboard/stats")
async def dashboard_stats():
    logger.info("GET /dashboard/stats")
    async with get_db_session() as session:
        total_articles_result = await session.execute(
            text("SELECT COUNT(*) AS count FROM articles")
        )
        total_articles = total_articles_result.scalar_one()

        sentiment_result = await session.execute(
            text(
                """
                SELECT sentiment, COUNT(*) AS count
                FROM analysis_results
                GROUP BY sentiment
                """
            )
        )
        sentiment_counts = {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
        }
        for row in sentiment_result.fetchall():
            value = row._mapping["sentiment"]
            if value in sentiment_counts:
                sentiment_counts[value] = row._mapping["count"]

        urgency_result = await session.execute(
            text(
                """
                SELECT urgency, COUNT(*) AS count
                FROM analysis_results
                GROUP BY urgency
                """
            )
        )
        urgency_counts = {
            "normal": 0,
            "high": 0,
            "urgent": 0,
        }
        for row in urgency_result.fetchall():
            value = row._mapping["urgency"]
            if value in urgency_counts:
                urgency_counts[value] = row._mapping["count"]

        top_sources_result = await session.execute(
            text(
                """
                SELECT source, COUNT(*) AS count
                FROM articles
                GROUP BY source
                ORDER BY count DESC
                LIMIT 5
                """
            )
        )
        top_sources = [
            {"source": row._mapping["source"], "count": row._mapping["count"]}
            for row in top_sources_result.fetchall()
        ]

        category_result = await session.execute(
            text(
                """
                SELECT category, COUNT(*) AS count
                FROM (
                    SELECT unnest(COALESCE(categories, ARRAY[]::text[])) AS category
                    FROM analysis_results
                ) AS expanded
                GROUP BY category
                """
            )
        )
        category_counts = {
            row._mapping["category"]: row._mapping["count"]
            for row in category_result.fetchall()
        }

        latency_result = await session.execute(
            text(
                """
                SELECT AVG(processing_latency_ms) AS avg_latency_ms
                FROM analytics_metrics
                """
            )
        )
        avg_latency_ms = latency_result.scalar_one()

        return {
            "total_articles": total_articles,
            "sentiment_counts": sentiment_counts,
            "urgency_counts": urgency_counts,
            "top_sources": top_sources,
            "category_counts": category_counts,
            "avg_latency_ms": avg_latency_ms,
        }


@app.get("/dashboard/articles/{article_id}")
async def dashboard_article_detail(article_id: str):
    async with get_db_session() as session:
        result = await session.execute(
            text("""
                SELECT
                    a.id, a.title, a.content, a.source, a.timestamp,
                    ar.summary, ar.sentiment, ar.keywords, ar.categories,
                    ar.companies, ar.countries, ar.urgency, ar.importance_score
                FROM articles a
                LEFT JOIN analysis_results ar ON ar.article_id = a.id
                WHERE a.id = :article_id
            """),
            {"article_id": article_id},
        )
        row = result.fetchone()
        if row is None:
            return {}
        data = dict(row._mapping)
        # Replace None arrays with empty lists
        for field in ["keywords", "categories", "companies", "countries"]:
            if data.get(field) is None:
                data[field] = []
        return data

@app.get("/article/{article_id}")
async def article_detail_page(article_id: str):
    return FileResponse("static/article_detail.html")

@app.get("/health")
async def health():
    return {"status": "ok"}