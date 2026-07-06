-- Stores analysis results generated for each ingested article.
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR NOT NULL REFERENCES articles(id),
    summary TEXT,
    sentiment VARCHAR,
    keywords TEXT[],
    categories TEXT[],
    companies TEXT[],
    countries TEXT[],
    importance_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);