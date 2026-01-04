"""Web scraper for VC blog posts."""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from src.config import Config
from src.models import BlogPost


class ScraperError(Exception):
    """Base exception for scraper errors."""

    pass


def scrape_source(
    source_config: Dict[str, str],
    start_date: datetime,
    end_date: datetime,
    max_retries: int = None,
) -> List[BlogPost]:
    """Scrape blog posts from a single VC source.

    Args:
        source_config: Source configuration dict with URL and selectors
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        max_retries: Maximum retry attempts (defaults to Config.MAX_RETRIES)

    Returns:
        List of BlogPost objects within the date range

    Raises:
        ScraperError: If scraping fails after all retries
    """
    max_retries = max_retries or Config.MAX_RETRIES
    last_error = None

    for attempt in range(max_retries):
        try:
            html = _fetch_url(source_config["url"])
            posts = parse_blog_html(html, source_config)
            filtered_posts = filter_by_date(posts, start_date, end_date)
            return filtered_posts
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(Config.RETRY_DELAY * (attempt + 1))  # Exponential backoff
                continue
            else:
                raise ScraperError(
                    f"Failed to scrape {source_config['name']} after {max_retries} attempts: {e}"
                ) from e

    return []  # Should not reach here, but for type safety


def _fetch_url(url: str, timeout: int = None) -> str:
    """Fetch HTML content from URL with proper headers.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content as string

    Raises:
        requests.RequestException: If request fails
    """
    timeout = timeout or Config.REQUEST_TIMEOUT
    headers = {"User-Agent": Config.USER_AGENT}

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse_blog_html(html: str, source_config: Dict[str, str]) -> List[BlogPost]:
    """Parse HTML into BlogPost objects using source-specific selectors.

    Args:
        html: HTML content to parse
        source_config: Configuration with CSS selectors

    Returns:
        List of BlogPost objects (may be empty if no posts found)
    """
    soup = BeautifulSoup(html, "html.parser")
    posts = []

    # Find all article elements
    articles = soup.select(source_config["article_selector"])

    for article in articles:
        try:
            # Extract title
            title_elem = article.select_one(source_config["title_selector"])
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)

            # Extract date
            date_elem = article.select_one(source_config["date_selector"])
            if not date_elem:
                continue

            # Try to parse date from datetime attribute or text
            date_str = date_elem.get("datetime") or date_elem.get_text(strip=True)
            try:
                post_date = date_parser.parse(date_str)
            except (ValueError, TypeError):
                continue  # Skip posts with unparseable dates

            # Extract content
            content_elem = article.select_one(source_config["content_selector"])
            content = content_elem.get_text(strip=True) if content_elem else ""

            # Extract URL (try common patterns)
            url = ""
            link_elem = article.find("a", href=True)
            if link_elem:
                url = urljoin(source_config["url"], link_elem["href"])

            # Create BlogPost
            post = BlogPost(
                title=title,
                date=post_date,
                content=content,
                source=source_config["name"],
                url=url,
            )
            posts.append(post)

        except Exception as e:
            # Log and continue with other articles
            continue

    return posts


def filter_by_date(
    posts: List[BlogPost], start_date: datetime, end_date: datetime
) -> List[BlogPost]:
    """Filter posts to only include those within date range.

    Args:
        posts: List of BlogPost objects
        start_date: Start of range (inclusive)
        end_date: End of range (inclusive)

    Returns:
        Filtered list of BlogPost objects
    """
    filtered = []
    for post in posts:
        # Make dates timezone-naive for comparison if needed
        post_date = (
            post.date.replace(tzinfo=None) if post.date.tzinfo else post.date
        )
        start = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
        end = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date

        if start <= post_date <= end:
            filtered.append(post)

    return filtered


def calculate_date_range(weeks_back: int) -> tuple[datetime, datetime]:
    """Calculate start and end dates for scraping.

    Args:
        weeks_back: Number of weeks to look back (1, 2, or 3)

    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks_back)
    return start_date, end_date
