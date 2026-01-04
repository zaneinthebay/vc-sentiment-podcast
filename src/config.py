"""Configuration module for VC Sentiment Podcast Generator."""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    @staticmethod
    def get_anthropic_api_key() -> Optional[str]:
        """Get Anthropic API key from environment."""
        return os.getenv("ANTHROPIC_API_KEY")

    @staticmethod
    def get_elevenlabs_api_key() -> Optional[str]:
        """Get ElevenLabs API key from environment."""
        return os.getenv("ELEVENLABS_API_KEY")

    @staticmethod
    def get_desktop_path() -> str:
        """Get desktop path from environment or auto-detect."""
        return os.getenv("DESKTOP_PATH") or str(Path.home() / "Desktop")

    # LLM Configuration
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
    SCRIPT_TARGET_WORDS = 2000  # Approximately 12-15 minutes spoken
    SCRIPT_MIN_WORDS = 100  # Minimum for quality

    # TTS Configuration
    ELEVENLABS_VOICE = "Rachel"  # Professional female voice
    AUDIO_FORMAT = "mp3_44100_128"

    # Scraping Configuration
    REQUEST_TIMEOUT = 10  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    USER_AGENT = "VC-Sentiment-Podcast-Bot/1.0"

    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        if not cls.get_anthropic_api_key():
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it in .env file or environment variables."
            )
        if not cls.get_elevenlabs_api_key():
            raise ValueError(
                "ELEVENLABS_API_KEY not found. "
                "Set it in .env file or environment variables."
            )


# VC Source Configuration
VC_SOURCES: List[Dict[str, str]] = [
    {
        "name": "a16z",
        "url": "https://a16z.com/blog/",
        "type": "html",  # HTML scraping
        "article_selector": "article.post",
        "title_selector": "h2.post-title",
        "date_selector": "time",
        "content_selector": "div.post-content",
    },
    {
        "name": "Sequoia Capital",
        "url": "https://www.sequoiacap.com/articles/",
        "type": "html",
        "article_selector": "article",
        "title_selector": "h3",
        "date_selector": "time",
        "content_selector": "div.article-content",
    },
    {
        "name": "First Round Review",
        "url": "https://review.firstround.com/latest",
        "type": "html",
        "article_selector": "div.article-item",
        "title_selector": "h2",
        "date_selector": "span.date",
        "content_selector": "div.content",
    },
    {
        "name": "AVC (Fred Wilson)",
        "url": "https://avc.com/",
        "type": "html",
        "article_selector": "article",
        "title_selector": "h1.entry-title",
        "date_selector": "time.entry-date",
        "content_selector": "div.entry-content",
    },
    {
        "name": "Tomasz Tunguz",
        "url": "https://tomtunguz.com/",
        "type": "html",
        "article_selector": "article",
        "title_selector": "h1",
        "date_selector": "time",
        "content_selector": "div.post-content",
    },
]


def get_vc_sources() -> List[Dict[str, str]]:
    """Get the list of VC sources to scrape."""
    return VC_SOURCES
