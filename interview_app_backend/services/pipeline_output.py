"""Existing relevance-gate output and pipeline metadata formatting."""

from collections.abc import Mapping
from typing import Any

from interview_app_backend.services.evaluation_decisions import (
    apply_decision_adjustments, build_evaluation_summary, classify_failure_type,
)


def attach_relevance_gate(result: dict[str, Any], input_state: Mapping[str, Any], relevance_state: Mapping[str, Any]) -> dict[str, Any]:
    evaluation = dict(result)
    evaluation["topic_match"] = False
    evaluation["relevance_gate_applied"] = True
    evaluation["failure_type"] = "off_topic"
    evaluation["overall_decision"] = "fail"
    evaluation["overall_decision_detail"] = {
        "value": "fail",
        "score_based_value": "fail",
        "trust_level": "low",
        "score_confidence": 0.0,
        "decision_confidence": "high",
        "gating_applied": True,
        "reason": "The answer is not relevant to the question.",
    }
    evaluation["trust"] = {
        "trust_level": "low",
        "trust_definition": "Low evaluation depth but high decision confidence because the answer is not relevant to the question.",
        "score_confidence": 0.0,
        "decision_confidence": "high",
        "impact_strength": "unknown",
        "reason": "The answer is not relevant to the question, so the off-topic decision is certain.",
    }
    evaluation["validation_warning"] = {
        "severity": "info",
        "trust_level": "low",
        "score_confidence": 0.0,
        "reasoning_depth": "not_applicable",
        "interpretation": "This answer is not relevant to the question, so detailed evaluation is not applicable.",
        "has_warning": True,
        "anomaly_flags": ["off_topic"],
        "validation": {
            "severity": "info",
            "severity_definition": "Expected behaviour; the answer is not relevant to the question.",
            "trust_level": "low",
            "trust_definition": evaluation["trust"]["trust_definition"],
            "score_confidence": 0.0,
            "impact_strength": "unknown",
            "anomaly_influence": {},
        },
    }
    evaluation["feedback"] = {
        "summary": "The answer is not relevant to the question.",
        "strengths": [],
        "key_issues": ["The answer is not relevant to the question."],
        "improvements": [f"Address the original question directly: {input_state['question']}"],
    }
    evaluation["reasoning"] = {
        "clarity": "The response does not answer the prompt directly.",
        "alternative_approaches": "Not assessed because the answer is not relevant to the question.",
        "trade_off_awareness": "Not assessed because the answer is not relevant to the question.",
        "evidence": "No supported evidence for the requested topic was provided.",
    }
    evaluation["follow_up"] = {
        "question": f"Please address the original question directly: {input_state['question']}",
        "type": "relevance_gate",
        "target_dimension": "relevance",
        "reasoning_action": "Address the substance of the original question.",
        "context_note": f"Original question: {input_state['question']}",
        "stage": 1,
    }
    evaluation["evaluation_confidence"] = {"relevance": 0.0, "grounding": 0.0, "completeness": 0.0, "overall": 0.0, "conflict": False}
    evaluation["grounding_score"] = 0.0
    evaluation["relevance_assessment"] = relevance_state.get("assessment", {})
    return evaluation


def attach_pipeline(result: dict[str, Any], input_state: Mapping[str, Any], relevance_state: Mapping[str, Any], grounded: bool) -> dict[str, Any]:
    evaluation = dict(result)
    evaluation["question"] = input_state["question"]
    evaluation["answer"] = input_state["answer"]
    evaluation_context = dict(evaluation.get("evaluation_context", {}))
    grounding_score = _grounding_score(evaluation)
    evaluation["grounding_score"] = grounding_score
    evaluation["evaluation_confidence"] = _evaluation_confidence(evaluation, relevance_state, grounding_score)
    evaluation["failure_type"] = evaluation.get(
        "failure_type",
        classify_failure_type(evaluation, evaluation_context, grounding_score, evaluation["evaluation_confidence"]),
    )
    evaluation = apply_decision_adjustments(evaluation, evaluation["evaluation_confidence"], grounding_score)
    evaluation["evaluation_summary"] = build_evaluation_summary(
        evaluation, evaluation["failure_type"], evaluation["evaluation_confidence"], grounding_score
    )
    if evaluation.get("trust", {}).get("trust_level") == "low":
        evaluation["evaluation_summary"]["confidence_label"] = "Low"
    evaluation["evaluation_pipeline"] = {
        "stages": [
            {"name": "input_validator", "status": "ok", "issues": list(input_state.get("issues", []))},
            {
                "name": "pre_classifier",
                "status": "ok",
                "match": bool(relevance_state["preclassification"]["match"]),
                "confidence": relevance_state["preclassification"].get("confidence", "low"),
                "reason": relevance_state["preclassification"].get("reason", ""),
            },
            {
                "name": "semantic_verifier",
                "status": "uncertain" if relevance_state.get("assessment", {}).get("status") == "uncertain" else "ok",
                "match": bool(relevance_state["combined_verdict"]),
                "conflict": bool(relevance_state["conflict"]),
            },
            {"name": "evaluation_engine", "status": "ok" if grounded else "skipped"},
            {"name": "grounding_validator", "status": "ok" if grounded else "skipped", "grounding_score": evaluation.get("grounding_score", 0.0)},
            {"name": "rule_enforcer", "status": "ok" if grounded else "applied"},
            {"name": "trust_calculator", "status": "ok", "evaluation_confidence": evaluation.get("evaluation_confidence", {})},
            {"name": "follow_up_generator", "status": "ok", "grounding_score": evaluation.get("follow_up", {}).get("grounding_score", 0.0)},
            {"name": "output_formatter", "status": "ok"},
        ],
        "classifier_conflict": bool(relevance_state["conflict"]),
        "input_issues": list(input_state.get("issues", [])),
        "grounded": grounded,
    }
    from interview_app_backend.services.evaluation_output import finalise_evaluation

    return finalise_evaluation(evaluation)


def _grounding_score(evaluation: Mapping[str, Any]) -> float:
    warning = evaluation.get("validation_warning", {}) if isinstance(evaluation.get("validation_warning"), Mapping) else {}
    trust = evaluation.get("trust", {}) if isinstance(evaluation.get("trust"), Mapping) else {}
    value = warning.get("score_confidence", trust.get("score_confidence", 0.0))
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _evaluation_confidence(evaluation: Mapping[str, Any], relevance_state: Mapping[str, Any], grounding_score: float) -> dict[str, Any]:
    context = evaluation.get("evaluation_context", {}) if isinstance(evaluation.get("evaluation_context"), Mapping) else {}
    coverage_values = [1.0 if context.get(key) else 0.0 for key in ("has_metrics", "has_structure", "has_reasoning", "has_tradeoffs", "has_alternatives")]
    completeness = round(sum(coverage_values) / len(coverage_values), 2) if coverage_values else 0.0
    relevance = round(float(relevance_state.get("confidence", 0.0)), 2)
    grounding = round(grounding_score, 2)
    overall = min(relevance, grounding)
    if relevance_state.get("assessment", {}).get("status") == "uncertain":
        overall = min(overall, 0.29)
    return {
        "relevance": relevance,
        "grounding": grounding,
        "completeness": completeness,
        "overall": overall,
        "conflict": bool(relevance_state.get("conflict")),
    }
