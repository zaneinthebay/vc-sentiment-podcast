# Claude Code Configuration - VC Sentiment Podcast

## Project Context
This project analyzes venture capital sentiment from podcast transcripts.

## Custom Agents

### Product Idea to Requirement Writer
**Location:** `.claude/agents/product-idea-to-requirement-writer.md`
**Purpose:** Transforms brainstorm ideas into comprehensive, executable PRDs (Product Requirements Documents)

**When to use:**
- Converting product ideas into structured specifications
- Creating test-driven requirement documents
- Defining implementation sequences for new features

**Key Features:**
- Test-first, spec-driven approach
- Git workflow integration
- Atomic, independently testable units
- Self-correction loops for agents

**Example Usage:**
```
Use the product-idea-to-requirement-writer agent to create a PRD for [your idea]
```

## Project-Specific Instructions
- Follow test-first development principles
- Commit frequently with clear, conventional commit messages
- Use semantic versioning for releases

## Notes
- Project initialized: 2026-01-04
- Custom agents are version-controlled in `.claude/agents/`
