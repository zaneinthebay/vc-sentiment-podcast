"""CLI interface for VC Sentiment Podcast Generator."""

from enum import Enum
from typing import Optional
import click
import logging

from src.config import Config
from src.scraper import calculate_date_range
from src.aggregator import scrape_all_sources, deduplicate_content, aggregate_posts
from src.script_generator import generate_script, estimate_speaking_duration
from src.tts import text_to_speech, estimate_audio_cost
from src.file_handler import save_audio

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")


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

    try:
        # Step 1: Scrape VC blogs
        click.echo("📡 Step 1/5: Scraping VC blogs...")
        start_date, end_date = calculate_date_range(time_period.value // 7)
        all_posts = scrape_all_sources(start_date, end_date)
        click.echo(f"   ✓ Collected {len(all_posts)} posts from VC sources")

        # Step 2: Deduplicate content
        click.echo("\n🔍 Step 2/5: Deduplicating content...")
        unique_posts = deduplicate_content(all_posts)
        click.echo(f"   ✓ Deduplicated to {len(unique_posts)} unique posts")

        if len(unique_posts) < 3:
            click.echo(
                f"\n❌ Error: Insufficient content ({len(unique_posts)} posts). "
                "Try a longer timeframe or different topic.",
                err=True,
            )
            return

        # Step 3: Generate script
        click.echo("\n✍️  Step 3/5: Generating podcast script...")
        markdown_content = aggregate_posts(unique_posts)
        script = generate_script(markdown_content, topic, time_period.value)
        duration = estimate_speaking_duration(script)
        click.echo(f"   ✓ Script generated ({len(script.split())} words, ~{duration:.1f} min)")

        # Step 4: Convert to audio
        click.echo("\n🎙️  Step 4/5: Converting text to speech...")
        cost = estimate_audio_cost(script)
        click.echo(f"   💰 Estimated cost: ${cost:.2f}")
        audio_data = text_to_speech(script)
        click.echo(f"   ✓ Audio generated ({len(audio_data) / 1024 / 1024:.2f} MB)")

        # Step 5: Save file
        click.echo("\n💾 Step 5/5: Saving podcast file...")
        metadata = {"topic": topic, "timeframe_days": time_period.value}
        filepath = save_audio(audio_data, metadata)

        # Success summary
        click.echo("\n" + "=" * 60)
        click.echo("✅ Podcast generated successfully!")
        click.echo("=" * 60)
        click.echo(f"📁 File: {filepath}")
        click.echo(f"⏱️  Duration: ~{duration:.1f} minutes")
        click.echo(f"📊 Sources: {len(unique_posts)} unique posts")
        click.echo(f"💰 Cost: ${cost:.2f}")
        click.echo("\n🎧 Your podcast is ready to listen!")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        import traceback
        if click.confirm("\n🐛 Show detailed error trace?", default=False):
            click.echo("\n" + traceback.format_exc(), err=True)


if __name__ == "__main__":
    main()
