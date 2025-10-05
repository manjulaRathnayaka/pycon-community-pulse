"""Shared configuration for all services"""
import os
from typing import Optional

class Config:
    """Application configuration"""

    # Database - Choreo injects these environment variables from database connections
    _db_host = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_HOSTNAME")
    _db_port = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_PORT")
    _db_user = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_USERNAME")
    _db_password = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_PASSWORD")
    _db_name = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_DATABASENAME")

    if all([_db_host, _db_port, _db_user, _db_password, _db_name]):
        DATABASE_URL = f"postgresql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
    else:
        DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "postgresql://pycon_app:password@localhost:5432/pycon_pulse"
        )

    # AI API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Data Collection
    DEVTO_API_KEY: Optional[str] = os.getenv("DEVTO_API_KEY")  # Optional, public API works without
    YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY")
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")  # Optional for public data

    # Collection Settings
    COLLECTION_INTERVAL_MINUTES: int = int(os.getenv("COLLECTION_INTERVAL_MINUTES", "30"))
    MAX_POSTS_PER_SOURCE: int = int(os.getenv("MAX_POSTS_PER_SOURCE", "20"))

    # Search Keywords
    PYCON_KEYWORDS: list[str] = ["PyCon", "PyCon 2025", "PyCon US", "#PyCon", "#PyCon2025"]

    # API Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # CORS
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

config = Config()
