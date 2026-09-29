"""Read supported client JSON streams without inferring events from prose.

Claude stream shapes follow anthropics/skills skill-creator/scripts/run_eval.py;
this parser additionally assembles complete tool input and deduplicates events.
Unknown/missing usage stays unavailable instead of becoming zero.
"""

import json
import math


def events(raw: str) -> list[dict]:
    result = []
    for line in raw.splitlines():
        try:
            value = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def tool_calls(raw: str, client: str | None = None) -> list[dict]:
    """Return normalized calls; partial and final Claude messages share call IDs."""
    calls = {}
    pending = {}
    failed = set()

    def add(block, source, fallback, status=None):
        if not isinstance(block, dict):
            return
        identifier = block.get("id") if isinstance(block.get("id"), str) else None
        call_id = identifier or fallback
        inputs = block.get("input")
        calls[call_id] = {
            "tool": block.get("name"), "input": inputs if isinstance(inputs, dict) else {},
            "tool_use_id": identifier, "event": source, "status": status,
        }

    def flush(index):
        record = pending.pop(index, None)
        if not record:
            return
        block, fragments, fallback = record
        if fragments:
            try:
                inputs = json.loads("".join(fragments))
            except ValueError:
                return
            if not isinstance(inputs, dict):
                return
            block = {**block, "input": inputs}
        add(block, "content_block", fallback)

    for seq, ev in enumerate(events(raw)):
        if client in (None, "opencode") and ev.get("type") in ("tool_use", "tool"):
            part = ev.get("part")
            if isinstance(part, dict):
                state = part.get("state")
                state = state if isinstance(state, dict) else {}
                add({"name": part.get("tool"), "input": state.get("input"),
                     "id": part.get("callID") or part.get("id")}, "tool_use", str(seq),
                    state.get("status"))
        if client not in (None, "claude"):
            continue
        if ev.get("type") in ("assistant", "user"):
            message = ev.get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), list):
                continue
            for index, block in enumerate(message["content"]):
                if not isinstance(block, dict):
                    continue
                if ev["type"] == "assistant" and block.get("type") == "tool_use":
                    add(block, "assistant", f"{seq}:{index}")
                if (block.get("type") == "tool_result" and block.get("is_error") is True
                        and isinstance(block.get("tool_use_id"), str)):
                    failed.add(block.get("tool_use_id"))
        if ev.get("type") != "stream_event" or not isinstance(ev.get("event"), dict):
            continue
        stream = ev["event"]
        index = stream.get("index")
        if not isinstance(index, (int, type(None))):
            continue
        if stream.get("type") == "message_start":
            for old_index in list(pending):
                flush(old_index)
        elif stream.get("type") == "content_block_start":
            block = stream.get("content_block")
            if isinstance(block, dict) and block.get("type") == "tool_use":
                pending[index] = (block, [], f"{seq}:{index}")
        elif stream.get("type") == "content_block_delta" and index in pending:
            delta = stream.get("delta")
            if isinstance(delta, dict) and delta.get("type") == "input_json_delta":
                fragment = delta.get("partial_json")
                if isinstance(fragment, str):
                    pending[index][1].append(fragment)
        elif stream.get("type") == "content_block_stop":
            flush(index)
    for index in list(pending):
        flush(index)
    for record in calls.values():
        if record["tool_use_id"] in failed:
            record["status"] = "error"
    return list(calls.values())


def assistant_text(raw: str) -> str:
    texts = []
    result_text = None
    for ev in events(raw):
        part = ev.get("part")
        if ev.get("type") == "text" and isinstance(part, dict) and isinstance(part.get("text"), str):
            texts.append(part["text"])
        message = ev.get("message")
        if ev.get("type") == "assistant" and isinstance(message, dict):
            content = message.get("content")
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                    texts.append(block["text"])
        if ev.get("type") == "result" and isinstance(ev.get("result"), str):
            result_text = ev["result"]
    return "\n".join(texts).strip() if texts else (result_text if result_text is not None else raw.strip())


def execution_error(raw: str, client: str) -> str | None:
    """Clients may encode a failed run inside JSON even when the process exits 0."""
    for ev in events(raw):
        if client == "opencode" and ev.get("type") == "error":
            return "opencode emitted an error event"
        if client == "claude" and ev.get("type") == "result":
            subtype = ev.get("subtype")
            if ev.get("is_error") is True or (isinstance(subtype, str) and subtype.startswith("error")):
                return "claude emitted an error result"
    return None


def stream_metrics(raw: str, client: str) -> dict:
    models = set()
    total = None
    token_source = None

    def number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0

    token_steps = []
    for ev in events(raw):
        message = ev.get("message")
        if isinstance(message, dict) and isinstance(message.get("model"), str):
            models.add(message["model"])
        if ev.get("type") == "system" and isinstance(ev.get("model"), str):
            models.add(ev["model"])
        if client == "claude" and ev.get("type") == "result":
            model_usage = ev.get("modelUsage")
            if isinstance(model_usage, dict):
                models.update(name for name in model_usage if isinstance(name, str))
            usage = ev.get("usage")
            if isinstance(usage, dict) and all(number(usage.get(key)) for key in ("input_tokens", "output_tokens")):
                values = [usage.get(key, 0) for key in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")]
                if all(number(value) for value in values):
                    total = sum(values)
                    token_source = "claude_result_usage"
        if client == "opencode" and ev.get("type") == "step_finish":
            part = ev.get("part")
            tokens = part.get("tokens") if isinstance(part, dict) else None
            token_steps.append(tokens.get("total") if isinstance(tokens, dict) else None)
    if client == "opencode" and token_steps and all(number(value) for value in token_steps):
        total = sum(token_steps)
        token_source = "opencode_step_finish_total"
    parsed = events(raw)
    return {
        "model": next(iter(models)) if len(models) == 1 else None,
        "models": sorted(models), "total_tokens": total, "tokens_source": token_source,
        "total_tool_calls": len(tool_calls(raw, client)) if parsed else None,
        "tool_calls_source": "structured_tool_events" if parsed else None,
    }
