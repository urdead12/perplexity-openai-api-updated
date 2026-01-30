"""Conversation management"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

# Add src to path for local development
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(script_dir, "src"))

from perplexity_webui_scraper import (
    CitationMode,
    Conversation,
    ConversationConfig,
    Perplexity,
)


@dataclass
class ConversationSession:
    """Active conversation session."""
    conversation: Conversation
    created_at: datetime
    last_used: datetime
    user_id: str | None = None
    model: str = "perplexity-auto"
    message_count: int = 0


class ConversationManager:
    """Manages persistent conversations with automatic cleanup."""

    def __init__(self, client: Perplexity, timeout: int, max_per_user: int):
        self._client = client
        self._timeout = timeout
        self._max_per_user = max_per_user
        self._sessions: Dict[str, ConversationSession] = {}
        self._cleanup_task: asyncio.Task | None = None

    def start_cleanup(self) -> None:
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self) -> None:
        """Periodically clean up expired sessions."""
        while True:
            await asyncio.sleep(300)
            now = datetime.now()
            expired = [
                cid for cid, sess in self._sessions.items()
                if (now - sess.last_used).total_seconds() > self._timeout
            ]
            for cid in expired:
                del self._sessions[cid]
            if expired:
                logging.info(f"Cleaned up {len(expired)} expired conversations")

    def get_or_create(
        self,
        conversation_id: str | None,
        user_id: str | None,
        model: str,
        citation_mode: CitationMode,
    ) -> tuple[str, ConversationSession]:
        """Get existing or create new conversation session."""
        # Return existing
        if conversation_id and conversation_id in self._sessions:
            session = self._sessions[conversation_id]
            session.last_used = datetime.now()
            session.message_count += 1
            return conversation_id, session

        # Enforce per-user limit
        if user_id:
            user_sessions = [s for s in self._sessions.values() if s.user_id == user_id]
            if len(user_sessions) >= self._max_per_user:
                oldest = min(user_sessions, key=lambda s: s.last_used)
                for cid, sess in list(self._sessions.items()):
                    if sess is oldest:
                        del self._sessions[cid]
                        break

        # Create new
        config = ConversationConfig(citation_mode=citation_mode)
        conversation = self._client.create_conversation(config)
        new_id = conversation_id or str(uuid.uuid4())

        session = ConversationSession(
            conversation=conversation,
            created_at=datetime.now(),
            last_used=datetime.now(),
            user_id=user_id,
            model=model,
        )
        self._sessions[new_id] = session
        return new_id, session

    def list_sessions(self, user_id: str | None) -> list[dict]:
        """List sessions, optionally filtered by user."""
        result = []
        for cid, sess in self._sessions.items():
            if not user_id or sess.user_id == user_id:
                result.append({
                    "id": cid,
                    "created_at": sess.created_at.isoformat(),
                    "last_used": sess.last_used.isoformat(),
                    "message_count": sess.message_count,
                    "model": sess.model,
                })
        return sorted(result, key=lambda x: x["last_used"], reverse=True)

    def delete(self, conversation_id: str, user_id: str | None) -> bool:
        """Delete a conversation session."""
        if conversation_id not in self._sessions:
            return False
        session = self._sessions[conversation_id]
        if user_id and session.user_id and session.user_id != user_id:
            return False
        del self._sessions[conversation_id]
        return True

    def get_stats(self) -> dict:
        """Get conversation statistics."""
        return {
            "total": len(self._sessions),
            "users": len(set(s.user_id for s in self._sessions.values() if s.user_id)),
            "messages": sum(s.message_count for s in self._sessions.values()),
        }

    def close(self) -> None:
        """Close the Perplexity client."""
        self._client.close()
