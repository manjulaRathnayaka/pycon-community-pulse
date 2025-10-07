"""Configuration for Collector service"""
import os
from typing import Optional

class Config:
    """Application configuration"""

    # Database - Choreo auto-injects from connection: connection-pycon-collector-defaultdb
    _db_host = os.getenv("CHOREO_CONNECTION_PYCON_COLLECTOR_DEFAULTDB_HOSTNAME")
    _db_port = os.getenv("CHOREO_CONNECTION_PYCON_COLLECTOR_DEFAULTDB_PORT")
    _db_user = os.getenv("CHOREO_CONNECTION_PYCON_COLLECTOR_DEFAULTDB_USERNAME")
    _db_password = os.getenv("CHOREO_CONNECTION_PYCON_COLLECTOR_DEFAULTDB_PASSWORD")
    _db_name = os.getenv("CHOREO_CONNECTION_PYCON_COLLECTOR_DEFAULTDB_DATABASENAME")

    if all([_db_host, _db_port, _db_user, _db_password, _db_name]):
        # Build connection URL for Choreo-managed databases
        # SSL configuration is handled in database.py connect_args
        DATABASE_URL = f"postgresql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
    else:
        DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "postgresql://pycon_app:password@localhost:5432/pycon_pulse"
        )

    # Data Collection API Keys
    YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY")
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")

    # Collection Settings
    MAX_POSTS_PER_SOURCE: int = int(os.getenv("MAX_POSTS_PER_SOURCE", "20"))

    # Search Keywords
    PYCON_KEYWORDS: list[str] = ["PyCon", "PyCon 2025", "PyCon US", "#PyCon", "#PyCon2025"]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

config = Config()
