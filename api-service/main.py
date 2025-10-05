"""
API Service - Main REST API for PyCon Community Pulse
Provides endpoints for accessing posts, sentiment, and trends
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS

# Flask app - this needs to be named 'app' for Gunicorn to find it
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

@app.route("/")
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Welcome to PyCon Community Pulse API", 
        "version": "1.0.0"
    })

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "service": "api-service"
    })

@app.route("/posts")
def get_posts():
    """Get recent posts"""
    return jsonify({
        "posts": [], 
        "message": "Database connection pending"
    })

@app.route("/sentiment/stats")
def get_sentiment_stats():
    """Get sentiment statistics"""
    return jsonify({
        "total_posts": 0,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "average_sentiment": 0.0
    })

@app.route("/topics/trending")
def get_trending_topics():
    """Get trending topics"""
    return jsonify({
        "topics": [], 
        "message": "Database connection pending"
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
