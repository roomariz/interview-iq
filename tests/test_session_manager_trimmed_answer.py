import sys

sys.path.append(r"D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main")

import pytest
import streamlit as st

from interview_app_frontend.state.session_manager import ensure_session_state, submit_answer


@pytest.fixture(autouse=True)
def reset_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def test_submit_answer_persists_trimmed_answer():
    ensure_session_state()
    expected_answer = "Strong example answer with enough detail to pass the minimum length gate."
    st.session_state["answer"] = f"  {expected_answer}  "
    st.session_state["answers"] = []
    st.session_state["answer_submit_error"] = ""
    st.session_state["current_question"] = "Describe a time you improved system performance under constraints."
    st.session_state["session_start_time"] = 1000.0
    st.session_state["session_duration_minutes"] = 0

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "interview_app_frontend.state.session_manager.evaluate_submission",
            lambda question, answer: {
                "question": question,
                "answer": answer.strip(),
                "reference_answer": "Model answer.",
                "semantic_similarity_score": 0.91,
                "overall_decision": "pass",
                "scores": {"relevance": 7, "structure": 4, "specificity": 4, "communication": 7, "problem_solving_approach": 5},
                "labels": {},
                "feedback": {"summary": "Strong response.", "strengths": ["Provides a concrete example"], "key_issues": [], "improvements": []},
                "follow_up": {"question": "How would you tighten the example?", "type": "depth_probe", "target_dimension": "problem_solving_approach"},
                "memory_storage_allowed": True,
                "trust": {"trust_level": "high", "score_confidence": 0.9},
                "feedback_validation": {"status": "checked"},
                "relevance_gate_applied": False,
                "topic_match": True,
            },
        )

        submit_answer()

    stored = st.session_state["answers"][0]
    assert stored["answer"] == expected_answer
    assert stored["question"] == "Describe a time you improved system performance under constraints."
    assert stored["scores"] == {"relevance": 7, "structure": 4, "specificity": 4, "communication": 7, "problem_solving_approach": 5}
    assert st.session_state["answer"] == f"  {expected_answer}  "
    assert st.session_state["answer_submit_error"] == ""
    assert st.session_state["current_screen"] == "feedback"
    assert st.session_state["session_complete"] is False
    assert st.session_state["feedback"]["answer"] == expected_answer
    assert "performance under constraints" in st.session_state["feedback"]["question"]
    assert st.session_state["future_session_memory"]
    assert st.session_state["future_session_memory"][0]["takeaway"]
