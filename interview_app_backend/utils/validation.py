from __future__ import annotations


MIN_ANSWER_LENGTH = 40
MAX_ANSWER_LENGTH = 2000
PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard previous instructions",
    "system prompt",
    "developer message",
    "act as",
)


def validate_text(value: str) -> bool:
    return bool(value and value.strip())


def validate_answer_length(answer: str, minimum: int = MIN_ANSWER_LENGTH, maximum: int = MAX_ANSWER_LENGTH) -> bool:
    text = answer.strip()
    return minimum <= len(text) <= maximum


def validate_answer_relevance(answer: str) -> bool:
    text = answer.lower().strip()
    if not text:
        return False

    interview_keywords = (
        "challenge",
        "project",
        "team",
        "result",
        "improved",
        "built",
        "designed",
        "worked",
        "implemented",
    )
    return any(keyword in text for keyword in interview_keywords)


def block_prompt_injection(answer: str) -> bool:
    text = answer.lower()
    return not any(marker in text for marker in PROMPT_INJECTION_MARKERS)
