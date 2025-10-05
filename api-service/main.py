"""
API Service - Main REST API for PyCon Community Pulse
Provides endpoints for accessing posts, sentiment, and trends
"""
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy import desc, func, text

# Add current directory to path to import shared module
sys.path.insert(0, os.path.dirname(__file__))

from shared import get_db_context, config, Post, SentimentAnalysis, Topic

# Flask app - this needs to be named 'app' for Gunicorn to find it
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

@app.route("/")
def root():
    """Root endpoint"""
    return jsonify({
        "service": "PyCon Community Pulse API",
        "status": "healthy",
        "version": "1.0.0"
    })

@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        return jsonify({
            "status": "healthy",
            "service": "api-service",
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "service": "api-service",
            "database": "error",
            "error": str(e)
        }), 500

@app.route("/posts")
def get_posts():
    """Get recent posts"""
    try:
        limit = int(request.args.get('limit', 20))
        with get_db_context() as db:
            posts = db.query(Post).order_by(desc(Post.published_at)).limit(limit).all()
            return jsonify({
                "posts": [
                    {
                        "id": p.id,
                        "source": p.source,
                        "title": p.title,
                        "author": p.author_name,
                        "url": p.source_url,
                        "published_at": p.published_at.isoformat() if p.published_at else None,
                        "analyzed": p.analyzed
                    }
                    for p in posts
                ],
                "count": len(posts)
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sentiment/stats")
def get_sentiment_stats():
    """Get sentiment statistics"""
    try:
        with get_db_context() as db:
            total_posts = db.query(func.count(Post.id)).scalar() or 0

            # Get sentiment counts
            sentiments = db.query(SentimentAnalysis).all()
            positive = sum(1 for s in sentiments if s.sentiment == "positive")
            negative = sum(1 for s in sentiments if s.sentiment == "negative")
            neutral = sum(1 for s in sentiments if s.sentiment == "neutral")

            # Calculate average sentiment score
            avg_sentiment = 0.0
            if sentiments:
                avg_sentiment = sum(s.positive_score - s.negative_score for s in sentiments) / len(sentiments)

            return jsonify({
                "total_posts": total_posts,
                "analyzed_posts": len(sentiments),
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "average_sentiment": round(float(avg_sentiment), 2)
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/topics/trending")
def get_trending_topics():
    """Get trending topics"""
    try:
        limit = int(request.args.get('limit', 10))
        with get_db_context() as db:
            topics = db.query(
                Topic.topic,
                func.count(Topic.id).label("count")
            ).group_by(Topic.topic).order_by(desc("count")).limit(limit).all()

            return jsonify({
                "topics": [
                    {"topic": t.topic, "count": t.count}
                    for t in topics
                ],
                "count": len(topics)
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
