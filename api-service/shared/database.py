"""Database connection and session management"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .config import config
import os

# Lazy-load engine and session factory
_engine = None
_SessionLocal = None

# Base class for ORM models
Base = declarative_base()

def get_engine():
    """Get or create database engine (lazy initialization)"""
    global _engine
    if _engine is None:
        connect_args = {
            "connect_timeout": 10,
        }

        # SSL configuration for Aiven/managed PostgreSQL databases
        if "aivencloud.com" in config.DATABASE_URL:
            connect_args["sslmode"] = "require"

            # Use the CA certificate file from the project root
            ca_cert_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "ca-85f67baa-6594-4397-b2a4-59b362a01435.pem"
            )
            if os.path.exists(ca_cert_path):
                connect_args["sslrootcert"] = ca_cert_path

        _engine = create_engine(
            config.DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Auto-reconnect on connection loss
            echo=False,  # Set to True for SQL debugging
            connect_args=connect_args
        )
    return _engine

def get_session_factory():
    """Get or create session factory (lazy initialization)"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

# Keep these for backward compatibility
engine = property(lambda self: get_engine())
SessionLocal = property(lambda self: get_session_factory())

def get_db():
    """Dependency for FastAPI to get database session"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for database session"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
