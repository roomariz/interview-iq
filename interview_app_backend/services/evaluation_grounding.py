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


def _restrict_low_grounding_feedback(evaluation: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(evaluation)
    data["labels"] = {
        "relevance": "Only limited evidence is available.",
        "structure": "The response is understandable, but the evidence is sparse.",
        "specificity": "Only limited evidence is available.",
        "communication": "The response is understandable at a high level.",
        "problem_solving_approach": "The reasoning is too thin for a detailed review.",
    }
    data["feedback"] = {
        "summary": "The response has limited support in the available evidence, so only broad guidance is appropriate.",
        "strengths": ["The response is readable and attempts to address the prompt."],
        "key_issues": ["The evidence is too limited for trade-off-specific feedback."],
        "improvements": ["Add one concrete metric or measurable impact.", "Keep the explanation close to the evidence you can support."],
    }
    data["reasoning"] = {
        "clarity": "The response is understandable, but the evidence is too limited for deeper review.",
        "alternative_approaches": "Do not infer alternatives that are not clearly stated.",
        "trade_off_awareness": "Keep trade-off comments general until the answer provides support.",
        "evidence": "The available evidence is too thin for detailed claims.",
    }
    data["evaluation_summary"] = {
        "confidence_label": "Low",
        "grounding_label": "Weak",
        "failure_type": "low_evidence",
        "reason": "The response has limited support in the available evidence.",
        "decision": str(data.get("overall_decision", "")).strip(),
    }
    data["grounding_validation"] = {
        "source_of_truth": "evaluation_context",
        "contract_priority": list(CONTRACT_PRIORITY),
        "grounded_fields": ["scores", "labels", "feedback", "reasoning", "follow_up", "trust", "overall_decision_detail"],
        "enforced": True,
        "note": "Low grounding restricts feedback to broad guidance only.",
        "feedback_depth": "generic",
    }
    return data


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
    if grounded_trust["score_confidence"] < 0.4:
        grounded = _restrict_low_grounding_feedback(grounded)
        scores = _copy_mapping(grounded.get("scores"))
        validation_warning = _copy_mapping(grounded.get("validation_warning"))
        trust = _copy_mapping(validation_warning.get("trust")) or _copy_mapping(grounded.get("trust"))
        grounded_trust = _grounded_trust(validation_warning, trust, scores)
        grounded["trust"] = grounded_trust
        grounded["overall_decision_detail"] = build_overall_decision_detail(
            scores,
            trust_level=grounded_trust["trust_level"],
            score_confidence=grounded_trust["score_confidence"],
        )
    validation_warning["trust"] = grounded_trust
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
