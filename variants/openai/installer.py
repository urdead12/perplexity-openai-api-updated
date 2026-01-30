"""
OpenAI Variant Installer
Simple installer for the OpenAI variant
"""

import os
import sys
import subprocess
from pathlib import Path

class Colors:
    """ANSI color codes"""
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    OKCYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_status(message, status="info"):
    """Print status message"""
    if status == "success":
        print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")
    elif status == "error":
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")
    elif status == "warning":
        print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")
    else:
        print(f"{Colors.OKCYAN}→ {message}{Colors.ENDC}")


def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_status(f"Python 3.8+ is required. You have {version.major}.{version.minor}", "error")
        return False
    print_status(f"Python {version.major}.{version.minor}.{version.micro} detected", "success")
    return True


def install_dependencies():
    """Install required dependencies"""
    print()
    print_status("Installing dependencies...")

    requirements = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "slowapi",
        "curl_cffi",
        "python-dotenv",
    ]

    # Install perplexity-webui-scraper from local source
    print_status("Installing perplexity-webui-scraper from local source...")
    try:
        repo_root = Path(__file__).parent.parent.parent
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(repo_root)],
            check=True,
            capture_output=True
        )
        print_status("Installed perplexity-webui-scraper", "success")
    except subprocess.CalledProcessError as e:
        print_status(f"Failed to install perplexity-webui-scraper: {e}", "error")
        return False

    # Install other requirements
    for package in requirements:
        print_status(f"Installing {package}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                capture_output=True
            )
            print_status(f"Installed {package}", "success")
        except subprocess.CalledProcessError as e:
            print_status(f"Failed to install {package}: {e}", "error")
            return False

    return True


def create_env_file():
    """Create .env file template"""
    print()
    print_status("Creating .env file template...")

    repo_root = Path(__file__).parent.parent.parent
    env_file = repo_root / ".env.openai"

    if env_file.exists():
        print_status(".env.openai already exists", "warning")
        return True

    env_content = """# Perplexity OpenAI API Configuration (OpenAI Variant)

# Required: Your Perplexity session token
# Get this from browser cookies after logging in to perplexity.ai
PERPLEXITY_SESSION_TOKEN=your_token_here

# Optional: Server configuration
# PORT=8000
# HOST=0.0.0.0
# LOG_LEVEL=INFO

# Optional: API key authentication
# OPENAI_API_KEY=your_api_key_here

# Optional: Rate limiting
# ENABLE_RATE_LIMITING=true
# REQUESTS_PER_MINUTE=60

# Optional: Conversation settings
# CONVERSATION_TIMEOUT=3600
# MAX_CONVERSATIONS_PER_USER=100

# Optional: Defaults
# DEFAULT_MODEL=perplexity-auto
# DEFAULT_CITATION_MODE=CLEAN
"""

    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print_status(f"Created {env_file}", "success")
        return True
    except Exception as e:
        print_status(f"Failed to create .env file: {e}", "error")
        return False


def print_next_steps():
    """Print next steps for the user"""
    print()
    print(f"{Colors.BOLD}{Colors.OKGREEN}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}Installation Complete!{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}{'=' * 70}{Colors.ENDC}")
    print()

    print(f"{Colors.BOLD}Next Steps:{Colors.ENDC}")
    print()

    print("1. Get your Perplexity session token:")
    print("   - Log in at https://www.perplexity.ai")
    print("   - Open DevTools (F12) → Application → Cookies")
    print("   - Copy the '__Secure-next-auth.session-token' value")
    print()

    print("2. Set the session token:")
    print(f"   {Colors.OKCYAN}export PERPLEXITY_SESSION_TOKEN='your_token_here'{Colors.ENDC}")
    print("   Or edit .env.openai file")
    print()

    print("3. Start the server:")
    print(f"   {Colors.OKCYAN}python -m variants.openai.launcher{Colors.ENDC}")
    print("   Or:")
    print(f"   {Colors.OKCYAN}python variants/openai/launcher.py{Colors.ENDC}")
    print()

    print("4. Use with OpenAI SDK:")
    print("""
   from openai import OpenAI

   client = OpenAI(
       base_url="http://localhost:8000/v1",
       api_key="dummy"
   )

   response = client.chat.completions.create(
       model="perplexity-auto",
       messages=[{"role": "user", "content": "Hello!"}]
   )
""")

    print(f"{Colors.BOLD}Documentation:{Colors.ENDC}")
    print("  - API Docs: http://localhost:8000/docs (after starting server)")
    print("  - OpenAI API Reference: https://platform.openai.com/docs/api-reference")
    print()


def main():
    """Main installer"""
    print()
    print(f"{Colors.BOLD}{Colors.OKCYAN}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}Perplexity OpenAI API Installer (OpenAI Variant){Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}{'=' * 70}{Colors.ENDC}")
    print()

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Create env file
    if not create_env_file():
        sys.exit(1)

    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
