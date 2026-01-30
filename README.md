# Perplexity OpenAI-Compatible API Server + Claude Code Integration

Transform Perplexity AI into a drop-in replacement for OpenAI's API with seamless Claude Code integration. This project bridges the gap between Perplexity's powerful search-augmented intelligence and Claude Code, allowing you to leverage Perplexity's models directly within your Claude development environment.

It is forked from [henrique-coder/perplexity-webui-scraper](https://github.com/henrique-coder/perplexity-webui-scraper) and uses Python and FastAPI to create a RESTful API server.

## 🎯 Goal

Use Perplexity's models and search capabilities within Claude Code through an OpenAI-compatible API. This allows you to:

- Access Perplexity's search-augmented AI directly in Claude Code
- Choose from multiple models available on Perplexity (auto, research, sonar, and more)
- Maintain a single unified interface through the LiteLLM proxy
- Automatically discover and configure available models

## ✨ Features

- **Automatic Model Discovery** - Models are automatically discovered from Perplexity and configured
- **Claude Code Integration** - Dedicated launcher scripts for seamless integration with Claude Code
- **Real-time Monitoring** - Health checks and auto-alerts when services go down
- **Logging & Debugging** - Timestamped log files for both stdout and stderr of each service
- **Live Tail Windows** - Real-time output windows on Windows showing service logs
- **OpenAI Compatible** - Drop-in replacement for OpenAI's API
- **Multi-Model Support** - Access all Perplexity models and other LLMs through LiteLLM
- **Request Rate Limiting** - Built-in protection against API abuse
- **Docker Support** - One-click deployment with Docker

## 📋 Prerequisites

- **Perplexity Pro/Max account**
- **Session token** (`__Secure-next-auth.session-token` cookie from your browser)
- **Python 3.8+** (for local installation)
- **Claude Code CLI** (for Claude integration)
- **PowerShell** (for real-time tail windows on Windows)

## 🚀 Quick Start - Claude Code Integration

The easiest way to use Perplexity with Claude Code is with the launcher scripts:

### Installation

```bash
# Run the installation script (one-time setup)
python install_claude_perplexity.py
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up the configuration files
- Configure your Perplexity session token

### Usage

#### 1. Default Mode: Start Everything Together

```bash
python launch_claude_perplexity.py
```

This will:
1. Start the Perplexity wrapper server (port 8000)
2. Discover available models
3. Update LiteLLM configuration
4. Start the LiteLLM proxy (port 8080)
5. Open live tail windows showing service output (Windows only)
6. Ask you to select a model
7. Launch Claude Code with the selected model
8. Monitor services and alert if they go down

#### 2. Services Only Mode: Keep Services Running

```bash
python launch_claude_perplexity.py --services-only
```

Starts and keeps the services running (useful for running in one terminal while using Claude in another). Opens live tail windows automatically on Windows.

```
Services are running!
  Perplexity Wrapper: http://localhost:8000
  LiteLLM Proxy: http://localhost:8080

Press Ctrl+C to stop services...
Logs are saved in: C:\Users\user\.claude-perplexity\logs
```

#### 3. Claude Only Mode: Launch Claude with Existing Services

```bash
python launch_claude_perplexity.py --claude-only
```

Assumes services are already running, displays available models, and launches Claude with your selection:

```
Available Models:
  1. perplexity-auto
  2. perplexity-research
  3. perplexity-sonar

Select model (1-3) or press Enter for first: _
```

#### 4. Pass Arguments to Claude

You can pass any arguments directly to Claude Code using `--`:

```bash
# Launch with a file
python launch_claude_perplexity.py -- /path/to/file.py

# Launch with a prompt
python launch_claude_perplexity.py -- -p "Write a Python script"

# Launch with model selection and message
python launch_claude_perplexity.py --claude-only -- -m "Explain this code"

# Get Claude help
python launch_claude_perplexity.py -- --help
```

## 🔧 How It Works

The launcher scripts create a complete stack:

```
┌─────────────────────────────────────────────────────┐
│                    Claude Code                      │
│   (ANTHROPIC_BASE_URL=http://localhost:8080)       │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│          LiteLLM Proxy (port 8080)                  │
│   (Maps Claude requests to available models)        │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│    Perplexity OpenAI API (port 8000)                │
│   (Handles Perplexity authentication & requests)    │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│         Perplexity AI (via web scraper)             │
└─────────────────────────────────────────────────────┘
```

### Step-by-Step Process

1. **Model Discovery**: After the Perplexity wrapper starts, the launcher queries `/v1/models` to discover available models
2. **Config Update**: The discovered models are written to `litellm_config.yaml` with proper mappings
3. **LiteLLM Start**: LiteLLM starts with the updated configuration
4. **Health Checks**: Services are health-checked before proceeding
5. **Live Output**: Tail windows open (Windows only) showing real-time service logs
6. **User Selection**: Available models are displayed and user selects one
7. **Claude Launch**: Claude Code starts with `ANTHROPIC_MODEL` set to the selected model
8. **Monitoring**: Background service monitor alerts if services go down

## 📝 Configuration

### Environment Variables

Create a `.env` file in the project directory:

```bash
# Required: Perplexity session token
PERPLEXITY_SESSION_TOKEN=your_session_token_here

# Optional
PORT=8000                    # Server port (default: 8000)
LOG_LEVEL=INFO              # Logging level (default: INFO)
ENABLE_RATE_LIMITING=true   # Enable rate limiting (default: true)
REQUESTS_PER_MINUTE=60      # Rate limit (default: 60)
CONVERSATION_TIMEOUT=3600   # Session timeout in seconds (default: 3600)
DEFAULT_MODEL=perplexity-auto  # Default model (default: perplexity-auto)
```

### Getting Your Session Token

You can obtain your session token in two ways:

#### Option 1: Automatic (CLI Tool)

```bash
get-perplexity-session-token
```

This interactive tool will:
1. Ask for your Perplexity email
2. Send a verification code to your email
3. Accept either a 6-digit code or magic link
4. Extract and display your session token
5. Optionally save it to your `.env` file

#### Option 2: Manual (Browser)

1. Log in at [perplexity.ai](https://www.perplexity.ai)
2. Open DevTools (`F12`) → Application/Storage → Cookies
3. Copy the value of `__Secure-next-auth.session-token`
4. Add to `.env`: `PERPLEXITY_SESSION_TOKEN=your_token`

## 📊 Logging and Debugging

### Log Files

All service output is automatically captured to timestamped log files in `~/.claude-perplexity/logs/`:

```
20260130_230715_Perplexity_stdout.log   # Perplexity server output
20260130_230715_Perplexity_stderr.log   # Perplexity errors
20260130_230715_LiteLLM_stdout.log      # LiteLLM proxy output
20260130_230715_LiteLLM_stderr.log      # LiteLLM errors
```

### Real-Time Tail Windows (Windows)

On Windows, tail windows automatically open showing:
- Live-updating service output
- Last 50 lines shown initially
- Auto-updates as new logs are written
- Separate windows for each service

### Service Monitoring

The launcher monitors services in the background:
- **Health Checks**: Every 30 seconds (configurable)
- **Alerts**: Notified when service goes down
- **Recovery**: Alerts when service comes back online
- **Non-intrusive**: Only shows changes, doesn't spam console

## 🐳 Docker Deployment

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

## 🛠️ Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -e .

# 2. Copy and configure .env
cp .env.example .env
# Edit .env with your session token

# 3. Run the server
python openai_server.py
```

## 📡 API Usage

The server is 100% OpenAI API compatible:

### Python

```python
import openai

client = openai.OpenAI(
    api_key="dummy",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="perplexity-auto",
    messages=[{"role": "user", "content": "What's the latest news about AI?"}]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "perplexity-auto",
    "messages": [{"role": "user", "content": "What is AI?"}]
  }'
```

## 📚 Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat completions |
| `/v1/models` | GET | List available models |
| `/v1/models/refresh` | POST | Refresh models from Perplexity |
| `/conversations` | GET | List conversations |
| `/stats` | GET | Server statistics |
| `/health` | GET | Health check |

## 🤖 Available Models

Models are automatically discovered from Perplexity. Common models include:

- `perplexity-auto` - Auto-select best model (default)
- `perplexity-sonar` - Fast responses
- `perplexity-research` - Deep research capabilities
- `perplexity-labs` - Multi-step tasks with advanced troubleshooting

Other models may be available including:
- GPT models (via Perplexity)
- Claude models (via Perplexity)
- Gemini models (via Perplexity)
- Grok models (via Perplexity)

Check available models with:
```bash
curl http://localhost:8000/v1/models
```

## 🔍 Troubleshooting

### Services Won't Start

**Problem**: Port already in use
```
Port 8000 in use but not responding
```

**Solution**: Kill the process using the port:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Claude Can't Connect

**Problem**: Claude says it can't connect to the model

**Solution**: Verify services are running:
```bash
curl http://localhost:8000/health
curl http://localhost:8080/health/readiness
```

### Model Not Available

**Problem**: Selected model doesn't work

**Solution**: Models are discovered at startup. Restart services to refresh:
```bash
python launch_claude_perplexity.py --services-only
```

### Tail Windows Don't Open (Windows)

**Problem**: Tail windows don't appear on Windows

**Solution**:
- Ensure PowerShell is installed
- Check that the log files are being created (check logs directory)
- Logs are still saved even if tail windows fail to open

### Unicode Errors on Startup

**Problem**: UnicodeEncodeError on Windows

**Solution**: This is automatically fixed - the launcher sets UTF-8 encoding. If still happening:
```bash
set PYTHONIOENCODING=utf-8
python launch_claude_perplexity.py
```

## 📋 Configuration Files

### litellm_config.yaml

Automatically generated and updated with discovered models:

```yaml
model_list:
  - model_name: perplexity-auto
    litellm_params:
      model: openai/perplexity-auto
      api_base: http://localhost:8000/v1
      api_key: dummy

litellm_settings:
  set_verbose: false
  drop_params: true
```

## 📖 API Documentation

### Chat Completions

```python
response = client.chat.completions.create(
    model="perplexity-auto",
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Query here"}
    ],
    temperature=0.7,
    max_tokens=2000,
    stream=False
)
```

### List Models

```python
models = client.models.list()
for model in models.data:
    print(f"- {model.id}")
```

## 📄 License

MIT

## ⚠️ Disclaimer

This is an **unofficial** implementation using internal Perplexity APIs. Use at your own risk.

By using this project, you agree to Perplexity AI's Terms of Service.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔗 References

- [Perplexity WebUI Scraper](https://github.com/henrique-coder/perplexity-webui-scraper)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Claude Code Documentation](https://claude.ai/claude-code)
