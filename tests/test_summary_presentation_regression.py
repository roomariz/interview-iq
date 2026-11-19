"""Presentation must retain existing assessments without evaluating again."""

from copy import deepcopy
from unittest.mock import patch

import pytest
import streamlit as st

from interview_app_frontend.components.session_summary_screen import (
    _render_latest_question_recap, _render_score_breakdown,
)
from interview_app_frontend.state.session_feedback import _apply_answer_feedback
from interview_app_frontend.utils.feedback_model import FEEDBACK_DIMENSIONS, score_band
from interview_app_frontend.utils.session_summary_view import build_session_summary_view
from shared.scoring import derive_overall_decision


def feedback(index=1):
    return {
        "question": f"Question {index}?", "answer": f"Answer {index}.",
        "scores": dict.fromkeys((key for key, _ in FEEDBACK_DIMENSIONS), 7),
        "overall_decision": "pass",
        "feedback": {"summary": f"Existing takeaway {index}.",
                     "strengths": [f"Strength {index}"],
                     "improvements": [f"Improvement {index}"]},
    }


@pytest.mark.parametrize("score,label", [
    (0, "Needs Work"), (3.9, "Needs Work"), (4, "Needs Work"),
    (6.9, "Needs Work"), (7, "Good"), (8.9, "Good"),
    (9, "Excellent"), (10, "Excellent"),
])
def test_summary_score_thresholds(score, label):
    with patch("interview_app_frontend.components.session_summary_screen.st.markdown") as render:
        _render_score_breakdown({"average_scores": {"relevance": score}})
    assert f"{score}/10 ({label})" in render.call_args_list[1].args[0]


@pytest.mark.parametrize("score,band", [(0, "Weak"), (3, "Weak"),
    (4, "Needs improvement"), (6, "Needs improvement"), (7, "Strong"),
    (8, "Strong"), (9, "Excellent"), (10, "Excellent")])
def test_individual_answer_bands_remain_distinct(score, band):
    assert score_band(score) == band


def test_individual_reasoning_gate_and_session_average_remain_distinct():
    scores = dict(zip((key for key, _ in FEEDBACK_DIMENSIONS), [8, 8, 8, 7, 4]))
    assert sum(scores.values()) / 5 == 7
    assert derive_overall_decision(scores) == "fail"
    assert build_session_summary_view({"answers": [{"scores": scores}]})["overall_performance"] == "70% (Good)"


@pytest.mark.parametrize("count", [1, 3, 5])
def test_recap_retains_all_stored_takeaways_for_partial_and_complete_sessions(count):
    st.session_state.clear()
    try:
        for index in range(1, count + 1):
            payload = feedback(index)
            _apply_answer_feedback(st.session_state, payload["question"], payload["answer"], payload)
        history = deepcopy(st.session_state.answers)
        assert [answer["summary"] for answer in history] == [f"Existing takeaway {i}." for i in range(1, count + 1)]
        for live in (st.session_state.feedback, []):
            summary = build_session_summary_view({"answers": history, "feedback": live})
            recap = summary["latest_question_recap"]
            assert recap["question"] == f"Question {count}?"
            assert recap["summary"] == f"Existing takeaway {count}."
            assert recap["strengths"] == [f"Strength {count}"]
            assert recap["improvement_areas"] == [f"Improvement {count}"]
            assert summary["questions_completed"] == count
        assert st.session_state.answers == history
    finally:
        st.session_state.clear()


def test_existing_blank_history_can_use_matching_feedback_without_mutation():
    payload = feedback()
    answer = {"question": payload["question"], "answer": payload["answer"],
              "summary": "", "overall_decision": "pass", "scores": payload["scores"]}
    original = deepcopy(answer)
    recap = build_session_summary_view({"answers": [answer], "feedback": payload})["latest_question_recap"]
    assert recap["summary"] == "Existing takeaway 1."
    assert recap["strengths"] == ["Strength 1"]
    assert recap["improvement_areas"] == ["Improvement 1"]
    assert answer == original


@pytest.mark.parametrize("field", ["question", "answer"])
def test_stale_feedback_is_not_attached_to_latest_answer(field):
    payload = feedback()
    answer = {"question": payload["question"], "answer": payload["answer"], field: "Different"}
    recap = build_session_summary_view({"answers": [answer], "feedback": payload})["latest_question_recap"]
    assert recap["summary"] == ""
    assert recap["strengths"] == []
    assert recap["improvement_areas"] == []


def test_recap_uses_recorded_key_issues_when_improvements_are_empty():
    recap = build_session_summary_view({"answers": [{"question": "Q?", "improvements": [],
        "key_issues": ["Existing issue"]}]})["latest_question_recap"]
    assert recap["summary"] == ""
    assert recap["decision"] == ""
    assert recap["improvement_areas"] == ["Existing issue"]
    assert "latest_question_recap" not in build_session_summary_view({"answers": []})


def test_recap_escapes_stored_feedback():
    with patch("interview_app_frontend.components.session_summary_screen.st.markdown") as render:
        _render_latest_question_recap({"latest_question_recap": {
            "question": "<img src=x>", "summary": "<script>unsafe</script>",
            "strengths": ["<b>strength</b>"], "improvement_areas": ["A & B"]}})
    html = render.call_args.args[0]
    assert "<script>" not in html and "<img src=x>" not in html
    assert "&lt;script&gt;unsafe&lt;/script&gt;" in html
    assert "&lt;b&gt;strength&lt;/b&gt;" in html and "A &amp; B" in html
