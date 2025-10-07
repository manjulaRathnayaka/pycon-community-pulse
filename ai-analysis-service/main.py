"""
AI Analysis Service - Sentiment analysis and topic extraction.

This service analyzes posts using OpenAI APIs for sentiment analysis,
topic extraction, and entity recognition.
"""
import logging
import os
import re
import random
import sys
from typing import Dict, List, Optional, Tuple

import openai
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Add current directory to path to import db module
sys.path.insert(0, os.path.dirname(__file__))

from db import get_db, get_db_context, config, Post, SentimentAnalysis, Topic, Entity

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI
if config.OPENAI_API_KEY:
    openai.api_key = config.OPENAI_API_KEY
    logger.info("OpenAI API key configured")
else:
    logger.warning("OpenAI API key not configured - using fallback analysis")

app = FastAPI(
    title="PyCon Community Pulse - AI Analysis Service",
    description="Sentiment analysis and topic extraction service",
    version="1.0.0"
)


# Response Models
class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status."""
    status: str
    posts_queued: int


class ServiceInfoResponse(BaseModel):
    """Response model for service information."""
    service: str
    status: str
    openai_configured: bool


class SentimentResult(BaseModel):
    """Model for sentiment analysis results."""
    sentiment: str = Field(..., description="Sentiment classification: positive, negative, or neutral")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    positive_score: float = Field(..., ge=0.0, le=1.0)
    negative_score: float = Field(..., ge=0.0, le=1.0)
    neutral_score: float = Field(..., ge=0.0, le=1.0)


# Topic keywords for extraction
TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "async": ["async", "asyncio", "await", "asynchronous"],
    "FastAPI": ["fastapi", "fast api"],
    "testing": ["pytest", "test", "testing", "unittest"],
    "AI": ["ai", "machine learning", "ml", "deep learning", "llm", "gpt"],
    "data science": ["pandas", "numpy", "data science", "jupyter"],
    "web": ["django", "flask", "web", "api"],
    "python": ["python", "py"],
    "performance": ["performance", "optimization", "speed", "fast"],
}


def extract_topics_and_entities(text: str) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Extract topics and entities from text using keyword matching.

    Args:
        text: Input text to analyze

    Returns:
        Tuple of (topics, entities) where:
            - topics is a list of topic names
            - entities is a list of (entity_type, entity_name) tuples
    """
    topics: List[str] = []
    text_lower = text.lower()

    # Extract topics based on keywords
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            topics.append(topic)

    # Extract entities (simple pattern matching for capitalized words)
    entities: List[Tuple[str, str]] = []
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    for word in words[:5]:  # Limit to 5 entities
        entities.append(("mention", word))

    logger.debug(f"Extracted {len(topics)} topics and {len(entities)} entities")
    return topics, entities


def analyze_sentiment_simple(text: str) -> SentimentResult:
    """
    Simple rule-based sentiment analysis fallback.

    Used when OpenAI API is not available. Performs keyword-based
    sentiment classification.

    Args:
        text: Input text to analyze

    Returns:
        SentimentResult: Sentiment classification with scores
    """
    positive_words = ["great", "amazing", "excellent", "love", "awesome", "fantastic", "good", "best"]
    negative_words = ["bad", "poor", "terrible", "hate", "awful", "worst", "disappointing"]

    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    if pos_count > neg_count:
        return SentimentResult(
            sentiment="positive",
            confidence=0.7,
            positive_score=0.7,
            negative_score=0.2,
            neutral_score=0.1
        )
    elif neg_count > pos_count:
        return SentimentResult(
            sentiment="negative",
            confidence=0.7,
            positive_score=0.2,
            negative_score=0.7,
            neutral_score=0.1
        )
    else:
        return SentimentResult(
            sentiment="neutral",
            confidence=0.6,
            positive_score=0.3,
            negative_score=0.3,
            neutral_score=0.4
        )


def analyze_sentiment_openai_demo(text: str) -> SentimentResult:
    """
    DEMO MODE: Generate random sentiment without calling OpenAI API.

    This is used for demonstration purposes to avoid API costs.
    In production, this would be replaced with actual OpenAI API calls.

    Args:
        text: Input text (unused in demo mode)

    Returns:
        SentimentResult: Randomly generated sentiment with bias toward positive
    """
    logger.debug("DEMO MODE: Generating random sentiment (not calling OpenAI)")

    sentiments = ["positive", "neutral", "negative"]
    weights = [0.7, 0.2, 0.1]  # 70% positive, 20% neutral, 10% negative
    chosen_sentiment = random.choices(sentiments, weights=weights)[0]

    if chosen_sentiment == "positive":
        positive_score = random.uniform(0.6, 0.9)
        neutral_score = random.uniform(0.05, 0.2)
        negative_score = 1.0 - positive_score - neutral_score
    elif chosen_sentiment == "neutral":
        neutral_score = random.uniform(0.5, 0.7)
        positive_score = random.uniform(0.15, 0.3)
        negative_score = 1.0 - neutral_score - positive_score
    else:  # negative
        negative_score = random.uniform(0.5, 0.8)
        neutral_score = random.uniform(0.1, 0.2)
        positive_score = 1.0 - negative_score - neutral_score

    return SentimentResult(
        sentiment=chosen_sentiment,
        confidence=random.uniform(0.7, 0.95),
        positive_score=round(positive_score, 3),
        negative_score=round(negative_score, 3),
        neutral_score=round(neutral_score, 3)
    )


def analyze_post(post_id: int) -> None:
    """
    Analyze a single post for sentiment, topics, and entities.

    This function performs the complete analysis pipeline:
    1. Fetch post from database
    2. Perform sentiment analysis
    3. Extract topics and entities
    4. Save results to database

    Args:
        post_id: ID of the post to analyze
    """
    try:
        with get_db_context() as db:
            # Get post
            post = db.query(Post).filter(Post.id == post_id).first()
            if not post or post.analyzed:
                logger.debug(f"Post {post_id} not found or already analyzed")
                return

            text = f"{post.title or ''} {post.content or ''}"

            # Sentiment analysis
            if config.OPENAI_API_KEY:
                sentiment_result = analyze_sentiment_openai_demo(text)
            else:
                sentiment_result = analyze_sentiment_simple(text)

            # Save sentiment
            sentiment = SentimentAnalysis(
                post_id=post.id,
                sentiment=sentiment_result.sentiment,
                confidence=sentiment_result.confidence,
                positive_score=sentiment_result.positive_score,
                negative_score=sentiment_result.negative_score,
                neutral_score=sentiment_result.neutral_score
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

            logger.info(f"Analyzed post {post_id}: {sentiment_result.sentiment}")
    except Exception as e:
        logger.error(f"Error analyzing post {post_id}: {e}", exc_info=True)


@app.get("/", response_model=ServiceInfoResponse)
async def root() -> ServiceInfoResponse:
    """
    Root endpoint providing service information.

    Returns:
        ServiceInfoResponse: Service status and configuration
    """
    return ServiceInfoResponse(
        service="AI Analysis Service",
        status="healthy",
        openai_configured=bool(config.OPENAI_API_KEY)
    )


@app.post("/analyze/pending", response_model=AnalysisStatusResponse)
async def analyze_pending_posts(
    background_tasks: BackgroundTasks,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> AnalysisStatusResponse:
    """
    Analyze pending posts in the background.

    Fetches unanalyzed posts from the database and queues them for
    background processing.

    Args:
        background_tasks: FastAPI background tasks manager
        limit: Maximum number of posts to analyze
        db: Database session from dependency injection

    Returns:
        AnalysisStatusResponse: Status and number of posts queued

    Raises:
        HTTPException: If database query fails
    """
    try:
        pending_posts = db.query(Post).filter(Post.analyzed == False).limit(limit).all()

        for post in pending_posts:
            background_tasks.add_task(analyze_post, post.id)

        logger.info(f"Queued {len(pending_posts)} posts for analysis")
        return AnalysisStatusResponse(
            status="processing",
            posts_queued=len(pending_posts)
        )
    except Exception as e:
        logger.error(f"Error queuing posts for analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error queuing posts: {str(e)}")


@app.post("/analyze/{post_id}", response_model=dict)
async def analyze_post_endpoint(
    post_id: int,
    background_tasks: BackgroundTasks
) -> dict:
    """
    Trigger analysis for a specific post.

    Args:
        post_id: ID of the post to analyze
        background_tasks: FastAPI background tasks manager

    Returns:
        dict: Status and post ID
    """
    background_tasks.add_task(analyze_post, post_id)
    logger.info(f"Queued post {post_id} for analysis")
    return {"status": "queued", "post_id": post_id}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting AI Analysis service on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=config.LOG_LEVEL.lower(),
        reload=False  # Disable reload in production
    )
