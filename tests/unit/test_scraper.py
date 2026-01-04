"""Unit tests for scraper module."""

from datetime import datetime, timedelta
from pathlib import Path
import pytest
import requests
from unittest.mock import Mock, patch

from src.scraper import (
    scrape_source,
    parse_blog_html,
    filter_by_date,
    calculate_date_range,
    ScraperError,
    _fetch_url,
)
from src.models import BlogPost


@pytest.fixture
def sample_html():
    """Load sample HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_blog_posts.html"
    return fixture_path.read_text()


@pytest.fixture
def sample_source_config():
    """Sample VC source configuration."""
    return {
        "name": "Test VC",
        "url": "https://example.com/blog/",
        "type": "html",
        "article_selector": "article.post",
        "title_selector": "h2.post-title",
        "date_selector": "time",
        "content_selector": "div.post-content",
    }


@pytest.mark.unit
class TestFetchUrl:
    """Tests for URL fetching."""

    @patch("requests.get")
    def test_fetch_url_success(self, mock_get):
        """Test successful URL fetch."""
        mock_response = Mock()
        mock_response.text = "<html>test</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = _fetch_url("https://example.com")
        assert result == "<html>test</html>"
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_fetch_url_with_proper_headers(self, mock_get):
        """Test that proper User-Agent header is sent."""
        mock_response = Mock()
        mock_response.text = "<html>test</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        _fetch_url("https://example.com")

        # Check that User-Agent was set
        call_kwargs = mock_get.call_args[1]
        assert "User-Agent" in call_kwargs["headers"]

    @patch("requests.get")
    def test_fetch_url_timeout(self, mock_get):
        """Test handling of timeout errors."""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        with pytest.raises(requests.Timeout):
            _fetch_url("https://example.com")


@pytest.mark.unit
class TestParseBlogHtml:
    """Tests for HTML parsing."""

    def test_parse_blog_html_success(self, sample_html, sample_source_config):
        """Test parsing valid HTML returns structured BlogPost objects."""
        posts = parse_blog_html(sample_html, sample_source_config)

        assert len(posts) == 3
        assert all(isinstance(post, BlogPost) for post in posts)

        # Check first post
        assert posts[0].title == "The AI Revolution in 2026"
        assert posts[0].source == "Test VC"
        assert posts[0].date.year == 2026
        assert posts[0].date.month == 1
        assert "Artificial intelligence" in posts[0].content

    def test_parse_blog_html_with_urls(self, sample_html, sample_source_config):
        """Test that URLs are extracted and resolved."""
        posts = parse_blog_html(sample_html, sample_source_config)

        assert posts[0].url == "https://example.com/blog/ai-revolution"
        assert posts[1].url == "https://example.com/blog/future-of-saas"

    def test_parse_blog_html_empty_content(self, sample_source_config):
        """Test parsing empty HTML returns empty list."""
        empty_html = "<html><body></body></html>"
        posts = parse_blog_html(empty_html, sample_source_config)

        assert posts == []

    def test_parse_blog_html_malformed_date_skipped(self, sample_source_config):
        """Test that articles with malformed dates are skipped."""
        html_with_bad_date = """
        <article class="post">
            <h2 class="post-title">Test Post</h2>
            <time>Not a valid date</time>
            <div class="post-content">Content here</div>
        </article>
        """
        posts = parse_blog_html(html_with_bad_date, sample_source_config)

        assert len(posts) == 0  # Should skip post with invalid date


@pytest.mark.unit
class TestFilterByDate:
    """Tests for date filtering."""

    def test_filter_by_date_within_range(self):
        """Test that posts within date range are included."""
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 1, 31)

        posts = [
            BlogPost(
                title="Post 1",
                date=datetime(2026, 1, 15),
                content="Content",
                source="Test",
                url="http://test.com/1",
            ),
            BlogPost(
                title="Post 2",
                date=datetime(2025, 12, 20),
                content="Content",
                source="Test",
                url="http://test.com/2",
            ),
        ]

        filtered = filter_by_date(posts, start_date, end_date)
        assert len(filtered) == 2

    def test_filter_by_date_excludes_outside_range(self):
        """Test that posts outside date range are excluded."""
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2025, 12, 31)

        posts = [
            BlogPost(
                title="Post 1",
                date=datetime(2026, 1, 15),  # Too recent
                content="Content",
                source="Test",
                url="http://test.com/1",
            ),
            BlogPost(
                title="Post 2",
                date=datetime(2025, 11, 20),  # Too old
                content="Content",
                source="Test",
                url="http://test.com/2",
            ),
            BlogPost(
                title="Post 3",
                date=datetime(2025, 12, 15),  # In range
                content="Content",
                source="Test",
                url="http://test.com/3",
            ),
        ]

        filtered = filter_by_date(posts, start_date, end_date)
        assert len(filtered) == 1
        assert filtered[0].title == "Post 3"

    def test_filter_by_date_boundary_conditions(self):
        """Test that boundary dates (start and end) are inclusive."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 1, 31)

        posts = [
            BlogPost(
                title="Start Post",
                date=datetime(2026, 1, 1),
                content="Content",
                source="Test",
                url="http://test.com/1",
            ),
            BlogPost(
                title="End Post",
                date=datetime(2026, 1, 31),
                content="Content",
                source="Test",
                url="http://test.com/2",
            ),
        ]

        filtered = filter_by_date(posts, start_date, end_date)
        assert len(filtered) == 2


@pytest.mark.unit
class TestCalculateDateRange:
    """Tests for date range calculation."""

    def test_calculate_date_range_one_week(self):
        """Test calculating date range for 1 week."""
        start, end = calculate_date_range(1)

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert (end - start).days == 7

    def test_calculate_date_range_two_weeks(self):
        """Test calculating date range for 2 weeks."""
        start, end = calculate_date_range(2)

        assert (end - start).days == 14

    def test_calculate_date_range_three_weeks(self):
        """Test calculating date range for 3 weeks."""
        start, end = calculate_date_range(3)

        assert (end - start).days == 21


@pytest.mark.unit
class TestScrapeSource:
    """Tests for complete source scraping with retries."""

    @patch("src.scraper._fetch_url")
    def test_scrape_source_success(self, mock_fetch, sample_html, sample_source_config):
        """Test successful scraping of a source."""
        mock_fetch.return_value = sample_html

        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 1, 31)

        posts = scrape_source(sample_source_config, start_date, end_date)

        assert len(posts) == 2  # Should filter out the 2024 post
        assert all(isinstance(post, BlogPost) for post in posts)

    @patch("src.scraper._fetch_url")
    def test_scrape_source_retry_on_failure(self, mock_fetch, sample_source_config):
        """Test retry logic on network failures."""
        # Fail twice, then succeed
        mock_fetch.side_effect = [
            requests.Timeout("Timeout"),
            requests.ConnectionError("Connection failed"),
            "<html><body></body></html>",
        ]

        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 1, 31)

        posts = scrape_source(sample_source_config, start_date, end_date, max_retries=3)

        assert isinstance(posts, list)
        assert mock_fetch.call_count == 3

    @patch("src.scraper._fetch_url")
    def test_scrape_source_failure_after_retries(self, mock_fetch, sample_source_config):
        """Test that ScraperError is raised after all retries fail."""
        mock_fetch.side_effect = requests.Timeout("Timeout")

        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 1, 31)

        with pytest.raises(ScraperError):
            scrape_source(sample_source_config, start_date, end_date, max_retries=2)
