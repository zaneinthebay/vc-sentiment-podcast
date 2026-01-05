# VC Sentiment Podcast Generator

Automated podcast generator that analyzes venture capitalist blog posts and creates professional audio content about VC sentiment and trends.

## Features

- 📡 **Multi-Source Scraping**: Collects content from top VC firms (a16z, Sequoia, First Round, AVC, Tomasz Tunguz)
- 🤖 **AI Script Generation**: Uses Claude AI to synthesize insights into lecture-style narratives
- 🎙️ **Professional Audio**: ElevenLabs TTS creates broadcast-quality voice narration
- 🔍 **Smart Deduplication**: Removes duplicate content using fuzzy matching
- ⚡ **Fast & Reliable**: Concurrent scraping with automatic retry logic
- 💾 **Easy Output**: Saves MP3 files directly to your desktop

## Installation

### Prerequisites

- Python 3.11 or higher
- API Keys:
  - [Anthropic Claude API](https://console.anthropic.com/) - For script generation
  - [ElevenLabs API](https://elevenlabs.io/) - For text-to-speech

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/zaneinthebay/vc-sentiment-podcast.git
   cd vc-sentiment-podcast
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys:
   # ANTHROPIC_API_KEY=sk-ant-xxx
   # ELEVENLABS_API_KEY=xxx
   ```

## Usage

### Basic Usage

Run the CLI and follow the prompts:

```bash
python -m src.cli
```

### Example Session

```
============================================================
🎙️  VC Sentiment Podcast Generator
============================================================

🔍 Select time period to analyze:
  1) 1 week
  2) 2 weeks
  3) 3 weeks
Enter your choice [1]: 1

📝 Enter topic of interest [artificial intelligence]: machine learning

⚙️  Configuration:
   Time period: 7 days
   Topic: machine learning
   Output: /Users/you/Desktop

▶️  Start generating podcast? [Y/n]: y

🚀 Starting podcast generation...

📡 Step 1/5: Scraping VC blogs...
   ✓ Collected 23 posts from VC sources

🔍 Step 2/5: Deduplicating content...
   ✓ Deduplicated to 18 unique posts

✍️  Step 3/5: Generating podcast script...
   ✓ Script generated (2043 words, ~13.6 min)

🎙️  Step 4/5: Converting text to speech...
   💰 Estimated cost: $0.61
   ✓ Audio generated (3.2 MB)

💾 Step 5/5: Saving podcast file...
   ✓ Audio saved to: /Users/you/Desktop/vc_podcast_20260104_1430_machine_learning.mp3

============================================================
✅ Podcast generated successfully!
============================================================
📁 File: /Users/you/Desktop/vc_podcast_20260104_1430_machine_learning.mp3
⏱️  Duration: ~13.6 minutes
📊 Sources: 18 unique posts
💰 Cost: $0.61

🎧 Your podcast is ready to listen!
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key for Claude |
| `ELEVENLABS_API_KEY` | Yes | Your ElevenLabs API key for TTS |
| `DESKTOP_PATH` | No | Custom desktop path (auto-detected if not set) |

### VC Sources

The tool scrapes from these sources by default (configured in `src/config.py`):

- **a16z** - Andreessen Horowitz
- **Sequoia Capital** - Sequoia Capital articles
- **First Round Review** - First Round Capital
- **AVC** - Fred Wilson's blog
- **Tomasz Tunguz** - Redpoint Ventures

To add or modify sources, edit `VC_SOURCES` in `src/config.py`.

## API Costs

### Anthropic Claude API

- **Model**: claude-3-5-sonnet-20241022
- **Typical Usage**: ~5K input tokens + 2K output tokens per podcast
- **Cost per Podcast**: ~$0.20-0.25

### ElevenLabs API

- **Free Tier**: 10,000 characters/month
- **Paid Tier**: $5/month for 30,000 characters
- **Typical Usage**: ~2,000 words = ~10,000 characters per podcast
- **Cost per Podcast**: ~$0.30-0.60 (paid tier)

**Total Estimated Cost**: ~$0.50-0.85 per podcast

## Development

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest --cov=src tests/

# Specific module
pytest tests/unit/test_scraper.py -v
```

### Project Structure

```
vc-sentiment-podcast/
├── src/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── config.py           # Configuration & VC sources
│   ├── scraper.py          # Web scraping
│   ├── aggregator.py       # Content deduplication
│   ├── script_generator.py # Claude AI integration
│   ├── tts.py              # ElevenLabs TTS
│   ├── file_handler.py     # File operations
│   └── models.py           # Data models
├── tests/
│   ├── unit/               # Unit tests (97 tests)
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test fixtures
├── requirements.txt
├── .env.example
└── README.md
```

### Code Quality

- **Test Coverage**: 97 unit tests covering all modules
- **Type Hints**: Full type annotations
- **Error Handling**: Comprehensive error handling with retries
- **Logging**: Structured logging for debugging

## Troubleshooting

### Common Issues

**API Key Not Found**
```
Error: ANTHROPIC_API_KEY not found
```
Solution: Ensure `.env` file exists with valid API keys

**Desktop Path Not Writable**
```
Error: Desktop path is not writable
```
Solution: Check permissions or set custom `DESKTOP_PATH` in `.env`

**Insufficient Content**
```
Error: Insufficient content (2 posts)
```
Solution: Try a longer timeframe (2-3 weeks) or broader topic

**Rate Limit Errors**
```
Error: Rate limit exceeded
```
Solution: The tool automatically retries with exponential backoff. Wait a moment and try again.

## Roadmap

Future enhancements:

- [ ] RSS feed generation for podcast platforms
- [ ] Scheduled/automated podcast generation
- [ ] Multiple voice options
- [ ] Custom VC source lists
- [ ] Email delivery
- [ ] Web dashboard
- [ ] Multi-language support

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Credits

Built with:
- [Claude AI](https://www.anthropic.com/) - Script generation
- [ElevenLabs](https://elevenlabs.io/) - Text-to-speech
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - Web scraping
- [Click](https://click.palletsprojects.com/) - CLI interface

---

**Generated with ❤️ by Claude Code**
