# Claude Code + Perplexity Integration Scripts

Two Python scripts to install and run Claude Code with Perplexity backend on Windows and Unix-like systems.

## Overview

These scripts set up a proxy chain that allows Claude Code to use Perplexity's models:
- **No Docker required** - Pure Python implementation
- **Cross-platform** - Windows, Linux, macOS support
- **Automatic service management** - Checks and starts services as needed
- **Real-time monitoring** - Health checks with auto-alerts
- **Live output windows** - Real-time tail windows on Windows
- **Automatic logging** - Timestamped logs for debugging
- **Uses your Perplexity subscription** - No additional API costs

## Files

1. **install_claude_perplexity.py** - One-time installation script
2. **launch_claude_perplexity.py** - Service launcher and Claude Code starter

## Installation

### Prerequisites

- Python 3.8 or higher
- Perplexity Pro or Max account
- Claude Code installed (optional for setup, required for launch)
- PowerShell (for real-time tail windows on Windows)

### Step 1: Run Installer

```bash
python install_claude_perplexity.py
```

The installer will:
1. Check Python version
2. Create `~/.claude-perplexity/` directory
3. Create a virtual environment
4. Install Perplexity OpenAI wrapper
5. Install LiteLLM proxy
6. Create configuration files
7. Prompt for your Perplexity session token

### Getting Your Session Token

**Option 1: Automatic (after installation)**
```bash
~/.claude-perplexity/venv/Scripts/get-perplexity-session-token.exe
```

**Option 2: Manual**
1. Go to [perplexity.ai](https://perplexity.ai) and log in
2. Press F12 to open DevTools
3. Go to Application → Cookies → perplexity.ai
4. Copy the value of `__Secure-next-auth.session-token`
5. Paste when prompted by installer

### Installation Directory

Everything is installed to: `~/.claude-perplexity/`

```
.claude-perplexity/
├── venv/                          # Virtual environment
├── perplexity-openai-api/         # Wrapper code
├── litellm_config.yaml            # LiteLLM configuration (auto-generated)
├── logs/                          # Timestamped log files
├── .env                           # Session token (gitignored)
└── INSTALLATION_INFO.txt          # Installation details
```

## Usage

### Mode 1: Default - Start Everything Together

```bash
python launch_claude_perplexity.py
```

**What happens:**
1. Starts Perplexity wrapper (port 8000)
2. Discovers available models from Perplexity
3. Updates `litellm_config.yaml` with discovered models
4. Starts LiteLLM proxy (port 8080)
5. Opens live tail windows showing service output (Windows only)
6. Displays available models and asks for selection
7. Launches Claude Code with selected model
8. Monitors services in background, alerts on issues

**Output:**
```
→ Install directory: C:\Users\user\.claude-perplexity

Service Status Check

✓ Perplexity Wrapper - Ready on http://localhost:8000
→ Perplexity stdout: C:\Users\user\.claude-perplexity\logs\20260130_230715_Perplexity_stdout.log
...

Discovering Models

✓ Found 5 model(s)
  - perplexity-auto
  - perplexity-sonar
  - perplexity-research
  ...

Available Models:
  1. perplexity-auto
  2. perplexity-sonar
  3. perplexity-research

Select model (1-3) or press Enter for first: 1

Launching Claude Code with Perplexity Backend

Environment:
  ANTHROPIC_BASE_URL = http://localhost:8080
  ANTHROPIC_MODEL = perplexity-auto
```

### Mode 2: Services Only - Keep Services Running

```bash
python launch_claude_perplexity.py --services-only
```

**Perfect for:**
- Running services in one terminal
- Using Claude in another terminal
- Testing the APIs
- Keeping services running between Claude sessions

**Output:**
```
Services are running!
  Perplexity Wrapper: http://localhost:8000
  LiteLLM Proxy: http://localhost:8080

Press Ctrl+C to stop services...
Logs are saved in: C:\Users\user\.claude-perplexity\logs

Opening tail windows...
✓ Opened tail window for Perplexity
✓ Opened tail window for LiteLLM

⚠ Perplexity Wrapper is not responding          [5 sec in...]
✓ Perplexity Wrapper recovered                  [service healthy]
```

### Mode 3: Claude Only - Use Existing Services

```bash
python launch_claude_perplexity.py --claude-only
```

**Perfect for:**
- Launching Claude when services are already running
- Model re-selection
- Using different model without restarting services

**Output:**
```
Available Models:
  1. perplexity-auto
  2. perplexity-sonar
  3. perplexity-research

Select model (1-3) or press Enter for first: 2

✓ Selected model: perplexity-sonar

Launching Claude Code with Perplexity Backend

Environment:
  ANTHROPIC_BASE_URL = http://localhost:8080
  ANTHROPIC_MODEL = perplexity-sonar
```

### Mode 4: Pass Arguments to Claude

You can pass any Claude Code arguments using `--` separator:

```bash
# Launch with a file
python launch_claude_perplexity.py -- /path/to/file.py

# Launch with a prompt
python launch_claude_perplexity.py -- -p "Write a Python script"

# Multiple arguments with model selection
python launch_claude_perplexity.py --claude-only -- -m "Explain this code"

# Get Claude help
python launch_claude_perplexity.py -- --help

# With spaces in arguments
python launch_claude_perplexity.py -- -p "Write a hello world script"
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Claude Code                      │
│   (ANTHROPIC_BASE_URL=http://localhost:8080)       │
│   (ANTHROPIC_MODEL=selected-model)                  │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│          LiteLLM Proxy (port 8080)                  │
│   (Translates Anthropic ↔ OpenAI formats)          │
│   (Routes to Perplexity wrapper)                    │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│    Perplexity OpenAI API (port 8000)                │
│   (Wraps Perplexity in OpenAI-compatible API)       │
│   (Handles authentication & web scraping)           │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│         Perplexity AI (via web scraper)             │
│   (Uses your Pro/Max subscription)                  │
└─────────────────────────────────────────────────────┘
```

## Logging and Debugging

### Log Files

All service output is automatically saved with timestamps:

```
~/.claude-perplexity/logs/

20260130_230715_Perplexity_stdout.log    # Perplexity server output
20260130_230715_Perplexity_stderr.log    # Perplexity errors
20260130_230715_LiteLLM_stdout.log       # LiteLLM proxy output
20260130_230715_LiteLLM_stderr.log       # LiteLLM errors
```

**View logs:**
```bash
# Windows PowerShell
Get-Content -Path "$env:USERPROFILE\.claude-perplexity\logs\*_stdout.log" -Tail 100

# Linux/macOS
tail -f ~/.claude-perplexity/logs/*_stdout.log
```

### Real-Time Tail Windows (Windows)

On Windows, tail windows automatically open showing:
- **Live output** - Updates in real-time as logs are written
- **Last 50 lines** - Initial context showing previous activity
- **Separate windows** - One for each service
- **Auto-closing** - Close when service stops

### Service Health Monitoring

The launcher monitors services every 30 seconds:

**Status messages:**
```
⚠ Perplexity Wrapper is not responding       [Service detected unhealthy]
✓ Perplexity Wrapper recovered               [Service recovered]
✗ LiteLLM Proxy process died (code: 1)       [Process crashed]
```

Non-intrusive alerts - only shown on state changes!

## Model Mapping

The launcher automatically discovers models from Perplexity and creates entries in `litellm_config.yaml`:

```yaml
model_list:
  - model_name: perplexity-auto
    litellm_params:
      model: openai/perplexity-auto
      api_base: http://localhost:8000/v1
      api_key: dummy

  - model_name: perplexity-sonar
    litellm_params:
      model: openai/perplexity-sonar
      api_base: http://localhost:8000/v1
      api_key: dummy

  - model_name: perplexity-research
    litellm_params:
      model: openai/perplexity-research
      api_base: http://localhost:8000/v1
      api_key: dummy
```

**Common Models:**
- `perplexity-auto` - Best model auto-selection
- `perplexity-sonar` - Fast responses
- `perplexity-research` - Research with deep web search
- `perplexity-labs` - Advanced troubleshooting

## Configuration

### Environment Variables

Create or edit `~/.claude-perplexity/.env`:

```bash
# Required
PERPLEXITY_SESSION_TOKEN=your_token_here

# Optional
PORT=8000
LOG_LEVEL=INFO
ENABLE_RATE_LIMITING=true
REQUESTS_PER_MINUTE=60
CONVERSATION_TIMEOUT=3600
DEFAULT_MODEL=perplexity-auto
PYTHONIOENCODING=utf-8
```

### Change Service Ports

Edit `.env`:
```bash
PORT=9000  # Change Perplexity wrapper port
```

Then restart launcher.

## Troubleshooting

### "Installation directory not found"

Run the installer:
```bash
python install_claude_perplexity.py
```

### "Port 8000 already in use"

Another process is using the port:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/macOS
lsof -ti:8000 | xargs kill -9
```

### "Invalid session token"

Your token expired. Get a new one:
```bash
python install_claude_perplexity.py
# Or manually update .env with new token
```

### Tail windows don't open (Windows)

- Check PowerShell is installed
- Logs are still saved (check `logs/` directory)
- Try running from PowerShell instead of Command Prompt

### Services won't start

Check the error logs:
```bash
cat ~/.claude-perplexity/logs/*_stderr.log
```

**Common issues:**
- Missing PERPLEXITY_SESSION_TOKEN
- Port already in use
- Invalid session token
- Network issues

### Unicode/Encoding errors

Automatically handled by launcher, but if needed:
```bash
set PYTHONIOENCODING=utf-8
python launch_claude_perplexity.py
```

### Claude Code not found

The launcher will still start services. Options:
- Install Claude Code and run launcher again
- Use the APIs directly from other tools

### Check service health

```bash
# Perplexity Wrapper
curl http://localhost:8000/health

# LiteLLM Proxy
curl http://localhost:8080/health/readiness

# List available models
curl http://localhost:8000/v1/models
```

## Advanced Usage

### Run services permanently

```bash
python launch_claude_perplexity.py --services-only

# In another terminal, keep using Claude
python launch_claude_perplexity.py --claude-only
```

### Use with other tools

The services can be used with any OpenAI or Anthropic-compatible client:

**OpenAI format (direct to wrapper):**
```python
from openai import OpenAI

client = OpenAI(
    api_key="dummy",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="perplexity-auto",
    messages=[{"role": "user", "content": "Latest AI news"}]
)
print(response.choices[0].message.content)
```

**Anthropic format (via LiteLLM):**
```python
import anthropic

client = anthropic.Anthropic(
    api_key="dummy",
    base_url="http://localhost:8080"
)

message = client.messages.create(
    model="perplexity-auto",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Latest AI news"}]
)
print(message.content[0].text)
```

### Environment Variables for Claude

The launcher automatically sets:
- `ANTHROPIC_BASE_URL=http://localhost:8080`
- `ANTHROPIC_API_KEY=dummy`
- `ANTHROPIC_MODEL=<selected-model>`

Override them:
```bash
# Windows
set ANTHROPIC_MODEL=perplexity-research
python launch_claude_perplexity.py

# Linux/macOS
export ANTHROPIC_MODEL=perplexity-research
python launch_claude_perplexity.py
```

## Uninstall

```bash
# Windows
rmdir /s %USERPROFILE%\.claude-perplexity

# Linux/macOS
rm -rf ~/.claude-perplexity
```

## Security Notes

- Session tokens stored locally in `~/.claude-perplexity/.env`
- Services run only on localhost (not accessible from network)
- No data sent to external services except Perplexity
- All connections are local and encrypted (HTTPS to Perplexity)

## Limitations

- Requires active Perplexity Pro/Max subscription
- Subject to Perplexity's usage limits
- Session tokens expire periodically (need refresh)
- Unofficial implementation (may break with Perplexity updates)

## Support

For issues with:
- **These scripts**: Create an issue or modify locally
- **Perplexity wrapper**: https://github.com/henrique-coder/perplexity-webui-scraper
- **LiteLLM**: https://docs.litellm.ai/
- **Claude Code**: Claude Code support channels

## License

MIT License - Feel free to modify and distribute

## Credits

- [henrique-coder/perplexity-webui-scraper](https://github.com/henrique-coder/perplexity-webui-scraper) - Base scraper
- [BerriAI/litellm](https://github.com/BerriAI/litellm) - API proxy/translation
