import logging
import re
from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.evaluation_calibration import (
    build_normalisation_detail,
    confidence_level_from_value,
    decision_confidence_from_trust,
)
from interview_app_backend.services.evaluation_insights import apply_evaluation_consistency, build_evaluation_context
from interview_app_backend.services.relevance_preclassifier import classify_relevance
from interview_app_backend.llm.client import get_openrouter_client
from interview_app_backend.llm.provider_clients import get_google_client
from interview_app_backend.llm.provider_clients import get_grok_client
from config.settings import PRIMARY_PROVIDER


LOGGER = logging.getLogger(__name__)


def _get_single_provider_client():
    if PRIMARY_PROVIDER == "open-router":
        return get_openrouter_client()
    return get_openrouter_client()

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
_WORK_SIGNALS = {
    "built",
    "designed",
    "delivered",
    "implemented",
    "improved",
    "led",
    "reduced",
    "shipped",
    "worked",
    "team",
    "project",
}


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def _keyword_relevance_match(question: str, answer: str) -> bool:
    question_tokens = {token for token in _tokens(question) if token not in _STOPWORDS}
    answer_tokens = _tokens(answer)
    if not question_tokens or not answer_tokens:
        return False
    overlap = question_tokens & answer_tokens
    keyword_hits = answer_tokens & _RELEVANCE_KEYWORDS
    work_hits = answer_tokens & _WORK_SIGNALS
    return bool(overlap or (keyword_hits and work_hits))


def _semantic_relevance_match(question: str, answer: str) -> bool | None:
    from interview_app_backend.llm.client import call_llm

    try:
        client = _get_single_provider_client()
    except Exception:
        raise ValueError("No LLM client configured")
    prompt = (
        f"Question:\n{question}\n\nAnswer:\n{answer}\n\n"
        "Does this answer directly address the question about system performance, constraints, and measurable results? "
        "Answer only YES or NO."
    )
    payload = call_llm(prompt, client, temperature=0, task="evaluation.relevance_check")
    verdict = payload.strip().upper()
    if "YES" in verdict:
        return True
    if "NO" in verdict:
        return False
    return None


def is_answer_relevant(question: str, answer: str) -> bool:
    preclassification = classify_relevance(question, answer)
    if not answer.strip():
        return False
    if not preclassification["match"] and preclassification["confidence"] == "high":
        return False
    try:
        semantic_match = _semantic_relevance_match(question, answer)
    except Exception:
        return bool(preclassification["match"])
    if semantic_match is False:
        return False
    if semantic_match is True:
        return bool(preclassification["match"]) or semantic_match
    return bool(preclassification["match"])


def derive_overall_decision(scores: Mapping[str, Any]) -> str:
    values = [int(scores.get(key) or 0) for key in ("relevance", "structure", "specificity", "communication", "problem_solving_approach")]
    if not any(values):
        return "pass"
    average = sum(values) / len(values)
    reasoning_score = values[4]
    if average >= 7 and reasoning_score >= 6:
        return "pass"
    if average < 5 or reasoning_score <= 4:
        return "fail"
    return "borderline pass"


def build_overall_decision_detail(scores: Mapping[str, Any], trust_level: str = "high", score_confidence: float | int | None = None) -> dict[str, Any]:
    if not trust_level:
        trust_level = "low"
        score_confidence = 0.3
    score_based_value = derive_overall_decision(scores)
    detail_value = "borderline" if score_based_value == "borderline pass" else score_based_value
    score_confidence_level = confidence_level_from_value(score_confidence)
    decision_confidence = decision_confidence_from_trust(trust_level, score_confidence_level)
    reason = "Score-based decision retained."
    if trust_level == "medium":
        reason = "Decision retained with medium trust."
    elif trust_level == "low":
        reason = "Decision should be reviewed because trust level is low"
    return {
        "value": detail_value,
        "score_based_value": detail_value,
        "trust_level": trust_level,
        "score_confidence": score_confidence_level,
        "decision_confidence": decision_confidence,
        "gating_applied": trust_level != "high",
        "reason": reason,
    }


def classify_fallback_failure(scores: Mapping[str, Any], topic_match: bool, relevance_gate_applied: bool) -> str:
    if relevance_gate_applied or not topic_match:
        return "off_topic"
    relevance = int(scores.get("relevance") or 0)
    specificity = int(scores.get("specificity") or 0)
    reasoning = int(scores.get("problem_solving_approach") or 0)
    if relevance >= 4 and specificity <= 4 and reasoning <= 5:
        return "low_specificity"
    if relevance >= 4 and specificity >= 5 and reasoning <= 5:
        return "low_evidence"
    if relevance >= 4 and reasoning <= 5:
        return "low_evidence"
    return "low_specificity"


def build_normalisation(scores: Mapping[str, Any]) -> dict[str, Any]:
    return build_normalisation_detail(scores)


def validate_evaluation_consistency(evaluation: Mapping[str, Any], evaluation_context: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(evaluation)
    scores = dict(data.get("scores", {}))
    metrics_detected = bool(evaluation_context.get("metrics_detected") or evaluation_context.get("has_metrics") or evaluation_context.get("metric_count"))
    if not metrics_detected and "specificity" in scores:
        scores["specificity"] = min(int(scores.get("specificity") or 0), 3)
        data["scores"] = scores
    result = apply_evaluation_consistency(data, evaluation_context)
    if result.get("validation_warnings"):
        LOGGER.warning("Evaluation contradictions and anomalies normalised: %s", "; ".join(result["validation_warnings"]))
    return result
