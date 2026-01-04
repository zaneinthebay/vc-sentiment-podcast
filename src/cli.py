"""CLI interface for VC Sentiment Podcast Generator."""

from enum import Enum
from typing import Optional
import click
from src.config import Config


class TimePeriod(Enum):
    """Time period options for blog post collection."""

    ONE_WEEK = 7
    TWO_WEEKS = 14
    THREE_WEEKS = 21


def prompt_time_period() -> TimePeriod:
    """Prompt user to select a time period.

    Returns:
        TimePeriod: Selected time period enum
    """
    click.echo("\n🔍 Select time period to analyze:")
    click.echo("  1) 1 week")
    click.echo("  2) 2 weeks")
    click.echo("  3) 3 weeks")

    choice = click.prompt(
        "Enter your choice",
        type=click.IntRange(1, 3),
        default=1,
        show_default=True,
    )

    period_map = {1: TimePeriod.ONE_WEEK, 2: TimePeriod.TWO_WEEKS, 3: TimePeriod.THREE_WEEKS}
    return period_map[choice]


def prompt_topic() -> str:
    """Prompt user to enter a topic of interest.

    Returns:
        str: Topic string (defaults to "artificial intelligence")
    """
    topic = click.prompt(
        "\n📝 Enter topic of interest",
        type=str,
        default="artificial intelligence",
        show_default=True,
    )

    # Validate non-empty
    if not topic or not topic.strip():
        click.echo("❌ Topic cannot be empty. Using default.", err=True)
        return "artificial intelligence"

    return topic.strip()


def display_progress(step: str, current: int, total: int) -> None:
    """Display progress indicator.

    Args:
        step: Current step description
        current: Current step number
        total: Total number of steps
    """
    percentage = int((current / total) * 100)
    bar_length = 30
    filled = int((percentage / 100) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)

    click.echo(f"\r[{bar}] {percentage}% - {step}", nl=False)
    if current == total:
        click.echo()  # New line at completion


@click.command()
@click.version_option(version="0.1.0")
def main() -> None:
    """VC Sentiment Podcast Generator.

    Generates audio podcasts from venture capitalist blog posts and articles.
    """
    try:
        # Validate configuration
        Config.validate()
    except ValueError as e:
        click.echo(f"❌ Configuration Error: {e}", err=True)
        click.echo("\n💡 Setup instructions:")
        click.echo("   1. Copy .env.example to .env")
        click.echo("   2. Add your API keys to .env")
        click.echo("   3. Get Anthropic API key: https://console.anthropic.com/")
        click.echo("   4. Get ElevenLabs API key: https://elevenlabs.io/")
        return

    # Display welcome message
    click.echo("=" * 60)
    click.echo("🎙️  VC Sentiment Podcast Generator")
    click.echo("=" * 60)

    # Get user inputs
    time_period = prompt_time_period()
    topic = prompt_topic()

    click.echo(f"\n⚙️  Configuration:")
    click.echo(f"   Time period: {time_period.value} days")
    click.echo(f"   Topic: {topic}")
    click.echo(f"   Output: {Config.get_desktop_path()}")

    # Confirm before proceeding
    if not click.confirm("\n▶️  Start generating podcast?", default=True):
        click.echo("❌ Cancelled.")
        return

    click.echo("\n🚀 Starting podcast generation...\n")

    # TODO: Implement actual workflow
    # For now, show mock progress
    steps = [
        "Scraping VC blogs",
        "Aggregating content",
        "Generating script",
        "Creating audio",
        "Saving file",
    ]

    for i, step in enumerate(steps, 1):
        display_progress(step, i, len(steps))
        import time
        time.sleep(0.5)  # Mock delay

    # Mock success message
    click.echo("\n✅ Success! Podcast would be saved to:")
    click.echo(f"   {Config.get_desktop_path()}/vc_podcast_[timestamp].mp3")
    click.echo("\n📝 Note: Full implementation in progress.")


if __name__ == "__main__":
    main()
