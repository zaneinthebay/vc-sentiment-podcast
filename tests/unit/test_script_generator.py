"""Unit tests for script generator module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.script_generator import (
    generate_script,
    build_prompt,
    validate_script,
    estimate_speaking_duration,
    ScriptGenerationError,
)


@pytest.fixture
def sample_content():
    """Sample aggregated blog post content."""
    return """# VC Blog Posts Collection

## a16z (2 posts)

### The AI Revolution
**Date:** 2026-01-15
**URL:** https://a16z.com/post1

Artificial intelligence is transforming every industry. We're seeing unprecedented growth...

### Future of Enterprise AI
**Date:** 2026-01-10
**URL:** https://a16z.com/post2

Enterprise AI adoption is accelerating faster than we predicted...
"""


@pytest.fixture
def valid_script():
    """Sample valid podcast script."""
    return """Over the past week, venture capitalists have been focused intensely on artificial intelligence and its transformative impact across industries.

Marc Andreessen and the team at a16z highlighted that we're seeing unprecedented growth in AI startups. As they noted in their recent analysis, enterprise adoption is accelerating faster than anyone predicted just six months ago.

Fred Wilson from AVC took a slightly different angle, emphasizing the importance of responsible AI development. He argued that while the technology is powerful, we need frameworks to ensure it benefits society broadly.

Looking at the data from Sequoia Capital's portfolio analysis, three key themes emerge. First, AI infrastructure spending is reaching new heights. Second, application-layer companies are finding product-market fit faster than in previous technology cycles. Third, the talent war for AI engineers has intensified dramatically.

The consensus across these leading investors is clear: artificial intelligence represents the most significant technological shift since mobile computing. However, as Wilson cautioned, the path forward requires both innovation and thoughtful governance.

Looking ahead, these investors are watching several key indicators. Enterprise procurement cycles, open-source model development, and regulatory frameworks will shape the next phase of AI investment. The question isn't whether AI will transform industries, but how quickly and equitably that transformation occurs."""


@pytest.fixture
def invalid_script_too_short():
    """Invalid script that's too short."""
    return "AI is important. VCs are investing."


@pytest.fixture
def invalid_script_bullet_points():
    """Invalid script with too many bullet points."""
    return """
- AI is transforming industries
- VCs are investing heavily
- Enterprise adoption is growing
- Talent war is intensifying
- Infrastructure spending is up
- Application layer is strong
- Regulation is coming
"""


@pytest.mark.unit
class TestBuildPrompt:
    """Tests for prompt construction."""

    def test_build_prompt_includes_content(self, sample_content):
        """Test that prompt includes the source content."""
        prompt = build_prompt(sample_content, "artificial intelligence", 7)

        assert sample_content in prompt
        assert "artificial intelligence" in prompt

    def test_build_prompt_includes_requirements(self):
        """Test that prompt includes generation requirements."""
        prompt = build_prompt("content", "AI", 7)

        assert "podcast narrator" in prompt.lower()
        assert "conversational" in prompt.lower()
        assert "lecture-style" in prompt.lower()
        assert "2000 words" in prompt or "words" in prompt

    def test_build_prompt_timeframe_formatting(self):
        """Test that timeframe is formatted correctly."""
        prompt_7 = build_prompt("content", "AI", 7)
        prompt_14 = build_prompt("content", "AI", 14)
        prompt_21 = build_prompt("content", "AI", 21)

        assert "7 days" in prompt_7
        assert "14 days" in prompt_14
        assert "21 days" in prompt_21

    def test_build_prompt_topic_integration(self):
        """Test that topic is integrated throughout prompt."""
        topic = "machine learning"
        prompt = build_prompt("content", topic, 7)

        # Topic should appear multiple times in the prompt
        assert prompt.lower().count(topic) >= 2


@pytest.mark.unit
class TestValidateScript:
    """Tests for script validation."""

    def test_validate_empty_script(self):
        """Test that empty scripts fail validation."""
        assert validate_script("") is False
        assert validate_script("   ") is False
        assert validate_script(None) is False

    def test_validate_too_short_script(self, invalid_script_too_short):
        """Test that scripts below minimum word count fail."""
        assert validate_script(invalid_script_too_short) is False

    def test_validate_too_many_bullets(self, invalid_script_bullet_points):
        """Test that scripts with too many bullet points fail."""
        assert validate_script(invalid_script_bullet_points) is False

    def test_validate_valid_script(self, valid_script):
        """Test that valid scripts pass validation."""
        assert validate_script(valid_script) is True

    def test_validate_insufficient_paragraphs(self):
        """Test that scripts without paragraph structure fail."""
        # Long script but no paragraph breaks
        single_paragraph = "Word " * 200  # 200 words in one paragraph
        assert validate_script(single_paragraph) is False

    def test_validate_insufficient_sentences(self):
        """Test that scripts without proper sentence structure fail."""
        # Many words but no sentences
        no_sentences = "word " * 200
        assert validate_script(no_sentences) is False


@pytest.mark.unit
class TestEstimateSpeakingDuration:
    """Tests for duration estimation."""

    def test_estimate_duration_150_words(self):
        """Test duration estimate for exactly 150 words (1 minute)."""
        script = " ".join(["word"] * 150)
        duration = estimate_speaking_duration(script)

        assert duration == pytest.approx(1.0, rel=0.1)

    def test_estimate_duration_2000_words(self):
        """Test duration estimate for 2000 words (~13 minutes)."""
        script = " ".join(["word"] * 2000)
        duration = estimate_speaking_duration(script)

        assert duration == pytest.approx(13.33, rel=0.1)

    def test_estimate_duration_empty_script(self):
        """Test duration estimate for empty script."""
        assert estimate_speaking_duration("") == 0.0


@pytest.mark.unit
class TestGenerateScript:
    """Tests for complete script generation."""

    @patch("src.script_generator.Anthropic")
    def test_generate_script_success(self, mock_anthropic, sample_content, valid_script):
        """Test successful script generation."""
        # Mock Claude API response
        mock_response = Mock()
        mock_response.content = [Mock(text=valid_script)]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        script = generate_script(sample_content, "AI", 7)

        assert script == valid_script
        mock_client.messages.create.assert_called_once()

    @patch("src.script_generator.Anthropic")
    def test_generate_script_api_call_parameters(self, mock_anthropic, sample_content, valid_script):
        """Test that API is called with correct parameters."""
        mock_response = Mock()
        mock_response.content = [Mock(text=valid_script)]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        generate_script(sample_content, "AI", 7)

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["max_tokens"] == 4096
        assert "temperature" in call_kwargs
        assert len(call_kwargs["messages"]) == 1

    @patch("src.script_generator.Anthropic")
    def test_generate_script_retry_on_quality_failure(
        self, mock_anthropic, sample_content, valid_script, invalid_script_too_short
    ):
        """Test retry logic when script quality is insufficient."""
        mock_response_bad = Mock()
        mock_response_bad.content = [Mock(text=invalid_script_too_short)]

        mock_response_good = Mock()
        mock_response_good.content = [Mock(text=valid_script)]

        mock_client = Mock()
        # First call returns bad script, second returns good
        mock_client.messages.create.side_effect = [mock_response_bad, mock_response_good]
        mock_anthropic.return_value = mock_client

        script = generate_script(sample_content, "AI", 7, max_retries=3)

        assert script == valid_script
        assert mock_client.messages.create.call_count == 2

    @patch("src.script_generator.Anthropic")
    def test_generate_script_failure_after_retries(
        self, mock_anthropic, sample_content, invalid_script_too_short
    ):
        """Test that error is raised after all retries fail."""
        mock_response = Mock()
        mock_response.content = [Mock(text=invalid_script_too_short)]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        with pytest.raises(ScriptGenerationError):
            generate_script(sample_content, "AI", 7, max_retries=2)

    @patch("src.script_generator.Anthropic")
    def test_generate_script_api_error(self, mock_anthropic, sample_content):
        """Test handling of API errors."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        with pytest.raises(ScriptGenerationError):
            generate_script(sample_content, "AI", 7, max_retries=2)

    @patch("src.script_generator.Anthropic")
    def test_generate_script_empty_response(self, mock_anthropic, sample_content):
        """Test handling of empty API response."""
        mock_response = Mock()
        mock_response.content = [Mock(text="")]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        with pytest.raises(ScriptGenerationError):
            generate_script(sample_content, "AI", 7, max_retries=2)
