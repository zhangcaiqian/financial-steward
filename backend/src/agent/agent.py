"""Agent orchestration."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

from src.portfolio.service import get_prompt
from .strategy import load_strategy_context
from .tools import TOOLS, TOOL_SPECS
from .llm_client import chat_complete, chat_stream, extract_tool_calls

logger = logging.getLogger(__name__)

class AgentSession:
    def __init__(self) -> None:
        self.messages: List[Dict[str, Any]] = []

    def system_message(self) -> Dict[str, Any]:
        prompt = get_prompt("agent_system")
        system_prompt = prompt.content if prompt else ""
        strategy = load_strategy_context()
        if strategy:
            system_prompt = f"{system_prompt}\n\n【配置策略】\n{strategy}\n"
        system_prompt += (
            "\n【输出格式（用于流式展示，必须严格遵守）】\n"
            f"{TEXT_DELIM}\n"
            "这里输出给用户阅读的 Markdown 正文（用于流式显示）。\n"
            f"{BLOCKS_DELIM}\n"
            "这里输出 JSON：{\"blocks\": [...]}。\n"
            "blocks 类型支持: text, table, chart, buttons, form。\n"
            "chart 需要包含 chartType 与 data。\n"
            "如需写入数据库，只能通过 buttons/form 请求用户确认。\n"
        )
        return {"role": "system", "content": system_prompt}

    async def handle_user_message(
        self,
        content: str,
        on_delta,
        on_tool_event: Optional["ToolEventCallback"] = None,
    ) -> Dict[str, Any]:
        if not self.messages:
            self.messages.append(self.system_message())
        self.messages.append({"role": "user", "content": content})

        # Step 1: tool planning (non-stream)
        tool_response = await chat_complete(self.messages, tools=TOOL_SPECS)
        tool_calls = extract_tool_calls(tool_response)
        if tool_calls:
            self.messages.append(tool_response["choices"][0]["message"])
            for call in tool_calls:
                name = call.get("function", {}).get("name")
                args_text = call.get("function", {}).get("arguments", "{}")
                try:
                    args = json.loads(args_text)
                except json.JSONDecodeError:
                    args = {}
                tool = TOOLS.get(name)
                event_id = str(uuid.uuid4())
                if on_tool_event:
                    await on_tool_event({"type": "tool.start", "event_id": event_id, "tool": {"name": name}})
                logger.info("Tool call start name=%s args=%s", name, args)
                try:
                    result = tool(args) if tool else {"error": "unknown_tool"}
                    if not tool and on_tool_event:
                        await on_tool_event(
                            {
                                "type": "tool.error",
                                "event_id": event_id,
                                "tool": {"name": name, "error": "unknown_tool"},
                            }
                        )
                    elif on_tool_event:
                        await on_tool_event({"type": "tool.end", "event_id": event_id, "tool": {"name": name}})
                    logger.info("Tool call end name=%s status=success", name)
                except Exception as exc:
                    result = {"error": "tool_failed", "detail": str(exc)}
                    if on_tool_event:
                        await on_tool_event(
                            {"type": "tool.error", "event_id": event_id, "tool": {"name": name, "error": str(exc)}}
                        )
                    logger.exception("Tool call failed name=%s", name)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        # Step 2: final response streaming
        stream_state = {"mode": "search_text", "buffer": "", "has_text": False}

        async def on_raw_delta(chunk: str) -> None:
            text_chunk = _extract_stream_text(chunk, stream_state)
            if text_chunk:
                await on_delta(text_chunk)

        full_text = await chat_stream(self.messages, on_delta=on_raw_delta)
        self.messages.append({"role": "assistant", "content": full_text})
        parsed = _parse_blocks(full_text)
        text = parsed.get("text") or _extract_text_from_blocks(parsed.get("blocks", [])) or ""
        return {"text": text, "blocks": parsed.get("blocks", [])}


ToolEventCallback = Callable[[Dict[str, Any]], Awaitable[None]]


def _parse_blocks(content: str) -> Dict[str, Any]:
    text_part, blocks_part = _split_text_blocks(content)
    data = _safe_json_load(_normalize_json(blocks_part))

    if isinstance(data, str):
        nested = _safe_json_load(data)
        if isinstance(nested, dict) and "blocks" in nested:
            return {"text": text_part, "blocks": nested.get("blocks", [])}

    if isinstance(data, dict) and "blocks" in data:
        return {"text": text_part, "blocks": data.get("blocks", [])}

    if text_part:
        return {"text": text_part, "blocks": [{"type": "text", "content": text_part}]}
    return {"text": "", "blocks": [{"type": "text", "content": content}]}


def _normalize_json(text: str) -> str:
    if not text:
        return "{}"
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped.replace("json", "", 1).strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1]
    return stripped


def _safe_json_load(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def _split_text_blocks(content: str) -> tuple[str, str]:
    if TEXT_DELIM in content and BLOCKS_DELIM in content:
        _, after_text = content.split(TEXT_DELIM, 1)
        text_part, blocks_part = after_text.split(BLOCKS_DELIM, 1)
        return text_part.strip(), blocks_part.strip()
    return "", content


def _extract_text_from_blocks(blocks: list[Dict[str, Any]]) -> str:
    texts = []
    for block in blocks or []:
        if block.get("type") == "text" and block.get("content"):
            texts.append(str(block.get("content")))
    return "\n\n".join(texts).strip()


def _extract_stream_text(chunk: str, state: Dict[str, Any]) -> str:
    buffer = f"{state.get('buffer', '')}{chunk}"
    mode = state.get("mode", "search_text")

    if mode == "search_text":
        idx = buffer.find(TEXT_DELIM)
        if idx == -1:
            # keep tail to detect delimiter across chunks
            tail_len = max(len(TEXT_DELIM) - 1, 0)
            state["buffer"] = buffer[-tail_len:] if tail_len else ""
            return ""
        buffer = buffer[idx + len(TEXT_DELIM):]
        state["mode"] = "stream_text"
        mode = "stream_text"

    if mode == "stream_text":
        idx = buffer.find(BLOCKS_DELIM)
        if idx != -1:
            text_part = buffer[:idx]
            state["mode"] = "after_text"
            state["buffer"] = buffer[idx + len(BLOCKS_DELIM):]
            state["has_text"] = True
            return text_part
        state["buffer"] = ""
        if buffer:
            state["has_text"] = True
        return buffer

    state["buffer"] = buffer
    return ""


TEXT_DELIM = "<<<TEXT>>>"
BLOCKS_DELIM = "<<<BLOCKS>>>"
