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
import requests

# Add current directory to path to import shared module
sys.path.insert(0, os.path.dirname(__file__))

from shared import get_db_context, init_db, config, Post, SentimentAnalysis, Topic

# AI Analysis Service URL (Choreo auto-injects from connection: connection-ai-analysis)
AI_SERVICE_URL = os.getenv("CHOREO_CONNECTION_AI_ANALYSIS_SERVICEURL", "http://localhost:8001")

# Flask app - this needs to be named 'app' for Gunicorn to find it
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Flag to track if DB is initialized
_db_initialized = False

@app.before_request
def initialize_database():
    """Initialize database tables on first request"""
    global _db_initialized
    if not _db_initialized:
        try:
            init_db()
            print("Database tables initialized successfully")
            _db_initialized = True
        except Exception as e:
            print(f"Database initialization error: {e}")
            # Don't set flag if initialization failed, will retry on next request

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

def trigger_ai_analysis_if_needed(db, min_analyzed=10):
    """Trigger AI analysis if we don't have enough analyzed posts"""
    try:
        analyzed_count = db.query(func.count(Post.id)).filter(Post.analyzed == True).scalar() or 0

        # If we have fewer than min_analyzed posts, trigger analysis
        if analyzed_count < min_analyzed:
            pending_count = db.query(func.count(Post.id)).filter(Post.analyzed == False).scalar() or 0

            if pending_count > 0:
                # Trigger AI analysis for pending posts (limit to avoid excessive costs)
                limit = min(20, pending_count)  # Max 20 posts per trigger
                print(f"🤖 Triggering AI analysis for {limit} pending posts...")

                try:
                    response = requests.post(
                        f"{AI_SERVICE_URL.rstrip('/')}/analyze/pending",
                        params={"limit": limit},
                        timeout=2  # Don't wait for completion, fire and forget
                    )
                    print(f"✅ AI analysis triggered: {response.status_code}")
                except requests.exceptions.Timeout:
                    print("⏰ AI analysis triggered (timeout expected - processing in background)")
                except Exception as e:
                    print(f"⚠️  AI analysis trigger failed: {e}")
    except Exception as e:
        print(f"❌ Error checking analysis status: {e}")

@app.route("/sentiment/stats")
def get_sentiment_stats():
    """Get sentiment statistics"""
    try:
        with get_db_context() as db:
            # Trigger AI analysis if needed (on-demand)
            trigger_ai_analysis_if_needed(db, min_analyzed=10)

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
