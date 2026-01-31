# Scripts Documentation

Complete reference for all scripts in the Perplexity OpenAI API project.

## 🚀 Quick Reference

| Script | Purpose | Variant | Location |
|--------|---------|---------|----------|
| `perplexity_setup.py` | Interactive setup CLI | Both | Root |
| `install_claude_perplexity.py` | Claude installer | Claude | Root |
| `launch_claude_perplexity.py` | Claude launcher | Claude | Root |
| `install_opencode_perplexity.py` | OpenCode installer | OpenCode | `setup/opencode/` |
| `launch_opencode_perplexity.py` | OpenCode launcher | OpenCode | `setup/opencode/` |
| `openai_server.py` | API server | Core | Root |
| `fetch_models.py` | Model discovery | Utility | Root |

---

## 📋 Main Entry Point

### `perplexity_setup.py`

**Interactive Setup CLI** - Choose and configure either variant through a menu system.

```bash
python perplexity_setup.py
```

**Features**:
- Choose between Claude Code or OpenCode
- Install dependencies
- Launch services
- View information
- User-friendly menus

**When to use**: First-time setup or guided experience

---

## 🔧 Claude Code Variant

### Installation: `install_claude_perplexity.py`

**Complete installation with state tracking and validation**.

```bash
python install_claude_perplexity.py
```

**Process**:
1. ✅ Python 3.10+ check
2. ✅ Git check (optional)
3. ✅ Create `~/.claude-perplexity/`
4. ✅ Prompt for Perplexity token
5. ✅ Create virtual environment
6. ✅ Install FastAPI, LiteLLM, dependencies
7. ✅ Clone repository
8. ✅ Install perplexity-webui-scraper
9. ✅ Create `.env` file
10. ✅ Create LiteLLM config
11. ✅ Validate installation

**State Tracking**: Resumes from last successful stage if interrupted.

**Output**: `~/.claude-perplexity/` directory

---

### Launcher: `launch_claude_perplexity.py`

**Starts services, discovers models, launches Claude Code**.

```bash
# Default: Start everything
python launch_claude_perplexity.py

# Services only (keep running)
python launch_claude_perplexity.py --services-only

# Claude only (existing services)
python launch_claude_perplexity.py --claude-only

# Pass arguments to Claude
python launch_claude_perplexity.py -- <args>
```

**Default Mode Process**:
1. ✅ Check ports 8000/8080
2. ✅ Create log manager
3. ✅ Start Perplexity server (8000)
4. ✅ Fetch available models
5. ✅ Update litellm_config.yaml
6. ✅ Start LiteLLM proxy (8080)
7. ✅ Open tail windows (Windows)
8. ✅ Start health monitoring
9. ✅ Show model selection
10. ✅ Launch Claude Code

**Debugging**:
- Log files in `~/.claude-perplexity/logs/`
- Live tail windows (Windows)
- Background health monitoring
- Automatic alerts

---

## 🎯 OpenCode Variant

### Installation: `setup/opencode/install_opencode_perplexity.py`

**Simpler installation for OpenCode (no LiteLLM)**.

```bash
python setup/opencode/install_opencode_perplexity.py
```

**Process**:
1. ✅ Python 3.10+ check
2. ✅ Git check (optional)
3. ✅ Create `~/.opencode-perplexity/`
4. ✅ Prompt for Perplexity token
5. ✅ Create virtual environment
6. ✅ Install FastAPI, dependencies (no LiteLLM)
7. ✅ Clone repository
8. ✅ Install perplexity-webui-scraper
9. ✅ Create `.env` file
10. ✅ Check/install OpenCode CLI
11. ✅ Create OpenCode config

**OpenCode Config**: `~/.config/opencode/opencode.json`

**Output**: `~/.opencode-perplexity/` directory

---

### Launcher: `setup/opencode/launch_opencode_perplexity.py`

**Starts server, discovers models, launches OpenCode**.

```bash
# Default: Start everything
python setup/opencode/launch_opencode_perplexity.py

# Server only (keep running)
python setup/opencode/launch_opencode_perplexity.py --server-only

# OpenCode only (existing server)
python setup/opencode/launch_opencode_perplexity.py --opencode-only

# Pass arguments to OpenCode
python setup/opencode/launch_opencode_perplexity.py -- <args>
```

**Default Mode Process**:
1. ✅ Check port 8000
2. ✅ Create log manager
3. ✅ Start Perplexity server (8000)
4. ✅ Start health monitoring
5. ✅ Fetch available models
6. ✅ Update OpenCode config
7. ✅ Open tail window (Windows)
8. ✅ Launch OpenCode

**Debugging**:
- Log files in `~/.opencode-perplexity/logs/`
- Live tail window (Windows)
- Background health monitoring

---

## 🔑 Core Components

### `openai_server.py`

**FastAPI server providing OpenAI-compatible API**.

```bash
# Direct usage (not recommended)
python openai_server.py
```

**Endpoints**:
- `GET /health` - Health check
- `GET /v1/models` - List models
- `POST /v1/chat/completions` - Chat
- `POST /v1/completions` - Legacy
- `GET /conversations` - List conversations
- `POST /v1/models/refresh` - Refresh models

**Use launchers instead** for proper setup.

---

### `fetch_models.py`

**Utility to discover and display Perplexity models**.

```bash
python fetch_models.py
```

**Output**: List of available models

**When to use**: Debugging or checking models

---

## 🛠️ Shared Utilities

### `setup/common/utils.py`

**Installation utilities for both variants**.

**Key Classes**:
- `InstallationState` - State tracking
- `InstallationStage` - Stage management
- `Colors` - Terminal colors

**Key Functions**:
- `check_python_version()`
- `create_venv()`
- `install_pip_package()`
- `clone_repository()`
- `get_perplexity_token()`

---

### `setup/common/launcher_utils.py`

**Launcher and debugging utilities**.

**Key Classes**:
- `LogManager` - Log file management
- `ServiceMonitor` - Health monitoring

**Key Functions**:
- `start_perplexity_server()`
- `check_service_health()`
- `is_port_in_use()`
- `fetch_available_models()`

---

## 🐛 Debugging Features

### Log Files

**All variants create timestamped logs**:

```
~/.{variant}-perplexity/logs/
├── YYYYMMDD_HHMMSS_Perplexity_stdout.log
├── YYYYMMDD_HHMMSS_Perplexity_stderr.log
├── YYYYMMDD_HHMMSS_LiteLLM_stdout.log  (Claude only)
└── YYYYMMDD_HHMMSS_LiteLLM_stderr.log  (Claude only)
```

### Live Tail Windows (Windows)

**PowerShell windows showing real-time output**:
- Last 50 lines initially
- Auto-updates as logs grow
- Separate window per service

### Service Monitoring

**Background health checks**:
- Every 30 seconds
- Alerts when down
- Recovery notifications
- Non-intrusive

---

## 📝 Command Reference

### Installation
```bash
python perplexity_setup.py                           # Interactive
python install_claude_perplexity.py                  # Claude
python setup/opencode/install_opencode_perplexity.py # OpenCode
```

### Launching (Full Stack)
```bash
python launch_claude_perplexity.py                   # Claude
python setup/opencode/launch_opencode_perplexity.py  # OpenCode
```

### Server Only
```bash
python launch_claude_perplexity.py --services-only   # Claude
python setup/opencode/launch_opencode_perplexity.py --server-only  # OpenCode
```

### CLI Only (Existing Server)
```bash
python launch_claude_perplexity.py --claude-only     # Claude
python setup/opencode/launch_opencode_perplexity.py --opencode-only  # OpenCode
```

### Utilities
```bash
python fetch_models.py                               # List models
curl http://localhost:8000/v1/models                 # API models
curl http://localhost:8000/health                    # Health check
```

---

## 🔍 Troubleshooting

### View Installation State

```bash
# Claude
cat ~/.claude-perplexity/install_state.json

# OpenCode
cat ~/.opencode-perplexity/install_state.json
```

### View Logs

```bash
# Claude
ls ~/.claude-perplexity/logs/
tail -f ~/.claude-perplexity/logs/<latest>

# OpenCode
ls ~/.opencode-perplexity/logs/
tail -f ~/.opencode-perplexity/logs/<latest>
```

### Manual Server Start

```bash
cd ~/.opencode-perplexity/perplexity-openai-api-updated
source ../venv/bin/activate
python openai_server.py
```

---

## 📊 Architecture Comparison

### Claude Code
```
Claude → LiteLLM (8080) → Perplexity (8000) → Perplexity.ai
```

**Components**: 3 (Claude + LiteLLM + Perplexity)
**Ports**: 2 (8000 + 8080)
**Logs**: 4 files (2 services × 2 streams)

### OpenCode
```
OpenCode → Perplexity (8000) → Perplexity.ai
```

**Components**: 2 (OpenCode + Perplexity)
**Ports**: 1 (8000)
**Logs**: 2 files (1 service × 2 streams)

---

For detailed documentation:
- [README.md](README.md) - Main documentation
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [README_VARIANTS.md](README_VARIANTS.md) - Variant comparison
