# Quick Start Guide

Get up and running with Perplexity AI coding assistant in 5 minutes!

## Step 1: Get Your Session Token

1. Go to [perplexity.ai](https://www.perplexity.ai) and log in
2. Press `F12` to open Developer Tools
3. Go to: Application → Cookies → https://www.perplexity.ai
4. Copy the value of `__Secure-next-auth.session-token`
5. Save this token - you'll need it in step 3

## Step 2: Choose Your Variant

### Option A: OpenCode (Recommended for new users)

**Why OpenCode?**
- ✅ Open source
- ✅ Simpler setup (no proxy)
- ✅ Uses only one port (8000)

```bash
# Run the unified setup
python perplexity_setup.py

# Select: 2 (OpenCode) → 1 (Install)
```

### Option B: Claude Code

**Why Claude Code?**
- ✅ Anthropic's official CLI
- ✅ Familiar if you already use Claude

```bash
# Run the unified setup
python perplexity_setup.py

# Select: 1 (Claude Code) → 1 (Install)
```

## Step 3: Configure

Set your session token:

```bash
export PERPLEXITY_SESSION_TOKEN='your_token_from_step_1'
```

Or add it to the `.env` file:
- **Claude**: `~/.claude-perplexity/perplexity-openai-api-updated/.env`
- **OpenCode**: `~/.opencode-perplexity/perplexity-openai-api-updated/.env`

## Step 4: Launch

### OpenCode

```bash
python perplexity_setup.py
# Select: 2 (OpenCode) → 2 (Launch)
```

Or directly:
```bash
python setup/opencode/launch_opencode_perplexity.py
```

### Claude Code

```bash
python perplexity_setup.py
# Select: 1 (Claude Code) → 2 (Launch)
```

Or directly:
```bash
python launch_claude_perplexity.py
```

## Step 5: Start Coding!

The AI coding assistant will start automatically. Try asking:

- "What does this code do?"
- "Help me refactor this function"
- "Find and fix bugs in this file"
- "Write tests for this module"

## What's Running?

### OpenCode Variant
- **Perplexity Server** on http://localhost:8000
- **OpenCode CLI** connected to the server

### Claude Code Variant
- **Perplexity Server** on http://localhost:8000
- **LiteLLM Proxy** on http://localhost:8080
- **Claude Code** connected through LiteLLM

## Available Models

Both variants automatically discover available models:

- `perplexity-auto` - Best model (recommended)
- `perplexity-sonar` - Fast queries
- `perplexity-research` - Deep research
- `perplexity-labs` - Experimental
- Plus: GPT-5.x, Claude 4.5, Gemini 3, Grok 4.1

## Troubleshooting

### "PERPLEXITY_SESSION_TOKEN not set"

Make sure you exported it:
```bash
export PERPLEXITY_SESSION_TOKEN='your_token'
```

Or add it to your `.env` file.

### "Port already in use"

Another service is using port 8000 or 8080. Stop it or use a different port:

```bash
# For OpenCode
PORT=9000 python setup/opencode/launch_opencode_perplexity.py
```

### "OpenCode/Claude not found"

Install the CLI:

**OpenCode:**
```bash
curl -fsSL https://opencode.ai/install | bash
# or
npm i -g opencode-ai@latest
```

**Claude Code:**
Follow [Claude Code installation guide](https://claude.ai/code)

### Server won't start

Check your session token hasn't expired. Get a fresh one from perplexity.ai.

## Next Steps

- Read [README_VARIANTS.md](README_VARIANTS.md) for detailed documentation
- Check [OpenCode docs](https://opencode.ai/docs) or [Claude Code docs](https://claude.ai/code)
- Explore available models: `curl http://localhost:8000/v1/models`

## Advanced Usage

### Server-Only Mode

Run just the server without the CLI:

```bash
# OpenCode
python setup/opencode/launch_opencode_perplexity.py --server-only

# Claude Code
python launch_claude_perplexity.py --services-only
```

Then use with any OpenAI-compatible client:

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

### Use with Your Own Code

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

# Ask a question
response = client.chat.completions.create(
    model="perplexity-research",  # Use research mode
    messages=[
        {"role": "user", "content": "Explain async/await in Python"}
    ]
)

print(response.choices[0].message.content)
```

```python
# Streaming example
stream = client.chat.completions.create(
    model="perplexity-auto",
    messages=[{"role": "user", "content": "Tell me about FastAPI"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

**Need help?** Open an issue on GitHub or check the full documentation in [README_VARIANTS.md](README_VARIANTS.md).
