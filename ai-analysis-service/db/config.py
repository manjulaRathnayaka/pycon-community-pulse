"""Configuration for AI Analysis service"""
import os
from typing import Optional

class Config:
    """Application configuration"""

    # Database - Choreo auto-injects from connection: connection-pycon-ai-analysis-defaultdb
    _db_host = os.getenv("CHOREO_CONNECTION_PYCON_AI_ANALYSIS_DEFAULTDB_HOSTNAME") or os.getenv("DB_HOST")
    _db_port = os.getenv("CHOREO_CONNECTION_PYCON_AI_ANALYSIS_DEFAULTDB_PORT") or os.getenv("DB_PORT")
    _db_user = os.getenv("CHOREO_CONNECTION_PYCON_AI_ANALYSIS_DEFAULTDB_USERNAME") or os.getenv("DB_USER")
    _db_password = os.getenv("CHOREO_CONNECTION_PYCON_AI_ANALYSIS_DEFAULTDB_PASSWORD") or os.getenv("DB_PASSWORD")
    _db_name = os.getenv("CHOREO_CONNECTION_PYCON_AI_ANALYSIS_DEFAULTDB_DATABASENAME") or os.getenv("DB_NAME")

    if all([_db_host, _db_port, _db_user, _db_password, _db_name]):
        # Build connection URL for Choreo-managed databases
        DATABASE_URL = f"postgresql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
    else:
        DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "postgresql://pycon_app:password@localhost:5432/pycon_pulse"
        )

    # AI API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

config = Config()
