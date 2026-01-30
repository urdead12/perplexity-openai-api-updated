# Perplexity OpenAI API - Two Variants

This project provides an OpenAI-compatible API for Perplexity AI, with support for two different AI coding assistant variants:

1. **Claude Code Variant** - Integration with Anthropic's Claude Code CLI
2. **OpenCode Variant** - Integration with OpenCode (open-source alternative)

## Quick Comparison

| Feature | Claude Code | OpenCode |
|---------|-------------|----------|
| **License** | Proprietary | Open Source |
| **Setup Complexity** | Moderate | Simple |
| **Proxy Required** | Yes (LiteLLM) | No |
| **Ports Used** | 8000 + 8080 | 8000 only |
| **Installation** | Requires Claude Code CLI | Install via npm/brew/curl |
| **Configuration** | Auto-configured | JSON config file |

## Architecture

### Claude Code Variant

```
Claude Code CLI
    ↓
LiteLLM Proxy (port 8080)
    ↓
Perplexity OpenAI Server (port 8000)
    ↓
Perplexity Web Scraper
    ↓
Perplexity.ai
```

**Key Components:**
- Perplexity OpenAI server provides OpenAI-compatible API
- LiteLLM proxy routes requests and handles model mapping
- Claude Code connects to LiteLLM as if it were OpenAI

### OpenCode Variant

```
OpenCode CLI
    ↓
Perplexity OpenAI Server (port 8000)
    ↓
Perplexity Web Scraper
    ↓
Perplexity.ai
```

**Key Components:**
- Perplexity OpenAI server provides OpenAI-compatible API
- OpenCode connects directly using `@ai-sdk/openai-compatible`
- No proxy needed (simpler setup)

---

## Quick Start

### Using the Unified CLI (Recommended)

```bash
python perplexity_setup.py
```

This interactive menu lets you:
- Choose between Claude Code or OpenCode
- Install dependencies
- Launch the variant
- View detailed information

### Claude Code Variant

#### Installation

```bash
# Option 1: Use unified CLI
python perplexity_setup.py
# Select: 1 (Claude Code) → 1 (Install)

# Option 2: Direct installation
python install_claude_perplexity.py
```

#### Setup

1. Get your Perplexity session token:
   - Log in at https://www.perplexity.ai
   - Open DevTools (F12) → Application → Cookies
   - Copy `__Secure-next-auth.session-token` value

2. Set environment variable:
   ```bash
   export PERPLEXITY_SESSION_TOKEN='your_token_here'
   ```

#### Launch

```bash
# Option 1: Use unified CLI
python perplexity_setup.py
# Select: 1 (Claude Code) → 2 (Launch)

# Option 2: Direct launch
python launch_claude_perplexity.py

# Option 3: Server only
python launch_claude_perplexity.py --services-only

# Option 4: Claude only (with existing services)
python launch_claude_perplexity.py --claude-only
```

### OpenCode Variant

#### Installation

```bash
# Option 1: Use unified CLI
python perplexity_setup.py
# Select: 2 (OpenCode) → 1 (Install)

# Option 2: Direct installation
python setup/opencode/install_opencode_perplexity.py
```

The installer will:
- Create Python virtual environment
- Install dependencies
- Clone perplexity-openai-api repository
- Install OpenCode CLI (optional)
- Configure OpenCode to use Perplexity server

#### Setup

1. Get your Perplexity session token (same as Claude variant)

2. Add to `.env` file in repository:
   ```bash
   PERPLEXITY_SESSION_TOKEN=your_token_here
   ```

#### Launch

```bash
# Option 1: Use unified CLI
python perplexity_setup.py
# Select: 2 (OpenCode) → 2 (Launch)

# Option 2: Direct launch
python setup/opencode/launch_opencode_perplexity.py

# Option 3: Server only
python setup/opencode/launch_opencode_perplexity.py --server-only

# Option 4: OpenCode only (with existing server)
python setup/opencode/launch_opencode_perplexity.py --opencode-only
```

---

## Available Models

Both variants support all Perplexity models:

- **perplexity-auto** - Best model (auto-selected)
- **perplexity-sonar** - Fast queries
- **perplexity-research** - Deep research mode
- **perplexity-labs** - Experimental features
- Plus external models: GPT-5.x, Claude 4.5, Gemini 3, Grok 4.1, etc.

Models are automatically discovered when the server starts.

---

## Installation Directories

### Claude Code Variant
```
~/.claude-perplexity/
├── venv/                           # Python virtual environment
├── perplexity-openai-api-updated/  # Cloned repository
├── litellm_config.yaml             # LiteLLM configuration
├── logs/                           # Service logs
└── install_state.json              # Installation state
```

### OpenCode Variant
```
~/.opencode-perplexity/
├── venv/                           # Python virtual environment
├── perplexity-openai-api-updated/  # Cloned repository
├── logs/                           # Service logs
└── install_state.json              # Installation state

~/.config/opencode/
└── opencode.json                   # OpenCode configuration
```

---

## Configuration

### Claude Code Variant

Configuration is automatic:
- LiteLLM config is auto-generated at `~/.claude-perplexity/litellm_config.yaml`
- Models are discovered and configured automatically
- Claude Code environment variables are set by the launcher

### OpenCode Variant

Configuration file: `~/.config/opencode/opencode.json`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "perplexity": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Perplexity AI",
      "options": {
        "baseURL": "http://localhost:8000/v1",
        "apiKey": "dummy"
      },
      "models": {
        "perplexity-auto": {
          "name": "Perplexity Auto (Best)"
        },
        "perplexity-sonar": {
          "name": "Perplexity Sonar (Fast)"
        }
      }
    }
  },
  "model": "perplexity/perplexity-auto"
}
```

Models are automatically added when you run the launcher.

---

## Which Variant Should You Choose?

### Choose Claude Code Variant if you:
- ✅ Already use Claude Code
- ✅ Want Anthropic's Claude Code experience
- ✅ Need model routing through LiteLLM
- ✅ Have Claude Code CLI installed

### Choose OpenCode Variant if you:
- ✅ Want an open-source solution
- ✅ Prefer simpler setup (no proxy)
- ✅ Don't need LiteLLM features
- ✅ Want to try an open-source AI coding assistant
- ✅ Value transparency and community development

---

## Environment Variables

### Common (Both Variants)

```bash
PERPLEXITY_SESSION_TOKEN=your_token  # Required - your Perplexity session token
```

### Claude Code Variant

Set automatically by launcher:
```bash
ANTHROPIC_BASE_URL=http://localhost:8080
ANTHROPIC_API_KEY=dummy
ANTHROPIC_MODEL=model_name
```

### OpenCode Variant

Optional:
```bash
PORT=8000                    # Server port (default: 8000)
HOST=0.0.0.0                # Server host (default: 0.0.0.0)
LOG_LEVEL=INFO              # Log level (default: INFO)
```

---

## Troubleshooting

### Claude Code Variant

**Services won't start:**
- Check ports 8000 and 8080 are free
- Verify LiteLLM is installed in venv
- Check installation logs

**Claude Code not found:**
- Install Claude Code CLI
- Ensure `claude` command is in PATH

**Models not showing up:**
- Wait for model discovery to complete
- Check `~/.claude-perplexity/litellm_config.yaml`

### OpenCode Variant

**Server won't start:**
- Check `PERPLEXITY_SESSION_TOKEN` is set
- Verify port 8000 is not in use
- Check Python version (3.10+ required)

**OpenCode not connecting:**
- Verify server is running: `curl http://localhost:8000/health`
- Check OpenCode config: `~/.config/opencode/opencode.json`
- Ensure `baseURL` points to `http://localhost:8000/v1`

**OpenCode not installed:**
- Install via: `curl -fsSL https://opencode.ai/install | bash`
- Or: `npm i -g opencode-ai@latest`
- Or: `brew install opencode`

---

## Project Structure

```
perplexity-openai-api-updated/
├── setup/                          # Organized setup scripts
│   ├── common/                     # Shared utilities
│   │   ├── utils.py                # Common installation utilities
│   │   └── launcher_utils.py       # Common launcher utilities
│   ├── claude/                     # Claude Code variant
│   │   ├── install_claude_perplexity.py
│   │   └── launch_claude_perplexity.py
│   └── opencode/                   # OpenCode variant
│       ├── install_opencode_perplexity.py
│       └── launch_opencode_perplexity.py
├── src/
│   └── perplexity_webui_scraper/   # Core Perplexity scraper library
├── openai_server.py                # Perplexity OpenAI-compatible API server
├── fetch_models.py                 # Model discovery utility
├── perplexity_setup.py             # Unified CLI (new!)
├── install_claude_perplexity.py    # Claude installer (compatibility)
└── launch_claude_perplexity.py     # Claude launcher (compatibility)
```

---

## API Endpoints (Both Variants)

The Perplexity OpenAI server provides these endpoints:

- `GET /health` - Health check
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions (streaming supported)
- `POST /v1/completions` - Legacy completions
- `GET /conversations` - List active conversations
- `DELETE /conversations/{id}` - Delete conversation
- `POST /v1/models/refresh` - Force refresh models

---

## Advanced Usage

### Running Multiple Variants

You can install both variants on the same system. They use separate installation directories and don't conflict.

### Custom OpenCode Models

Edit `~/.config/opencode/opencode.json` to add custom model configurations:

```json
{
  "provider": {
    "perplexity": {
      "models": {
        "my-custom-model": {
          "name": "My Custom Model",
          "maxTokens": 4096
        }
      }
    }
  }
}
```

### Server-Only Mode

Both variants support running just the server:

```bash
# Claude variant
python launch_claude_perplexity.py --services-only

# OpenCode variant
python setup/opencode/launch_opencode_perplexity.py --server-only
```

Then use the server with any OpenAI-compatible client:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

response = client.chat.completions.create(
    model="perplexity-auto",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Contributing

Contributions are welcome! The modular setup makes it easy to:
- Add new variants
- Improve shared utilities
- Enhance existing variants

---

## License

See LICENSE file for details.

---

## Credits

- Perplexity AI for the excellent search-augmented AI
- Anthropic for Claude Code
- Anomaly for OpenCode
- BerriAI for LiteLLM
- FastAPI for the web framework
