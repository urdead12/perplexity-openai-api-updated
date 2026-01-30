# Perplexity OpenAI-Compatible API Server

Transform Perplexity AI into a drop-in replacement for OpenAI's API. This server bridges the gap between Perplexity's powerful search-augmented intelligence and applications built for OpenAI's standard interface. Deploy in seconds with Docker, no code changes required. 
It is forked from [henrique-coder/perplexity-webui-scraper](https://github.com/henrique-coder/perplexity-webui-scraper) and uses Python and FastAPI to create a RESTful API server.


### Features

- Models are automatically discovered from Perplexity.
- One-click deployment with Docker
- Request rate limiting 

## Quick Start

### Docker (Recommended)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Add your Perplexity session token to .env

# 3. Start the server
docker-compose up -d

# 4. Test
curl http://localhost:8000/health
curl http://localhost:8000/v1/models
```

### Manual

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Copy and configure .env
cp .env.example .env
# Edit .env with your session token

# Run
python openai_server.py
```

## Getting Your Session Token
uv pip install perplexity-webui-scraper  # from PyPI (stable)
uv pip install git+https://github.com/henrique-coder/perplexity-webui-scraper.git@dev  # from GitHub (development)
```

## Requirements

- **Perplexity Pro/Max account**
- **Session token** (`__Secure-next-auth.session-token` cookie from your browser)

### Getting Your Session Token

You can obtain your session token in two ways:

#### Option 1: Automatic (CLI Tool)

The package includes a CLI tool to automatically generate and save your session token:

```bash
get-perplexity-session-token
```

This interactive tool will:

1. Ask for your Perplexity email
2. Send a verification code to your email
3. Accept either a 6-digit code or magic link
4. Extract and display your session token
5. Optionally save it to your `.env` file

**Features:**

- Secure ephemeral session (cleared on exit)
- Automatic `.env` file management
- Support for both OTP codes and magic links
- Clean terminal interface with status updates

#### Option 2: Manual (Browser)

If you prefer to extract the token manually:

1. Log in at [perplexity.ai](https://www.perplexity.ai)
2. Open DevTools (F12) → Application → Cookies
3. Copy `__Secure-next-auth.session-token` value
4. Add to `.env`: `PERPLEXITY_SESSION_TOKEN=your_token`
2. Open DevTools (`F12`) → Application/Storage → Cookies
3. Copy the value of `__Secure-next-auth.session-token`
4. Store in `.env`: `PERPLEXITY_SESSION_TOKEN="your_token"`

## API Usage

The server is 100% OpenAI API compatible:

```python
import openai

client = openai.OpenAI(
    api_key="your-api-key",  # Optional
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="perplexity-auto",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "perplexity-auto", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat completions |
| `/v1/models` | GET | List available models |
| `/v1/models/refresh` | POST | Refresh models from Perplexity |
| `/conversations` | GET | List conversations |
| `/stats` | GET | Server statistics |
| `/health` | GET | Health check |
## API

### `Perplexity(session_token, config?)`

| Parameter       | Type           | Description        |
| --------------- | -------------- | ------------------ |
| `session_token` | `str`          | Browser cookie     |
| `config`        | `ClientConfig` | Timeout, TLS, etc. |

### `Conversation.ask(query, model?, files?, citation_mode?, stream?)`

| Parameter       | Type                    | Default       | Description         |
| --------------- | ----------------------- | ------------- | ------------------- |
| `query`         | `str`                   | -             | Question (required) |
| `model`         | `Model`                 | `Models.BEST` | AI model            |
| `files`         | `list[str \| PathLike]` | `None`        | File paths          |
| `citation_mode` | `CitationMode`          | `CLEAN`       | Citation format     |
| `stream`        | `bool`                  | `False`       | Enable streaming    |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PERPLEXITY_SESSION_TOKEN` | - | Required: Session token |
| `OPENAI_API_KEY` | - | Optional: API key for auth |
| `PORT` | 8000 | Server port |
| `LOG_LEVEL` | INFO | Logging level |
| `ENABLE_RATE_LIMITING` | true | Enable rate limiting |
| `REQUESTS_PER_MINUTE` | 60 | Rate limit |
| `CONVERSATION_TIMEOUT` | 3600 | Session timeout (seconds) |
| `DEFAULT_MODEL` | perplexity-auto | Default model |

## Models

Models are automatically fetched from Perplexity. Common models include:

- `perplexity-auto` - Auto-select best model
- `perplexity-sonar` - Fast responses
- `perplexity-research` - Deep research
- GPT, Claude, Gemini, Grok models via Perplexity

Use `/v1/models` to see all available models.

## License

MIT
| Model                              | Description                                                               |
| ---------------------------------- | ------------------------------------------------------------------------- |
| `Models.RESEARCH`                  | Research - Fast and thorough for routine research                         |
| `Models.LABS`                      | Labs - Multi-step tasks with advanced troubleshooting                     |
| `Models.BEST`                      | Best - Automatically selects the most responsive model based on the query |
| `Models.SONAR`                     | Sonar - Perplexity's fast model                                           |
| `Models.GPT_52`                    | GPT-5.2 - OpenAI's latest model                                           |
| `Models.GPT_52_THINKING`           | GPT-5.2 Thinking - OpenAI's latest model with thinking                    |
| `Models.CLAUDE_45_OPUS`            | Claude Opus 4.5 - Anthropic's Opus reasoning model                        |
| `Models.CLAUDE_45_OPUS_THINKING`   | Claude Opus 4.5 Thinking - Anthropic's Opus reasoning model with thinking |
| `Models.GEMINI_3_PRO`              | Gemini 3 Pro - Google's newest reasoning model                            |
| `Models.GEMINI_3_FLASH`            | Gemini 3 Flash - Google's fast reasoning model                            |
| `Models.GEMINI_3_FLASH_THINKING`   | Gemini 3 Flash Thinking - Google's fast reasoning model with thinking     |
| `Models.GROK_41`                   | Grok 4.1 - xAI's latest advanced model                                    |
| `Models.GROK_41_THINKING`          | Grok 4.1 Thinking - xAI's latest reasoning model                          |
| `Models.KIMI_K2_THINKING`          | Kimi K2 Thinking - Moonshot AI's latest reasoning model                   |
| `Models.CLAUDE_45_SONNET`          | Claude Sonnet 4.5 - Anthropic's newest advanced model                     |
| `Models.CLAUDE_45_SONNET_THINKING` | Claude Sonnet 4.5 Thinking - Anthropic's newest reasoning model           |

### CitationMode

| Mode       | Output                |
| ---------- | --------------------- |
| `DEFAULT`  | `text[1]`             |
| `MARKDOWN` | `text[1](url)`        |
| `CLEAN`    | `text` (no citations) |

### ConversationConfig

| Parameter         | Default       | Description        |
| ----------------- | ------------- | ------------------ |
| `model`           | `Models.BEST` | Default model      |
| `citation_mode`   | `CLEAN`       | Citation format    |
| `save_to_library` | `False`       | Save to library    |
| `search_focus`    | `WEB`         | Search type        |
| `source_focus`    | `WEB`         | Source types       |
| `time_range`      | `ALL`         | Time filter        |
| `language`        | `"en-US"`     | Response language  |
| `timezone`        | `None`        | Timezone           |
| `coordinates`     | `None`        | Location (lat/lng) |

## Exceptions

The library provides specific exception types for better error handling:

| Exception                          | Description                                                  |
| ---------------------------------- | ------------------------------------------------------------ |
| `PerplexityError`                  | Base exception for all library errors                        |
| `AuthenticationError`              | Session token is invalid or expired (HTTP 403)               |
| `RateLimitError`                   | Rate limit exceeded (HTTP 429)                               |
| `FileUploadError`                  | File upload failed                                           |
| `FileValidationError`              | File validation failed (size, type, etc.)                    |
| `ResearchClarifyingQuestionsError` | Research mode is asking clarifying questions (not supported) |
| `ResponseParsingError`             | API response could not be parsed                             |
| `StreamingError`                   | Error during streaming response                              |

### Handling Research Mode Clarifying Questions

When using Research mode (`Models.RESEARCH`), the API may ask clarifying questions before providing an answer. Since programmatic interaction is not supported, the library raises a `ResearchClarifyingQuestionsError` with the questions:

```python
from perplexity_webui_scraper import (
    Perplexity,
    ResearchClarifyingQuestionsError,
)

try:
    conversation.ask("Research this topic", model=Models.RESEARCH)
except ResearchClarifyingQuestionsError as error:
    print("The AI needs clarification:")
    for question in error.questions:
        print(f"  - {question}")
    # Consider rephrasing your query to be more specific
```

## MCP Server (Model Context Protocol)

The library includes an MCP server that allows AI assistants (like Claude) to search using Perplexity AI directly.

### Installation

```bash
uv pip install perplexity-webui-scraper[mcp]
```

### Running the Server

```bash
# Set your session token
export PERPLEXITY_SESSION_TOKEN="your_token_here"  # For Linux/Mac
set PERPLEXITY_SESSION_TOKEN="your_token_here"  # For Windows

# Run with FastMCP
uv run fastmcp run src/perplexity_webui_scraper/mcp/server.py

# Or test with the dev inspector
uv run fastmcp dev src/perplexity_webui_scraper/mcp/server.py
```

### Claude Desktop Configuration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "uv",
      "args": [
        "run",
        "fastmcp",
        "run",
        "path/to/perplexity_webui_scraper/mcp/server.py"
      ],
      "env": {
        "PERPLEXITY_SESSION_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Available Tool

| Tool             | Description                                                                 |
| ---------------- | --------------------------------------------------------------------------- |
| `perplexity_ask` | Ask questions and get AI-generated answers with real-time data from the web |

**Parameters:**

| Parameter      | Type  | Default  | Description                                                   |
| -------------- | ----- | -------- | ------------------------------------------------------------- |
| `query`        | `str` | -        | Question to ask (required)                                    |
| `model`        | `str` | `"best"` | AI model (`best`, `research`, `gpt52`, `claude_sonnet`, etc.) |
| `source_focus` | `str` | `"web"`  | Source type (`web`, `academic`, `social`, `finance`, `all`)   |

## Disclaimer

This is an unofficial implementation using internal Perplexity APIs. Use at your own risk.
This is an **unofficial** library. It uses internal APIs that may change without notice. Use at your own risk.

By using this library, you agree to Perplexity AI's Terms of Service.
