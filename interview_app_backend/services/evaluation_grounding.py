from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.evaluation_rules import build_overall_decision_detail, derive_overall_decision, validate_evaluation_consistency

CONTRACT_PRIORITY = ("evidence", "scores", "labels", "feedback", "reasoning", "follow_up", "trust")


def _copy_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _numeric_confidence(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _grounded_trust(validation_warning: Mapping[str, Any], trust: Mapping[str, Any], scores: Mapping[str, Any]) -> dict[str, Any]:
    score_confidence = _numeric_confidence(validation_warning.get("score_confidence", trust.get("score_confidence", 0.0)))
    detail = build_overall_decision_detail(scores, trust_level=str(validation_warning.get("trust_level", "high")), score_confidence=score_confidence)
    return {
        "trust_level": detail["trust_level"],
        "trust_definition": str(validation_warning.get("trust_definition", trust.get("trust_definition", ""))).strip(),
        "score_confidence": score_confidence,
        "decision_confidence": detail["decision_confidence"],
        "impact_strength": str(validation_warning.get("trust", {}).get("impact_strength", trust.get("impact_strength", ""))).strip(),
        "reason": detail["reason"],
    }


def ground_evaluation_result(evaluation: Mapping[str, Any], evaluation_context: Mapping[str, Any]) -> dict[str, Any]:
    grounded = validate_evaluation_consistency(evaluation, evaluation_context)
    scores = _copy_mapping(grounded.get("scores"))
    validation_warning = _copy_mapping(grounded.get("validation_warning"))
    trust = _copy_mapping(validation_warning.get("trust")) or _copy_mapping(grounded.get("trust"))
    grounded_trust = _grounded_trust(validation_warning, trust, scores)
    grounded["trust"] = grounded_trust
    grounded["overall_decision"] = derive_overall_decision(scores)
    grounded["overall_decision_detail"] = build_overall_decision_detail(
        scores,
        trust_level=grounded_trust["trust_level"],
        score_confidence=grounded_trust["score_confidence"],
    )
    validation_warning.pop("trust", None)
    validation_warning["validation"] = {
        "severity": validation_warning.get("severity", ""),
        "severity_definition": validation_warning.get("severity_definition", ""),
        "trust_level": grounded_trust["trust_level"],
        "trust_definition": grounded_trust["trust_definition"],
        "score_confidence": grounded_trust["score_confidence"],
        "impact_strength": grounded_trust["impact_strength"],
        "anomaly_influence": validation_warning.get("validation", {}).get("anomaly_influence", {}),
    }
    validation_warning["contract_priority"] = list(CONTRACT_PRIORITY)
    validation_warning["source_of_truth"] = "evaluation_context"
    validation_warning["grounding_status"] = "enforced"
    grounded["validation_warning"] = validation_warning
    grounded["grounding_validation"] = {
        "source_of_truth": "evaluation_context",
        "contract_priority": list(CONTRACT_PRIORITY),
        "grounded_fields": ["scores", "labels", "feedback", "reasoning", "follow_up", "trust", "overall_decision_detail"],
        "enforced": True,
        "note": "Raw trust values are overridden by evidence-grounded trust.",
    }
    return grounded
