"""
Collector Service - Background data collection from public sources.

This service collects posts from Dev.to, Medium, YouTube, and GitHub
about PyCon conferences and stores them in the database for analysis.
"""
import logging
import os
import sys
from typing import Dict, List

# Add current directory to path to import db module
sys.path.insert(0, os.path.dirname(__file__))

from collectors import (
    DevToCollector,
    MediumCollector,
    YouTubeCollector,
    GitHubCollector
)
from db import get_db_context, config, Post, CollectionLog, init_db

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_all_sources() -> Dict[str, List[Dict]]:
    """
    Collect data from all configured sources.

    Returns:
        Dict mapping source name to list of collected posts
    """
    logger.info("=" * 80)
    logger.info("Starting data collection from all sources...")
    logger.info("=" * 80)

    # Initialize collectors
    collectors = {
        "devto": DevToCollector(config.PYCON_KEYWORDS, config.MAX_POSTS_PER_SOURCE),
        "medium": MediumCollector(config.PYCON_KEYWORDS, config.MAX_POSTS_PER_SOURCE),
        "youtube": YouTubeCollector(
            config.PYCON_KEYWORDS,
            config.MAX_POSTS_PER_SOURCE,
            config.YOUTUBE_API_KEY
        ),
        "github": GitHubCollector(
            config.PYCON_KEYWORDS,
            config.MAX_POSTS_PER_SOURCE,
            config.GITHUB_TOKEN
        )
    }

    # Collect from all sources
    results: Dict[str, List[Dict]] = {}
    for source_name, collector in collectors.items():
        try:
            logger.info(f"Collecting from {source_name}...")
            posts = collector.collect()
            results[source_name] = posts
        except Exception as e:
            logger.error(f"Error collecting from {source_name}: {e}", exc_info=True)
            results[source_name] = []

    total = sum(len(posts) for posts in results.values())
    logger.info(f"Collection complete. Total posts collected: {total}")
    return results


def save_posts_to_db(posts: List[Dict], source: str) -> None:
    """
    Save collected posts to the database.

    This function handles duplicate detection and logs collection statistics.

    Args:
        posts: List of post dictionaries to save
        source: Source name for logging
    """
    try:
        with get_db_context() as db:
            posts_found = len(posts)
            posts_new = 0
            posts_duplicate = 0

            for post_data in posts:
                try:
                    # Check if post already exists
                    existing = db.query(Post).filter(
                        Post.source_url == post_data["source_url"]
                    ).first()

                    if not existing:
                        post = Post(**post_data)
                        db.add(post)
                        db.flush()  # Flush to detect duplicates before final commit
                        posts_new += 1
                    else:
                        posts_duplicate += 1
                except Exception as e:
                    # Skip duplicates that might occur due to race conditions
                    logger.debug(f"Skipping duplicate post: {e}")
                    db.rollback()
                    posts_duplicate += 1
                    continue

            # Log collection results
            log = CollectionLog(
                source=source,
                posts_found=posts_found,
                posts_new=posts_new,
                status="success"
            )
            db.add(log)
            db.commit()

            logger.info(
                f"Saved {posts_new} new posts from {source} "
                f"({posts_duplicate} duplicates skipped)"
            )
    except Exception as e:
        logger.error(f"Error saving posts from {source}: {e}", exc_info=True)
        # Log failed collection
        try:
            with get_db_context() as db:
                log = CollectionLog(
                    source=source,
                    posts_found=len(posts),
                    posts_new=0,
                    status="error",
                    error_message=str(e)
                )
                db.add(log)
                db.commit()
        except Exception as log_error:
            logger.error(f"Failed to log collection error: {log_error}")


def main() -> None:
    """
    Main entry point for the collector service.

    Performs a single collection run from all sources and saves results
    to the database. Designed to be run as a scheduled task or cron job.
    """
    try:
        logger.info("""
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║       PyCon Community Pulse - Data Collector        ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
        """)

        # Initialize database tables on first run
        logger.info("Initializing database tables...")
        init_db()
        logger.info("Database tables initialized successfully")

        # Collect from all sources
        results = collect_all_sources()

        # Save to database
        for source, posts in results.items():
            if posts:
                save_posts_to_db(posts, source)
            else:
                logger.warning(f"No posts collected from {source}")

        logger.info("=" * 80)
        logger.info("Collection completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Fatal error in collection: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
