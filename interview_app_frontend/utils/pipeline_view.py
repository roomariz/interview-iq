from collections.abc import Mapping
from typing import Any


def _value(source: Mapping[str, Any], key: str, fallback: Any = "") -> Any:
    value = source.get(key, fallback)
    return value if value is not None else fallback


def _number(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def build_pipeline_summary(raw_feedback: Mapping[str, Any] | None, view_model: Mapping[str, Any]) -> dict[str, str]:
    raw = dict(raw_feedback or {})
    confidence = raw.get("evaluation_confidence")
    if not isinstance(confidence, Mapping):
        confidence = _value(view_model, "evaluation_confidence", {})
    summary = raw.get("evaluation_summary")
    if not isinstance(summary, Mapping):
        summary = _value(view_model, "evaluation_summary", {})
    failure_type = str(_value(raw, "failure_type", _value(view_model, "failure_type", "none"))).strip() or "none"
    confidence_label = str(summary.get("confidence_label", "Medium")).strip() or "Medium"
    grounding_label = str(summary.get("grounding_label", "Partial")).strip() or "Partial"
    reason = str(summary.get("reason", "")).strip()
    if not reason:
        grounding_score = _number(confidence.get("grounding", _value(raw, "grounding_score", 0.0)))
        if grounding_score >= 0.7:
            reason = "The feedback is well supported by the answer."
        elif grounding_score < 0.4:
            reason = "Only broad guidance is appropriate because the evidence is thin."
        else:
            reason = "Some parts of the feedback are only partially supported by the evidence."
    trust_level = str(_value(raw, "trust", _value(view_model, "trust", {})).get("trust_level", "")).strip().lower() if isinstance(_value(raw, "trust", _value(view_model, "trust", {})), Mapping) else ""
    if trust_level == "low":
        confidence_label = "Low"
    return {
        "confidence_label": confidence_label,
        "grounding_label": grounding_label,
        "failure_type": failure_type,
        "reason": reason,
    }


def build_reliability_card(raw_feedback: Mapping[str, Any] | None, view_model: Mapping[str, Any]) -> dict[str, str]:
    summary = build_pipeline_summary(raw_feedback, view_model)
    failure_type = summary["failure_type"]
    confidence = summary["confidence_label"]
    grounding = summary["grounding_label"]
    validation = _value(view_model, "validation_warning", {})
    validation_note = str(validation.get("interpretation", "")).strip() if isinstance(validation, Mapping) else ""
    dot_colour = "#7f8ea8"
    if failure_type == "off_topic":
        return {
            "title": "Evaluation Reliability",
            "confidence": "Low",
            "grounding": "Weak",
            "assessment": "Off-topic answer",
            "message": "The answer does not sufficiently address the question, so only broad guidance is appropriate.",
            "dot_colour": "#7f8ea8",
        }
    if failure_type in {"hallucination_risk", "low_evidence", "low_specificity", "structural_gap"}:
        assessment = "Limited evidence"
        if confidence == "Low":
            grounding = "Weak"
    elif confidence == "High" and grounding == "Strong":
        assessment = "Strong evidence"
    else:
        assessment = "Limited evidence"
    if confidence == "High":
        dot_colour = "#2f7a4f"
    elif confidence == "Medium":
        dot_colour = "#b8891d"
    message = validation_note or _reliability_message(confidence, grounding, failure_type)
    return {
        "title": "Evaluation Reliability",
        "confidence": confidence,
        "grounding": grounding,
        "assessment": assessment,
        "message": message,
        "dot_colour": dot_colour,
    }


def _reliability_message(confidence: str, grounding: str, failure_type: str) -> str:
    if failure_type == "off_topic":
        return "The answer does not sufficiently address the question, so only broad guidance is appropriate."
    if confidence == "Low" and grounding == "Weak":
        return "This evaluation is provisional because the evidence is thin."
    if confidence == "Medium" and grounding == "Strong":
        return "This evaluation is generally reliable, but some areas may benefit from clearer evidence."
    if confidence == "High" and grounding == "Strong":
        return "This evaluation is well supported by the answer."
    return "This feedback is based on the answer provided, but some parts rest on limited evidence."
