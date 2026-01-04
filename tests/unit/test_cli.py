"""Unit tests for CLI module."""

import pytest
from click.testing import CliRunner
from src.cli import main, prompt_time_period, prompt_topic, TimePeriod, display_progress


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.mark.unit
class TestTimePeriodPrompt:
    """Tests for time period selection."""

    def test_one_week_selection(self, runner, monkeypatch):
        """Test selecting 1 week option."""
        monkeypatch.setattr('click.prompt', lambda *args, **kwargs: 1)
        period = prompt_time_period()
        assert period == TimePeriod.ONE_WEEK
        assert period.value == 7

    def test_two_weeks_selection(self, runner, monkeypatch):
        """Test selecting 2 weeks option."""
        monkeypatch.setattr('click.prompt', lambda *args, **kwargs: 2)
        period = prompt_time_period()
        assert period == TimePeriod.TWO_WEEKS
        assert period.value == 14

    def test_three_weeks_selection(self, runner, monkeypatch):
        """Test selecting 3 weeks option."""
        monkeypatch.setattr('click.prompt', lambda *args, **kwargs: 3)
        period = prompt_time_period()
        assert period == TimePeriod.THREE_WEEKS
        assert period.value == 21


@pytest.mark.unit
class TestTopicPrompt:
    """Tests for topic input."""

    def test_default_topic(self, runner, monkeypatch):
        """Test that default topic is 'artificial intelligence'."""
        # Simulate pressing Enter for default
        monkeypatch.setattr('click.prompt', lambda *args, **kwargs: kwargs.get('default'))
        topic = prompt_topic()
        assert topic == "artificial intelligence"

    def test_custom_topic(self, runner, monkeypatch):
        """Test entering a custom topic."""
        monkeypatch.setattr('click.prompt', lambda *args, **kwargs: "machine learning")
        topic = prompt_topic()
        assert topic == "machine learning"

    def test_empty_topic_uses_default(self, runner, monkeypatch):
        """Test that empty topic falls back to default."""
        monkeypatch.setattr('click.prompt', lambda *args, **kwargs: "")
        topic = prompt_topic()
        assert topic == "artificial intelligence"

    def test_whitespace_only_topic_uses_default(self, runner, monkeypatch):
        """Test that whitespace-only topic falls back to default."""
        monkeypatch.setattr('click.prompt', lambda *args, **kwargs: "   ")
        topic = prompt_topic()
        assert topic == "artificial intelligence"

    def test_topic_trimmed(self, runner, monkeypatch):
        """Test that topic whitespace is trimmed."""
        monkeypatch.setattr('click.prompt', lambda *args, **kwargs: "  blockchain  ")
        topic = prompt_topic()
        assert topic == "blockchain"


@pytest.mark.unit
class TestDisplayProgress:
    """Tests for progress display."""

    def test_progress_at_start(self, capsys):
        """Test progress display at 0%."""
        display_progress("Starting", 0, 5)
        captured = capsys.readouterr()
        assert "0%" in captured.out
        assert "Starting" in captured.out

    def test_progress_at_middle(self, capsys):
        """Test progress display at 50%."""
        display_progress("Processing", 3, 6)
        captured = capsys.readouterr()
        assert "50%" in captured.out
        assert "Processing" in captured.out

    def test_progress_at_completion(self, capsys):
        """Test progress display at 100%."""
        display_progress("Complete", 5, 5)
        captured = capsys.readouterr()
        assert "100%" in captured.out
        assert "Complete" in captured.out


@pytest.mark.unit
class TestMainCLI:
    """Tests for main CLI function."""

    def test_cli_without_api_keys(self, runner, monkeypatch):
        """Test CLI fails gracefully without API keys."""
        # Clear API keys
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        monkeypatch.setenv("ELEVENLABS_API_KEY", "")

        result = runner.invoke(main)
        assert result.exit_code == 0  # Graceful exit, not crash
        assert "Configuration Error" in result.output

    def test_cli_with_api_keys_and_confirmation(self, runner, monkeypatch):
        """Test CLI runs with valid API keys and user confirmation."""
        # Set mock API keys
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test-elevenlabs-key")

        # Provide inputs: time period (1), topic (default), confirm (yes)
        result = runner.invoke(main, input="1\n\ny\n")
        assert result.exit_code == 0
        assert "VC Sentiment Podcast Generator" in result.output
        assert "Success" in result.output or "podcast" in result.output.lower()

    def test_cli_user_cancels(self, runner, monkeypatch):
        """Test CLI handles user cancellation."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test-elevenlabs-key")

        # Provide inputs: time period (1), topic (default), confirm (no)
        result = runner.invoke(main, input="1\n\nn\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output
