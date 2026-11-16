"""Candidate performance and evaluator reliability are independent contracts."""

import copy
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from interview_app_backend.services.evaluation_decisions import apply_decision_adjustments
from interview_app_backend.services.evaluation_output import finalise_evaluation
from interview_app_backend.services.evaluation_rules import derive_overall_decision
from interview_app_backend.services.feedback_repair import repair_feedback
from interview_app_backend.services.feedback_support import validate_feedback_support
from interview_app_backend.services.question_followup import question_bound_followup


@pytest.fixture
def live():
    return json.loads((Path(__file__).parent / "fixtures/live_evaluation.json").read_text(encoding="utf-8"))


def supported_payload(live, confidence):
    data = copy.deepcopy(live)
    data.update(feedback={"summary": live["summary"], "strengths": ["Clear diagnostic sequence"],
                          "key_issues": [], "improvements": ["Explain the evidence behind the recovery choice"]},
                feedback_validation={"status": "checked", "issues": [], "removed_claims": []},
                relevance_assessment={"status": "relevant", "question_type": "scenario_troubleshooting"},
                evaluation_confidence={"relevance": .95})
    data["validation_warning"] = {"score_confidence": confidence, "severity": "info"}
    data["trust"] = {"score_confidence": confidence, "trust_level": "low"}
    return data


@pytest.mark.parametrize("confidence", [.0, .2, .44, .75])
def test_low_confidence_never_changes_candidate_verdict(live, confidence):
    data = supported_payload(live, confidence)
    data["overall_decision"] = "borderline pass"  # A stale confidence downgrade.
    adjusted = apply_decision_adjustments(data, {"overall": confidence}, confidence)
    result = finalise_evaluation(adjusted)
    assert result["overall_decision"] == derive_overall_decision(live["scores"])
    assert result["overall_decision_detail"]["score_based_value"] == result["overall_decision"]
    assert result["score_confidence"] == confidence
    assert result["assessment_status"] == "provisional"
    assert not result["overall_decision_detail"]["gating_applied"]
    assert result["failure_type"] == "none"
    assert result["failure_reasons"] == []


def test_point_75_without_material_issues_is_medium_not_low(live):
    result = finalise_evaluation(supported_payload(live, .75))
    assert result["trust"]["trust_level"] == "medium"
    assert result["score_confidence"] == .75


def test_real_unsupported_advice_has_traceable_reason(live):
    data = supported_payload(live, .75)
    data["feedback"]["improvements"] = ["Introduce Redis caching and asynchronous messaging"]
    result = finalise_evaluation(data)
    assert not result["feedback"]["improvements"]
    assert result["failure_type"] == "hallucination_risk"
    assert "unsupported_technology" in result["failure_reasons"]
    assert result["reliability_issues"][0]["action"] == "removed"
    assert result["overall_decision"] == derive_overall_decision(live["scores"])


def test_missing_support_is_not_evidence_of_hallucination(live):
    data = supported_payload(live, .75)
    data = validate_feedback_support(data, {}, live["question"], live["answer"])
    result = finalise_evaluation(data)
    assert result["failure_type"] == "none"
    assert result["provisional"]
    assert any(issue["code"] == "missing_claim_support" for issue in result["reliability_issues"])


def test_support_matching_tolerates_formatting_without_allowing_different_inputs(live):
    data = {"feedback": {"strengths": ["Clear   diagnostic sequence."]}}
    raw = {"feedback_support": [{"claim": "Clear diagnostic sequence",
                                "answer_quote": " ".join(live["answer"].split()),
                                "question_quote": live["question"]}]}
    result = validate_feedback_support(data, raw, live["question"], live["answer"])
    assert result["feedback"]["strengths"]


def test_feedback_only_repair_restores_grounded_coaching_without_rescoring(live):
    data = supported_payload(live, .75)
    data["feedback"] = {"strengths": [], "key_issues": [], "improvements": []}
    candidate = {"feedback": {"strengths": ["Considers recovery compatibility"], "key_issues": [],
                              "improvements": ["Explain what would determine your recovery choice"]}}
    candidate["feedback_support"] = [
        {"claim": claim, "answer_quote": "ensuring that the rollback would not create database or compatibility problems",
         "question_quote": "isolate the cause and recover safely"}
        for key in ("strengths", "improvements") for claim in candidate["feedback"][key]
    ]
    call = Mock(return_value=json.dumps(candidate))
    scores = copy.deepcopy(data["scores"])
    result = repair_feedback(data, live["question"], live["answer"], object(), call)
    assert result["feedback"]["strengths"] == candidate["feedback"]["strengths"]
    assert result["feedback"]["improvements"] == candidate["feedback"]["improvements"]
    assert result["feedback"]["key_issues"] == []
    assert result["scores"] == scores
    assert result["trust"]["score_confidence"] == .75
    assert call.call_count == 1


@pytest.mark.parametrize("response", ["{}", "invalid JSON", '{"feedback":{"strengths":["Invented claim"]}}'])
def test_invalid_repair_does_not_create_feedback_or_change_scores(live, response):
    data = supported_payload(live, .2)
    data["feedback"] = {"strengths": [], "key_issues": [], "improvements": []}
    call = Mock(return_value=response)
    result = repair_feedback(data, live["question"], live["answer"], object(), call)
    assert result["scores"] == live["scores"]
    assert result["feedback"]["strengths"] == []
    assert call.call_count == 1


def test_live_followup_probes_a_specific_decision(live):
    result = question_bound_followup(live["question"], live["answer"], {"question_type": "scenario_troubleshooting"})
    assert live["question"] not in result["question"]
    assert "rollback" in result["question"] and "disabling" in result["question"]
    assert len(result["question"].split()) < 25
    assert live["question"] in result["context_note"]


@pytest.mark.parametrize("kind,question,answer", [
    ("technical_knowledge", "How does a hash table resolve collisions?", "Chaining stores colliding entries in a bucket."),
    ("system_design", "Design a notification service.", "I would queue messages and deduplicate deliveries."),
    ("behavioural", "Tell me about a disagreement.", "I listened and proposed a compromise we both accepted."),
])
def test_followup_is_anchored_to_each_answer(kind, question, answer):
    result = question_bound_followup(question, answer, {"question_type": kind})
    assert answer in result["question"]
    assert question not in result["question"]


def test_genuine_off_topic_and_low_quality_still_fail(live):
    data = supported_payload(live, .75)
    data.update(topic_match=False, relevance_gate_applied=True)
    result = finalise_evaluation(data)
    assert result["overall_decision"] == "fail"
    assert result["trust"]["decision_confidence"] == "high"
    data = supported_payload(live, .75)
    data["scores"] = dict.fromkeys(live["scores"], 2)
    assert finalise_evaluation(data)["overall_decision"] == "fail"


def test_extraction_confidence_is_not_replaced_with_presence_constants():
    from interview_app_backend.services.evaluation_rules import build_evaluation_context
    from interview_app_backend.services.evaluation_interpretation import _score_confidence

    evidence = {"has_structure": True, "has_reasoning": True, "confidence": {"structure": .75, "reasoning": .75}}
    context = build_evaluation_context(evidence, "I would check the evidence because it distinguishes the causes.")
    assert context["confidence"] == evidence["confidence"]
    context.update(question_type="scenario_troubleshooting", anomaly_flags=[])
    assert _score_confidence(context, {}) == .75


@pytest.mark.parametrize("confidence", [.2, .75])
def test_supported_coaching_survives_complete_pipeline_at_low_confidence(live, monkeypatch, confidence):
    from interview_app_backend.services import evaluation_service as service
    from interview_app_frontend.utils.feedback_model import normalise_feedback_payload

    scoring = supported_payload(live, confidence)
    scoring.pop("failure_type")
    scoring["feedback_support"] = [
        {"claim": claim, "answer_quote": live["answer"], "question_quote": live["question"]}
        for key in ("strengths", "improvements") for claim in scoring["feedback"][key]
    ]
    monkeypatch.setattr(service, "_get_evaluation_client", lambda: object())
    monkeypatch.setattr(service, "is_answer_relevant", lambda *args: {
        "status": "relevant", "confidence": .95, "question_type": "scenario_troubleshooting"})
    monkeypatch.setattr(service, "generate_reference_answer", lambda *args: "")
    monkeypatch.setattr(service, "calculate_semantic_similarity", lambda *args: 0)
    monkeypatch.setattr(service, "extract_evidence_context", lambda *args, **kwargs: {
        "has_metrics": False, "has_structure": True, "has_reasoning": True,
        "has_tradeoffs": True, "has_alternatives": True, "impact_strength": "weak",
        "confidence": {"structure": confidence, "reasoning": confidence}, "anomaly_flags": [],
    })
    call = Mock(return_value=json.dumps(scoring))
    monkeypatch.setattr(service, "call_llm", call)
    result = service.evaluate_submission(live["question"], live["answer"])
    view = normalise_feedback_payload(result)
    assert call.call_count == 1  # Already grounded feedback needs no repair.
    assert result["overall_decision"] == derive_overall_decision(live["scores"])
    assert result["score_confidence"] == confidence
    assert result["failure_type"] == "none"
    assert view["strengths"] == scoring["feedback"]["strengths"]
    assert view["improvements"] == scoring["feedback"]["improvements"]
    assert view["key_issues"] == []
    assert view["criteria"] and all("STAR" not in item for item in view["criteria"])
