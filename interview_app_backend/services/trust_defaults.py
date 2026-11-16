"""Missing validation never implies confidence merely because scores are high."""

from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.evaluation_rules import derive_overall_decision, classify_fallback_failure


def build_fallback_review_state(
    scores: Mapping[str, Any], *, topic_match: bool = True,
    relevance_gate_applied: bool = False, overall_decision: str = "",
) -> dict[str, Any]:
    off_topic = relevance_gate_applied or not topic_match
    decision = "fail" if off_topic else overall_decision or derive_overall_decision(scores)
    definition = (
        "Low evaluation depth but high decision confidence because the answer is not relevant to the question."
        if off_topic else "Evaluation confidence is unavailable; treat the result as provisional."
    )
    reason = "The answer is not relevant to the question." if off_topic else definition
    trust = {
        "trust_level": "low", "trust_definition": definition, "score_confidence": 0.0,
        "decision_confidence": "high" if off_topic else "low", "impact_strength": "unknown",
        "reason": reason,
    }
    return {
        "failure_type": classify_fallback_failure(scores, topic_match, relevance_gate_applied),
        "trust": trust,
        "validation_warning": {
            "has_warning": True, "severity": "info" if off_topic else "medium",
            "trust_level": "low", "score_confidence": 0.0,
            "reasoning_depth": "not_applicable" if off_topic else "unknown", "interpretation": reason,
        },
        "overall_decision_detail": {
            "value": decision, "score_based_value": decision, "trust_level": "low",
            "score_confidence": 0.0, "decision_confidence": trust["decision_confidence"],
            "gating_applied": True, "reason": reason,
        },
    }
