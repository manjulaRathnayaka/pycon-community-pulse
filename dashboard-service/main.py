"""
Dashboard Service - Web UI for PyCon Community Pulse.

Displays sentiment trends, popular topics, and recent posts in a
user-friendly web interface.
"""
import logging
import os
import sys
from typing import Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PyCon Community Pulse - Dashboard",
    version="1.0.0"
)

# Templates
templates = Jinja2Templates(directory="templates")

# Get API connection details from Choreo auto-injected environment variables
# Connection name: dashboard-to-api -> env: CHOREO_DASHBOARD_TO_API_SERVICEURL
API_SERVICE_URL = os.getenv("CHOREO_DASHBOARD_TO_API_SERVICEURL", "http://localhost:8080")
API_BASE_URL = API_SERVICE_URL.rstrip('/')

# Log configuration on startup
logger.info("=" * 80)
logger.info("DASHBOARD SERVICE CONFIGURATION")
logger.info("=" * 80)
logger.info(f"API_SERVICE_URL: {API_SERVICE_URL}")
logger.info(f"API_BASE_URL: {API_BASE_URL}")
logger.info(f"PORT: {os.getenv('PORT', '8080')}")
logger.info(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'info')}")
logger.info("=" * 80)
sys.stdout.flush()
sys.stderr.flush()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """
    Render the main dashboard page shell.

    The page loads with skeleton loaders, then fetches data client-side
    using JavaScript for better perceived performance.

    Args:
        request: FastAPI request object

    Returns:
        HTMLResponse: Rendered dashboard page shell
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "api_base_url": API_BASE_URL
        }
    )


@app.get("/health")
async def health() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Dict with service name and status
    """
    return {"status": "healthy", "service": "Dashboard"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    logger.info(f"Starting Dashboard service on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=log_level,
        reload=False  # Disable reload in production
    )
