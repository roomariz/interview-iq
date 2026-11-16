import pytest
from unittest.mock import patch

from interview_app_backend.services.evaluation_service import evaluate_submission
from interview_app_frontend.utils.pipeline_view import build_pipeline_summary, build_reliability_card


QUESTION = "Describe a time you improved system performance under constraints."
ANSWER = "I reduced latency from 2s to 200ms by profiling hot paths and removing one slow query."


def _base_result() -> dict:
    return {
        "question": QUESTION,
        "answer": ANSWER,
        "scores": {"relevance": 8, "structure": 7, "specificity": 8, "communication": 8, "problem_solving_approach": 7},
        "labels": {key: "" for key in ("relevance", "structure", "specificity", "communication", "problem_solving_approach")},
        "feedback": {"summary": "Strong answer.", "strengths": ["Direct"], "key_issues": ["Trade-offs need more detail"], "improvements": ["Name one rejected alternative"]},
        "reasoning": {"clarity": "Clear", "alternative_approaches": "One alternative", "trade_off_awareness": "Some trade-off", "evidence": "Latencies improved"},
        "follow_up": {"question": "", "type": "", "target_dimension": ""},
        "evaluation_context": {
            "evaluation_version": "trust-v4",
            "evaluation_trace": ["version:trust-v4"],
            "has_metrics": True,
            "has_structure": True,
            "has_reasoning": True,
            "has_tradeoffs": False,
            "has_alternatives": False,
            "confidence": {"metrics": 0.9, "structure": 0.8, "reasoning": 0.7, "tradeoffs": 0.2, "alternatives": 0.2},
            "contradiction_flags": [],
            "anomaly_flags": [],
            "numeric_signals": ["2s", "200ms"],
            "impact_strength": "strong",
            "topic_match": True,
        },
        "validation_warning": {"severity": "low", "trust_level": "high", "score_confidence": 0.9, "reasoning_depth": "explicit", "interpretation": "Use normally."},
        "trust": {"trust_level": "high", "trust_definition": "High confidence", "score_confidence": 0.9, "decision_confidence": "high", "impact_strength": "strong", "reason": "Grounded"},
        "overall_decision": "pass",
        "overall_decision_detail": {"value": "pass", "score_based_value": "pass", "trust_level": "high", "score_confidence": 0.9, "decision_confidence": "high", "gating_applied": False, "reason": "Grounded"},
        "reference_answer": "Reference answer.",
        "semantic_similarity_score": 0.88,
    }


def test_pipeline_exposes_stages_and_confidence() -> None:
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=True), patch(
        "interview_app_backend.services.evaluation_service.evaluate_answer", return_value=_base_result()
    ):
        result = evaluate_submission(QUESTION, ANSWER)

    pipeline = result["evaluation_pipeline"]
    assert [stage["name"] for stage in pipeline["stages"]] == [
        "input_validator",
        "pre_classifier",
        "semantic_verifier",
        "evaluation_engine",
        "grounding_validator",
        "rule_enforcer",
        "trust_calculator",
        "follow_up_generator",
        "output_formatter",
    ]
    assert result["grounding_score"] == 0.9
    assert result["evaluation_confidence"]["overall"] >= 0.7
    assert pipeline["grounded"] is True


def test_classifier_conflict_downgrades_trust() -> None:
    with patch("interview_app_backend.services.evaluation_pipeline.classify_relevance", return_value={"match": False, "confidence": "low", "reason": "no domain overlap"}), patch(
        "interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=True
    ), patch("interview_app_backend.services.evaluation_service.evaluate_answer", return_value=_base_result()):
        result = evaluate_submission(QUESTION, ANSWER)

    assert result["evaluation_pipeline"]["classifier_conflict"] is True
    assert "classifier_conflict" in result["validation_warning"]["anomaly_flags"]
    assert result["validation_warning"]["trust_level"] in {"low", "medium"}
    assert result["evaluation_confidence"]["conflict"] is True
    assert result["failure_type"] == "none"
    assert result["provisional"]


def test_off_topic_answer_is_forced_to_fail() -> None:
    payload = _base_result()
    payload["evaluation_context"]["topic_match"] = False
    payload["topic_match"] = False
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=False), patch(
        "interview_app_backend.services.evaluation_service.evaluate_answer", return_value=payload
    ):
        result = evaluate_submission("How do you manage system performance?", "Documentation and collaboration.")

    assert result["topic_match"] is False
    assert result["relevance_gate_applied"] is True
    assert result["overall_decision"] == "fail"
    assert result["failure_type"] == "off_topic"
    assert result["overall_decision_detail"]["gating_applied"] is True
    assert result["trust"]["trust_level"] == "low"


def test_low_grounding_preserves_pass() -> None:
    payload = _base_result()
    payload["validation_warning"]["score_confidence"] = 0.2
    payload["trust"]["score_confidence"] = 0.2
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=True), patch(
        "interview_app_backend.services.evaluation_service.evaluate_answer", return_value=payload
    ):
        result = evaluate_submission(QUESTION, ANSWER)

    assert result["overall_decision"] == "pass"
    assert result["assessment_status"] == "provisional"
    assert result["failure_type"] == "none"
    assert result["grounding_score"] == 0.2


def test_follow_up_is_grounded_from_issue_context() -> None:
    payload = _base_result()
    payload["follow_up"] = {"question": "", "type": "", "target_dimension": ""}
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=True), patch(
        "interview_app_backend.services.evaluation_service.evaluate_answer", return_value=payload
    ):
        result = evaluate_submission(QUESTION, ANSWER)

    follow_up = result["follow_up"]
    assert follow_up["question"].strip()
    assert QUESTION not in follow_up["question"]
    assert "latency" in follow_up["question"]
    assert ANSWER in follow_up["context_note"]
    assert "decid" in follow_up["question"] or "decision" in follow_up["question"]


def test_pipeline_summary_is_user_facing() -> None:
    summary = build_pipeline_summary(
        {
            "evaluation_summary": {"confidence_label": "Medium", "grounding_label": "Partial", "failure_type": "low_specificity", "reason": "The answer needs more concrete evidence and metrics."},
            "evaluation_confidence": {"overall": 0.52, "grounding": 0.45, "relevance": 0.6, "completeness": 0.5},
            "grounding_score": 0.45,
            "failure_type": "low_specificity",
        },
        {"evaluation_summary": {}, "evaluation_confidence": {}},
    )

    assert summary["confidence_label"] == "Medium"
    assert summary["grounding_label"] == "Partial"
    assert summary["failure_type"] == "low_specificity"
    assert "metrics" in summary["reason"].lower()


def test_reliability_card_matches_user_copy() -> None:
    card = build_reliability_card(
        {
            "evaluation_summary": {"confidence_label": "Low", "grounding_label": "Weak", "failure_type": "off_topic", "reason": "The answer does not sufficiently address the question, so the evaluation is limited."},
            "failure_type": "off_topic",
        },
        {"evaluation_summary": {}, "evaluation_confidence": {}},
    )

    assert card["title"] == "Evaluation Reliability"
    assert card["confidence"] == "Low"
    assert card["grounding"] == "Weak"
    assert card["assessment"] == "Off-topic answer"
    assert "appropriate" in card["message"].lower()


def test_reliability_card_reflects_low_backend_trust() -> None:
    card = build_reliability_card(
        {
            "trust": {"trust_level": "low"},
            "evaluation_summary": {"confidence_label": "Medium", "grounding_label": "Weak", "failure_type": "off_topic", "reason": "The answer does not directly address the question."},
            "failure_type": "off_topic",
        },
        {"evaluation_summary": {}, "evaluation_confidence": {}},
    )

    assert card["confidence"] == "Low"


def test_reliability_card_uses_pattern_based_interpretation() -> None:
    card = build_reliability_card(
        {
            "evaluation_summary": {"confidence_label": "Medium", "grounding_label": "Strong", "failure_type": "low_specificity"},
            "failure_type": "low_specificity",
        },
        {"evaluation_summary": {}, "evaluation_confidence": {}},
    )

    assert card["confidence"] == "Medium"
    assert card["grounding"] == "Strong"
    assert card["assessment"] == "Limited evidence"
    assert "generally reliable" in card["message"].lower()


def test_pipeline_reports_failure_without_fabricated_scores() -> None:
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=True), patch(
        "interview_app_backend.services.evaluation_service.evaluate_answer",
        side_effect=RuntimeError("model chain exhausted"),
    ), pytest.raises(RuntimeError, match="no scores were recorded"):
        evaluate_submission(QUESTION, ANSWER)
