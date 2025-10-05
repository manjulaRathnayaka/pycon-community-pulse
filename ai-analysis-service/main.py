"""
AI Analysis Service - Sentiment analysis and topic extraction
Analyzes posts using OpenAI/Anthropic APIs
"""
import sys
import os

# Add the parent directory to the path to import shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional
import uvicorn
import openai
from datetime import datetime
import re

from shared import get_db, get_db_context, config, Post, SentimentAnalysis, Topic, Entity

# Initialize OpenAI
if config.OPENAI_API_KEY:
    openai.api_key = config.OPENAI_API_KEY

app = FastAPI(
    title="PyCon Community Pulse - AI Analysis Service",
    description="Sentiment analysis and topic extraction service",
    version="1.0.0"
)


def extract_topics_and_entities(text: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Simple keyword-based topic and entity extraction"""
    # Common PyCon-related topics
    topics = []
    topic_keywords = {
        "async": ["async", "asyncio", "await", "asynchronous"],
        "FastAPI": ["fastapi", "fast api"],
        "testing": ["pytest", "test", "testing", "unittest"],
        "AI": ["ai", "machine learning", "ml", "deep learning", "llm", "gpt"],
        "data science": ["pandas", "numpy", "data science", "jupyter"],
        "web": ["django", "flask", "web", "api"],
        "python": ["python", "py"],
        "performance": ["performance", "optimization", "speed", "fast"],
    }

    text_lower = text.lower()
    for topic, keywords in topic_keywords.items():
        if any(kw in text_lower for kw in keywords):
            topics.append(topic)

    # Extract entities (simple pattern matching)
    entities = []
    # Find capitalized words (potential names/libraries)
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    for word in words[:5]:  # Limit to 5
        entities.append(("mention", word))

    return topics, entities


def analyze_sentiment_simple(text: str) -> dict:
    """Simple sentiment analysis fallback"""
    positive_words = ["great", "amazing", "excellent", "love", "awesome", "fantastic", "good", "best"]
    negative_words = ["bad", "poor", "terrible", "hate", "awful", "worst", "disappointing"]

    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    if pos_count > neg_count:
        return {
            "sentiment": "positive",
            "confidence": 0.7,
            "positive_score": 0.7,
            "negative_score": 0.2,
            "neutral_score": 0.1
        }
    elif neg_count > pos_count:
        return {
            "sentiment": "negative",
            "confidence": 0.7,
            "positive_score": 0.2,
            "negative_score": 0.7,
            "neutral_score": 0.1
        }
    else:
        return {
            "sentiment": "neutral",
            "confidence": 0.6,
            "positive_score": 0.3,
            "negative_score": 0.3,
            "neutral_score": 0.4
        }


def analyze_sentiment_openai(text: str) -> dict:
    """Analyze sentiment using OpenAI"""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sentiment analysis expert. Analyze the sentiment of the given text and respond ONLY with a JSON object containing: sentiment (positive/negative/neutral), confidence (0-1), positive_score (0-1), negative_score (0-1), neutral_score (0-1). Scores should sum to 1.0."
                },
                {
                    "role": "user",
                    "content": f"Analyze sentiment: {text[:500]}"
                }
            ],
            temperature=0.3,
            max_tokens=150
        )

        result = response.choices[0].message.content
        # Parse JSON response
        import json
        return json.loads(result)
    except Exception as e:
        print(f"OpenAI analysis failed: {e}, falling back to simple analysis")
        return analyze_sentiment_simple(text)


def analyze_post(post_id: int):
    """Analyze a single post"""
    with get_db_context() as db:
        # Get post
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post or post.analyzed:
            return

        text = f"{post.title or ''} {post.content or ''}"

        # Sentiment analysis
        if config.OPENAI_API_KEY:
            sentiment_result = analyze_sentiment_openai(text)
        else:
            sentiment_result = analyze_sentiment_simple(text)

        # Save sentiment
        sentiment = SentimentAnalysis(
            post_id=post.id,
            sentiment=sentiment_result["sentiment"],
            confidence=sentiment_result["confidence"],
            positive_score=sentiment_result["positive_score"],
            negative_score=sentiment_result["negative_score"],
            neutral_score=sentiment_result["neutral_score"]
        )
        db.add(sentiment)

        # Extract topics and entities
        topics, entities = extract_topics_and_entities(text)

        # Save topics
        for topic_name in topics:
            topic = Topic(
                post_id=post.id,
                topic=topic_name,
                relevance_score=0.8  # Simple scoring
            )
            db.add(topic)

        # Save entities
        for entity_type, entity_name in entities:
            entity = Entity(
                post_id=post.id,
                entity_type=entity_type,
                entity_name=entity_name,
                mention_count=1
            )
            db.add(entity)

        # Mark as analyzed
        post.analyzed = True
        db.commit()

        print(f"✅ Analyzed post {post_id}: {sentiment_result['sentiment']}")


@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "AI Analysis Service",
        "status": "healthy",
        "openai_configured": bool(config.OPENAI_API_KEY)
    }


@app.post("/analyze/{post_id}")
async def analyze_post_endpoint(post_id: int, background_tasks: BackgroundTasks):
    """Trigger analysis for a specific post"""
    background_tasks.add_task(analyze_post, post_id)
    return {"status": "queued", "post_id": post_id}


@app.post("/analyze/pending")
async def analyze_pending_posts(
    limit: int = 10,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Analyze pending posts"""
    pending_posts = db.query(Post).filter(Post.analyzed == False).limit(limit).all()

    for post in pending_posts:
        if background_tasks:
            background_tasks.add_task(analyze_post, post.id)
        else:
            analyze_post(post.id)

    return {
        "status": "processing",
        "posts_queued": len(pending_posts)
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
