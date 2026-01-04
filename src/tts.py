"""Text-to-speech conversion using ElevenLabs."""

import logging
import time
from typing import Optional

from elevenlabs import ElevenLabs, VoiceSettings

from src.config import Config

logger = logging.getLogger(__name__)


class TTSError(Exception):
    """Exception raised when TTS conversion fails."""

    pass


def text_to_speech(
    script: str,
    voice: Optional[str] = None,
    max_retries: int = 3,
) -> bytes:
    """Convert script text to audio using ElevenLabs.

    Args:
        script: Script text to convert
        voice: Voice ID to use (defaults to Config.ELEVENLABS_VOICE)
        max_retries: Maximum retry attempts for rate limits

    Returns:
        Audio data as bytes (MP3 format)

    Raises:
        TTSError: If conversion fails after all retries
    """
    if not script or not script.strip():
        raise TTSError("Cannot convert empty script to audio")

    voice = voice or Config.ELEVENLABS_VOICE
    client = ElevenLabs(api_key=Config.get_elevenlabs_api_key())

    last_error = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Converting script to audio (attempt {attempt + 1}/{max_retries})...")

            # Generate audio using ElevenLabs API
            audio_generator = client.text_to_speech.convert(
                text=script,
                voice_id=voice,
                model_id="eleven_monolingual_v1",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True,
                ),
            )

            # Collect audio chunks
            audio_chunks = []
            for chunk in audio_generator:
                if chunk:
                    audio_chunks.append(chunk)

            audio_data = b"".join(audio_chunks)

            # Validate audio
            if validate_audio(audio_data):
                logger.info(f"✓ Audio generated successfully ({len(audio_data)} bytes)")
                return audio_data
            else:
                raise TTSError("Generated audio failed validation")

        except Exception as e:
            last_error = e
            logger.warning(f"TTS error: {e}")

            # Check if it's a rate limit error
            if "rate" in str(e).lower() or "limit" in str(e).lower():
                if attempt < max_retries - 1:
                    delay = Config.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Rate limited. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue

            # For other errors or last attempt, raise
            if attempt >= max_retries - 1:
                raise TTSError(
                    f"Failed to generate audio after {max_retries} attempts: {last_error}"
                ) from last_error

    raise TTSError("TTS conversion failed unexpectedly")


def validate_audio(audio_data: bytes) -> bool:
    """Validate generated audio data.

    Args:
        audio_data: Audio bytes to validate

    Returns:
        True if audio is valid, False otherwise
    """
    if not audio_data:
        logger.warning("Validation failed: Empty audio data")
        return False

    # Check minimum size (at least 1KB for a valid MP3)
    if len(audio_data) < 1024:
        logger.warning(f"Validation failed: Audio too small ({len(audio_data)} bytes)")
        return False

    # Basic MP3 header check (should start with ID3 tag or MPEG frame sync)
    # MP3 files typically start with 'ID3' or 0xFF 0xFB (MPEG sync)
    if not (audio_data[:3] == b"ID3" or (audio_data[0] == 0xFF and audio_data[1] & 0xE0 == 0xE0)):
        logger.warning("Validation failed: Invalid MP3 header")
        return False

    logger.debug(f"Audio validation passed: {len(audio_data)} bytes")
    return True


def estimate_audio_cost(script: str) -> float:
    """Estimate ElevenLabs API cost for script.

    Args:
        script: Script text

    Returns:
        Estimated cost in USD
    """
    # ElevenLabs pricing: ~$0.30 per 1000 characters on paid tier
    # Free tier: 10,000 characters/month
    char_count = len(script)
    cost_per_1k_chars = 0.30
    return (char_count / 1000) * cost_per_1k_chars
