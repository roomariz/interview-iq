"""Regression checks use the user's unchanged live evaluation and mocked inference."""

import copy
import json
from pathlib import Path

import pytest

from interview_app_backend.services.evaluation_output import finalise_evaluation
from interview_app_backend.services.evaluation_rules import classify_fallback_failure
from interview_app_backend.services.feedback_integrity import clean_feedback, example_text, memory_is_allowed
from interview_app_backend.services.feedback_support import validate_feedback_support
from interview_app_backend.services.question_validation import validate_generated_items
from interview_app_backend.services.question_followup import question_bound_followup
from interview_app_frontend.utils.feedback_model import normalise_feedback_payload
from interview_app_frontend.utils.feedback_view import build_follow_up, build_key_takeaway, build_behaviour_aware_trust
from tests.question_contract_fixtures import valid_bundle


@pytest.fixture
def live():
    return json.loads((Path(__file__).parent / "fixtures/live_evaluation.json").read_text())


def test_empty_feedback_never_injects_demo_advice(live):
    live.update(feedback={"summary": live["summary"], "strengths": [], "key_issues": [], "improvements": []})
    view = normalise_feedback_payload(live)
    assert view["strengths"] == view["key_issues"] == view["improvements"] == []
    assert view["example_answer"] == ""
    assert view["trust"]["score_confidence"] == 0.0
    assert view["summary"] == live["summary"]


def test_live_claim_contradictions_are_withheld(live):
    cleaned = clean_feedback(live)
    assert not any("not relevant" in item for item in cleaned["strengths"])
    assert not any("caching" in item or "vertical scaling" in item for item in cleaned["key_issues"])
    assert cleaned["scores"] == live["scores"]
    assert cleaned["feedback_validation"]["removed_claims"]


def test_final_confidence_cannot_increase_to_resolve_conflict(live):
    result = finalise_evaluation(live)
    for section in ("trust", "validation_warning", "overall_decision_detail"):
        assert result[section]["score_confidence"] == 0.0
        assert result[section]["trust_level"] == "low"
        assert "High confidence" not in result[section]["trust_definition"]
    assert result["evaluation_confidence"]["overall"] == 0.0
    assert not result["memory_storage_allowed"]
    assert result["future_session_memory"] == []
    assert "key_takeaway" not in result


@pytest.mark.parametrize("value", [{}, [], "{}", "[]", "null", '{"answer": ""}', None, "```json\n{}\n```"])
def test_malformed_examples_are_unavailable(value):
    assert example_text(value) == ""


def test_real_example_text_is_preserved():
    assert example_text("I would compare the release logs.") == "I would compare the release logs."


def test_high_scores_have_no_default_failure(live):
    assert classify_fallback_failure(live["scores"], True, False) == "none"
    assert classify_fallback_failure({"relevance": 5, "specificity": 2}, True, False) == "low_specificity"
    assert classify_fallback_failure(live["scores"], False, True) == "off_topic"


@pytest.mark.parametrize("question,answer", [
    ("How would you diagnose a failed release?", "I would correlate logs with the deployment time."),
    ("How do hash tables resolve collisions?", "Chaining stores colliding entries in a bucket."),
    ("Tell me about a disagreement at work?", "We disagreed about priorities and agreed a compromise."),
])
def test_claim_support_is_bound_to_current_inputs(question, answer):
    evaluation = {"feedback": {"strengths": ["Explains the approach"], "key_issues": [], "improvements": []}}
    raw = {"feedback_support": [{"claim": "Explains the approach", "answer_quote": answer,
                                 "question_quote": question}]}
    supported = validate_feedback_support(copy.deepcopy(evaluation), raw, question, answer)
    assert supported["feedback"]["strengths"]
    raw["feedback_support"][0]["answer_quote"] = "An invented answer from another session."
    unsupported = validate_feedback_support(copy.deepcopy(evaluation), raw, question, answer)
    assert unsupported["feedback"]["strengths"] == []
    assert unsupported["feedback_validation"]["status"] == "withheld_claims"


@pytest.mark.parametrize("support", [None, {}, [None], [{"claim": "bad"}], "malformed"])
def test_missing_or_malformed_support_withholds_claims(support):
    evaluation = {"feedback": {"strengths": ["Unsupported strength"]}}
    result = validate_feedback_support(evaluation, {"feedback_support": support}, "A question?", "An answer.")
    assert result["feedback"]["strengths"] == []


def test_followup_does_not_infer_repeat_gap_from_memory(live):
    live["follow_up"] = question_bound_followup(live["question"], live["answer"],
                                               {"question_type": "scenario_troubleshooting"})
    view = normalise_feedback_payload(live)
    followup = build_follow_up(view)
    assert live["question"] not in followup["question"]
    assert "rollback" in followup["question"]
    assert "same gap" not in followup["question"]
    assert "real example" not in followup["question"]


def test_memory_requires_validation_and_trust(live):
    assert not memory_is_allowed(live)
    result = finalise_evaluation(live)
    view = normalise_feedback_payload(result)
    assert "not relevant" not in build_key_takeaway(view)
    assert "no established weakness" in build_key_takeaway(view)
    result.update(memory_storage_allowed=True, feedback_validation={"status": "checked"})
    result["trust"].update(trust_level="medium", score_confidence=.6)
    result["validation_warning"]["severity"] = "info"
    assert memory_is_allowed(result)


def test_off_topic_trust_distinguishes_verdict_from_scoring(live):
    live.update(failure_type="off_topic", topic_match=False, relevance_gate_applied=True)
    result = finalise_evaluation(live)
    view = normalise_feedback_payload(result)
    trust = build_behaviour_aware_trust(view)
    assert result["trust"]["score_confidence"] == 0
    assert result["trust"]["decision_confidence"] == "high"
    assert "Decision confidence: high" in trust["summary"]
    assert not result["memory_storage_allowed"]


def test_non_performance_scenarios_ignore_incidental_focus_name():
    bundle = valid_bundle()
    bundle["questions"][0]["focus_area"] = "Performance"
    bundle["questions"][0]["question"] = (
        "A backend release causes a production incident. Which evidence would you gather before recovering safely?")
    validate_generated_items(bundle["questions"], count=5, role="Backend Engineer", cv_context="", jd_context="")


def test_performance_and_technology_restrictions_still_apply():
    from interview_app_backend.llm.question_contract import QuestionValidationError

    bundle = valid_bundle()
    bundle["questions"][1]["question"] = "Your backend application behaves incorrectly. How would you investigate the issue?"
    with pytest.raises(QuestionValidationError, match="missing_performance_keyword"):
        validate_generated_items(bundle["questions"], count=5, role="Backend Engineer", cv_context="", jd_context="")
    bundle = valid_bundle()
    bundle["questions"][0]["question"] += " Would Redis help?"
    with pytest.raises(QuestionValidationError, match="scenario_a_contains_tech"):
        validate_generated_items(bundle["questions"], count=5, role="Backend Engineer", cv_context="", jd_context="")


def test_live_fixture_through_scoring_pipeline_and_ui(live, monkeypatch):
    from interview_app_backend.services import evaluation_service as service

    monkeypatch.setattr(service, "_get_evaluation_client", lambda: object())
    monkeypatch.setattr(service, "is_answer_relevant", lambda *args: {
        "status": "relevant", "confidence": .95, "question_type": "scenario_troubleshooting"})
    monkeypatch.setattr(service, "generate_reference_answer", lambda *args: "")
    monkeypatch.setattr(service, "calculate_semantic_similarity", lambda *args: 0)
    monkeypatch.setattr(service, "extract_evidence_context", lambda *args, **kwargs: {
        "has_metrics": False, "has_structure": True, "has_reasoning": True,
        "has_tradeoffs": True, "has_alternatives": True, "impact_strength": "weak",
        "confidence": {"structure": .9, "reasoning": .9}, "anomaly_flags": [],
    })
    monkeypatch.setattr(service, "call_llm", lambda *args, **kwargs: json.dumps(live))
    result = service.evaluate_submission(live["question"], live["answer"])
    view = normalise_feedback_payload(result)
    assert result["scores"]["specificity"] == live["scores"]["specificity"]
    assert result["overall_decision"] == live["overall_decision"]
    assert result["failure_type"] != "low_specificity"
    assert result["failure_scope"] == "evaluation_reliability"
    assert result["feedback"]["strengths"] == view["strengths"] == []
    assert not view["key_issues"] and not view["improvements"]
    assert result["evaluation"]["scores"] == result["scores"]
    assert not result["memory_storage_allowed"]
    assert "rollback" in build_follow_up(view)["question"]
    assert view["example_answer"] == ""
