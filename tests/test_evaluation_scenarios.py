import json
import pytest
import streamlit as st
from unittest.mock import patch

from interview_app_backend.services.evaluation_service import evaluate_submission
from interview_app_frontend.state.session_manager import submit_answer
from interview_app_frontend.utils.feedback_model import normalise_feedback_payload
from interview_app_frontend.utils.feedback_view import (
    build_behaviour_aware_trust,
    build_follow_up,
    build_key_takeaway,
    build_score_consistency,
)


QUESTION = "Describe a time you improved system performance under constraints."


@pytest.fixture(autouse=True)
def reset_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def _scores(relevance, structure, specificity, communication, problem_solving_approach, technical_accuracy=None, clarity=None):
    return {
        "technical_accuracy": specificity if technical_accuracy is None else technical_accuracy,
        "clarity": communication if clarity is None else clarity,
        "structure": structure,
        "relevance": relevance,
        "problem_solving_approach": problem_solving_approach,
        "specificity": specificity,
        "communication": communication,
    }


def _payload(scores, *, key_issues=None, improvements=None, strengths=None, summary="Clear summary.", labels=None, reasoning=None, follow_up=None):
    return {
        "evidence": {"metrics": [], "actions": [], "reasoning": ""},
        "scores": scores,
        "labels": labels or {key: "" for key in ("relevance", "structure", "specificity", "communication", "problem_solving_approach")},
        "feedback": {"summary": summary, "strengths": strengths or [], "key_issues": key_issues or [], "improvements": improvements or []},
        "reasoning": reasoning or {"clarity": "", "alternative_approaches": "", "trade_off_awareness": "", "evidence": ""},
        "follow_up": follow_up or {"question": "", "type": "", "target_dimension": ""},
        "example_answer": {},
        "strengths": strengths or [],
        "improvement_areas": improvements or [],
        "overall_summary": summary,
        "evaluation_version": "trust-v4",
        "evaluation_trace": ["version:trust-v4"],
        "impact_strength": "weak",
    }


def _evaluate(answer, context, payload, relevant=True):
    support = {"feedback_support": [
        {"claim": claim, "answer_quote": answer, "question_quote": QUESTION}
        for key in ("strengths", "key_issues", "improvements")
        for claim in payload.get("feedback", {}).get(key, [])
    ]}
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=relevant), patch(
        "interview_app_backend.services.evaluation_service.get_openrouter_client", return_value=object()
    ), patch(
        "interview_app_backend.services.evaluation_service.call_llm", return_value=json.dumps(support)
    ), patch(
        "interview_app_backend.services.evaluation_service.generate_reference_answer", return_value="Reference answer."
    ), patch("interview_app_backend.services.evaluation_service.calculate_semantic_similarity", return_value=0.88), patch(
        "interview_app_backend.services.evaluation_service.extract_evidence_context", return_value=context
    ), patch("interview_app_backend.services.evaluation_service.parse_json_response", return_value=payload):
        return evaluate_submission(QUESTION, answer)


def test_out_of_scope_answer_fails():
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=False), patch(
        "interview_app_backend.services.evaluation_service.generate_reference_answer"
    ) as ref, patch("interview_app_backend.services.evaluation_service.calculate_semantic_similarity") as sim:
        result = evaluate_submission(QUESTION, "I documented the rollout plan and ran weekly status meetings.")

    assert result["overall_decision"] == "fail"
    assert result["scores"]["relevance"] <= 2
    assert result["scores"]["specificity"] <= 2
    assert result["validation_warning"]["trust_level"] == "low"
    assert not result["memory_storage_allowed"]
    assert result["follow_up"]["type"] == "relevance_gate"
    assert "system performance" in result["follow_up"]["question"].lower()
    assert "cache" not in " ".join(result["feedback"]["improvements"]).lower()
    ref.assert_not_called()
    sim.assert_not_called()


def test_weak_answer_borderline_or_fail():
    payload = _payload(_scores(6, 5, 4, 6, 3), key_issues=["Missing specific metrics for improvement"], improvements=["Add metrics to show impact"])
    result = _evaluate("I improved the service a bit by tuning the slowest part and cleaning up the path.", {"has_metrics": False, "has_structure": False, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.1, "structure": 0.2, "reasoning": 0.2, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "weak"}, payload)
    view = normalise_feedback_payload(result)
    follow_up = build_follow_up(view)
    assert result["overall_decision"] in {"borderline pass", "fail"}
    assert result["scores"]["relevance"] >= 4
    assert result["scores"]["specificity"] <= 4
    assert view["improvements"] == payload["feedback"]["improvements"]
    assert not result["memory_storage_allowed"]
    assert result["validation_warning"]["reasoning_depth"] in {"none", "implicit", "developing"}
    assert QUESTION not in follow_up["question"]
    assert "decid" in follow_up["question"] or "decision" in follow_up["question"]


def test_metrics_without_reasoning_flagged():
    payload = _payload(_scores(8, 7, 8, 7, 5), key_issues=["Trade-offs are only implied", "Explain technical decisions and trade-offs"], improvements=["Name the trade-off you accepted", "Explain why this approach was chosen"])
    result = _evaluate("I cut latency from 400ms to 90ms by caching repeated work and simplifying one query.", {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.9, "structure": 0.8, "reasoning": 0.2, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["400ms", "90ms"], "topic_match": True, "impact_strength": "strong"}, payload)
    view = normalise_feedback_payload(result)
    follow_up = build_follow_up(view)
    assert result["scores"]["specificity"] >= 7
    assert result["scores"]["problem_solving_approach"] <= 6
    assert result["validation_warning"]["reasoning_depth"] in {"implicit", "developing"}
    assert view["key_issues"] == payload["feedback"]["key_issues"]
    assert not result["memory_storage_allowed"]
    assert follow_up["target_dimension"] == "problem_solving_approach"


def test_strong_answer_passes_with_trust():
    payload = _payload(_scores(8, 7, 8, 8, 6), key_issues=["Alternative approaches were not discussed"], improvements=["Mention one rejected alternative"], strengths=["Direct, relevant answer"])
    result = _evaluate("I reduced latency from 2s to 200ms by profiling hot paths and removing a slow query.", {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.9, "structure": 0.9, "reasoning": 0.8, "tradeoffs": 0.4, "alternatives": 0.4}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["2s", "200ms"], "topic_match": True, "impact_strength": "strong"}, payload)
    assert result["overall_decision"] == "pass"
    assert result["scores"]["relevance"] >= 8 and result["scores"]["specificity"] >= 7 and result["scores"]["structure"] >= 6
    assert result["validation_warning"]["trust_level"] in {"medium", "high"}


def test_best_answer_high_trust():
    payload = _payload(_scores(9, 9, 9, 9, 9), key_issues=["Alternative approaches were compared lightly"], improvements=["Mention one rejected alternative"], strengths=["Clear STAR structure", "Concise answer"])
    result = _evaluate("I led a three-month optimisation because latency was affecting users, compared two alternatives, and chose the lower-risk trade-off.", {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": True, "has_alternatives": True, "reasoning_markers": ["because"], "tradeoff_markers": ["trade-off"], "alternative_markers": ["alternatives"], "confidence": {"metrics": 0.95, "structure": 0.95, "reasoning": 0.95, "tradeoffs": 0.95, "alternatives": 0.95}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["90%"], "topic_match": True, "impact_strength": "strong"}, payload)
    view = normalise_feedback_payload(result)
    follow_up = build_follow_up(view)
    assert result["overall_decision"] == "pass"
    assert all(result["scores"][key] >= 8 for key in ("relevance", "structure", "specificity", "communication", "problem_solving_approach"))
    assert result["validation_warning"]["reasoning_depth"] == "deep"
    assert result["validation_warning"]["trust_level"] == "high"
    assert len(view["improvements"]) <= 2
    assert QUESTION not in follow_up["question"]
    assert "decid" in follow_up["question"] or "decision" in follow_up["question"]


def test_misleading_metrics_reduce_trust():
    payload = _payload(_scores(7, 6, 6, 7, 4), key_issues=["Impact is unclear despite the number"], improvements=["Explain the real user or business impact"], labels={"relevance": "", "structure": "", "specificity": "Strong measurable results", "communication": "", "problem_solving_approach": ""}, summary="Numbers are present, but the impact is unclear.")
    result = _evaluate("I handled 100 requests and it was a huge improvement.", {"has_metrics": True, "metrics": [{"type": "volume"}], "has_structure": False, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.8, "structure": 0.3, "reasoning": 0.2, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": [], "anomaly_flags": ["misleading_metrics"], "numeric_signals": ["100"], "topic_match": True, "impact_strength": "moderate"}, payload)
    view = normalise_feedback_payload(result)
    assert "misleading_metrics" in result["validation_warning"]["anomaly_flags"]
    assert result["scores"]["specificity"] <= 6
    assert result["validation_warning"]["trust_level"] in {"low", "medium"}
    assert view["improvements"] == payload["feedback"]["improvements"]
    assert not result["memory_storage_allowed"]


def test_score_consistency_gap_reduces_trust():
    payload = _payload(_scores(8, 8, 8, 8, 8), labels={"relevance": "", "structure": "", "specificity": "Strong measurable results", "communication": "", "problem_solving_approach": ""}, key_issues=["Strong measurable results"], improvements=["Tighten reasoning"], summary="Looks strong, but the signals do not line up.")
    result = _evaluate("I improved the system, but I will not mention metrics.", {"has_metrics": False, "metrics": [], "has_structure": True, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.7, "structure": 0.8, "reasoning": 0.2, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": ["metrics_contradiction"], "anomaly_flags": [], "numeric_signals": [], "topic_match": True, "impact_strength": "moderate"}, payload)
    view = normalise_feedback_payload(result)
    view["overall_decision"] = "pass"
    view["overall_decision_detail"]["score_based_value"] = "fail"
    consistency = build_score_consistency(view)
    assert consistency["has_gap"]
    assert consistency["note"]
    assert result["validation_warning"]["trust_level"] in {"low", "medium"}


def test_low_trust_pass_case_shows_review_cue():
    payload = _payload(_scores(8, 8, 8, 8, 8), key_issues=["Reasoning is thin despite the strong scores"], improvements=["Explain why the trade-off was acceptable"])
    result = _evaluate("I delivered the change with numbers, but the reasoning is thin.", {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": False, "has_tradeoffs": False, "has_alternatives": False, "confidence": {"metrics": 0.85, "structure": 0.85, "reasoning": 0.2, "tradeoffs": 0.2, "alternatives": 0.2}, "contradiction_flags": ["reasoning_contradiction"], "anomaly_flags": ["misleading_metrics"], "numeric_signals": ["80%"], "topic_match": True, "impact_strength": "weak"}, payload)
    view = normalise_feedback_payload(result)
    trust = build_behaviour_aware_trust(view)
    assert result["overall_decision"] == "pass"
    assert result["validation_warning"]["trust_level"] == "low"
    assert result["overall_decision_detail"]["decision_confidence"] == "low"
    assert "provisional" in trust["summary"].lower()


def test_memory_storage_rules_and_cap():
    st.session_state["answer"] = "I improved the service by profiling the slow step and changing one query."
    st.session_state["answers"] = []
    st.session_state["answer_submit_error"] = ""
    st.session_state["current_question"] = QUESTION
    repeated = {
        "question": QUESTION,
        "answer": st.session_state["answer"],
        "reference_answer": "Reference answer.",
        "semantic_similarity_score": 0.8,
        "overall_decision": "borderline pass",
        "scores": _scores(6, 5, 4, 6, 5),
        "labels": {key: "" for key in ("relevance", "structure", "specificity", "communication", "problem_solving_approach")},
        "feedback": {"summary": "Weak but relevant.", "strengths": [], "key_issues": ["Missing specific metrics for improvement"], "improvements": ["Add metrics to show impact"]},
        "follow_up": {"question": "How would you prove the impact of this change with one concrete metric?", "type": "depth_probe", "target_dimension": "specificity"},
        "validation_warning": {"reasoning_depth": "implicit", "trust_level": "medium", "interpretation": "Use with caution."},
        "overall_decision_detail": {"decision_confidence": "medium", "trust_level": "medium"},
        "memory_storage_allowed": True,
        "feedback_validation": {"status": "checked"},
        "trust": {"trust_level": "medium", "score_confidence": .6},
        "topic_match": True,
    }
    with patch("interview_app_frontend.state.session_manager.evaluate_submission", return_value=repeated):
        for _ in range(6):
            submit_answer()
    assert len(st.session_state["future_session_memory"]) == 5
    st.session_state["future_session_memory"] = [{"focus": "specificity"}]
    weak_view = normalise_feedback_payload(repeated | {"future_session_memory": []})
    assert build_follow_up(weak_view | {"future_session_memory": []})["stage"] == 1
    assert build_follow_up(weak_view | {"future_session_memory": [{"focus": "specificity"}]})["stage"] == 1
    assert build_follow_up(weak_view | {"future_session_memory": [{"focus": "specificity"}, {"focus": "specificity"}]})["stage"] == 1


def test_memory_count_cannot_invent_repeat_gaps():
    base = normalise_feedback_payload(_payload(_scores(5, 4, 4, 6, 5), key_issues=["Missing specific metrics for improvement"], improvements=["Add metrics to show impact"]))
    q1 = build_follow_up(base | {"future_session_memory": []})
    q2 = build_follow_up(base | {"future_session_memory": [{"focus": "specificity"}]})
    q3 = build_follow_up(base | {"future_session_memory": [{"focus": "specificity"}, {"focus": "specificity"}]})
    assert [q1["stage"], q2["stage"], q3["stage"]] == [1, 1, 1]
    assert len({q1["question"], q2["question"], q3["question"]}) == 1
    assert "same gap" not in q3["question"].lower()


def test_takeaway_quality():
    takeaway = build_key_takeaway(normalise_feedback_payload(_payload(_scores(6, 5, 4, 6, 5), strengths=["Direct answer"], improvements=["Add metrics to prove impact"])))
    assert len(takeaway.split()) <= 20
    assert "provisional" in takeaway.lower()
    assert "no established weakness" in takeaway.lower()
    assert "keep the answer concrete" not in takeaway.lower()


def test_trust_display_integrity():
    result = _evaluate("I reduced latency from 2s to 200ms by removing a slow query.", {"has_metrics": True, "metrics": [{"type": "latency"}], "has_structure": True, "has_reasoning": True, "has_tradeoffs": True, "has_alternatives": False, "confidence": {"metrics": 0.9, "structure": 0.9, "reasoning": 0.9, "tradeoffs": 0.8, "alternatives": 0.3}, "contradiction_flags": [], "anomaly_flags": [], "numeric_signals": ["2s", "200ms"], "topic_match": True, "impact_strength": "strong"}, _payload(_scores(8, 8, 8, 8, 8), strengths=["Clear result"], improvements=["Explain one rejected alternative"]))
    view = normalise_feedback_payload(result)
    trust = build_behaviour_aware_trust(view)
    assert trust["summary"].strip()
    assert trust["detail"].strip()
    assert trust["decision"].strip()
    assert trust["depth"].strip()
    assert view["overall_decision_detail"]["decision_confidence"].strip()
    assert view["validation_warning"]["interpretation"].strip()
