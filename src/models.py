"""Data models for VC Sentiment Podcast Generator."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BlogPost:
    """Represents a blog post from a VC source."""

    title: str
    date: datetime
    content: str
    source: str
    url: str
    excerpt: Optional[str] = None

    def __hash__(self):
        """Make BlogPost hashable for deduplication."""
        return hash((self.title, self.source, self.url))

    def __eq__(self, other):
        """Check equality for deduplication."""
        if not isinstance(other, BlogPost):
            return False
        return (
            self.title == other.title
            and self.source == other.source
            and self.url == other.url
        )
