from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.evaluation_calibration import confidence_level_from_value
from interview_app_backend.services.evaluation_rules import derive_overall_decision

_SCORE_KEYS = ("relevance", "structure", "specificity", "communication", "problem_solving_approach")


def _clamp_score(value: Any) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        score = 0
    return max(0, min(10, score))


def _score_confidence(scores: Mapping[str, Any]) -> float:
    values = [_clamp_score(scores.get(key)) for key in _SCORE_KEYS]
    if not any(values):
        return 0.0
    return round((sum(values) / len(values)) / 10, 2)


def _trust_level(score_confidence: float, topic_match: bool, relevance_gate_applied: bool) -> str:
    if relevance_gate_applied or not topic_match:
        return "high"
    if score_confidence >= 0.75:
        return "high"
    if score_confidence >= 0.45:
        return "medium"
    return "low"


def build_fallback_review_state(
    scores: Mapping[str, Any],
    *,
    topic_match: bool = True,
    relevance_gate_applied: bool = False,
    overall_decision: str = "",
) -> dict[str, Any]:
    decision = str(overall_decision).strip().lower()
    if decision not in {"pass", "borderline pass", "fail"}:
        decision = derive_overall_decision(scores)

    score_confidence = _score_confidence(scores)
    trust_level = _trust_level(score_confidence, topic_match, relevance_gate_applied)
    if relevance_gate_applied or not topic_match:
        failure_type = "off_topic"
        trust_level = "low"
        trust_definition = "Low evaluation depth but high decision confidence because the answer is not relevant to the question."
        reason = "The answer is not relevant to the question, but the off-topic decision is certain."
        impact_strength = "weak"
        severity = "high"
        reasoning_depth = "none"
        interpretation = "This answer is not relevant to the question, so detailed evaluation is not applicable."
        decision_confidence = "high"
    elif trust_level == "high":
        failure_type = "none"
        trust_definition = "High confidence because the score pattern is well supported by the answer."
        reason = "The score pattern is broadly supported by the available evidence."
        impact_strength = "strong"
        severity = "low"
        reasoning_depth = "explicit"
        interpretation = "Use normally; the score pattern is well supported."
        decision_confidence = confidence_level_from_value(score_confidence)
    elif trust_level == "medium":
        failure_type = "low_specificity"
        trust_definition = "Medium confidence because the answer is relevant but only partially evidenced."
        reason = "The answer is relevant, but the evidence is incomplete."
        impact_strength = "moderate"
        severity = "medium"
        reasoning_depth = "developing"
        interpretation = "Use with caution; the answer is relevant, but the evidence is incomplete."
        decision_confidence = "medium"
    else:
        failure_type = "low_specificity"
        trust_definition = "Medium confidence because the answer is relevant but lacks concrete evidence."
        reason = "The answer is relevant, but it does not provide measurable results or deeper reasoning."
        impact_strength = "moderate"
        severity = "medium"
        reasoning_depth = "developing"
        interpretation = "Use with caution; the answer is relevant, but it lacks concrete evidence."
        decision_confidence = "medium"

    trust = {
        "trust_level": trust_level,
        "trust_definition": trust_definition,
        "score_confidence": score_confidence,
        "decision_confidence": decision_confidence,
        "impact_strength": impact_strength,
        "reason": reason,
    }
    validation_warning = {
        "has_warning": relevance_gate_applied or trust_level in {"low", "medium"},
        "severity": severity,
        "trust_level": trust_level,
        "score_confidence": score_confidence,
        "reasoning_depth": reasoning_depth,
        "interpretation": interpretation,
    }
    overall_decision_detail = {
        "value": decision,
        "score_based_value": decision,
        "trust_level": trust_level,
        "score_confidence": score_confidence,
        "decision_confidence": decision_confidence,
        "gating_applied": relevance_gate_applied or trust_level != "high",
        "reason": reason,
    }
    return {
        "failure_type": failure_type,
        "trust": trust,
        "validation_warning": validation_warning,
        "overall_decision_detail": overall_decision_detail,
    }
