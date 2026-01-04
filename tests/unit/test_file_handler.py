"""Unit tests for file handler module."""

from pathlib import Path
import pytest
from unittest.mock import Mock, patch, mock_open

from src.file_handler import (
    save_audio,
    get_desktop_path,
    generate_filename,
    handle_collision,
    FileHandlerError,
)


@pytest.fixture
def sample_audio_data():
    """Sample audio binary data."""
    return b"ID3\x00\x00\x00" + b"\x00" * 2000


@pytest.fixture
def sample_metadata():
    """Sample metadata for file naming."""
    return {
        "topic": "artificial intelligence",
        "timeframe_days": 7,
    }


@pytest.mark.unit
class TestGenerateFilename:
    """Tests for filename generation."""

    def test_generate_filename_basic(self, sample_metadata):
        """Test basic filename generation."""
        filename = generate_filename(sample_metadata)

        assert filename.startswith("vc_podcast_")
        assert filename.endswith(".mp3")
        assert "artificial_intelligence" in filename or "ai" in filename.lower()

    def test_generate_filename_cleans_special_chars(self):
        """Test that special characters are removed from topic."""
        metadata = {"topic": "AI & Machine-Learning!"}
        filename = generate_filename(metadata)

        # Should not contain &, -, or !
        assert "&" not in filename
        assert "!" not in filename
        # Hyphens should be converted to underscores
        assert filename.count("_") >= 1

    def test_generate_filename_limits_length(self):
        """Test that very long topics are truncated."""
        metadata = {"topic": "a" * 100}
        filename = generate_filename(metadata)

        # Filename should not be excessively long
        assert len(filename) < 100

    def test_generate_filename_no_duplicate_underscores(self):
        """Test that duplicate underscores are removed."""
        metadata = {"topic": "AI___Machine___Learning"}
        filename = generate_filename(metadata)

        assert "__" not in filename

    def test_generate_filename_timestamp_format(self):
        """Test that filename includes timestamp in correct format."""
        metadata = {"topic": "AI"}
        filename = generate_filename(metadata)

        # Should contain timestamp in format YYYYMMDD_HHMM
        parts = filename.split("_")
        assert len(parts) >= 4  # vc_podcast_YYYYMMDD_HHMM_topic.mp3


@pytest.mark.unit
class TestHandleCollision:
    """Tests for filename collision handling."""

    def test_handle_collision_no_existing_file(self, tmp_path):
        """Test that path is returned unchanged if file doesn't exist."""
        filepath = tmp_path / "test.mp3"
        result = handle_collision(filepath)

        assert result == filepath

    def test_handle_collision_existing_file(self, tmp_path):
        """Test that counter is appended when file exists."""
        filepath = tmp_path / "test.mp3"
        filepath.touch()  # Create the file

        result = handle_collision(filepath)

        assert result != filepath
        assert result.name == "test_2.mp3"
        assert result.parent == filepath.parent

    def test_handle_collision_multiple_existing_files(self, tmp_path):
        """Test handling multiple collisions."""
        filepath = tmp_path / "test.mp3"
        filepath.touch()
        (tmp_path / "test_2.mp3").touch()
        (tmp_path / "test_3.mp3").touch()

        result = handle_collision(filepath)

        assert result.name == "test_4.mp3"


@pytest.mark.unit
class TestGetDesktopPath:
    """Tests for desktop path retrieval."""

    @patch("src.file_handler.Config.get_desktop_path")
    def test_get_desktop_path_valid(self, mock_config, tmp_path):
        """Test getting valid desktop path."""
        mock_config.return_value = str(tmp_path)

        desktop = get_desktop_path()

        assert desktop == tmp_path
        assert desktop.exists()
        assert desktop.is_dir()

    @patch("src.file_handler.Config.get_desktop_path")
    def test_get_desktop_path_not_exists(self, mock_config):
        """Test error when desktop path doesn't exist."""
        mock_config.return_value = "/nonexistent/path"

        with pytest.raises(FileHandlerError):
            get_desktop_path()

    @patch("src.file_handler.Config.get_desktop_path")
    def test_get_desktop_path_not_directory(self, mock_config, tmp_path):
        """Test error when desktop path is not a directory."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        mock_config.return_value = str(file_path)

        with pytest.raises(FileHandlerError):
            get_desktop_path()

    @patch("src.file_handler.Config.get_desktop_path")
    def test_get_desktop_path_not_writable(self, mock_config, tmp_path):
        """Test error when desktop path is not writable."""
        mock_config.return_value = str(tmp_path)

        # Mock the touch method to raise PermissionError
        with patch.object(Path, "touch", side_effect=PermissionError("No write access")):
            with pytest.raises(FileHandlerError):
                get_desktop_path()


@pytest.mark.unit
class TestSaveAudio:
    """Tests for audio file saving."""

    @patch("src.file_handler.get_desktop_path")
    def test_save_audio_success(self, mock_get_desktop, tmp_path, sample_audio_data, sample_metadata):
        """Test successful audio file saving."""
        mock_get_desktop.return_value = tmp_path

        filepath = save_audio(sample_audio_data, sample_metadata)

        assert Path(filepath).exists()
        assert Path(filepath).read_bytes() == sample_audio_data
        assert filepath.endswith(".mp3")

    @patch("src.file_handler.get_desktop_path")
    def test_save_audio_empty_data(self, mock_get_desktop, tmp_path, sample_metadata):
        """Test that saving empty audio raises error."""
        mock_get_desktop.return_value = tmp_path

        with pytest.raises(FileHandlerError):
            save_audio(b"", sample_metadata)

    @patch("src.file_handler.get_desktop_path")
    def test_save_audio_collision_handling(
        self, mock_get_desktop, tmp_path, sample_audio_data, sample_metadata
    ):
        """Test that filename collisions are handled."""
        mock_get_desktop.return_value = tmp_path

        # Save first file
        filepath1 = save_audio(sample_audio_data, sample_metadata)

        # Mock generate_filename to return same filename
        with patch("src.file_handler.generate_filename", return_value=Path(filepath1).name):
            filepath2 = save_audio(sample_audio_data, sample_metadata)

            # Second file should have different name
            assert filepath1 != filepath2
            assert Path(filepath2).exists()
            assert "_2.mp3" in filepath2

    @patch("src.file_handler.get_desktop_path")
    @patch("src.file_handler.Path.write_bytes")
    def test_save_audio_fallback_to_current_dir(
        self, mock_write, mock_get_desktop, sample_audio_data, sample_metadata
    ):
        """Test fallback to current directory when desktop fails."""
        mock_get_desktop.return_value = Path("/tmp/desktop")

        # First write fails (desktop), second succeeds (current dir)
        mock_write.side_effect = [PermissionError("No access"), None]

        with patch("src.file_handler.Path.cwd", return_value=Path("/tmp/fallback")):
            filepath = save_audio(sample_audio_data, sample_metadata)

            # Should have attempted both locations
            assert mock_write.call_count == 2
            assert "/tmp/fallback" in filepath

    @patch("src.file_handler.get_desktop_path")
    @patch("src.file_handler.Path.write_bytes")
    def test_save_audio_both_locations_fail(
        self, mock_write, mock_get_desktop, sample_audio_data, sample_metadata
    ):
        """Test error when both desktop and fallback fail."""
        mock_get_desktop.return_value = Path("/tmp/desktop")
        mock_write.side_effect = PermissionError("No access")

        with pytest.raises(FileHandlerError):
            save_audio(sample_audio_data, sample_metadata)
