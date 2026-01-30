# Perplexity OpenAI API - Two Variants

This project now supports **two variants** for using Perplexity AI through an OpenAI-compatible API:

1. **OpenAI Variant** - Direct OpenAI API usage (NEW!)
2. **Claude Code Variant** - Integration with Claude Code CLI

## Quick Comparison

| Feature | OpenAI Variant | Claude Code Variant |
|---------|---------------|---------------------|
| **Setup Complexity** | Simple | Moderate |
| **Dependencies** | Minimal (FastAPI, Perplexity scraper) | More (+ LiteLLM, Claude Code CLI) |
| **Proxy Required** | No | Yes (LiteLLM) |
| **Use Case** | General OpenAI API usage | Claude Code integration |
| **Client Compatibility** | Any OpenAI client | Claude Code CLI |
| **Port** | 8000 | 8000 (Perplexity) + 8080 (LiteLLM) |

---

## OpenAI Variant (Recommended for most users)

### Overview

The OpenAI variant provides a **direct OpenAI-compatible API** for Perplexity AI. No proxy needed - just start the server and use any OpenAI SDK!

### Architecture

```
Your Application (OpenAI SDK)
    ↓
Perplexity OpenAI API Server (port 8000)
    ↓
Perplexity Web Scraper
    ↓
Perplexity.ai
```

### Installation

#### Option 1: Using the unified CLI

```bash
python perplexity_cli.py
# Select "1. OpenAI Variant" → "1. Install dependencies"
```

#### Option 2: Manual installation

```bash
# Install dependencies
python variants/openai/installer.py

# Or manually
pip install fastapi uvicorn pydantic slowapi curl_cffi python-dotenv
pip install -e .
```

### Configuration

1. Get your Perplexity session token:
   - Log in at https://www.perplexity.ai
   - Open DevTools (F12) → Application → Cookies
   - Copy the `__Secure-next-auth.session-token` value

2. Set environment variable:

```bash
export PERPLEXITY_SESSION_TOKEN='your_token_here'

# Optional configuration
export PORT=8000
export HOST=0.0.0.0
export LOG_LEVEL=INFO
```

Or create a `.env` file:

```env
PERPLEXITY_SESSION_TOKEN=your_token_here
PORT=8000
LOG_LEVEL=INFO
```

### Usage

#### Start the server

```bash
# Option 1: Using the unified CLI
python perplexity_cli.py
# Select "1. OpenAI Variant" → "2. Launch server"

# Option 2: Direct launch
python variants/openai/launcher.py

# Option 3: As a module
python -m variants.openai.launcher

# Option 4: With examples
python variants/openai/launcher.py --examples
```

#### Use with Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # API key not required by default
)

response = client.chat.completions.create(
    model="perplexity-auto",
    messages=[
        {"role": "user", "content": "What is the weather like today?"}
    ]
)

print(response.choices[0].message.content)
```

#### Use with Node.js (OpenAI SDK)

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:8000/v1',
  apiKey: 'dummy'
});

const response = await client.chat.completions.create({
  model: 'perplexity-auto',
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(response.choices[0].message.content);
```

#### Use with cURL

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "perplexity-auto",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

#### Use with LangChain

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy",
    model="perplexity-auto"
)

response = llm.invoke("What's the weather like?")
print(response.content)
```

### Available Models

- `perplexity-auto` - Best model (auto-selected)
- `perplexity-sonar` - Fast queries
- `perplexity-research` - Deep research mode
- `perplexity-labs` - Experimental features
- Plus many more! (GPT-5.x, Claude 4.5, Gemini 3, Grok 4.1, etc.)

List all models:

```bash
curl http://localhost:8000/v1/models
```

### API Endpoints

- `GET /health` - Health check
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions (streaming supported)
- `POST /v1/completions` - Legacy completions
- `GET /conversations` - List active conversations
- `DELETE /conversations/{id}` - Delete conversation
- `POST /v1/models/refresh` - Force refresh models

---

## Claude Code Variant

### Overview

The Claude Code variant integrates Perplexity AI with Claude Code CLI through a LiteLLM proxy.

### Architecture

```
Claude Code CLI
    ↓
LiteLLM Proxy (port 8080)
    ↓
Perplexity OpenAI API Server (port 8000)
    ↓
Perplexity Web Scraper
    ↓
Perplexity.ai
```

### Installation

```bash
# Option 1: Using the unified CLI
python perplexity_cli.py
# Select "2. Claude Code Variant" → "1. Install dependencies"

# Option 2: Direct installation
python install_claude_perplexity.py
```

### Usage

```bash
# Option 1: Using the unified CLI
python perplexity_cli.py
# Select "2. Claude Code Variant" → "2. Launch server"

# Option 2: Direct launch (starts services + Claude)
python launch_claude_perplexity.py

# Option 3: Services only
python launch_claude_perplexity.py --services-only

# Option 4: Claude only (with existing services)
python launch_claude_perplexity.py --claude-only
```

The launcher will:
1. Start Perplexity wrapper (port 8000)
2. Start LiteLLM proxy (port 8080)
3. Discover and configure available models
4. Launch Claude Code with Perplexity backend

---

## Unified CLI

A convenient CLI menu system for managing both variants:

```bash
python perplexity_cli.py
```

Features:
- Interactive menu
- Install dependencies for either variant
- Launch servers with proper configuration
- View usage examples
- Easy switching between variants

---

## Project Structure

```
perplexity-openai-api-updated/
├── variants/
│   ├── __init__.py
│   ├── shared/                    # Shared components
│   │   ├── __init__.py
│   │   ├── config.py              # ServerConfig
│   │   ├── models.py              # ModelRegistry
│   │   ├── conversation.py        # ConversationManager
│   │   └── server.py              # FastAPI server
│   ├── claude/                    # Claude Code variant
│   │   ├── __init__.py
│   │   └── launcher.py            # Claude launcher
│   └── openai/                    # OpenAI variant
│       ├── __init__.py
│       ├── launcher.py            # OpenAI launcher
│       └── installer.py           # OpenAI installer
├── src/
│   └── perplexity_webui_scraper/  # Core scraper library
├── perplexity_cli.py              # Unified CLI
├── openai_server.py               # Original server (backward compat)
├── launch_claude_perplexity.py    # Claude launcher (backward compat)
├── install_claude_perplexity.py   # Claude installer
└── fetch_models.py                # Model discovery utility
```

---

## Which Variant Should You Use?

### Choose OpenAI Variant if you want to:
- ✅ Use Perplexity with any OpenAI-compatible client
- ✅ Integrate with Python/Node.js/other applications
- ✅ Simple, lightweight setup
- ✅ Direct API access without proxies
- ✅ Use with LangChain, OpenAI SDK, or custom clients

### Choose Claude Code Variant if you want to:
- ✅ Use with Claude Code CLI
- ✅ Existing Claude Code workflow
- ✅ Model routing through LiteLLM
- ✅ Claude-specific features and integration

---

## Environment Variables

### Common (both variants)

```bash
PERPLEXITY_SESSION_TOKEN=your_token  # Required
LOG_LEVEL=INFO                       # Optional
```

### OpenAI Variant Specific

```bash
PORT=8000                            # Server port
HOST=0.0.0.0                        # Server host
OPENAI_API_KEY=key                  # Optional auth
ENABLE_RATE_LIMITING=true           # Rate limiting
REQUESTS_PER_MINUTE=60              # Rate limit
CONVERSATION_TIMEOUT=3600           # Session timeout
MAX_CONVERSATIONS_PER_USER=100      # User limit
DEFAULT_MODEL=perplexity-auto       # Default model
DEFAULT_CITATION_MODE=CLEAN         # Citation mode
```

### Claude Code Variant Specific

```bash
ANTHROPIC_BASE_URL=http://localhost:8080  # Set by launcher
ANTHROPIC_MODEL=model_name                # Model selection
ANTHROPIC_API_KEY=dummy                   # Set by launcher
```

---

## Troubleshooting

### OpenAI Variant

**Server won't start:**
- Check `PERPLEXITY_SESSION_TOKEN` is set
- Verify port 8000 is not in use
- Check Python version (3.8+ required)

**Authentication errors:**
- Session token may have expired
- Get a fresh token from perplexity.ai

### Claude Code Variant

**Services won't start:**
- Check both ports 8000 and 8080 are free
- Verify LiteLLM is installed
- Check installation logs

**Claude Code not found:**
- Install Claude Code CLI
- Ensure `claude` is in your PATH

---

## Contributing

Contributions are welcome! The modular architecture makes it easy to:
- Add new variants
- Improve shared components
- Add features to specific variants

---

## License

See LICENSE file for details.

---

## Credits

Built on top of:
- [perplexity-webui-scraper](https://github.com/yourusername/perplexity-webui-scraper)
- FastAPI
- LiteLLM (Claude variant)
- OpenAI SDK
