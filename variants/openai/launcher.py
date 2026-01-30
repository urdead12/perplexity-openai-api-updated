"""
OpenAI Variant Launcher
Starts only the Perplexity OpenAI-compatible API server
No LiteLLM proxy needed - use OpenAI client directly
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)
    except (AttributeError, RuntimeError):
        pass

# Add parent directory to path to import shared modules
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from variants.shared.config import ServerConfig
from variants.shared.server import run_server


class Colors:
    """ANSI color codes"""
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    OKCYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_status(service, status, message=""):
    """Print service status"""
    if status == "running":
        symbol = "✓"
        color = Colors.OKGREEN
    elif status == "starting":
        symbol = "→"
        color = Colors.OKCYAN
    elif status == "stopped":
        symbol = "■"
        color = Colors.WARNING
    else:
        symbol = "✗"
        color = Colors.FAIL

    msg = f"{color}{symbol} {service}{Colors.ENDC}"
    if message:
        msg += f" - {message}"
    print(msg)


def print_banner():
    """Print startup banner"""
    print()
    print(f"{Colors.OKGREEN}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{Colors.BOLD}Perplexity OpenAI API Server (OpenAI Variant){Colors.ENDC}")
    print(f"{Colors.OKGREEN}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print()
    print(f"{Colors.OKCYAN}This variant provides direct OpenAI API compatibility.{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Use any OpenAI client to connect to http://localhost:8000{Colors.ENDC}")
    print()


def print_usage_examples():
    """Print usage examples"""
    print()
    print(f"{Colors.BOLD}Usage Examples:{Colors.ENDC}")
    print()

    print(f"{Colors.OKCYAN}Python (using OpenAI SDK):{Colors.ENDC}")
    print("""
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
""")

    print(f"{Colors.OKCYAN}cURL:{Colors.ENDC}")
    print("""
    curl http://localhost:8000/v1/chat/completions \\
      -H "Content-Type: application/json" \\
      -d '{
        "model": "perplexity-auto",
        "messages": [{"role": "user", "content": "Hello!"}]
      }'
""")

    print(f"{Colors.OKCYAN}Node.js (using OpenAI SDK):{Colors.ENDC}")
    print("""
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
""")

    print()
    print(f"{Colors.BOLD}Available Models:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  - perplexity-auto    (Best model, auto-selected){Colors.ENDC}")
    print(f"{Colors.OKCYAN}  - perplexity-sonar   (Fast queries){Colors.ENDC}")
    print(f"{Colors.OKCYAN}  - perplexity-research (Deep research){Colors.ENDC}")
    print(f"{Colors.OKCYAN}  - perplexity-labs    (Experimental features){Colors.ENDC}")
    print(f"{Colors.OKCYAN}  - Plus many more! Use GET /v1/models to list all{Colors.ENDC}")
    print()

    print(f"{Colors.BOLD}API Endpoints:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  GET  /health                  - Health check{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  GET  /v1/models               - List available models{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  POST /v1/chat/completions     - Chat completions (streaming supported){Colors.ENDC}")
    print(f"{Colors.OKCYAN}  POST /v1/completions          - Legacy completions{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  GET  /conversations           - List active conversations{Colors.ENDC}")
    print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Perplexity OpenAI API Server (OpenAI Variant)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This variant provides an OpenAI-compatible API for Perplexity AI.
No LiteLLM proxy needed - use OpenAI client directly!

Environment Variables:
  PERPLEXITY_SESSION_TOKEN  (required) - Your Perplexity session token
  PORT                      (optional) - Server port (default: 8000)
  HOST                      (optional) - Server host (default: 0.0.0.0)
  LOG_LEVEL                 (optional) - Logging level (default: INFO)
  OPENAI_API_KEY            (optional) - API key for authentication

Examples:
  # Start server with environment variables
  export PERPLEXITY_SESSION_TOKEN='your_token_here'
  python -m variants.openai.launcher

  # Start server and show usage examples
  python -m variants.openai.launcher --examples

  # Start on custom port
  PORT=9000 python -m variants.openai.launcher
        """
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show usage examples after starting server"
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Don't show startup banner"
    )

    args = parser.parse_args()

    # Print banner
    if not args.no_banner:
        print_banner()

    # Check for session token
    if not os.getenv("PERPLEXITY_SESSION_TOKEN"):
        print(f"{Colors.FAIL}❌ Error: PERPLEXITY_SESSION_TOKEN environment variable is required{Colors.ENDC}")
        print()
        print(f"{Colors.BOLD}To get your session token:{Colors.ENDC}")
        print("1. Log in at https://www.perplexity.ai")
        print("2. Open DevTools (F12) → Application → Cookies")
        print("3. Copy the '__Secure-next-auth.session-token' value")
        print("4. Set it: export PERPLEXITY_SESSION_TOKEN='your_token'")
        print()
        sys.exit(1)

    # Show usage examples if requested
    if args.examples:
        print_usage_examples()

    try:
        print(f"{Colors.OKCYAN}Starting Perplexity OpenAI API Server...{Colors.ENDC}")
        print()

        # Load config from environment
        config = ServerConfig.from_env()

        # Show configuration
        print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
        print(f"  Host: {config.host}")
        print(f"  Port: {config.port}")
        print(f"  Log Level: {config.log_level}")
        print(f"  Rate Limiting: {'Enabled' if config.enable_rate_limiting else 'Disabled'}")
        print(f"  API Key Auth: {'Yes' if config.api_key else 'No'}")
        print()

        # Run the server (this blocks)
        run_server(config)

    except KeyboardInterrupt:
        print()
        print(f"{Colors.WARNING}Server stopped by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
