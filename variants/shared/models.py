"""Model registry and management"""

from __future__ import annotations

import logging
import os
import re
import sys
from datetime import datetime

# Add src to path for local development
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(script_dir, "src"))

from perplexity_webui_scraper import Models
from perplexity_webui_scraper.models import Model

# Import from the parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from fetch_models import ModelInfo as FetchedModelInfo
from fetch_models import PerplexityModelsFetcher


class ModelRegistry:
    """Manages available models fetched from Perplexity."""

    def __init__(self):
        self._models: list[FetchedModelInfo] = []
        self._mapping: dict[str, Model] = {}
        self._available: list[dict[str, str]] = []
        self._last_fetch: datetime | None = None
        self._refresh_interval = 3600  # 1 hour

    def fetch(self, session_token: str) -> None:
        """Fetch available models from Perplexity."""
        logging.info("🔄 Fetching models from Perplexity...")

        try:
            with PerplexityModelsFetcher(session_token) as fetcher:
                self._models = fetcher.fetch_models()

            self._build_mappings()
            self._last_fetch = datetime.now()
            logging.info(f"✅ Loaded {len(self._models)} models")

        except Exception as e:
            logging.error(f"❌ Failed to fetch models: {e}")
            self._use_defaults()

    def _build_mappings(self) -> None:
        """Build model mappings and available list."""
        # Static aliases
        self._mapping = {
            "gpt-4": Models.BEST,
            "gpt-4-turbo": Models.BEST,
            "gpt-4o": Models.BEST,
            "perplexity": Models.BEST,
            "perplexity-auto": Models.BEST,
            "auto": Models.BEST,
            "perplexity-sonar": Models.SONAR,
            "perplexity-research": Models.RESEARCH,
            "perplexity-labs": Models.LABS,
            "sonar": Models.SONAR,
            "research": Models.RESEARCH,
            "labs": Models.LABS,
        }

        self._available = [
            {"id": "perplexity-auto", "name": "Perplexity Auto", "owned_by": "perplexity"},
            {"id": "perplexity-sonar", "name": "Perplexity Sonar", "owned_by": "perplexity"},
            {"id": "perplexity-research", "name": "Perplexity Research", "owned_by": "perplexity"},
            {"id": "perplexity-labs", "name": "Perplexity Labs", "owned_by": "perplexity"},
        ]

        # Add fetched models
        for model in self._models:
            model_obj = Model(identifier=model.identifier, mode=model.mode)

            # Add direct identifier
            self._mapping[model.identifier.lower()] = model_obj

            # Add aliases
            for alias in self._generate_aliases(model.identifier):
                self._mapping[alias.lower()] = model_obj

            # Add to available list
            if not any(m["id"] == model.identifier for m in self._available):
                self._available.append({
                    "id": model.identifier,
                    "name": model.name,
                    "owned_by": model.provider.lower(),
                })

    def _generate_aliases(self, identifier: str) -> list[str]:
        """Generate friendly aliases for a model identifier."""
        aliases = []
        id_lower = identifier.lower()

        # GPT: gpt51 -> gpt-5.1, gpt-51
        if id_lower.startswith("gpt"):
            match = re.match(r'gpt(\d)(\d)', id_lower)
            if match:
                aliases.extend([f"gpt-{match.group(1)}.{match.group(2)}", f"gpt-{match.group(1)}{match.group(2)}"])

        # Claude: claude45sonnet -> claude-4.5-sonnet
        elif id_lower.startswith("claude"):
            if "opus" in id_lower:
                match = re.search(r'opus(\d+)', id_lower)
                if match:
                    v = match.group(1)
                    aliases.extend([f"claude-opus-{v[0]}.{v[1:]}" if len(v) > 1 else f"claude-opus-{v}"])
            elif "sonnet" in id_lower:
                match = re.search(r'(\d+)sonnet', id_lower)
                if match:
                    v = match.group(1)
                    aliases.extend([f"claude-{v[0]}.{v[1:]}-sonnet" if len(v) > 1 else f"claude-{v}-sonnet"])

        # Gemini: gemini30pro -> gemini-3-pro
        elif id_lower.startswith("gemini"):
            match = re.search(r'gemini(\d+)pro', id_lower)
            if match:
                v = match.group(1)
                aliases.extend([f"gemini-{v[0]}-pro", f"gemini-{v}-pro"])

        # Grok: grok41 -> grok-4.1
        elif id_lower.startswith("grok"):
            match = re.search(r'grok(\d+)', id_lower)
            if match:
                v = match.group(1)
                aliases.extend([f"grok-{v[0]}.{v[1:]}" if len(v) > 1 else f"grok-{v}"])

        # Add thinking suffix variants
        if "thinking" in id_lower:
            aliases.extend([f"{a}-thinking" for a in aliases])

        return aliases

    def _use_defaults(self) -> None:
        """Use default models as fallback."""
        self._models = []
        self._mapping = {
            "perplexity-auto": Models.BEST,
            "perplexity-sonar": Models.SONAR,
            "perplexity-research": Models.RESEARCH,
            "auto": Models.BEST,
        }
        self._available = [
            {"id": "perplexity-auto", "name": "Perplexity Auto", "owned_by": "perplexity"},
            {"id": "perplexity-sonar", "name": "Perplexity Sonar", "owned_by": "perplexity"},
            {"id": "perplexity-research", "name": "Perplexity Research", "owned_by": "perplexity"},
        ]

    def get(self, name: str) -> Model:
        """Get a Model by name or alias."""
        key = name.lower().strip()
        if key in self._mapping:
            return self._mapping[key]
        logging.warning(f"Unknown model '{name}', using default")
        return Models.BEST

    def list_available(self) -> list[dict[str, str]]:
        """Get list of available models."""
        return self._available

    def needs_refresh(self) -> bool:
        """Check if models need refreshing."""
        if not self._last_fetch:
            return True
        return (datetime.now() - self._last_fetch).total_seconds() > self._refresh_interval
