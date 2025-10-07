"""Configuration for API service"""
import os

class Config:
    """Application configuration"""

    # Database - Choreo auto-injects from connection: connection-pycon-api-defaultdb
    _db_host = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_HOSTNAME")
    _db_port = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_PORT")
    _db_user = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_USERNAME")
    _db_password = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_PASSWORD")
    _db_name = os.getenv("CHOREO_CONNECTION_PYCON_API_DEFAULTDB_DATABASENAME")

    if all([_db_host, _db_port, _db_user, _db_password, _db_name]):
        # Build connection URL for Choreo-managed databases
        # SSL configuration is handled in database.py connect_args
        DATABASE_URL = f"postgresql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
    else:
        DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "postgresql://pycon_app:password@localhost:5432/pycon_pulse"
        )

    # CORS
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

config = Config()
