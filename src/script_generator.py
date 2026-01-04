"""Script generation using Claude AI."""

import logging
from typing import Optional

from anthropic import Anthropic

from src.config import Config

logger = logging.getLogger(__name__)


class ScriptGenerationError(Exception):
    """Exception raised when script generation fails."""

    pass


def generate_script(
    content: str,
    topic: str,
    timeframe_days: int,
    max_retries: int = 3,
) -> str:
    """Generate podcast script from aggregated content using Claude.

    Args:
        content: Markdown-formatted aggregated blog posts
        topic: Topic of interest (e.g., "artificial intelligence")
        timeframe_days: Number of days covered (7, 14, or 21)
        max_retries: Maximum retry attempts for quality issues

    Returns:
        Generated podcast script as string

    Raises:
        ScriptGenerationError: If generation fails or quality is insufficient
    """
    client = Anthropic(api_key=Config.get_anthropic_api_key())

    for attempt in range(max_retries):
        try:
            prompt = build_prompt(content, topic, timeframe_days)
            logger.info(f"Generating script (attempt {attempt + 1}/{max_retries})...")

            response = client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=4096,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            script = response.content[0].text

            # Validate script quality
            if validate_script(script):
                logger.info(f"✓ Script generated successfully ({len(script.split())} words)")
                return script
            else:
                logger.warning(f"Script quality check failed (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    continue
                else:
                    raise ScriptGenerationError(
                        "Script quality insufficient after all retries"
                    )

        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Script generation error: {e}. Retrying...")
                continue
            else:
                raise ScriptGenerationError(
                    f"Failed to generate script after {max_retries} attempts: {e}"
                ) from e

    raise ScriptGenerationError("Script generation failed unexpectedly")


def build_prompt(content: str, topic: str, timeframe_days: int) -> str:
    """Build the prompt for Claude to generate podcast script.

    Args:
        content: Aggregated blog post content
        topic: Topic of interest
        timeframe_days: Number of days of content

    Returns:
        Formatted prompt string
    """
    timeframe_text = f"{timeframe_days} days" if timeframe_days < 28 else f"{timeframe_days // 7} weeks"

    prompt = f"""You are a professional podcast narrator creating an audio essay about {topic} in venture capital.

SOURCE MATERIAL:
The following is a collection of blog posts from prominent venture capitalists over the past {timeframe_text}:

{content}

REQUIREMENTS:
1. Synthesize the key themes, trends, and sentiment about {topic} across all sources
2. Use a conversational, lecture-style narrative voice (NOT bullet points or lists)
3. Attribute specific ideas to their sources naturally (e.g., "As Fred Wilson noted...")
4. Target {Config.SCRIPT_TARGET_WORDS} words (approximately 12-15 minutes when spoken)
5. Structure:
   - Intro (30 seconds): Set the context and topic
   - Main themes (10-12 minutes): Discuss 3-5 key themes with evidence from sources
   - Conclusion (90 seconds): Synthesize insights and forward-looking perspective
6. Avoid:
   - Bullet points or numbered lists
   - Meta-commentary about the podcast itself (don't say "in this podcast" or "welcome listeners")
   - Overly promotional language
   - Repetitive phrasing

OUTPUT:
Write a complete podcast script ready for text-to-speech conversion. The script should flow naturally as spoken word.
Start directly with the content - no title, headers, or formatting markers.
"""

    return prompt


def validate_script(script: str) -> bool:
    """Validate that generated script meets quality standards.

    Args:
        script: Generated script text

    Returns:
        True if script passes validation, False otherwise
    """
    if not script or not script.strip():
        logger.warning("Validation failed: Empty script")
        return False

    word_count = len(script.split())

    # Check minimum length
    if word_count < Config.SCRIPT_MIN_WORDS:
        logger.warning(f"Validation failed: Too short ({word_count} words, min {Config.SCRIPT_MIN_WORDS})")
        return False

    # Check that it's not mostly bullet points or lists
    lines = script.split("\n")
    bullet_lines = sum(
        1 for line in lines if line.strip().startswith(("-", "*", "•", "1.", "2.", "3."))
    )
    if bullet_lines > len(lines) * 0.3:  # More than 30% bullet points
        logger.warning("Validation failed: Too many bullet points")
        return False

    # Check for proper narrative structure (should have paragraphs)
    paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
    if len(paragraphs) < 3:
        logger.warning("Validation failed: Insufficient paragraph structure")
        return False

    # Check for natural language patterns (not just a list of facts)
    if script.count(". ") < word_count / 30:  # At least one sentence per ~30 words
        logger.warning("Validation failed: Insufficient sentence structure")
        return False

    return True


def estimate_speaking_duration(script: str) -> float:
    """Estimate speaking duration in minutes.

    Args:
        script: Script text

    Returns:
        Estimated duration in minutes (assumes ~150 words per minute)
    """
    word_count = len(script.split())
    words_per_minute = 150
    return word_count / words_per_minute
