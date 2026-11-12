import json
import re


def _strip_code_fences(payload: str) -> str:
    text = payload.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _balanced_json_window(text: str) -> str | None:
    start = min((index for index in (text.find("{"), text.find("[")) if index != -1), default=-1)
    if start < 0:
        return None
    stack: list[str] = []
    in_string = False
    escape = False
    openings = {"{": "}", "[": "]"}
    closings = {"}": "{", "]": "["}
    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char in openings:
            stack.append(char)
            continue
        if char in closings and stack and stack[-1] == closings[char]:
            stack.pop()
            if not stack:
                return text[start : index + 1]
    return None


def repair_json_payload(payload: object) -> str | None:
    if not isinstance(payload, str):
        return None
    text = _strip_code_fences(payload)
    if not text:
        return None
    candidate = _balanced_json_window(text) or text
    candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)
    try:
        json.loads(candidate)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return candidate
