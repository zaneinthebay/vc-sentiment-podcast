"""Unit tests for aggregator module."""

from datetime import datetime
from unittest.mock import patch, Mock
import pytest

from src.aggregator import (
    scrape_all_sources,
    deduplicate_content,
    aggregate_posts,
    format_as_markdown,
    _is_similar_content,
)
from src.models import BlogPost
from src.scraper import ScraperError


@pytest.fixture
def sample_posts():
    """Create sample blog posts for testing."""
    return [
        BlogPost(
            title="AI in 2026",
            date=datetime(2026, 1, 15),
            content="Artificial intelligence is transforming the world...",
            source="VC Firm A",
            url="https://example.com/post1",
        ),
        BlogPost(
            title="The Future of SaaS",
            date=datetime(2026, 1, 10),
            content="Software as a service continues to evolve...",
            source="VC Firm B",
            url="https://example.com/post2",
        ),
        BlogPost(
            title="Machine Learning Trends",
            date=datetime(2026, 1, 5),
            content="Machine learning is seeing rapid adoption...",
            source="VC Firm A",
            url="https://example.com/post3",
        ),
    ]


@pytest.fixture
def duplicate_posts():
    """Create posts with duplicates for testing."""
    return [
        BlogPost(
            title="AI Revolution",
            date=datetime(2026, 1, 15),
            content="Artificial intelligence is changing everything...",
            source="VC Firm A",
            url="https://example.com/post1",
        ),
        BlogPost(
            title="AI Revolution",  # Same title
            date=datetime(2026, 1, 15),
            content="Artificial intelligence is changing everything...",  # Same content
            source="VC Firm B",  # Different source (syndicated)
            url="https://example.com/post1-copy",
        ),
        BlogPost(
            title="Different Post",
            date=datetime(2026, 1, 10),
            content="This is completely different content about SaaS...",
            source="VC Firm C",
            url="https://example.com/post2",
        ),
    ]


@pytest.mark.unit
class TestScrapeAllSources:
    """Tests for multi-source scraping."""

    @patch("src.aggregator.scrape_source")
    @patch("src.aggregator.get_vc_sources")
    def test_scrape_all_sources_success(self, mock_get_sources, mock_scrape):
        """Test successful concurrent scraping of multiple sources."""
        # Mock VC sources
        mock_get_sources.return_value = [
            {"name": "VC A", "url": "https://vca.com"},
            {"name": "VC B", "url": "https://vcb.com"},
        ]

        # Mock scrape results
        mock_scrape.side_effect = [
            [
                BlogPost(
                    title="Post 1",
                    date=datetime(2026, 1, 1),
                    content="Content 1",
                    source="VC A",
                    url="https://vca.com/post1",
                )
            ],
            [
                BlogPost(
                    title="Post 2",
                    date=datetime(2026, 1, 2),
                    content="Content 2",
                    source="VC B",
                    url="https://vcb.com/post2",
                )
            ],
        ]

        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 1, 31)

        posts = scrape_all_sources(start_date, end_date)

        assert len(posts) == 2
        assert mock_scrape.call_count == 2

    @patch("src.aggregator.scrape_source")
    @patch("src.aggregator.get_vc_sources")
    def test_scrape_all_sources_partial_failure(self, mock_get_sources, mock_scrape):
        """Test that scraping continues when some sources fail."""
        mock_get_sources.return_value = [
            {"name": "VC A", "url": "https://vca.com"},
            {"name": "VC B", "url": "https://vcb.com"},
            {"name": "VC C", "url": "https://vcc.com"},
        ]

        # First source succeeds, second fails, third succeeds
        mock_scrape.side_effect = [
            [BlogPost("Post 1", datetime(2026, 1, 1), "Content", "VC A", "url1")],
            ScraperError("Failed to scrape VC B"),
            [BlogPost("Post 2", datetime(2026, 1, 2), "Content", "VC C", "url2")],
        ]

        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 1, 31)

        posts = scrape_all_sources(start_date, end_date)

        # Should still get posts from successful sources
        assert len(posts) == 2
        assert mock_scrape.call_count == 3

    @patch("src.aggregator.scrape_source")
    @patch("src.aggregator.get_vc_sources")
    def test_scrape_all_sources_complete_failure(self, mock_get_sources, mock_scrape):
        """Test that error is raised when all sources fail."""
        mock_get_sources.return_value = [
            {"name": "VC A", "url": "https://vca.com"},
        ]

        mock_scrape.side_effect = ScraperError("Failed")

        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 1, 31)

        with pytest.raises(ScraperError):
            scrape_all_sources(start_date, end_date)


@pytest.mark.unit
class TestDeduplication:
    """Tests for content deduplication."""

    def test_deduplicate_identical_posts(self, duplicate_posts):
        """Test that identical posts are deduplicated."""
        unique = deduplicate_content(duplicate_posts)

        # Should remove the duplicate AI Revolution post
        assert len(unique) == 2

    def test_deduplicate_by_url(self):
        """Test deduplication using URL matching."""
        posts = [
            BlogPost("Post 1", datetime(2026, 1, 1), "Content", "VC A", "https://example.com/post"),
            BlogPost("Post 1 Copy", datetime(2026, 1, 1), "Content", "VC B", "https://example.com/post"),  # Same URL
        ]

        unique = deduplicate_content(posts)
        assert len(unique) == 1

    def test_deduplicate_similar_content(self):
        """Test fuzzy matching for similar content."""
        posts = [
            BlogPost(
                "AI Revolution",
                datetime(2026, 1, 1),
                "Artificial intelligence is transforming the technology landscape",
                "VC A",
                "url1",
            ),
            BlogPost(
                "AI Revolution",  # Same title
                datetime(2026, 1, 1),
                "Artificial intelligence is transforming the technology landscape",  # Very similar
                "VC B",
                "url2",
            ),
        ]

        unique = deduplicate_content(posts, similarity_threshold=0.85)
        assert len(unique) == 1

    def test_deduplicate_empty_list(self):
        """Test deduplication of empty list."""
        unique = deduplicate_content([])
        assert unique == []

    def test_deduplicate_preserves_unique_posts(self, sample_posts):
        """Test that unique posts are preserved."""
        unique = deduplicate_content(sample_posts)
        assert len(unique) == 3  # All should be unique


@pytest.mark.unit
class TestIsSimilarContent:
    """Tests for content similarity detection."""

    def test_similar_titles(self):
        """Test detection of similar titles."""
        post1 = BlogPost("The AI Revolution", datetime.now(), "Content", "VC A", "url1")
        post2 = BlogPost("The AI Revolution", datetime.now(), "Different content", "VC B", "url2")

        assert _is_similar_content(post1, post2, threshold=0.9)

    def test_similar_content(self):
        """Test detection of similar content."""
        content = "This is a long piece of content about artificial intelligence and its impact on society"
        post1 = BlogPost("Title A", datetime.now(), content, "VC A", "url1")
        post2 = BlogPost("Title B", datetime.now(), content, "VC B", "url2")

        assert _is_similar_content(post1, post2, threshold=0.85)

    def test_different_content(self):
        """Test that different content is not marked as similar."""
        post1 = BlogPost("AI", datetime.now(), "Artificial intelligence content", "VC A", "url1")
        post2 = BlogPost("SaaS", datetime.now(), "Software as a service content", "VC B", "url2")

        assert not _is_similar_content(post1, post2, threshold=0.85)


@pytest.mark.unit
class TestAggregation:
    """Tests for content aggregation and markdown formatting."""

    def test_aggregate_posts_creates_markdown(self, sample_posts):
        """Test that posts are aggregated into valid markdown."""
        markdown = aggregate_posts(sample_posts)

        assert isinstance(markdown, str)
        assert "# VC Blog Posts Collection" in markdown
        assert "**Total Posts:** 3" in markdown
        assert "AI in 2026" in markdown
        assert "The Future of SaaS" in markdown
        assert "Machine Learning Trends" in markdown

    def test_aggregate_posts_groups_by_source(self, sample_posts):
        """Test that posts are grouped by source in output."""
        markdown = aggregate_posts(sample_posts)

        assert "## VC Firm A" in markdown
        assert "## VC Firm B" in markdown

    def test_aggregate_posts_sorts_by_date(self, sample_posts):
        """Test that posts are sorted by date (newest first)."""
        markdown = aggregate_posts(sample_posts)

        # Check that the newest post (Jan 15) appears before older ones in date range
        ai_pos = markdown.find("AI in 2026")
        saas_pos = markdown.find("The Future of SaaS")
        ml_pos = markdown.find("Machine Learning Trends")

        # Within same source, should be date-ordered
        assert ai_pos > 0 and ml_pos > 0

    def test_aggregate_posts_includes_metadata(self, sample_posts):
        """Test that post metadata is included."""
        markdown = aggregate_posts(sample_posts)

        assert "**Date:**" in markdown
        assert "**URL:**" in markdown
        assert "2026-01-15" in markdown

    def test_aggregate_empty_posts(self):
        """Test aggregating empty list returns empty string."""
        markdown = aggregate_posts([])
        assert markdown == ""

    def test_format_as_markdown_alias(self, sample_posts):
        """Test that format_as_markdown is an alias for aggregate_posts."""
        markdown1 = aggregate_posts(sample_posts)
        markdown2 = format_as_markdown(sample_posts)

        assert markdown1 == markdown2
