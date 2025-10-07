"""
Data collectors for various public sources.

Each collector class is responsible for fetching data from a specific
source (Dev.to, Medium, YouTube, GitHub) and normalizing it into a
common format.
"""
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

import feedparser
import requests

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, keywords: List[str], max_posts: int):
        """
        Initialize the collector.

        Args:
            keywords: List of keywords to search for
            max_posts: Maximum number of posts to collect
        """
        self.keywords = keywords
        self.max_posts = max_posts

    @abstractmethod
    def collect(self) -> List[Dict]:
        """
        Collect posts from the source.

        Returns:
            List of post dictionaries in normalized format
        """
        pass

    def _normalize_post(
        self,
        source: str,
        url: str,
        title: str,
        content: str,
        author_name: Optional[str],
        author_url: Optional[str],
        published_at: Optional[datetime],
        tags: List[str],
        metadata: Dict
    ) -> Dict:
        """
        Normalize post data into standard format.

        Args:
            source: Source name (e.g., 'devto', 'medium')
            url: Post URL
            title: Post title
            content: Post content/description
            author_name: Author name
            author_url: Author profile URL
            published_at: Publication datetime
            tags: List of tags
            metadata: Additional metadata

        Returns:
            Dict: Normalized post data
        """
        return {
            "source": source,
            "source_url": url,
            "title": title,
            "content": content[:1000],  # Limit content length
            "author_name": author_name,
            "author_url": author_url,
            "published_at": published_at,
            "tags": json.dumps(tags),
            "extra_metadata": json.dumps(metadata)
        }


class DevToCollector(BaseCollector):
    """Collector for Dev.to articles."""

    BASE_URL = "https://dev.to/api/articles"

    def collect(self) -> List[Dict]:
        """
        Collect articles from Dev.to.

        Returns:
            List of normalized post dictionaries
        """
        posts: List[Dict] = []
        try:
            # Dev.to has a 'pycon' tag we can use
            url = f"{self.BASE_URL}?tag=pycon&per_page={self.max_posts}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            articles = response.json()
            for article in articles[:self.max_posts]:
                post = self._normalize_post(
                    source="devto",
                    url=article["url"],
                    title=article["title"],
                    content=article.get("description", ""),
                    author_name=article["user"]["name"],
                    author_url=f"https://dev.to/{article['user']['username']}",
                    published_at=datetime.fromisoformat(article["published_at"].replace("Z", "+00:00")),
                    tags=article.get("tag_list", []),
                    metadata={
                        "positive_reactions_count": article.get("positive_reactions_count", 0),
                        "comments_count": article.get("comments_count", 0)
                    }
                )
                posts.append(post)

            logger.info(f"Collected {len(posts)} posts from Dev.to")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error collecting from Dev.to: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error in DevTo collector: {e}", exc_info=True)

        return posts


class MediumCollector(BaseCollector):
    """Collector for Medium articles via RSS."""

    FEED_URL = "https://medium.com/feed/tag/pycon"

    def collect(self) -> List[Dict]:
        """
        Collect articles from Medium RSS feed.

        Returns:
            List of normalized post dictionaries
        """
        posts: List[Dict] = []
        try:
            feed = feedparser.parse(self.FEED_URL)

            for entry in feed.entries[:self.max_posts]:
                # Extract tags
                tags = [tag.term for tag in entry.get("tags", [])[:5]]

                # Parse published date
                published_at = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                post = self._normalize_post(
                    source="medium",
                    url=entry.link,
                    title=entry.title,
                    content=entry.get("summary", ""),
                    author_name=entry.get("author", "Unknown"),
                    author_url=entry.get("author_detail", {}).get("href", ""),
                    published_at=published_at,
                    tags=tags,
                    metadata={}
                )
                posts.append(post)

            logger.info(f"Collected {len(posts)} posts from Medium")
        except Exception as e:
            logger.error(f"Error collecting from Medium: {e}", exc_info=True)

        return posts


class YouTubeCollector(BaseCollector):
    """Collector for YouTube videos."""

    API_BASE_URL = "https://www.googleapis.com/youtube/v3/search"

    def __init__(self, keywords: List[str], max_posts: int, api_key: Optional[str]):
        """
        Initialize YouTube collector.

        Args:
            keywords: List of keywords to search for
            max_posts: Maximum number of videos to collect
            api_key: YouTube API key
        """
        super().__init__(keywords, max_posts)
        self.api_key = api_key

    def collect(self) -> List[Dict]:
        """
        Collect videos from YouTube.

        Returns:
            List of normalized post dictionaries
        """
        posts: List[Dict] = []

        if not self.api_key:
            logger.info("YouTube API key not configured, skipping")
            return posts

        try:
            params = {
                "part": "snippet",
                "q": "PyCon 2025",
                "type": "video",
                "maxResults": min(5, self.max_posts),
                "key": self.api_key
            }
            response = requests.get(self.API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            videos = response.json().get("items", [])
            for video in videos:
                snippet = video["snippet"]
                post = self._normalize_post(
                    source="youtube",
                    url=f"https://www.youtube.com/watch?v={video['id']['videoId']}",
                    title=snippet["title"],
                    content=snippet["description"],
                    author_name=snippet["channelTitle"],
                    author_url=f"https://www.youtube.com/channel/{snippet['channelId']}",
                    published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
                    tags=[],
                    metadata={}
                )
                posts.append(post)

            logger.info(f"Collected {len(posts)} videos from YouTube")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error collecting from YouTube: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error in YouTube collector: {e}", exc_info=True)

        return posts


class GitHubCollector(BaseCollector):
    """Collector for GitHub repositories."""

    API_BASE_URL = "https://api.github.com/search/repositories"

    def __init__(self, keywords: List[str], max_posts: int, token: Optional[str]):
        """
        Initialize GitHub collector.

        Args:
            keywords: List of keywords to search for
            max_posts: Maximum number of repositories to collect
            token: GitHub personal access token (optional)
        """
        super().__init__(keywords, max_posts)
        self.token = token

    def collect(self) -> List[Dict]:
        """
        Collect repositories from GitHub.

        Returns:
            List of normalized post dictionaries
        """
        posts: List[Dict] = []
        try:
            params = {
                "q": "pycon 2025",
                "sort": "updated",
                "per_page": min(5, self.max_posts)
            }
            headers = {}
            if self.token:
                headers["Authorization"] = f"token {self.token}"

            response = requests.get(self.API_BASE_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            repos = response.json().get("items", [])
            for repo in repos:
                description = repo.get("description") or "No description"
                post = self._normalize_post(
                    source="github",
                    url=repo["html_url"],
                    title=repo["name"],
                    content=description,
                    author_name=repo["owner"]["login"],
                    author_url=repo["owner"]["html_url"],
                    published_at=datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00")),
                    tags=repo.get("topics", [])[:5],
                    metadata={
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0)
                    }
                )
                posts.append(post)

            logger.info(f"Collected {len(posts)} repos from GitHub")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error collecting from GitHub: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error in GitHub collector: {e}", exc_info=True)

        return posts
