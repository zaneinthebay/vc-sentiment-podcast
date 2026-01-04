# VC Sentiment Podcast Generator

## One-Line Summary
Automated audio podcast generator that analyzes VC blog posts and creates lecture-style content about industry sentiment.

## Success State
User runs a CLI command, selects a timeframe and topic, and receives a professionally-narrated audio file on their desktop containing a curated summary of VC perspectives on that topic during the selected period.

## Scope Boundaries
- IN SCOPE:
  - CLI interface for time period selection (1, 2, or 3 weeks)
  - Topic selection with AI as default
  - Web scraping of VC blog posts from curated list
  - Content aggregation and deduplication
  - AI-generated lecture script from collected content
  - Text-to-speech conversion using ElevenLabs
  - Audio file download to desktop with descriptive filename
  - Error handling for network failures, API limits, and invalid inputs

- OUT OF SCOPE:
  - Web interface or GUI
  - User authentication/accounts
  - Cloud hosting or distribution
  - Real-time updates or scheduling
  - Multiple language support
  - Custom VC source configuration (hardcoded list for v1)
  - Audio editing or post-processing effects
  - Email delivery or sharing features

- DEFERRED (Future Considerations):
  - Production distribution system (RSS feed, podcast platforms)
  - User-submitted VC sources
  - Multi-language podcast generation
  - Automated scheduling/cron jobs
  - Historical archive browsing
  - Audio quality customization
  - Multiple voice options
  - Background music integration

---

## Success Criteria

### Exit Criteria (Ship when ALL are true)
1. [ ] User can run CLI and receive a valid audio file on desktop within 5 minutes for 1-week timeframe
2. [ ] Generated podcast accurately reflects content from at least 5 different VC sources
3. [ ] Audio quality is clear and professional (48kHz, proper volume normalization)
4. [ ] Script is coherent, lecture-style (not just concatenated quotes), 5-15 minutes in length
5. [ ] All edge cases (network failures, no posts found, API errors) display helpful error messages
6. [ ] Zero crashes on happy path execution
7. [ ] All unit tests passing (100% coverage of core functions)
8. [ ] Integration test completes end-to-end in test environment

### Test Architecture

#### Unit Tests
| Component | Test Description | Pass Condition |
|-----------|------------------|----------------|
| CLI Parser | Valid time period inputs (1, 2, 3 weeks) | Correct enum value returned |
| CLI Parser | Valid topic inputs (text strings) | Topic string stored, defaults to "artificial intelligence" |
| CLI Parser | Invalid inputs (negative numbers, non-strings) | Validation error with helpful message |
| VC Scraper | Fetch blog posts from single VC source | Returns structured data with title, date, content, source |
| VC Scraper | Handle 404/timeout on single source | Logs error, continues with other sources |
| VC Scraper | Date filtering (only posts within timeframe) | Posts outside range excluded |
| Content Aggregator | Deduplication of identical posts | Duplicate content removed |
| Content Aggregator | Markdown generation of aggregated content | Valid markdown with source attribution |
| Script Generator | LLM prompt construction | Prompt includes context, format instructions, word count target |
| Script Generator | LLM response parsing | Returns valid text script (string type) |
| TTS Converter | ElevenLabs API call with valid input | Returns audio binary data |
| TTS Converter | Handle API rate limit errors | Retry logic with exponential backoff (3 attempts) |
| File Writer | Save audio to desktop with valid filename | File exists at ~/Desktop/vc_podcast_[timestamp].mp3 |
| File Writer | Handle disk full error | Error message displayed, graceful exit |

#### Integration Tests
| Workflow | Steps | Expected Result |
|----------|-------|-----------------|
| Happy Path E2E | 1. Run CLI → 2. Select "1 week" → 3. Select "AI" → 4. Wait for completion | Audio file on desktop, 5-15min length, contains content from 5+ sources |
| Network Failure Recovery | 1. Run CLI → 2. Mock 3/5 sources fail → 3. Complete workflow | Audio still generated from 2 successful sources with warning message |
| No Posts Found | 1. Run CLI → 2. Select timeframe with zero posts | User-friendly error: "No posts found for this period. Try expanding timeframe." |
| API Key Missing | 1. Run without ElevenLabs key configured | Clear error: "ElevenLabs API key required. Set ELEVENLABS_API_KEY env variable." |
| Invalid Topic | 1. Run CLI → 2. Enter empty string for topic | Validation error, re-prompt user |

#### Edge Cases & Error Handling
| Scenario | Input | Expected Behavior |
|----------|-------|-------------------|
| Desktop directory not writable | Standard workflow | Error message with fallback to current directory |
| VC blog HTML structure changed | Standard workflow | Log parsing error, continue with other sources |
| LLM returns non-English text | Standard workflow | Detect language, retry with explicit English instruction |
| Generated script under 100 words | Content too sparse | Error: "Insufficient content. Try longer timeframe or different topic." |
| Audio generation takes >10min | Standard workflow | Progress indicator updates every 30s |
| Network disconnects mid-scrape | Standard workflow | Resume from last successful source |
| Filename collision on desktop | Standard workflow | Append counter: vc_podcast_[timestamp]_2.mp3 |

---

## Technical Specification

### Architecture

#### Tech Stack
- Language/Runtime: Python 3.11+
- Web Scraping: BeautifulSoup4, Requests (with retry logic)
- LLM: Anthropic Claude API (claude-3-5-sonnet-20241022)
- TTS: ElevenLabs API (v1)
- CLI Framework: Click (for argument parsing and prompts)
- Testing: pytest, pytest-mock, pytest-vcr (for HTTP mocking)
- Dependencies:
  - `requests` (HTTP client)
  - `beautifulsoup4` (HTML parsing)
  - `anthropic` (Claude API)
  - `elevenlabs` (TTS API)
  - `click` (CLI interface)
  - `python-dateutil` (date parsing)
  - `pytest`, `pytest-mock`, `pytest-vcr` (testing)
  - `python-dotenv` (environment variables)

#### Data Storage
- No persistent database required for v1
- In-memory storage during execution
- Output: Single MP3 file on desktop

### File Structure
```
vc-sentiment-podcast/
├── src/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point and user interaction
│   ├── config.py              # Configuration and VC source list
│   ├── scraper.py             # Web scraping logic
│   ├── aggregator.py          # Content collection and deduplication
│   ├── script_generator.py   # LLM-based script creation
│   ├── tts.py                 # Text-to-speech conversion
│   └── file_handler.py        # Audio file writing
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_cli.py
│   │   ├── test_scraper.py
│   │   ├── test_aggregator.py
│   │   ├── test_script_generator.py
│   │   ├── test_tts.py
│   │   └── test_file_handler.py
│   ├── integration/
│   │   └── test_end_to_end.py
│   └── fixtures/
│       ├── sample_blog_posts.html
│       └── sample_api_responses.json
├── .env.example               # Template for API keys
├── .gitignore
├── requirements.txt
├── setup.py                   # Package configuration
├── pytest.ini                 # Test configuration
├── README.md
└── PRD.md                     # This document
```

### Component Breakdown

#### 1. CLI Module (cli.py)
- **Purpose**: User interaction and orchestration of workflow
- **Inputs**: User selections via prompts
- **Outputs**: Triggers workflow, displays progress and results
- **Dependencies**: Click, all other modules
- **Tests**: test_cli.py (input validation, flow control)
- **Key Functions**:
  - `main()`: Entry point with Click decorators
  - `prompt_time_period()`: Returns enum (ONE_WEEK, TWO_WEEKS, THREE_WEEKS)
  - `prompt_topic()`: Returns string with default
  - `display_progress(step, total)`: Progress indicator

#### 2. Config Module (config.py)
- **Purpose**: Centralized configuration and VC source definitions
- **Inputs**: Environment variables
- **Outputs**: Configuration objects
- **Dependencies**: python-dotenv
- **Tests**: Implicit via other tests
- **Key Data**:
  - `VC_SOURCES`: List of dicts with {name, url, selector_strategy}
  - API keys loading
  - Desktop path detection (cross-platform)

#### 3. Scraper Module (scraper.py)
- **Purpose**: Fetch and parse blog posts from VC sources
- **Inputs**: VC source config, date range
- **Outputs**: List of BlogPost objects (title, date, content, source, url)
- **Dependencies**: Requests, BeautifulSoup4, dateutil
- **Tests**: test_scraper.py (parsing accuracy, error handling, date filtering)
- **Key Functions**:
  - `scrape_source(source_config, start_date, end_date)`: Returns List[BlogPost]
  - `parse_blog_html(html, strategy)`: HTML to structured data
  - `filter_by_date(posts, start_date, end_date)`: Date range filtering
  - Retry logic with exponential backoff

#### 4. Aggregator Module (aggregator.py)
- **Purpose**: Combine, deduplicate, and format collected content
- **Inputs**: List of BlogPost objects
- **Outputs**: Markdown-formatted document with metadata
- **Dependencies**: None (pure Python)
- **Tests**: test_aggregator.py (deduplication accuracy, markdown formatting)
- **Key Functions**:
  - `aggregate_posts(posts)`: Returns markdown string
  - `deduplicate_content(posts)`: Fuzzy matching for near-duplicates
  - `format_as_markdown(posts)`: Structured markdown with headings

#### 5. Script Generator Module (script_generator.py)
- **Purpose**: Convert aggregated content to lecture-style podcast script
- **Inputs**: Markdown content, topic, timeframe
- **Outputs**: Narrative script text (string)
- **Dependencies**: Anthropic Claude API
- **Tests**: test_script_generator.py (prompt construction, response validation)
- **Key Functions**:
  - `generate_script(content, topic, timeframe)`: Returns script string
  - `build_prompt(content, topic, timeframe)`: Constructs LLM prompt
  - `validate_script(script)`: Checks length, coherence indicators
  - Target length: 1500-2500 words (approx 10-15 min spoken)

#### 6. TTS Module (tts.py)
- **Purpose**: Convert script text to audio using ElevenLabs
- **Inputs**: Script text string
- **Outputs**: Audio binary data (MP3)
- **Dependencies**: ElevenLabs API
- **Tests**: test_tts.py (API integration, retry logic, audio validation)
- **Key Functions**:
  - `text_to_speech(script)`: Returns bytes (MP3 data)
  - `handle_rate_limit()`: Exponential backoff retry
  - `validate_audio(audio_data)`: Check file format and size
  - Voice: Default professional voice (Rachel or similar)
  - Settings: 48kHz, mono, MP3 format

#### 7. File Handler Module (file_handler.py)
- **Purpose**: Write audio file to desktop with proper naming
- **Inputs**: Audio binary data, metadata (topic, date)
- **Outputs**: File path of saved audio
- **Dependencies**: pathlib, os
- **Tests**: test_file_handler.py (file creation, naming, permissions)
- **Key Functions**:
  - `save_audio(audio_data, metadata)`: Returns saved file path
  - `get_desktop_path()`: Cross-platform desktop directory
  - `generate_filename(metadata)`: Format: vc_podcast_YYYYMMDD_HHmm_topic.mp3
  - `handle_collision(filename)`: Append counter if file exists

---

## Implementation Sequence

### Phase 1: Foundation & Configuration (3-4 commits)
| Step | Feature | Depends On | Tests | Commit Message |
|------|---------|------------|-------|----------------|
| 1.1 | Project structure and dependencies | None | N/A | "chore: initialize project structure with dependencies" |
| 1.2 | Config module with VC sources list | 1.1 | Manual verification | "feat(config): add VC source configuration and env loading" |
| 1.3 | CLI skeleton with Click prompts | 1.1 | test_cli.py | "feat(cli): implement user prompts for timeframe and topic" |
| 1.4 | Test fixtures and pytest setup | 1.1 | All passing | "test: add fixtures and pytest configuration" |

**Validation Checkpoint**: CLI runs, prompts user, displays mock success message.

### Phase 2: Data Collection (4-5 commits)
| Step | Feature | Depends On | Tests | Commit Message |
|------|---------|------------|-------|----------------|
| 2.1 | Scraper for single VC source | 1.2 | test_scraper.py (single source) | "feat(scraper): implement blog post scraping for single source" |
| 2.2 | Date filtering logic | 2.1 | test_scraper.py (date filter) | "feat(scraper): add date range filtering" |
| 2.3 | Multi-source scraping with parallelization | 2.2 | test_scraper.py (multiple sources) | "feat(scraper): add concurrent scraping for all VC sources" |
| 2.4 | Error handling and retry logic | 2.3 | test_scraper.py (network errors) | "feat(scraper): add error handling with retry logic" |
| 2.5 | Content aggregation and deduplication | 2.3 | test_aggregator.py | "feat(aggregator): implement content deduplication and markdown formatting" |

**Validation Checkpoint**: Can scrape real VC blogs and produce markdown document.

### Phase 3: Content Generation (3-4 commits)
| Step | Feature | Depends On | Tests | Commit Message |
|------|---------|------------|-------|----------------|
| 3.1 | Claude API integration and prompt design | 1.2, 2.5 | test_script_generator.py (API) | "feat(script): integrate Claude API for script generation" |
| 3.2 | Script validation and quality checks | 3.1 | test_script_generator.py (validation) | "feat(script): add script validation for length and coherence" |
| 3.3 | Retry logic for poor quality outputs | 3.2 | test_script_generator.py (retry) | "feat(script): add retry logic for script quality issues" |

**Validation Checkpoint**: Can generate coherent podcast script from markdown input.

### Phase 4: Audio Production (3-4 commits)
| Step | Feature | Depends On | Tests | Commit Message |
|------|---------|------------|-------|----------------|
| 4.1 | ElevenLabs API integration | 1.2, 3.2 | test_tts.py (API) | "feat(tts): integrate ElevenLabs text-to-speech" |
| 4.2 | Audio validation and format handling | 4.1 | test_tts.py (validation) | "feat(tts): add audio format validation" |
| 4.3 | File writing to desktop | 4.2 | test_file_handler.py | "feat(files): implement audio file saving with proper naming" |
| 4.4 | Collision handling and fallback paths | 4.3 | test_file_handler.py (edge cases) | "feat(files): add filename collision handling" |

**Validation Checkpoint**: Can generate and save audio file to desktop.

### Phase 5: Integration & Polish (3-4 commits)
| Step | Feature | Depends On | Tests | Commit Message |
|------|---------|------------|-------|----------------|
| 5.1 | End-to-end workflow integration | All above | test_end_to_end.py | "feat: integrate all components into complete workflow" |
| 5.2 | Progress indicators and user feedback | 5.1 | Manual testing | "feat(cli): add progress indicators and status messages" |
| 5.3 | Comprehensive error messages | 5.1 | test_end_to_end.py (errors) | "feat: add comprehensive error messaging" |
| 5.4 | README and setup documentation | All | N/A | "docs: add comprehensive README with setup instructions" |

**Validation Checkpoint**: Full integration test passes, all exit criteria met.

### Phase 6: Edge Cases & Hardening (2-3 commits)
| Step | Feature | Depends On | Tests | Commit Message |
|------|---------|------------|-------|----------------|
| 6.1 | Handle insufficient content scenarios | 5.1 | Edge case tests | "fix: handle scenarios with insufficient content" |
| 6.2 | Network resilience improvements | 5.1 | Network failure tests | "fix: improve network failure recovery" |
| 6.3 | Final bug fixes and cleanup | All | All tests | "fix: final bug fixes and code cleanup" |

**Total Estimated Commits**: 18-22

---

## Git Workflow Protocol

### Commit Cadence
- Commit after EVERY passing test suite
- Run full test suite before each commit (regression prevention)
- Commit message format: `type(scope): description`
- Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`

### Examples of Good Commit Messages
```
feat(scraper): add date range filtering for blog posts
test(aggregator): add deduplication unit tests
fix(tts): handle rate limit errors with exponential backoff
refactor(cli): extract prompt logic into separate functions
docs: update README with API key setup instructions
```

### Regression Prevention
After implementing feature N:
1. Run `pytest -v` (ALL tests, not just new ones)
2. If regression detected:
   - Do NOT commit broken state
   - Fix regression immediately
   - Document what caused it in Agent Notes
   - Add regression test to prevent recurrence
3. Only commit when full suite passes

### Checkpoint Strategy
- Tag milestones: `v0.1-foundation`, `v0.2-scraping`, `v0.3-generation`, `v0.4-audio`, `v1.0-release`
- If stuck >3 attempts on single feature:
  - Document issue in Agent Notes
  - Consider alternative approach
  - Revert to last tag if necessary
  - Reassess implementation strategy

### Branch Strategy (for future team collaboration)
- `main`: Always production-ready
- Feature branches: `feature/[component-name]`
- Merge only after all tests pass

---

## Agent Notes

### Session Log
| Timestamp | Phase | Status | Notes |
|-----------|-------|--------|-------|
| | | | Agent: Fill this in as you work |

### Decisions Made
**Agent: Document non-obvious implementation choices here**

Example:
- Chose BeautifulSoup over Scrapy for simplicity (no spider needed for v1)
- Selected Claude over GPT-4 for script generation due to longer context window
- Implemented fuzzy deduplication using difflib.SequenceMatcher (threshold: 0.85)

### Issues Encountered
| Issue | Attempted Solutions | Resolution |
|-------|---------------------|------------|
| | | Agent: Log problems and fixes |

### Context for Next Session
**Agent: If pausing mid-implementation, note:**
- Which phase are you in?
- What's the current blocker?
- What should be done next?
- Any API keys that need setup?

### Learnings
**Agent: After completion, document:**
- Which VC sources had most reliable HTML structure?
- Optimal script length for quality vs. processing time?
- ElevenLabs voice that worked best?
- Patterns that worked well / should be reused?

---

## Pre-Completion Checklist

### Code Quality
- [ ] All tests passing (pytest shows 100% pass rate)
- [ ] No debug print statements left in code
- [ ] Error handling implemented for all external API calls
- [ ] README updated with setup instructions and example usage
- [ ] .env.example created with required API keys listed

### Functional Completeness
- [ ] All 8 exit criteria met (see Success Criteria section)
- [ ] All edge cases from test architecture handled
- [ ] Integration test completes successfully in <5 minutes

### Documentation
- [ ] Inline comments on non-obvious logic (especially scraping selectors)
- [ ] API rate limits documented in README
- [ ] Example output audio file generated and validated
- [ ] Known limitations documented (VC source list, language support)

### User Experience
- [ ] Progress indicators show during long operations (scraping, TTS)
- [ ] Error messages are actionable (tell user what to do)
- [ ] Success message includes file path and duration
- [ ] Desktop fallback works if primary path fails

---

## VC Source Configuration (Initial List)

**Agent: Implement these in config.py**

| VC Firm/Person | Blog URL | Scraping Strategy |
|----------------|----------|-------------------|
| a16z | https://a16z.com/blog/ | Article list page, RSS fallback |
| Sequoia Capital | https://www.sequoiacap.com/articles/ | Article grid, date in metadata |
| First Round Review | https://review.firstround.com/latest | Structured article list |
| Fred Wilson (AVC) | https://avc.com/ | WordPress blog structure |
| Tomasz Tunguz | https://tomtunguz.com/ | Jekyll blog structure |

**Notes**:
- Each source requires custom CSS selectors (HTML structure varies)
- Include robots.txt compliance check
- Add User-Agent header to avoid blocking
- Fallback to RSS feed if available when scraping fails

---

## API Requirements & Setup

### Required API Keys
1. **Anthropic Claude API**
   - Sign up: https://console.anthropic.com/
   - Model: claude-3-5-sonnet-20241022
   - Estimated cost: $0.015 per 1K tokens (input), $0.075 per 1K tokens (output)
   - Typical usage: ~5K input + 2K output = ~$0.22 per podcast

2. **ElevenLabs API**
   - Sign up: https://elevenlabs.io/
   - Free tier: 10K characters/month
   - Paid tier: $5/month for 30K characters
   - Typical usage: 2000 words = ~10K characters per podcast

### Environment Variables (.env)
```
ANTHROPIC_API_KEY=sk-ant-xxx
ELEVENLABS_API_KEY=xxx
DESKTOP_PATH=/Users/username/Desktop  # Optional, auto-detected
```

---

## Example Usage (for README)

```bash
# Installation
git clone [repo-url]
cd vc-sentiment-podcast
pip install -r requirements.txt

# Setup API keys
cp .env.example .env
# Edit .env with your API keys

# Run
python -m src.cli

# Expected prompts:
# > Select time period: 1) 1 week  2) 2 weeks  3) 3 weeks
# [User enters: 1]
# > Enter topic of interest (default: artificial intelligence):
# [User enters: machine learning]
#
# Scraping VC blogs... [Progress bar]
# Generating script... [Progress bar]
# Creating audio... [Progress bar]
#
# Success! Podcast saved to:
# /Users/username/Desktop/vc_podcast_20260104_1430_machine_learning.mp3
# Duration: 12 minutes 34 seconds
```

---

## Future Enhancement Ideas (Post-v1)

**Not for initial implementation, but worth documenting:**

1. **RSS Feed Generation**: Auto-publish to podcast platforms
2. **Scheduled Execution**: Weekly automated podcasts
3. **Multiple Voice Profiles**: Different narrators for different topics
4. **Background Music**: Intro/outro theme music
5. **Show Notes**: Markdown file with links and citations
6. **Email Delivery**: Optional email with MP3 attachment
7. **Web Dashboard**: View past podcasts and analytics
8. **Custom VC Lists**: User-configured source lists
9. **Multi-language**: Generate in Spanish, Mandarin, etc.
10. **Transcript Generation**: Searchable text version

---

## Success Metrics (Post-Launch)

**How to know if v1 is actually useful:**

- User runs the tool more than once (repeat usage = value)
- Audio quality rated 4/5 or higher by test users
- Script coherence rated as "sounds like professional podcast" by 3+ users
- Execution time under 5 minutes for 1-week timeframe
- Zero crashes reported in first 10 uses
- Users share podcasts with colleagues (organic distribution)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| VC blogs change HTML structure | High | Medium | Implement fallback scrapers, RSS when available |
| API rate limits exceeded | Medium | High | Add retry logic, usage tracking, clear error messages |
| Generated script is incoherent | Medium | High | Script validation, retry with refined prompts |
| Audio quality issues | Low | Medium | Validate audio format, use reliable ElevenLabs voices |
| Insufficient content in timeframe | Medium | Medium | Allow user to expand timeframe, require min 3 sources |
| API costs exceed expectations | Low | Low | Track usage, add cost estimation in CLI |

---

## Testing Philosophy

**Test-First Principles:**
1. Write test BEFORE implementation
2. Test should fail initially (red)
3. Implement minimal code to pass (green)
4. Refactor with confidence (tests protect you)

**Coverage Targets:**
- Unit tests: 100% of core functions
- Integration tests: All user workflows
- Edge cases: All failure modes documented in PRD

**Mocking Strategy:**
- Mock external APIs (Anthropic, ElevenLabs) in unit tests
- Use pytest-vcr to record real API responses for integration tests
- Mock file system operations to avoid side effects

---

## Appendix: Technical Deep Dives

### A. Web Scraping Strategy

**Challenge**: Each VC blog has unique HTML structure

**Solution**: Strategy pattern with source-specific parsers

```python
# Pseudo-code example
class ScraperStrategy(ABC):
    @abstractmethod
    def extract_posts(self, html: str) -> List[BlogPost]:
        pass

class A16zScraper(ScraperStrategy):
    def extract_posts(self, html):
        # a16z-specific CSS selectors
        pass

class SequoiaScraper(ScraperStrategy):
    def extract_posts(self, html):
        # Sequoia-specific logic
        pass
```

### B. LLM Prompt Engineering

**Objective**: Generate lecture-style narrative, not bullet points

**Prompt Template**:
```
You are a professional podcast narrator creating a 12-minute audio essay about [TOPIC] in venture capital.

SOURCE MATERIAL:
[Aggregated blog posts in markdown]

REQUIREMENTS:
1. Synthesize the key themes and sentiment trends across all sources
2. Use a conversational, lecture-style narrative voice
3. Attribute specific ideas to their sources naturally ("As Fred Wilson noted...")
4. Target 2000 words (approximately 12 minutes spoken)
5. Structure: Intro (30 sec) → Main themes (10 min) → Conclusion (90 sec)
6. Avoid: Bullet points, lists, meta-commentary about the podcast itself

OUTPUT:
A complete podcast script ready for text-to-speech conversion.
```

### C. Deduplication Algorithm

**Problem**: Same VC post syndicated to multiple sites

**Solution**: Fuzzy matching with 85% similarity threshold

```python
from difflib import SequenceMatcher

def is_duplicate(post1: BlogPost, post2: BlogPost) -> bool:
    similarity = SequenceMatcher(None, post1.content, post2.content).ratio()
    return similarity > 0.85
```

### D. Audio Quality Specifications

**ElevenLabs Settings**:
- Model: eleven_monolingual_v1
- Voice: Rachel (professional female) or Adam (professional male)
- Stability: 0.5 (balanced between consistency and expressiveness)
- Similarity Boost: 0.75
- Output Format: mp3_44100_128 (44.1kHz, 128kbps)

---

## Final Implementation Notes

**Agent: Before you begin implementation:**

1. Verify all API keys are accessible
2. Check that desktop path is writable
3. Confirm network access to VC blog URLs
4. Review test fixtures are properly structured

**Agent: While implementing:**

1. Follow the phase sequence strictly (don't jump ahead)
2. Commit after every passing test
3. If a test fails 3 times, document in Agent Notes and consider alternative approach
4. Keep commits atomic (one feature/fix per commit)

**Agent: Before marking complete:**

1. Run full integration test end-to-end
2. Generate a real podcast and manually review quality
3. Validate all 8 exit criteria are met
4. Update README with actual setup steps tested on fresh environment

---

**END OF PRD**

This document is the complete specification. Implementation should require minimal additional clarification. If ambiguity arises, default to simplest solution that meets exit criteria.
