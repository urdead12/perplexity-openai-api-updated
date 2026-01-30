#!/usr/bin/env python3
"""
Perplexity OpenAI-compatible API Server
Main entry point - now uses modular shared components

This file maintains backwards compatibility with the original openai_server.py
but now uses the refactored modular architecture.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add variants directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from variants.shared.config import ServerConfig
from variants.shared.server import run_server


if __name__ == "__main__":
    # Load configuration from environment
    config = ServerConfig.from_env()

    # Run the server using the shared implementation
    run_server(config)
