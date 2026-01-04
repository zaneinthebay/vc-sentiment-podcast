"""File handling for saving audio files."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from src.config import Config

logger = logging.getLogger(__name__)


class FileHandlerError(Exception):
    """Exception raised when file operations fail."""

    pass


def save_audio(audio_data: bytes, metadata: Dict[str, str]) -> str:
    """Save audio data to desktop with descriptive filename.

    Args:
        audio_data: Audio bytes to save
        metadata: Dict with 'topic', 'timeframe_days', etc.

    Returns:
        Full path to saved file

    Raises:
        FileHandlerError: If file cannot be saved
    """
    if not audio_data:
        raise FileHandlerError("Cannot save empty audio data")

    try:
        desktop_path = get_desktop_path()
        filename = generate_filename(metadata)
        filepath = desktop_path / filename

        # Handle filename collision
        filepath = handle_collision(filepath)

        # Write audio file
        filepath.write_bytes(audio_data)

        logger.info(f"✓ Audio saved to: {filepath}")
        return str(filepath)

    except Exception as e:
        # Try fallback to current directory
        try:
            logger.warning(f"Failed to save to desktop: {e}. Trying current directory...")
            fallback_path = Path.cwd() / filename
            fallback_path = handle_collision(fallback_path)
            fallback_path.write_bytes(audio_data)
            logger.info(f"✓ Audio saved to fallback location: {fallback_path}")
            return str(fallback_path)
        except Exception as fallback_error:
            raise FileHandlerError(
                f"Failed to save audio file: {e}. Fallback also failed: {fallback_error}"
            ) from e


def get_desktop_path() -> Path:
    """Get desktop directory path (cross-platform).

    Returns:
        Path object for desktop directory

    Raises:
        FileHandlerError: If desktop path cannot be determined or is not writable
    """
    desktop_str = Config.get_desktop_path()
    desktop_path = Path(desktop_str)

    # Verify path exists and is writable
    if not desktop_path.exists():
        raise FileHandlerError(f"Desktop path does not exist: {desktop_path}")

    if not desktop_path.is_dir():
        raise FileHandlerError(f"Desktop path is not a directory: {desktop_path}")

    # Test write permissions
    test_file = desktop_path / ".vc_podcast_test"
    try:
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        raise FileHandlerError(
            f"Desktop path is not writable: {desktop_path}. Error: {e}"
        ) from e

    return desktop_path


def generate_filename(metadata: Dict[str, str]) -> str:
    """Generate descriptive filename for podcast audio.

    Args:
        metadata: Dict with 'topic' and optionally 'timeframe_days'

    Returns:
        Filename string (e.g., 'vc_podcast_20260104_1430_ai.mp3')
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # Clean topic for filename (remove special chars, limit length)
    topic = metadata.get("topic", "general")
    clean_topic = "".join(c if c.isalnum() else "_" for c in topic.lower())
    clean_topic = clean_topic[:30]  # Limit length

    # Remove duplicate underscores
    while "__" in clean_topic:
        clean_topic = clean_topic.replace("__", "_")
    clean_topic = clean_topic.strip("_")

    filename = f"vc_podcast_{timestamp}_{clean_topic}.mp3"
    return filename


def handle_collision(filepath: Path) -> Path:
    """Handle filename collisions by appending counter.

    Args:
        filepath: Original file path

    Returns:
        Unique file path (may be modified if collision occurred)
    """
    if not filepath.exists():
        return filepath

    # File exists, append counter
    stem = filepath.stem
    suffix = filepath.suffix
    parent = filepath.parent

    counter = 2
    while True:
        new_filepath = parent / f"{stem}_{counter}{suffix}"
        if not new_filepath.exists():
            logger.info(f"Filename collision detected. Using: {new_filepath.name}")
            return new_filepath
        counter += 1

        # Safety limit to prevent infinite loop
        if counter > 1000:
            raise FileHandlerError("Too many filename collisions")
