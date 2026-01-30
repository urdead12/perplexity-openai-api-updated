#!/usr/bin/env python3
"""Perplexity OpenAI-compatible API Server

This server provides an OpenAI-compatible API for Perplexity AI.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Add src to path for local development
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(script_dir, "src"))

from perplexity_webui_scraper import (
    CitationMode,
    Perplexity,
    PerplexityError
)
from perplexity_webui_scraper.models import Model

from .config import ServerConfig
from .models import ModelRegistry
from .conversation import ConversationManager, ConversationSession


# =============================================================================
# Pydantic Models
# =============================================================================

class ContentPart(BaseModel):
    """A content part for multi-modal messages."""
    type: str
    text: str | None = None
    image_url: dict[str, str] | None = None

    model_config = ConfigDict(extra="allow")


class ChatMessage(BaseModel):
    role: str
    content: str | list[dict[str, Any]]
    name: str | None = None

    model_config = ConfigDict(extra="allow")

    def get_text_content(self) -> str:
        """Extract text content, handling both string and array formats."""
        if isinstance(self.content, str):
            return self.content

        # Handle array format - extract text from content parts
        text_parts = []
        for part in self.content:
            if isinstance(part, dict):
                if part.get("type") == "text" and "text" in part:
                    text_parts.append(part["text"])

        return "\n".join(text_parts) if text_parts else ""


class ChatRequest(BaseModel):
    model: str = "perplexity-auto"
    messages: list[ChatMessage]
    stream: bool = False

    # Standard OpenAI parameters (not all may be supported by Perplexity)
    temperature: float | None = None
    top_p: float | None = None
    n: int | None = 1
    max_tokens: int | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    logit_bias: dict[str, float] | None = None
    user: str | None = None
    stop: str | list[str] | None = None

    # Additional OpenAI parameters
    seed: int | None = None
    logprobs: bool | None = None
    top_logprobs: int | None = None
    response_format: dict[str, Any] | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    parallel_tool_calls: bool | None = None

    # Perplexity-specific parameters
    conversation_id: str | None = None
    citation_mode: str | None = None

    model_config = ConfigDict(extra="allow")  # Allow additional fields


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"
    logprobs: dict[str, Any] | None = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: Usage
    system_fingerprint: str | None = None
    service_tier: str | None = None


class ChunkChoice(BaseModel):
    index: int
    delta: dict[str, Any]
    finish_reason: str | None = None
    logprobs: dict[str, Any] | None = None


class ChatChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChunkChoice]
    system_fingerprint: str | None = None
    service_tier: str | None = None


class ModelItem(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelsResponse(BaseModel):
    object: str = "list"
    data: list[ModelItem]


class ErrorDetail(BaseModel):
    """OpenAI-compatible error detail."""
    message: str
    type: str
    param: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    """OpenAI-compatible error response."""
    error: ErrorDetail


class CompletionRequest(BaseModel):
    """Legacy completions request."""
    model: str = "perplexity-auto"
    prompt: str | list[str]
    max_tokens: int | None = 16
    temperature: float | None = None
    top_p: float | None = None
    n: int | None = 1
    stream: bool = False
    stop: str | list[str] | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    user: str | None = None
    suffix: str | None = None
    echo: bool = False
    best_of: int | None = None
    logprobs: int | None = None

    model_config = ConfigDict(extra="allow")


class CompletionChoice(BaseModel):
    """Legacy completion choice."""
    text: str
    index: int
    logprobs: dict[str, Any] | None = None
    finish_reason: str = "stop"


class CompletionResponse(BaseModel):
    """Legacy completion response."""
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[CompletionChoice]
    usage: Usage
    system_fingerprint: str | None = None


# =============================================================================
# Global State
# =============================================================================

config: ServerConfig
models: ModelRegistry
manager: ConversationManager
start_time: datetime
request_count: int = 0


# =============================================================================
# Helpers
# =============================================================================

def verify_auth(request: Request) -> str | None:
    """Verify API key and return user ID."""
    if not config.api_key:
        return None

    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and auth[7:] == config.api_key:
        return hashlib.sha256(auth[7:].encode()).hexdigest()[:16]

    raise HTTPException(status_code=401, detail="Invalid API key")


def get_user(request: Request) -> str | None:
    """Get user identifier from request."""
    try:
        return verify_auth(request)
    except HTTPException:
        raise
    except Exception:
        return request.headers.get("X-User-ID")


def get_user_from_headers(headers: dict[str, str] | None) -> str | None:
    """Get user identifier from headers (e.g., WebSocket handshake headers)."""
    if not config.api_key:
        return None

    if not headers:
        raise HTTPException(status_code=401, detail="Invalid API key")

    auth = headers.get("authorization", "")
    if auth.startswith("Bearer ") and auth[7:] == config.api_key:
        return hashlib.sha256(auth[7:].encode()).hexdigest()[:16]

    raise HTTPException(status_code=401, detail="Invalid API key")


def messages_to_query(messages: list[ChatMessage]) -> str:
    """Convert messages to query string."""
    user_msgs = [m for m in messages if m.role == "user"]
    sys_msgs = [m for m in messages if m.role == "system"]

    if len(user_msgs) == 1 and not sys_msgs:
        return user_msgs[0].get_text_content()

    parts = []
    for msg in messages:
        if msg.role == "system":
            parts.append(f"[System]\n{msg.get_text_content()}")
        elif msg.role == "user":
            parts.append(f"User: {msg.get_text_content()}")
        elif msg.role == "assistant":
            parts.append(f"Assistant: {msg.get_text_content()}")
        elif msg.role == "tool":
            # Tool responses are included as context
            parts.append(f"[Tool Result]\n{msg.get_text_content()}")
        elif msg.role == "function":
            # Function responses (deprecated but still supported)
            parts.append(f"[Function Result]\n{msg.get_text_content()}")
    return "\n\n".join(parts)


def estimate_tokens(text: str) -> int:
    """Estimate token count."""
    return len(text) // 4


def parse_citation_mode(mode: str | None) -> CitationMode:
    """Parse citation mode string."""
    if not mode:
        return config.default_citation_mode
    try:
        return CitationMode[mode.upper()]
    except KeyError:
        return config.default_citation_mode


# =============================================================================
# Application Setup
# =============================================================================

def create_app(server_config: ServerConfig) -> FastAPI:
    """Create and configure the FastAPI application."""
    global config, models, manager, start_time

    config = server_config

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan handler."""
        global models, manager, start_time

        start_time = datetime.now()

        # Initialize model registry and fetch models
        models = ModelRegistry()
        models.fetch(config.session_token)

        # Initialize conversation manager
        client = Perplexity(session_token=config.session_token)
        manager = ConversationManager(client, config.conversation_timeout, config.max_conversations_per_user)
        manager.start_cleanup()

        # Setup rate limiting
        if config.enable_rate_limiting:
            limiter = Limiter(key_func=get_remote_address, default_limits=[f"{config.requests_per_minute}/minute"])
            app.state.limiter = limiter
            app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        logging.info(f"🚀 Server starting on http://{config.host}:{config.port}")
        logging.info(f"   Models loaded: {len(models._models)}")
        logging.info(f"   Rate limiting: {'Enabled' if config.enable_rate_limiting else 'Disabled'}")
        logging.info(f"   Auth required: {'Yes' if config.api_key else 'No'}")

        yield

        await manager.stop_cleanup()
        manager.close()

    app = FastAPI(
        title="Perplexity OpenAI API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if config.enable_rate_limiting:
        app.add_middleware(SlowAPIMiddleware)

    # Register routes
    register_routes(app)

    return app


# =============================================================================
# Routes
# =============================================================================

def register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "uptime": (datetime.now() - start_time).total_seconds(),
            "models": len(models._models),
        }

    @app.get("/stats")
    async def stats(request: Request):
        """Server statistics."""
        get_user(request)
        return {
            "uptime": (datetime.now() - start_time).total_seconds(),
            "requests": request_count,
            "conversations": manager.get_stats(),
            "models": {
                "count": len(models._models),
                "last_refresh": models._last_fetch.isoformat() if models._last_fetch else None,
            },
        }

    @app.get("/v1/models", response_model=ModelsResponse)
    async def list_models(request: Request):
        """List available models."""
        get_user(request)

        if models.needs_refresh():
            models.fetch(config.session_token)

        now = int(time.time())
        return ModelsResponse(
            data=[ModelItem(id=m["id"], created=now, owned_by=m["owned_by"]) for m in models.list_available()]
        )

    @app.get("/v1/models/{model_id}", response_model=ModelItem)
    async def get_model(model_id: str, request: Request):
        """Get model info."""
        get_user(request)

        for m in models.list_available():
            if m["id"] == model_id:
                return ModelItem(id=m["id"], created=int(time.time()), owned_by=m["owned_by"])

        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    @app.post("/v1/embeddings")
    async def embeddings(request: Request):
        """Embeddings endpoint (not supported)."""
        get_user(request)
        raise HTTPException(
            status_code=501,
            detail={
                "error": {
                    "message": "Embeddings are not supported by this API. This endpoint wraps Perplexity AI which does not provide embedding models.",
                    "type": "not_implemented_error",
                    "code": "unsupported_endpoint"
                }
            }
        )

    @app.post("/v1/completions")
    async def completions(request: Request, body: CompletionRequest):
        """Legacy completions endpoint for inline/code completions."""
        global request_count
        request_count += 1

        user_id = get_user(request)

        # Handle prompt as string or list
        prompt = body.prompt if isinstance(body.prompt, str) else "\n".join(body.prompt)

        if not prompt:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "prompt is required",
                        "type": "invalid_request_error",
                        "param": "prompt",
                        "code": "missing_required_parameter"
                    }
                }
            )

        # Validate n parameter
        if body.n and body.n > 1:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "n > 1 is not supported. Only single completions are available.",
                        "type": "invalid_request_error",
                        "param": "n",
                        "code": "unsupported_parameter"
                    }
                }
            )

        model_obj = models.get(body.model)
        citation_mode = CitationMode.CLEAN  # No citations for code completions

        conv_id, session = manager.get_or_create(
            None, user_id, body.model, citation_mode
        )

        response_id = f"cmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())

        try:
            # Run completion
            await asyncio.to_thread(session.conversation.ask, prompt, model=model_obj, stream=False)
            answer = session.conversation.answer or ""

            # Add suffix if provided
            if body.suffix:
                answer = answer + body.suffix

            return CompletionResponse(
                id=response_id,
                created=created,
                model=body.model,
                choices=[CompletionChoice(index=0, text=answer)],
                usage=Usage(
                    prompt_tokens=estimate_tokens(prompt),
                    completion_tokens=estimate_tokens(answer),
                    total_tokens=estimate_tokens(prompt) + estimate_tokens(answer),
                ),
                system_fingerprint="perplexity_v1",
            )
        except PerplexityError as e:
            logging.error(f"Perplexity error: {e}")
            raise HTTPException(status_code=502, detail=str(e))
        except Exception as e:
            logging.error(f"Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/v1/models/refresh")
    async def refresh_models(request: Request):
        """Force refresh models."""
        get_user(request)
        models.fetch(config.session_token)
        return {"status": "ok", "count": len(models._models)}

    @app.get("/conversations")
    async def list_conversations(request: Request):
        """List conversations."""
        user_id = get_user(request)
        return {"conversations": manager.list_sessions(user_id)}

    @app.delete("/conversations/{conversation_id}")
    async def delete_conversation(conversation_id: str, request: Request):
        """Delete conversation."""
        user_id = get_user(request)
        if manager.delete(conversation_id, user_id):
            return {"status": "deleted"}
        raise HTTPException(status_code=404, detail="Conversation not found")

    @app.get("/v1/chat/completions")
    async def chat_completions_info(request: Request):
        """Info about chat completions endpoint."""
        return {
            "object": "endpoint",
            "endpoint": "/v1/chat/completions",
            "methods": ["POST"],
            "description": "Create a chat completion. POST JSON with 'model' and 'messages' fields.",
            "documentation": "https://platform.openai.com/docs/api-reference/chat/create"
        }

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request, body: ChatRequest):
        """Chat completions endpoint."""
        global request_count
        request_count += 1

        user_id = get_user(request)

        if not body.messages:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "messages is required",
                        "type": "invalid_request_error",
                        "param": "messages",
                        "code": "missing_required_parameter"
                    }
                }
            )

        # Validate n parameter (number of completions)
        if body.n and body.n > 1:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "n > 1 is not supported. Only single completions are available.",
                        "type": "invalid_request_error",
                        "param": "n",
                        "code": "unsupported_parameter"
                    }
                }
            )

        model_obj = models.get(body.model)
        citation_mode = parse_citation_mode(body.citation_mode)

        conv_id, session = manager.get_or_create(
            body.conversation_id, user_id, body.model, citation_mode
        )

        query = messages_to_query(body.messages)
        response_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())

        try:
            if body.stream:
                return StreamingResponse(
                    stream_response(response_id, created, body.model, model_obj, query, session),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Conversation-ID": conv_id},
                )
            else:
                # The scraper client is synchronous and may block. Run in a worker thread.
                await asyncio.to_thread(session.conversation.ask, query, model=model_obj, stream=False)
                answer = session.conversation.answer or ""

                return ChatResponse(
                    id=response_id,
                    created=created,
                    model=body.model,
                    choices=[ChatChoice(index=0, message=ChatMessage(role="assistant", content=answer))],
                    usage=Usage(
                        prompt_tokens=estimate_tokens(query),
                        completion_tokens=estimate_tokens(answer),
                        total_tokens=estimate_tokens(query) + estimate_tokens(answer),
                    ),
                    system_fingerprint="perplexity_v1",
                )
        except PerplexityError as e:
            logging.error(f"Perplexity error: {e}")
            raise HTTPException(status_code=502, detail=str(e))
        except Exception as e:
            logging.error(f"Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def stream_response(
        response_id: str,
        created: int,
        model_name: str,
        model: Model,
        query: str,
        session: ConversationSession,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response."""
        # Initial chunk
        yield f"data: {ChatChunk(id=response_id, created=created, model=model_name, choices=[ChunkChoice(index=0, delta={'role': 'assistant', 'content': ''})], system_fingerprint='perplexity_v1').model_dump_json()}\n\n"

        # The underlying streaming generator is synchronous and can block the event loop.
        # Move it to a background thread and ship deltas back through an asyncio queue.
        queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def producer() -> None:
            last = ""
            try:
                for resp in session.conversation.ask(query, model=model, stream=True):
                    current = resp.answer or ""
                    if len(current) > len(last):
                        delta = current[len(last):]
                        last = current
                        loop.call_soon_threadsafe(queue.put_nowait, ("delta", delta))
                loop.call_soon_threadsafe(queue.put_nowait, ("done", ""))
            except Exception as e:
                # Some upstreams intermittently fail in streaming mode but still work in
                # non-stream mode. Fallback so clients still get an answer.
                try:
                    session.conversation.ask(query, model=model, stream=False)
                    current = session.conversation.answer or ""
                    if len(current) > len(last):
                        loop.call_soon_threadsafe(queue.put_nowait, ("delta", current[len(last):]))
                    loop.call_soon_threadsafe(queue.put_nowait, ("done", ""))
                except Exception as e2:
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", str(e2) or str(e)))

        threading.Thread(target=producer, daemon=True).start()

        while True:
            kind, payload = await queue.get()
            if kind == "delta":
                yield f"data: {ChatChunk(id=response_id, created=created, model=model_name, choices=[ChunkChoice(index=0, delta={'content': payload})], system_fingerprint='perplexity_v1').model_dump_json()}\n\n"
            elif kind == "error":
                logging.error(f"Streaming error: {payload}")
                yield f"data: {ChatChunk(id=response_id, created=created, model=model_name, choices=[ChunkChoice(index=0, delta={}, finish_reason='error')], system_fingerprint='perplexity_v1').model_dump_json()}\n\n"
                break
            else:
                break

        # Final chunk
        yield f"data: {ChatChunk(id=response_id, created=created, model=model_name, choices=[ChunkChoice(index=0, delta={}, finish_reason='stop')], system_fingerprint='perplexity_v1').model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    @app.websocket("/ws")
    async def ws_chat(ws: WebSocket):
        """WebSocket bridge for clients that expect a /ws endpoint.

        Protocol:
        - Client sends a JSON payload compatible with ChatRequest.
        - If stream=true, server sends SSE-formatted frames (same as HTTP streaming endpoint).
        - If stream=false, server sends one JSON ChatResponse.

        Notes:
        - By default the socket is closed after one request/response.
          Set keep_open=true to send multiple requests on the same connection.
        - If ws_stream_format="json", the server converts SSE frames to raw JSON strings
          (ChatChunk JSON) and sends a final {"type":"done"} message.
        """
        await ws.accept()

        # Auth (if enabled)
        try:
            user_id = get_user_from_headers(dict(ws.headers))
        except HTTPException:
            await ws.close(code=4401)
            return

        global request_count

        while True:
            try:
                raw = await ws.receive_text()
            except Exception:
                return

            try:
                payload = json.loads(raw)
            except Exception:
                await ws.send_text(json.dumps({"error": "Invalid JSON"}))
                await ws.close(code=1003)
                return

            # Lightweight ping/pong for clients that keep the socket alive
            if isinstance(payload, dict) and payload.get("type") == "ping":
                await ws.send_text('{"type":"pong"}')
                continue

            keep_open = bool(isinstance(payload, dict) and payload.get("keep_open", False))
            ws_stream_format = "sse"
            if isinstance(payload, dict):
                ws_stream_format = str(payload.get("ws_stream_format", "sse")).lower().strip()

            try:
                body = ChatRequest.model_validate(payload)
            except Exception as e:
                await ws.send_text(json.dumps({"error": f"Invalid request: {e}"}))
                await ws.close(code=1003)
                return

            request_count += 1

            if not body.messages:
                await ws.send_text(json.dumps({"error": "Messages required"}))
                await ws.close(code=1003)
                return

            model_obj = models.get(body.model)
            citation_mode = parse_citation_mode(body.citation_mode)

            conv_id, session = manager.get_or_create(
                body.conversation_id, user_id, body.model, citation_mode
            )

            response_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
            created = int(time.time())

            # Send conversation id so the client can reuse it
            await ws.send_text(json.dumps({"type": "meta", "conversation_id": conv_id, "response_id": response_id}))

            try:
                if body.stream:
                    async for frame in stream_response(
                        response_id,
                        created,
                        body.model,
                        model_obj,
                        messages_to_query(body.messages),
                        session,
                    ):
                        if ws_stream_format == "json" and frame.startswith("data: "):
                            data = frame[len("data: "):].strip()
                            if data == "[DONE]":
                                await ws.send_text(json.dumps({"type": "done"}))
                            else:
                                await ws.send_text(data)
                        else:
                            await ws.send_text(frame)
                else:
                    query = messages_to_query(body.messages)
                    await asyncio.to_thread(session.conversation.ask, query, model=model_obj, stream=False)
                    answer = session.conversation.answer or ""

                    resp = ChatResponse(
                        id=response_id,
                        created=created,
                        model=body.model,
                        choices=[ChatChoice(index=0, message=ChatMessage(role="assistant", content=answer))],
                        usage=Usage(
                            prompt_tokens=estimate_tokens(query),
                            completion_tokens=estimate_tokens(answer),
                            total_tokens=estimate_tokens(query) + estimate_tokens(answer),
                        ),
                        system_fingerprint="perplexity_v1",
                    )
                    await ws.send_text(resp.model_dump_json())

                if not keep_open:
                    await ws.close(code=1000)
                    return
            except Exception as e:
                logging.error(f"WebSocket request error: {e}")
                await ws.send_text(json.dumps({"error": str(e)}))
                await ws.close(code=1011)
                return


# =============================================================================
# Main Entry Point
# =============================================================================

def run_server(server_config: ServerConfig | None = None) -> None:
    """Run the server."""
    if server_config is None:
        server_config = ServerConfig.from_env()

    app = create_app(server_config)

    uvicorn.run(
        app,
        host=server_config.host,
        port=server_config.port,
        log_level=server_config.log_level.lower(),
    )


if __name__ == "__main__":
    run_server()
