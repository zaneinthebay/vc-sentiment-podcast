"""Content aggregation and deduplication for blog posts."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from difflib import SequenceMatcher
from typing import List, Set
import logging

from src.models import BlogPost
from src.scraper import scrape_source, ScraperError
from src.config import get_vc_sources

# Configure logging
logger = logging.getLogger(__name__)


def scrape_all_sources(
    start_date: datetime, end_date: datetime, max_workers: int = 5
) -> List[BlogPost]:
    """Scrape all VC sources concurrently.

    Args:
        start_date: Start of date range
        end_date: End of date range
        max_workers: Maximum number of concurrent scraping threads

    Returns:
        List of all scraped BlogPost objects (may contain duplicates)
    """
    vc_sources = get_vc_sources()
    all_posts = []
    errors = []

    logger.info(f"Scraping {len(vc_sources)} sources concurrently...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scraping tasks
        future_to_source = {
            executor.submit(scrape_source, source, start_date, end_date): source
            for source in vc_sources
        }

        # Collect results as they complete
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                posts = future.result()
                all_posts.extend(posts)
                logger.info(f"✓ {source['name']}: {len(posts)} posts")
            except ScraperError as e:
                errors.append((source["name"], str(e)))
                logger.warning(f"✗ {source['name']}: {e}")
            except Exception as e:
                errors.append((source["name"], str(e)))
                logger.error(f"✗ {source['name']}: Unexpected error - {e}")

    if errors and not all_posts:
        raise ScraperError(
            f"All sources failed to scrape. Errors: {errors}"
        )

    return all_posts


def deduplicate_content(posts: List[BlogPost], similarity_threshold: float = 0.85) -> List[BlogPost]:
    """Remove duplicate posts using fuzzy matching.

    Args:
        posts: List of BlogPost objects
        similarity_threshold: Similarity ratio threshold (0.0 to 1.0)

    Returns:
        Deduplicated list of BlogPost objects
    """
    if not posts:
        return []

    # Use a set to track unique posts, plus fuzzy matching for content
    unique_posts = []
    seen_urls: Set[str] = set()

    for post in posts:
        # Skip if we've seen this exact URL
        if post.url and post.url in seen_urls:
            continue

        # Check for content similarity with existing posts
        is_duplicate = False
        for existing_post in unique_posts:
            if _is_similar_content(post, existing_post, similarity_threshold):
                is_duplicate = True
                break

        if not is_duplicate:
            unique_posts.append(post)
            if post.url:
                seen_urls.add(post.url)

    logger.info(f"Deduplicated {len(posts)} posts to {len(unique_posts)} unique posts")
    return unique_posts


def _is_similar_content(post1: BlogPost, post2: BlogPost, threshold: float) -> bool:
    """Check if two posts have similar content using fuzzy matching.

    Args:
        post1: First BlogPost
        post2: Second BlogPost
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        True if posts are similar enough to be considered duplicates
    """
    # Check title similarity
    title_similarity = SequenceMatcher(None, post1.title, post2.title).ratio()
    if title_similarity > threshold:
        return True

    # Check content similarity (only if both have content)
    if post1.content and post2.content:
        # Use first 500 chars for performance
        content1 = post1.content[:500]
        content2 = post2.content[:500]
        content_similarity = SequenceMatcher(None, content1, content2).ratio()
        if content_similarity > threshold:
            return True

    return False


def aggregate_posts(posts: List[BlogPost]) -> str:
    """Aggregate posts into a markdown-formatted document.

    Args:
        posts: List of BlogPost objects

    Returns:
        Markdown-formatted string with all post content
    """
    if not posts:
        return ""

    # Sort posts by date (newest first)
    sorted_posts = sorted(posts, key=lambda p: p.date, reverse=True)

    # Build markdown document
    lines = []
    lines.append("# VC Blog Posts Collection\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**Total Posts:** {len(sorted_posts)}\n")
    lines.append(f"**Date Range:** {sorted_posts[-1].date.strftime('%Y-%m-%d')} to {sorted_posts[0].date.strftime('%Y-%m-%d')}\n")
    lines.append("\n---\n")

    # Group by source for better organization
    by_source = {}
    for post in sorted_posts:
        if post.source not in by_source:
            by_source[post.source] = []
        by_source[post.source].append(post)

    # Add posts grouped by source
    for source_name, source_posts in by_source.items():
        lines.append(f"\n## {source_name} ({len(source_posts)} posts)\n")

        for post in source_posts:
            lines.append(f"\n### {post.title}")
            lines.append(f"**Date:** {post.date.strftime('%Y-%m-%d')}")
            if post.url:
                lines.append(f"**URL:** {post.url}")
            lines.append(f"\n{post.content}\n")
            lines.append("---\n")

    return "\n".join(lines)


def format_as_markdown(posts: List[BlogPost]) -> str:
    """Format posts as markdown (alias for aggregate_posts).

    Args:
        posts: List of BlogPost objects

    Returns:
        Markdown-formatted string
    """
    return aggregate_posts(posts)
