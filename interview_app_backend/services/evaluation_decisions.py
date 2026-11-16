from collections.abc import Mapping
from typing import Any


_FAILURE_MESSAGES = {
    "off_topic": "The answer does not directly address the question.",
    "hallucination_risk": "Some feedback is only weakly supported by the answer.",
    "low_evidence": "There is too little evidence to trust the detailed scoring fully.",
    "low_specificity": "The answer needs more concrete evidence and metrics.",
    "structural_gap": "The answer needs clearer structure.",
}


def _confidence_value(evaluation_confidence: Mapping[str, Any]) -> float:
    try:
        return float(evaluation_confidence.get("overall", 0.0))
    except (TypeError, ValueError):
        return 0.0


def classify_failure_type(
    evaluation: Mapping[str, Any],
    evaluation_context: Mapping[str, Any],
    grounding_score: float,
    evaluation_confidence: Mapping[str, Any],
) -> str:
    scores = dict(evaluation.get("scores", {})) if isinstance(evaluation.get("scores"), Mapping) else {}
    anomaly_flags = set(evaluation_context.get("anomaly_flags", []))
    topic_match = bool(evaluation_context.get("topic_match", evaluation.get("topic_match", True)))
    if not topic_match or evaluation.get("relevance_gate_applied"):
        return "off_topic"
    if any(flag in anomaly_flags for flag in ("fake_metrics", "misleading_metrics")):
        return "hallucination_risk"
    if not evaluation_context.get("has_metrics") and int(scores.get("specificity", 0)) <= 3:
        return "low_specificity"
    if not evaluation_context.get("has_structure") and int(scores.get("structure", 0)) <= 3:
        return "structural_gap"
    if sum(1 for key in ("has_metrics", "has_structure", "has_reasoning", "has_tradeoffs", "has_alternatives") if evaluation_context.get(key)) <= 1:
        return "low_evidence"
    if _confidence_value(evaluation_confidence) < 0.35:
        return "low_evidence"
    return "none"


def apply_decision_adjustments(
    evaluation: Mapping[str, Any],
    evaluation_confidence: Mapping[str, Any],
    grounding_score: float,
) -> dict[str, Any]:
    data = dict(evaluation)
    from interview_app_backend.services.evaluation_rules import derive_overall_decision

    decision = derive_overall_decision(data["scores"]) if data.get("scores") else str(data.get("overall_decision", "")).strip() or "fail"
    confidence = _confidence_value(evaluation_confidence)
    if str(data.get("failure_type", "")).strip() == "off_topic":
        decision = "fail"
        detail = dict(data.get("overall_decision_detail", {}))
        detail["decision_confidence"] = "high"
        detail["reason"] = "The answer is not relevant to the question."
        data["overall_decision_detail"] = detail
    elif confidence < 0.3:
        detail = dict(data.get("overall_decision_detail", {}))
        detail["decision_confidence"] = "low"
        detail["gating_applied"] = True
        data["overall_decision_detail"] = detail
        trust = dict(data.get("trust", {}))
        trust["trust_level"] = "low"
        trust["trust_definition"] = "Low confidence or strong conflict; treat the result as provisional."
        trust["decision_confidence"] = "low"
        trust["reason"] = "Evaluation confidence is low; read the result cautiously."
        data["trust"] = trust
        warning = dict(data.get("validation_warning", {}))
        warning["trust_level"] = "low"
        warning["interpretation"] = "Some feedback is only partially supported by the answer."
        validation = dict(warning.get("validation", {}))
        validation["trust_level"] = "low"
        warning["validation"] = validation
        warning.pop("trust", None)
        data["validation_warning"] = warning
        detail["trust_level"] = "low"
        data["overall_decision_detail"] = detail
    data["overall_decision"] = decision
    detail = dict(data.get("overall_decision_detail", {}))
    if detail:
        detail["value"] = decision
        if not detail.get("score_based_value"):
            detail["score_based_value"] = str(evaluation.get("overall_decision", decision))
        data["overall_decision_detail"] = detail
    return data


def build_evaluation_summary(
    evaluation: Mapping[str, Any],
    failure_type: str,
    evaluation_confidence: Mapping[str, Any],
    grounding_score: float,
) -> dict[str, str]:
    confidence = _confidence_value(evaluation_confidence)
    if confidence >= 0.7:
        confidence_label = "High"
    elif confidence >= 0.4:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"
    if grounding_score >= 0.7:
        grounding_label = "Strong"
    elif grounding_score >= 0.4:
        grounding_label = "Partial"
    else:
        grounding_label = "Weak"
    failure_key = failure_type if failure_type in _FAILURE_MESSAGES else "none"
    reason = _FAILURE_MESSAGES.get(failure_key, "The feedback is broadly supported by the answer.")
    if confidence_label == "High" and failure_key == "none":
        reason = "The feedback is well supported by the answer."
    return {
        "confidence_label": confidence_label,
        "grounding_label": grounding_label,
        "failure_type": failure_key,
        "reason": reason,
        "decision": str(evaluation.get("overall_decision", "")).strip(),
    }
