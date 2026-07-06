-- Stores news articles ingested by the pipeline.
CREATE TABLE IF NOT EXISTS articles (
    id VARCHAR PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);