# Quick Start Guide

Get started with Perplexity OpenAI API in under 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Perplexity.ai account
- Your Perplexity session token

## Get Your Session Token

1. Log in to [perplexity.ai](https://www.perplexity.ai)
2. Open DevTools (press F12)
3. Go to: Application → Cookies → https://www.perplexity.ai
4. Copy the value of `__Secure-next-auth.session-token`

## Choose Your Path

### Path 1: OpenAI Variant (Recommended for most users)

**Use this if you want to:**
- Use Perplexity with Python/Node.js/any OpenAI client
- Integrate with existing OpenAI-based applications
- Keep it simple

**Steps:**

```bash
# 1. Clone or download this repository
cd perplexity-openai-api-updated

# 2. Install dependencies
pip install fastapi uvicorn pydantic slowapi curl_cffi python-dotenv
pip install -e .

# 3. Set your session token
export PERPLEXITY_SESSION_TOKEN='your_token_here'

# 4. Start the server
python variants/openai/launcher.py
```

**Use it:**

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

print(response.choices[0].message.content)
```

### Path 2: Claude Code Variant

**Use this if you want to:**
- Use Perplexity with Claude Code CLI
- Existing Claude Code workflow

**Steps:**

```bash
# 1. Clone or download this repository
cd perplexity-openai-api-updated

# 2. Install
python install_claude_perplexity.py

# 3. Set your session token
export PERPLEXITY_SESSION_TOKEN='your_token_here'

# 4. Launch
python launch_claude_perplexity.py
```

## Using the Unified CLI

For an interactive experience:

```bash
python perplexity_cli.py
```

This menu-driven interface lets you:
- Choose between variants
- Install dependencies
- Launch servers
- View usage examples

## Testing Your Setup

### Test OpenAI Variant

```bash
# Start the server
python variants/openai/launcher.py

# In another terminal, test with curl
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "perplexity-auto",
    "messages": [{"role": "user", "content": "Say hello!"}]
  }'
```

### Test Claude Code Variant

```bash
# Launch (starts services + Claude)
python launch_claude_perplexity.py

# Claude Code should start automatically
# Try asking: "What's the weather like today?"
```

## Next Steps

- Read [VARIANTS_README.md](VARIANTS_README.md) for detailed documentation
- Explore available models: `curl http://localhost:8000/v1/models`
- Check server health: `curl http://localhost:8000/health`
- View API docs (when server is running): http://localhost:8000/docs

## Common Issues

### "PERPLEXITY_SESSION_TOKEN not set"

Set the environment variable:

```bash
export PERPLEXITY_SESSION_TOKEN='your_token_here'
```

Or create a `.env` file:

```env
PERPLEXITY_SESSION_TOKEN=your_token_here
```

### "Port already in use"

Change the port:

```bash
PORT=9000 python variants/openai/launcher.py
```

### "Module not found"

Install dependencies:

```bash
pip install -e .
pip install fastapi uvicorn pydantic slowapi curl_cffi python-dotenv
```

## Support

- 📖 Full documentation: [VARIANTS_README.md](VARIANTS_README.md)
- 🐛 Report issues: GitHub Issues
- 💬 Questions: GitHub Discussions

## Example Use Cases

### Python Script

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"
)

# Simple query
response = client.chat.completions.create(
    model="perplexity-research",  # Use research mode
    messages=[{"role": "user", "content": "Latest AI news?"}]
)

print(response.choices[0].message.content)
```

### Streaming Response

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

stream = client.chat.completions.create(
    model="perplexity-auto",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### LangChain Integration

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy",
    model="perplexity-auto"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "{input}")
])

chain = prompt | llm

response = chain.invoke({"input": "What's new in AI?"})
print(response.content)
```

---

Happy coding! 🚀
