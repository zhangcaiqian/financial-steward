"""OpenAI-compatible LLM client with tool calling and streaming."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    return os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")


def _get_api_key() -> str:
    return os.getenv("LLM_API_KEY", "")


def _get_model() -> str:
    return os.getenv("LLM_MODEL", "qwen-max")


async def chat_complete(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = None,
) -> Dict[str, Any]:
    if not _get_api_key():
        raise RuntimeError("LLM_API_KEY is not set")
    payload: Dict[str, Any] = {
        "model": _get_model(),
        "messages": messages,
        "temperature": 0.2,
    }
    if tools is not None:
        payload["tools"] = tools
    if tool_choice:
        payload["tool_choice"] = tool_choice

    start_time = time.monotonic()
    logger.info(
        "LLM chat_complete request model=%s base_url=%s tools=%s",
        _get_model(),
        _get_base_url(),
        "yes" if tools else "no",
    )
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{_get_base_url()}/chat/completions",
                headers=_headers(),
                json=payload,
            )
            resp.raise_for_status()
        except Exception:
            logger.exception("LLM chat_complete request failed")
            raise
    logger.info("LLM chat_complete response status=%s elapsed=%.2fs", resp.status_code, time.monotonic() - start_time)
    return resp.json()


async def chat_stream(
    messages: List[Dict[str, Any]],
    on_delta,
) -> str:
    if not _get_api_key():
        raise RuntimeError("LLM_API_KEY is not set")
    payload: Dict[str, Any] = {
        "model": _get_model(),
        "messages": messages,
        "temperature": 0.2,
        "stream": True,
    }

    full_text = ""
    start_time = time.monotonic()
    logger.info("LLM chat_stream request model=%s base_url=%s", _get_model(), _get_base_url())
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.stream(
                "POST",
                f"{_get_base_url()}/chat/completions",
                headers=_headers(),
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line.replace("data: ", "").strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        full_text += content
                        await on_delta(content)
        except Exception:
            logger.exception("LLM chat_stream request failed")
            raise
    logger.info("LLM chat_stream complete elapsed=%.2fs", time.monotonic() - start_time)
    return full_text


def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    message = response.get("choices", [{}])[0].get("message", {})
    return message.get("tool_calls", []) or []


def _headers() -> Dict[str, str]:
    api_key = _get_api_key()
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
