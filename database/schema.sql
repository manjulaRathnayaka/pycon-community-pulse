-- PyCon Community Pulse Database Schema
-- PostgreSQL/MySQL compatible

CREATE TABLE IF NOT EXISTS posts (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    source_url VARCHAR(2048) NOT NULL UNIQUE,
    title TEXT,
    content TEXT,
    author_name VARCHAR(255),
    author_url VARCHAR(2048),
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSONB,
    extra_metadata JSONB,
    analyzed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_posts_source ON posts(source);
CREATE INDEX IF NOT EXISTS idx_posts_published ON posts(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_analyzed ON posts(analyzed);

CREATE TABLE IF NOT EXISTS sentiment_analysis (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    sentiment VARCHAR(20),
    confidence DECIMAL(5,4),
    positive_score DECIMAL(5,4),
    negative_score DECIMAL(5,4),
    neutral_score DECIMAL(5,4),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sentiment_post_id ON sentiment_analysis(post_id);

CREATE TABLE IF NOT EXISTS topics (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    topic VARCHAR(100),
    relevance_score DECIMAL(5,4)
);

CREATE INDEX IF NOT EXISTS idx_topics_post_id ON topics(post_id);
CREATE INDEX IF NOT EXISTS idx_topics_topic ON topics(topic);

CREATE TABLE IF NOT EXISTS entities (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    entity_type VARCHAR(50),
    entity_name VARCHAR(255),
    mention_count INT DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_entities_post_id ON entities(post_id);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(entity_name);

CREATE TABLE IF NOT EXISTS collection_log (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posts_found INT,
    posts_new INT,
    status VARCHAR(20),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_collection_log_collected_at ON collection_log(collected_at DESC);
