# Perplexity OpenAI API - AI Coding Assistant Integration

OpenAI-compatible API server for Perplexity AI with seamless integration for AI coding assistants.

Forked from [henrique-coder/perplexity-webui-scraper](https://github.com/henrique-coder/perplexity-webui-scraper) and built with Python and FastAPI.

## 🚀 Quick Start

**Interactive Setup (Recommended)**:
```bash
python perplexity_setup.py
```

**Or choose your variant**:

### OpenCode (Open Source - Simpler)

```bash
# Install
python setup/opencode/install_opencode_perplexity.py

# Set token
export PERPLEXITY_SESSION_TOKEN='your_token'

# Launch
python setup/opencode/launch_opencode_perplexity.py
```

### Claude Code (Anthropic's CLI)

```bash
# Install (original location)
python install_claude_perplexity.py

# Set token
export PERPLEXITY_SESSION_TOKEN='your_token'

# Launch (original location)
python launch_claude_perplexity.py
```

## 📖 Full Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get started in 5 minutes
- **[README_VARIANTS.md](README_VARIANTS.md)** - Detailed guide comparing both variants
- **[SCRIPTS_README.md](SCRIPTS_README.md)** - Script documentation and reference

## 🎯 What Is This?

Transform Perplexity AI into an OpenAI-compatible API with support for AI coding assistants:

✅ **Two Variants**:
- **OpenCode** - Open source, direct connection, single port (8000)
- **Claude Code** - With LiteLLM proxy, dual ports (8000 + 8080)

✅ **OpenAI API Compatible** - Works with any OpenAI SDK/client

✅ **Automatic Model Discovery** - Dynamically finds and configures models

✅ **Comprehensive Debugging** - Log files, tail windows, health monitoring

✅ **Streaming Support** - Real-time streaming responses

## 🔧 How It Works

### OpenCode Variant (Simpler)

```
OpenCode CLI → Perplexity OpenAI Server (8000) → Perplexity.ai
```

### Claude Code Variant

```
Claude Code → LiteLLM Proxy (8080) → Perplexity OpenAI Server (8000) → Perplexity.ai
```

## ✨ Key Features

### For Both Variants

- **Automatic Model Discovery** - Models discovered from Perplexity and configured
- **Real-time Monitoring** - Health checks and alerts when services go down
- **Comprehensive Logging** - Timestamped log files for stdout/stderr
- **Live Tail Windows** - Real-time output windows (Windows PowerShell)
- **OpenAI Compatible** - Drop-in replacement for OpenAI's API
- **Rate Limiting** - Built-in protection against API abuse
- **Conversation Management** - Persistent multi-turn conversations
- **Streaming Support** - Server-Sent Events for real-time responses

### Claude Code Variant Specific

- **LiteLLM Integration** - Advanced model routing and management
- **Multi-Service Monitoring** - Monitors both Perplexity and LiteLLM
- **Automatic Configuration** - Generates litellm_config.yaml automatically

### OpenCode Variant Specific

- **Direct Connection** - No proxy, simpler architecture
- **JSON Configuration** - Easy-to-edit OpenCode config file
- **Lightweight** - Fewer dependencies and moving parts

## 📋 Prerequisites

- **Perplexity Account** (Free or Pro)
- **Session Token** (`__Secure-next-auth.session-token` from browser)
- **Python 3.10+** (for local installation)
- **Claude Code CLI** (for Claude variant) OR **OpenCode** (for OpenCode variant)
- **PowerShell** (optional, for tail windows on Windows)

## 🔑 Getting Your Session Token

1. Log in at [perplexity.ai](https://www.perplexity.ai)
2. Open DevTools (F12) → Application → Cookies
3. Copy value of `__Secure-next-auth.session-token`
4. Set as environment variable: `export PERPLEXITY_SESSION_TOKEN='your_token'`

Or add to `.env` file in repository directory.

## 📁 Project Structure

```
perplexity-openai-api-updated/
├── setup/                          # Organized setup scripts
│   ├── common/                     # Shared utilities
│   │   ├── utils.py                # Installation utilities
│   │   └── launcher_utils.py       # Launcher & debugging utilities
│   ├── claude/                     # Claude Code variant
│   │   ├── install_claude_perplexity.py
│   │   └── launch_claude_perplexity.py
│   └── opencode/                   # OpenCode variant
│       ├── install_opencode_perplexity.py
│       └── launch_opencode_perplexity.py
├── src/
│   └── perplexity_webui_scraper/   # Core scraper library
├── openai_server.py                # OpenAI-compatible API server
├── fetch_models.py                 # Model discovery utility
├── perplexity_setup.py             # Unified interactive setup
├── install_claude_perplexity.py    # Claude installer (compatibility)
└── launch_claude_perplexity.py     # Claude launcher (compatibility)
```

## 🎨 Available Models

Both variants support all Perplexity models:

- `perplexity-auto` - Best model (recommended)
- `perplexity-sonar` - Fast queries
- `perplexity-research` - Deep research mode
- `perplexity-labs` - Experimental features

Plus external models via Perplexity:
- GPT-5.x, Claude 4.5, Gemini 3, Grok 4.1, and more

List models: `curl http://localhost:8000/v1/models`

## 🛠️ Advanced Usage

### Server-Only Mode

Run just the server without AI assistant:

```bash
# OpenCode
python setup/opencode/launch_opencode_perplexity.py --server-only

# Claude Code
python launch_claude_perplexity.py --services-only
```

### Use with OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # Not required by default
)

response = client.chat.completions.create(
    model="perplexity-auto",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### Streaming Responses

```python
stream = client.chat.completions.create(
    model="perplexity-auto",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/v1/models` | GET | List available models |
| `/v1/chat/completions` | POST | Chat completions (streaming supported) |
| `/v1/completions` | POST | Legacy completions |
| `/v1/models/refresh` | POST | Force refresh models |
| `/conversations` | GET | List active conversations |
| `/conversations/{id}` | DELETE | Delete conversation |
| `/stats` | GET | Server statistics |

## 🐛 Debugging Features

Both variants include comprehensive debugging:

### Log Files

All output captured in `~/.{variant}-perplexity/logs/`:
```
20260131_143022_Perplexity_stdout.log
20260131_143022_Perplexity_stderr.log
20260131_143022_LiteLLM_stdout.log  (Claude variant only)
20260131_143022_LiteLLM_stderr.log  (Claude variant only)
```

### Live Tail Windows (Windows)

On Windows, PowerShell windows automatically open showing:
- Last 50 lines initially
- Live-updating as new logs appear
- Separate window per service

### Service Monitoring

Background monitoring with:
- Health checks every 30 seconds
- Alerts when services go down
- Recovery notifications
- Non-intrusive console updates

## 🔍 Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Session Token Expired

Get a fresh token from perplexity.ai cookies and update:
```bash
export PERPLEXITY_SESSION_TOKEN='new_token'
```

### Services Won't Start

Check logs in `~/.{variant}-perplexity/logs/` for detailed error messages.

### OpenCode/Claude Not Found

Install the CLI:
- **OpenCode**: `curl -fsSL https://opencode.ai/install | bash`
- **Claude Code**: Follow [Anthropic's installation guide](https://claude.ai/code)

## 📊 Comparison: OpenCode vs Claude Code

| Feature | OpenCode | Claude Code |
|---------|----------|-------------|
| **License** | Open Source | Proprietary |
| **Setup** | Simple | Moderate |
| **Architecture** | Direct | via LiteLLM |
| **Ports** | 8000 only | 8000 + 8080 |
| **Dependencies** | Fewer | More |
| **Config** | JSON file | Auto YAML |

See [README_VARIANTS.md](README_VARIANTS.md) for detailed comparison.

## 📝 Configuration

### Environment Variables

```bash
# Required
PERPLEXITY_SESSION_TOKEN=your_token

# Optional
PORT=8000                    # Server port
LOG_LEVEL=INFO              # Logging level
ENABLE_RATE_LIMITING=true   # Rate limiting
REQUESTS_PER_MINUTE=60      # Rate limit
CONVERSATION_TIMEOUT=3600   # Session timeout
DEFAULT_MODEL=perplexity-auto
```

## 🐳 Docker Deployment

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your token

# 2. Start server
docker-compose up -d

# 3. Test
curl http://localhost:8000/health
```

## 🤝 Contributing

Contributions welcome! The modular architecture makes it easy to:
- Add new AI assistant variants
- Improve shared utilities
- Enhance existing features

## 📄 License

MIT License - See LICENSE file

## ⚠️ Disclaimer

This is an **unofficial** implementation using Perplexity's internal APIs. Use at your own risk.

By using this project, you agree to Perplexity AI's Terms of Service.

## 🙏 Credits

- [Perplexity AI](https://www.perplexity.ai) - Search-augmented AI platform
- [Henrique Coder](https://github.com/henrique-coder) - Original web scraper
- [Anthropic](https://www.anthropic.com) - Claude Code
- [Anomaly](https://github.com/anomalyco) - OpenCode
- [BerriAI](https://github.com/BerriAI) - LiteLLM proxy
- [FastAPI](https://fastapi.tiangolo.com) - Web framework

## 🔗 References

- [Perplexity WebUI Scraper](https://github.com/henrique-coder/perplexity-webui-scraper)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Claude Code](https://claude.ai/code)
- [OpenCode](https://github.com/anomalyco/opencode)

---

**Get Started**: Run `python perplexity_setup.py` for interactive setup!
