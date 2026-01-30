"""Server configuration"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

# Add src to path for local development
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(script_dir, "src"))

from perplexity_webui_scraper import CitationMode


@dataclass
class ServerConfig:
    """Server configuration loaded from environment variables."""

    session_token: str
    api_key: str | None = None
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # Rate Limiting
    requests_per_minute: int = 60
    enable_rate_limiting: bool = True

    # Conversations
    conversation_timeout: int = 3600
    max_conversations_per_user: int = 100

    # Defaults
    default_model: str = "perplexity-auto"
    default_citation_mode: CitationMode = CitationMode.CLEAN

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        session_token = os.getenv("PERPLEXITY_SESSION_TOKEN")
        if not session_token:
            session_token = os.environ.get("PERPLEXITY_SESSION_TOKEN")

        if not session_token:
            print("❌ Error: PERPLEXITY_SESSION_TOKEN environment variable is required")
            print("\n📋 To get your session token:")
            print("1. Log in at https://www.perplexity.ai")
            print("2. Open DevTools (F12) → Application → Cookies")
            print("3. Copy the '__Secure-next-auth.session-token' value")
            print("4. Set it: export PERPLEXITY_SESSION_TOKEN='your_token'")
            sys.exit(1)

        return cls(
            session_token=session_token,
            api_key=os.getenv("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            requests_per_minute=int(os.getenv("REQUESTS_PER_MINUTE", "60")),
            enable_rate_limiting=os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
            conversation_timeout=int(os.getenv("CONVERSATION_TIMEOUT", "3600")),
            max_conversations_per_user=int(os.getenv("MAX_CONVERSATIONS_PER_USER", "100")),
            default_model=os.getenv("DEFAULT_MODEL", "perplexity-auto"),
            default_citation_mode=CitationMode[os.getenv("DEFAULT_CITATION_MODE", "CLEAN").upper()],
        )
