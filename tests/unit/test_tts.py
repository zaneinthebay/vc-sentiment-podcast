"""Unit tests for TTS module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.tts import (
    text_to_speech,
    validate_audio,
    estimate_audio_cost,
    TTSError,
)


@pytest.fixture
def valid_mp3_data():
    """Create valid MP3-like binary data."""
    # Simple MP3 header (ID3v2)
    return b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 2000


@pytest.fixture
def valid_mpeg_data():
    """Create valid MPEG frame sync data."""
    # MPEG frame sync bytes
    return b"\xFF\xFB" + b"\x00" * 2000


@pytest.mark.unit
class TestValidateAudio:
    """Tests for audio validation."""

    def test_validate_empty_audio(self):
        """Test that empty audio fails validation."""
        assert validate_audio(b"") is False
        assert validate_audio(None) is False

    def test_validate_too_small_audio(self):
        """Test that audio smaller than 1KB fails."""
        small_audio = b"ID3" + b"\x00" * 500  # 503 bytes
        assert validate_audio(small_audio) is False

    def test_validate_invalid_header(self):
        """Test that audio with invalid header fails."""
        invalid_audio = b"INVALID" + b"\x00" * 2000
        assert validate_audio(invalid_audio) is False

    def test_validate_valid_id3_audio(self, valid_mp3_data):
        """Test that valid ID3 MP3 data passes."""
        assert validate_audio(valid_mp3_data) is True

    def test_validate_valid_mpeg_audio(self, valid_mpeg_data):
        """Test that valid MPEG frame sync data passes."""
        assert validate_audio(valid_mpeg_data) is True


@pytest.mark.unit
class TestEstimateAudioCost:
    """Tests for cost estimation."""

    def test_estimate_cost_1000_chars(self):
        """Test cost estimate for 1000 characters."""
        script = "a" * 1000
        cost = estimate_audio_cost(script)
        assert cost == pytest.approx(0.30, rel=0.01)

    def test_estimate_cost_2000_chars(self):
        """Test cost estimate for 2000 characters."""
        script = "a" * 2000
        cost = estimate_audio_cost(script)
        assert cost == pytest.approx(0.60, rel=0.01)

    def test_estimate_cost_empty_script(self):
        """Test cost estimate for empty script."""
        cost = estimate_audio_cost("")
        assert cost == 0.0


@pytest.mark.unit
class TestTextToSpeech:
    """Tests for TTS conversion."""

    @patch("src.tts.ElevenLabs")
    def test_text_to_speech_success(self, mock_elevenlabs, valid_mp3_data):
        """Test successful TTS conversion."""
        # Mock ElevenLabs client
        mock_generator = iter([valid_mp3_data[:1000], valid_mp3_data[1000:]])

        mock_tts = Mock()
        mock_tts.convert.return_value = mock_generator

        mock_client = Mock()
        mock_client.text_to_speech = mock_tts
        mock_elevenlabs.return_value = mock_client

        script = "This is a test script for podcast generation."
        audio = text_to_speech(script)

        assert isinstance(audio, bytes)
        assert len(audio) > 1024
        mock_tts.convert.assert_called_once()

    @patch("src.tts.ElevenLabs")
    def test_text_to_speech_empty_script(self, mock_elevenlabs):
        """Test that empty script raises error."""
        with pytest.raises(TTSError):
            text_to_speech("")

        with pytest.raises(TTSError):
            text_to_speech("   ")

    @patch("src.tts.ElevenLabs")
    @patch("src.tts.time.sleep")
    def test_text_to_speech_retry_on_rate_limit(
        self, mock_sleep, mock_elevenlabs, valid_mp3_data
    ):
        """Test retry logic on rate limit errors."""
        # First call raises rate limit error, second succeeds
        mock_generator_fail = MagicMock()
        mock_generator_fail.__iter__.side_effect = Exception("Rate limit exceeded")

        mock_generator_success = iter([valid_mp3_data])

        mock_tts = Mock()
        mock_tts.convert.side_effect = [mock_generator_fail, mock_generator_success]

        mock_client = Mock()
        mock_client.text_to_speech = mock_tts
        mock_elevenlabs.return_value = mock_client

        script = "Test script"
        audio = text_to_speech(script, max_retries=3)

        assert isinstance(audio, bytes)
        assert mock_tts.convert.call_count == 2
        mock_sleep.assert_called()  # Verify backoff was used

    @patch("src.tts.ElevenLabs")
    def test_text_to_speech_failure_after_retries(self, mock_elevenlabs):
        """Test that error is raised after all retries fail."""
        mock_generator = MagicMock()
        mock_generator.__iter__.side_effect = Exception("API Error")

        mock_tts = Mock()
        mock_tts.convert.return_value = mock_generator

        mock_client = Mock()
        mock_client.text_to_speech = mock_tts
        mock_elevenlabs.return_value = mock_client

        script = "Test script"

        with pytest.raises(TTSError):
            text_to_speech(script, max_retries=2)

    @patch("src.tts.ElevenLabs")
    def test_text_to_speech_api_parameters(self, mock_elevenlabs, valid_mp3_data):
        """Test that API is called with correct parameters."""
        mock_generator = iter([valid_mp3_data])

        mock_tts = Mock()
        mock_tts.convert.return_value = mock_generator

        mock_client = Mock()
        mock_client.text_to_speech = mock_tts
        mock_elevenlabs.return_value = mock_client

        script = "Test script"
        text_to_speech(script, voice="Rachel")

        call_kwargs = mock_tts.convert.call_args[1]
        assert call_kwargs["text"] == script
        assert call_kwargs["voice_id"] == "Rachel"
        assert call_kwargs["model_id"] == "eleven_monolingual_v1"
        assert "voice_settings" in call_kwargs

    @patch("src.tts.ElevenLabs")
    def test_text_to_speech_invalid_audio_output(self, mock_elevenlabs):
        """Test handling of invalid audio output from API."""
        # Return audio that fails validation (too small)
        invalid_audio = b"ID3" + b"\x00" * 100
        mock_generator = iter([invalid_audio])

        mock_tts = Mock()
        mock_tts.convert.return_value = mock_generator

        mock_client = Mock()
        mock_client.text_to_speech = mock_tts
        mock_elevenlabs.return_value = mock_client

        with pytest.raises(TTSError):
            text_to_speech("Test script", max_retries=1)
