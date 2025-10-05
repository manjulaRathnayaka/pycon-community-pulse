"""SQLAlchemy ORM models"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Integer, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(BigInteger, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    source_url = Column(String(2048), nullable=False, unique=True)
    title = Column(Text)
    content = Column(Text)
    author_name = Column(String(255))
    author_url = Column(String(2048))
    published_at = Column(DateTime)
    collected_at = Column(DateTime, server_default=func.now())
    tags = Column(JSON)
    extra_metadata = Column(JSON)
    analyzed = Column(Boolean, default=False, index=True)

    # Relationships
    sentiment = relationship("SentimentAnalysis", back_populates="post", cascade="all, delete-orphan")
    topics = relationship("Topic", back_populates="post", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="post", cascade="all, delete-orphan")


class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analysis"

    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    sentiment = Column(String(20))
    confidence = Column(DECIMAL(5, 4))
    positive_score = Column(DECIMAL(5, 4))
    negative_score = Column(DECIMAL(5, 4))
    neutral_score = Column(DECIMAL(5, 4))
    analyzed_at = Column(DateTime, server_default=func.now())

    # Relationships
    post = relationship("Post", back_populates="sentiment")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(100), index=True)
    relevance_score = Column(DECIMAL(5, 4))

    # Relationships
    post = relationship("Post", back_populates="topics")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50))
    entity_name = Column(String(255), index=True)
    mention_count = Column(Integer, default=1)

    # Relationships
    post = relationship("Post", back_populates="entities")


class CollectionLog(Base):
    __tablename__ = "collection_log"

    id = Column(BigInteger, primary_key=True, index=True)
    source = Column(String(50))
    collected_at = Column(DateTime, server_default=func.now(), index=True)
    posts_found = Column(Integer)
    posts_new = Column(Integer)
    status = Column(String(20))
    error_message = Column(Text)
