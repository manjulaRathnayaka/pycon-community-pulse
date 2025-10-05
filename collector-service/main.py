"""
Collector Service - Background data collection from public sources
Collects posts from Dev.to, Medium, YouTube, GitHub about PyCon
"""
import sys
import os

# Add current directory to path to import shared module
sys.path.insert(0, os.path.dirname(__file__))

import time
import requests
import feedparser
from datetime import datetime
from typing import List, Dict
import json

from shared import get_db_context, config, Post, CollectionLog


class DataCollector:
    """Collects data from various public sources"""

    def __init__(self):
        self.keywords = config.PYCON_KEYWORDS
        self.max_posts = config.MAX_POSTS_PER_SOURCE

    def collect_devto(self) -> List[Dict]:
        """Collect posts from Dev.to"""
        posts = []
        try:
            for keyword in self.keywords[:2]:  # Limit keywords
                url = f"https://dev.to/api/articles?tag=pycon&per_page=10"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                articles = response.json()
                for article in articles[:self.max_posts]:
                    posts.append({
                        "source": "devto",
                        "source_url": article["url"],
                        "title": article["title"],
                        "content": article.get("description", "")[:1000],
                        "author_name": article["user"]["name"],
                        "author_url": f"https://dev.to/{article['user']['username']}",
                        "published_at": datetime.fromisoformat(article["published_at"].replace("Z", "+00:00")),
                        "tags": json.dumps(article.get("tag_list", [])),
                        "extra_metadata": json.dumps({
                            "positive_reactions_count": article.get("positive_reactions_count", 0),
                            "comments_count": article.get("comments_count", 0)
                        })
                    })
                time.sleep(1)  # Rate limiting

            print(f"✅ Collected {len(posts)} posts from Dev.to")
        except Exception as e:
            print(f"❌ Error collecting from Dev.to: {e}")

        return posts

    def collect_medium_rss(self) -> List[Dict]:
        """Collect posts from Medium RSS"""
        posts = []
        try:
            # Medium tag RSS
            feed_url = "https://medium.com/feed/tag/pycon"
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:self.max_posts]:
                posts.append({
                    "source": "medium",
                    "source_url": entry.link,
                    "title": entry.title,
                    "content": entry.get("summary", "")[:1000],
                    "author_name": entry.get("author", "Unknown"),
                    "author_url": entry.get("author_detail", {}).get("href", ""),
                    "published_at": datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None,
                    "tags": json.dumps([tag.term for tag in entry.get("tags", [])[:5]]),
                    "extra_metadata": json.dumps({})
                })

            print(f"✅ Collected {len(posts)} posts from Medium")
        except Exception as e:
            print(f"❌ Error collecting from Medium: {e}")

        return posts

    def collect_youtube_comments(self) -> List[Dict]:
        """Collect comments from YouTube PyCon videos (if API key available)"""
        posts = []
        if not config.YOUTUBE_API_KEY:
            print("ℹ️  YouTube API key not configured, skipping")
            return posts

        try:
            # Search for PyCon videos
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": "PyCon 2025",
                "type": "video",
                "maxResults": 5,
                "key": config.YOUTUBE_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            videos = response.json().get("items", [])
            # For demo, we'll just collect video metadata instead of comments
            for video in videos:
                snippet = video["snippet"]
                posts.append({
                    "source": "youtube",
                    "source_url": f"https://www.youtube.com/watch?v={video['id']['videoId']}",
                    "title": snippet["title"],
                    "content": snippet["description"][:1000],
                    "author_name": snippet["channelTitle"],
                    "author_url": f"https://www.youtube.com/channel/{snippet['channelId']}",
                    "published_at": datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
                    "tags": json.dumps([]),
                    "extra_metadata": json.dumps({})
                })

            print(f"✅ Collected {len(posts)} videos from YouTube")
        except Exception as e:
            print(f"❌ Error collecting from YouTube: {e}")

        return posts

    def collect_github_discussions(self) -> List[Dict]:
        """Collect discussions from GitHub (public data)"""
        posts = []
        try:
            # Search GitHub repos/discussions
            url = "https://api.github.com/search/repositories"
            params = {
                "q": "pycon 2025",
                "sort": "updated",
                "per_page": 5
            }
            headers = {}
            if config.GITHUB_TOKEN:
                headers["Authorization"] = f"token {config.GITHUB_TOKEN}"

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            repos = response.json().get("items", [])
            for repo in repos:
                description = repo.get("description") or "No description"
                posts.append({
                    "source": "github",
                    "source_url": repo["html_url"],
                    "title": repo["name"],
                    "content": description[:1000],
                    "author_name": repo["owner"]["login"],
                    "author_url": repo["owner"]["html_url"],
                    "published_at": datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00")),
                    "tags": json.dumps(repo.get("topics", [])[:5]),
                    "extra_metadata": json.dumps({
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0)
                    })
                })

            print(f"✅ Collected {len(posts)} repos from GitHub")
        except Exception as e:
            print(f"❌ Error collecting from GitHub: {e}")

        return posts

    def collect_all(self) -> Dict[str, List[Dict]]:
        """Collect from all sources"""
        print("\n" + "="*60)
        print("🔍 Starting data collection...")
        print("="*60)

        results = {
            "devto": self.collect_devto(),
            "medium": self.collect_medium_rss(),
            "youtube": self.collect_youtube_comments(),
            "github": self.collect_github_discussions()
        }

        total = sum(len(posts) for posts in results.values())
        print(f"\n✨ Total posts collected: {total}")
        return results


def save_posts_to_db(posts: List[Dict], source: str):
    """Save posts to database"""
    with get_db_context() as db:
        posts_found = len(posts)
        posts_new = 0

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
            except Exception as e:
                # Skip duplicates that might occur due to race conditions
                db.rollback()
                continue

        # Log collection
        log = CollectionLog(
            source=source,
            posts_found=posts_found,
            posts_new=posts_new,
            status="success"
        )
        db.add(log)
        db.commit()

        print(f"💾 Saved {posts_new} new posts from {source}")


def main():
    """Main collection - single run for scheduled/manual task"""
    collector = DataCollector()

    try:
        print("""
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║       PyCon Community Pulse - Data Collector        ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
        """)

        # Collect from all sources
        results = collector.collect_all()

        # Save to database
        for source, posts in results.items():
            if posts:
                save_posts_to_db(posts, source)

        print("\n✅ Collection completed successfully!")

    except Exception as e:
        print(f"\n❌ Error in collection: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
