"""LLM-based chat intent extractor."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import httpx

from .db import get_session
from .models import PromptTemplate


DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

PROVIDER_BASE_URLS = {
    "openai": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    "deepseek": "https://api.deepseek.com/v1",
    "kimi": "https://api.moonshot.ai/v1",
    "moonshot": "https://api.moonshot.ai/v1",
    "minimax": "https://api.minimax.io/v1",
}


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["cash", "fund", "holding", "transaction", "unknown"],
        },
        "confidence": {"type": "number"},
        "data": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "fund_code": {"type": "string"},
                "fund_name": {"type": "string"},
                "fund_type": {"type": "string", "enum": ["open", "etf"]},
                "currency": {"type": "string"},
                "cycle_weights": {
                    "type": "object",
                    "additionalProperties": {"type": "number"},
                },
                "shares": {"type": "number"},
                "amount": {"type": "number"},
                "trade_type": {"type": "string", "enum": ["buy", "sell"]},
                "trade_date": {"type": "string"},
                "note": {"type": "string"},
            },
        },
        "reason": {"type": "string"},
    },
    "required": ["intent", "confidence", "data", "reason"],
}


FALLBACK_PROMPT = (
    "你是资产配置系统的信息抽取器。"
    "从用户输入中抽取结构化信息，不做数学计算。"
    "返回严格符合 JSON schema 的 JSON。"
    "trade_date 使用 YYYY-MM-DD 格式；无法确认时留空字符串。"
    "如果无法判断 intent，返回 unknown 并说明 reason。"
)


def extract_chat_intent(text: str) -> Dict[str, Any]:
    api_key = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    if not api_key:
        return {"ok": False, "error": "missing_llm_api_key"}

    prompt = _load_prompt("chat_extraction") or FALLBACK_PROMPT
    provider = DEFAULT_PROVIDER.lower()
    model = os.getenv("LLM_MODEL")
    if not model and provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not model:
        return {"ok": False, "error": "missing_llm_model"}

    base_url = os.getenv("LLM_BASE_URL")
    if not base_url:
        base_url = PROVIDER_BASE_URLS.get(provider, PROVIDER_BASE_URLS["openai"])
    base_url = base_url.rstrip("/")

    payload: Dict[str, Any]
    endpoint: str
    if provider in ("openai", "openai_responses"):
        endpoint = f"{base_url}/responses"
        payload = {
            "model": model,
            "input": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "portfolio_chat_intent",
                    "schema": SCHEMA,
                    "strict": True,
                }
            },
        }
    else:
        endpoint = f"{base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0,
        }
        if os.getenv("LLM_ENABLE_RESPONSE_FORMAT", "false").lower() == "true":
            payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
    except Exception as exc:
        return {"ok": False, "error": "llm_request_failed", "detail": str(exc)}

    try:
        data = resp.json()
        text_output = _extract_output_text(data, provider)
        cleaned = _normalize_json_text(text_output)
        parsed = json.loads(cleaned) if cleaned else None
        if not isinstance(parsed, dict):
            return {"ok": False, "error": "invalid_llm_output"}
        return {
            "ok": True,
            "parsed": parsed,
            "provider": provider,
            "model": model,
        }
    except Exception as exc:
        return {"ok": False, "error": "parse_failed", "detail": str(exc)}


def _extract_output_text(payload: Dict[str, Any], provider: str) -> str:
    if provider in ("openai", "openai_responses"):
        outputs = payload.get("output", [])
        for item in outputs:
            if item.get("type") == "message":
                contents = item.get("content", [])
                for content in contents:
                    if content.get("type") == "output_text":
                        return content.get("text", "")
        return ""

    choices = payload.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
    return ""


def _load_prompt(name: str) -> Optional[str]:
    session = get_session()
    try:
        prompt = session.query(PromptTemplate).filter(PromptTemplate.name == name).one_or_none()
        if prompt:
            return prompt.content
        return None
    finally:
        session.close()


def _normalize_json_text(text: str) -> str:
    if not text:
        return text
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped.replace("json", "", 1).strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    # Fallback: find first JSON object
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1]
    return stripped
