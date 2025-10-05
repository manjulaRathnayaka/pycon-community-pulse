"""
API Service - Main REST API for PyCon Community Pulse
Provides endpoints for accessing posts, sentiment, and trends
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# FastAPI app - this needs to be named 'app' for Gunicorn to find it
app = FastAPI(
    title="PyCon Community Pulse API",
    description="API for accessing PyCon community sentiment and trends",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to PyCon Community Pulse API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-service"}

@app.get("/posts")
async def get_posts():
    """Get recent posts"""
    return {"posts": [], "message": "Database connection pending"}

@app.get("/sentiment/stats")
async def get_sentiment_stats():
    """Get sentiment statistics"""
    return {
        "total_posts": 0,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "average_sentiment": 0.0
    }

@app.get("/topics/trending")
async def get_trending_topics():
    """Get trending topics"""
    return {"topics": [], "message": "Database connection pending"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
