import re
from typing import Any


_STOPWORDS = {
    "a",
    "an",
    "and",
    "about",
    "describe",
    "for",
    "from",
    "how",
    "into",
    "me",
    "my",
    "of",
    "on",
    "the",
    "this",
    "that",
    "time",
    "to",
    "under",
    "what",
    "when",
    "where",
    "why",
    "with",
    "you",
    "your",
}
_RELEVANCE_KEYWORDS = {
    "performance",
    "latency",
    "throughput",
    "optimisation",
    "optimization",
    "optimised",
    "optimized",
    "constraints",
    "constraint",
    "measurable",
    "metrics",
    "result",
    "results",
    "system",
    "cpu",
    "memory",
    "cache",
    "caching",
    "query",
    "database",
    "api",
}
_WORK_SIGNALS = {"built", "designed", "delivered", "implemented", "improved", "led", "reduced", "shipped", "worked", "team", "project"}


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def classify_relevance(question: str, answer: str) -> dict[str, Any]:
    if not answer.strip():
        return {"match": False, "confidence": "high", "reason": "empty answer"}
    question_tokens = {token for token in _tokens(question) if token not in _STOPWORDS}
    answer_tokens = _tokens(answer)
    if not question_tokens or not answer_tokens:
        return {"match": False, "confidence": "low", "reason": "insufficient tokens"}
    overlap = question_tokens & answer_tokens
    keyword_hits = answer_tokens & _RELEVANCE_KEYWORDS
    work_hits = answer_tokens & _WORK_SIGNALS
    match = bool(overlap or (keyword_hits and work_hits))
    confidence = "medium" if match else "low"
    reason = "keyword overlap" if match else "no domain overlap"
    return {"match": match, "confidence": confidence, "reason": reason}
