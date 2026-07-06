-- Stores analytics metrics for processed articles.
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL,
    processing_latency_ms FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);