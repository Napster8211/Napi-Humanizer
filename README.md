# NapsterTec Text Intelligence Engine

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/architecture-modular-green.svg)](architecture/TARGET_ARCHITECTURE.md)
[![Security & Privacy](https://img.shields.io/badge/security-hardened-blue.svg)](quality/SECURITY_AND_PRIVACY.md)

NapsterTec Text Intelligence Engine is an enterprise-grade, LLM-assisted writing and text-refinement platform. It helps authors, researchers, executives, and developers refine text with granular control over intent, editing mode, tone, audience, and intensity.

The system prioritizes **semantic preservation**, **factual integrity**, **security**, and **transparency**—deliberately replacing brittle, heuristic detector-evasion tricks with reliable editorial intelligence and context-aware natural language processing.

---

## Key Features

- **9 Specialized Editing Modes**:
  - `Proofread`: Correct grammar, spelling, punctuation, and typographical slips while strictly preserving authorial voice.
  - `Clarity`: Untangle convoluted syntax and eliminate ambiguity without altering meaning.
  - `Natural / Fluent`: Improve flow, cadence, and sentence transitions without fake anecdotes or hollow idioms.
  - `Professional`: Executive business communication register suitable for workplace reports and correspondence.
  - `Academic`: Formal, precise, and cautious language; strictly preserves citations (`[1]`, `Smith et al., 2024`) and domain terminology.
  - `Conversational`: Warm, approachable, direct, and accessible without forced slang.
  - `Concise`: Cut filler words, redundancies, and verbosity while retaining all vital data and nuances.
  - `Simplify`: Translate complex topics into plain language for broader audiences or lower reading levels.
  - `Custom`: Execute tailored editorial instructions subject to safety and factual integrity validation.
  - `Legacy`: Safe deterministic polish for backward compatibility.
- **Editing Intensity Controls**: Select between `Light` (targeted minimal polish), `Balanced` (standard polish), and `Substantial` (comprehensive restructuring), with all factual points and protected entities preserved.
- **Factual Integrity & Protected Spans**: Automatically detects, protects, and validates numbers, dates, currency amounts, percentages, citations, URLs, code blocks, and email addresses.
- **Provider-Independent Architecture**: Seamlessly switch between OpenRouter, OpenAI, custom OpenAI-compatible endpoints, or deterministic offline mock mode.
- **Resilient Provider Routing**: OpenRouter requests use a configured primary, fallback models, dynamically discovered free text models, bounded retries, circuit breaking, and a final `openrouter/free` route when enabled. Deterministic rule-based fallback is reserved for Proofread/Grammar and is labeled as limited mode.
- **Descriptive Quality Metrics**: Flesch Reading Ease, Flesch-Kincaid Grade Level, Lexical Diversity, and Reading Time. These metrics are strictly labeled as descriptive readability indicators, never as AI detection probabilities.
- **Hardened Security & Privacy**:
  - Treats all user input as untrusted content enclosed in boundary tags (`<untrusted_user_text>`) to prevent prompt injection attacks.
  - **Zero `innerHTML` interpolation**: The web interface exclusively uses safe DOM APIs (`textContent` and `.value`), mitigating XSS risks.
  - Strict Content-Security-Policy (CSP), X-Frame-Options (DENY), and X-Content-Type-Options (nosniff).
  - Sliding-window in-memory rate limiting.
  - Operational logging strictly omits raw user text and credentials by default.
- **Backward Compatibility**: Fully backward-compatible with legacy `ai_detector_bypass.py` and Flask entry points.

---

## Architecture Overview

```text
┌────────────────────────────────────────────────────────┐
│                   Web UI / CLI / API                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           Input Validation & Request Schema            │
│  (Empty check, size limits, mode & intensity check)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Document Analyzer                    │
│ (Metrics, paragraphs, sentences, protected span audit) │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                  Rewrite Orchestrator                  │
│  ├─ Prompt Builder (Anti-injection boundary tags)      │
│  ├─ Provider Adapter (OpenAI / OpenRouter / Mock)      │
│  └─ Timeout, retry policy & graceful local fallback    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                    Output Validator                    │
│ (Protected span verification, code fences, diff summary)│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│         Structured Response with Diagnostics           │
└────────────────────────────────────────────────────────┘
```

---

## Quickstart & Installation

### 1. Requirements
- Python 3.8 or higher (tested with Python 3.14.6)
- Git

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Copy the example environment configuration:
```bash
cp .env.example .env
```
Edit `.env` to configure your preferred provider:
```ini
# Application Mode
APP_ENV=development
PORT=5000
HOST=127.0.0.1
DEBUG=false

# LLM Provider: 'mock' (offline), 'openrouter', 'openai', or 'custom'
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_PRIMARY=openrouter/free
LLM_MODEL_FALLBACKS=
LLM_ALLOW_FREE_ROUTER=true
LLM_TIMEOUT_MS=45000
LLM_MAX_RETRIES=2

# Security & Limits
MAX_INPUT_CHARS=15000
MAX_WORDS_PER_RUN=500
RATE_LIMIT_PER_MINUTE=10
LOG_RAW_USER_TEXT=false
```

---

## Usage

### 1. Web Workspace
Launch the interactive writing workspace:
```bash
# Development mode
python web_ui.py
# or
python app.py

# Production WSGI server (using Waitress)
python wsgi.py
```
Open your browser to `http://127.0.0.1:5000`.

### 2. CLI Interface
The engine provides a feature-rich CLI via `cli.py`:

```bash
# List all editing modes and intensity levels
python cli.py modes

# Analyze readability and protected entities
python cli.py analyze "Revenue expanded by 18.5% ($4,500,000) on January 15, 2026."

# Rewrite text with a specific mode and intensity
python cli.py rewrite "We will recieve teh memo tomorrow ." --mode proofread --intensity balanced -v

# Rewrite text from a file and save output
python cli.py rewrite -f draft.txt -o refined.txt --mode clarity --tone authoritative

# Pipe text through stdin
cat report.txt | python cli.py rewrite --mode concise
```

### 3. Legacy Compatibility CLI
The previous prototype script `ai_detector_bypass.py` is fully preserved with safe defaults and deprecation warnings:
```bash
# Calculate readability score
python ai_detector_bypass.py --score-only "Sample text to score."

# Refine text safely
python ai_detector_bypass.py "We will recieve teh memo tomorrow."
```

### 4. REST API
The server exposes clean REST endpoints under `/api/v1`:

#### `POST /api/v1/rewrite`
```json
{
  "text": "Due to the fact that revenue increased by 18.5%, we celebrate on January 15, 2026.",
  "mode": "concise",
  "intensity": "balanced",
  "fallback_to_local": true
}
```
**Response**:
```json
{
  "original_text": "...",
  "revised_text": "Because revenue increased by 18.5%, we celebrate on January 15, 2026.",
  "mode": "concise",
  "intensity": "balanced",
  "provider": "openrouter",
  "model": "anthropic/claude-3.5-sonnet",
  "is_fallback": false,
  "warnings": [],
  "change_summary": {
    "added_words": 1,
    "removed_words": 5,
    "net_word_change": -4,
    "key_modifications": ["Rephrased 'Due to the' -> 'Because'"]
  },
  "metrics": {
    "char_count": 72,
    "word_count": 11,
    "flesch_reading_ease": 65.2,
    "flesch_kincaid_grade": 7.1,
    "metric_notice": "Descriptive writing metrics. These do not measure or estimate AI authorship or detection probability."
  },
  "request_id": "c1f4e928-...",
  "duration_ms": 32.4
}
```

#### `POST /api/v1/analyze`
Inspects structural counts, readability indexes, and protected spans without invoking an LLM.

#### `GET /api/v1/modes`
Lists all supported modes, descriptions, and intensity specifications.

#### `GET /api/v1/health`
Returns service health and non-sensitive configuration diagnostics (credentials strictly omitted).

---

## Testing

Run the full automated test suite:
```bash
pytest -v
```

The test suite covers:
- **Unit Tests**: Input/output validation, size limits, protected span extraction (numbers, dates, citations, URLs, code), syllable counting, Flesch formulas, prompt construction, and provider adapters.
- **Integration Tests**: Flask REST API contracts, health diagnostics, rate limiting, error fallbacks, and CLI workflows.
- **Security Tests**: Prompt injection mitigation inside source text, XSS regression tests verifying zero `innerHTML` usage and safe DOM rendering, and security headers validation.
- **Evaluation Benchmark**: Varied evaluation corpus (business email, academic paper with citations, casual note, technical instructions) evaluating factual preservation and formatting retention.

---

## Security and Privacy Commitments

1. **Untrusted Input Isolation**: All user-supplied text is isolated inside `<untrusted_user_text>` tags with closing tag sanitization, preventing prompt injection and system override attempts.
2. **Safe Frontend Rendering**: User input and LLM output are exclusively rendered using `textContent` and `.value` properties. `innerHTML` is never used.
3. **No Credential Leakage**: API credentials remain strictly server-side and are never rendered in frontend HTML, returned in API diagnostics, or committed to version control.
4. **No Raw Text in Server Logs**: Operational logs record request IDs, mode, provider, duration, and error category—never the raw user text.
5. **Production WSGI Ready**: Includes `wsgi.py` configured with Waitress for secure, multi-threaded production deployment.

---

## License

NapsterTec Text Intelligence Engine is released under the MIT License.
