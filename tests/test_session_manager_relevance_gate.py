import sys

sys.path.append(r"D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main")

import pytest
import streamlit as st

from interview_app_frontend.state.session_manager import submit_answer


@pytest.fixture(autouse=True)
def reset_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def test_submit_answer_skips_memory_for_irrelevant_answers():
    st.session_state["answer"] = "I documented project notes and joined planning meetings."
    st.session_state["answers"] = []
    st.session_state["answer_submit_error"] = ""
    st.session_state["future_session_memory"] = [{"takeaway": "Keep it concise"}]
    st.session_state["current_question"] = "Describe a time you improved system performance under constraints."

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "interview_app_frontend.state.session_manager.evaluate_submission",
            lambda question, answer: {
                "question": question,
                "answer": answer.strip(),
                "reference_answer": "",
                "semantic_similarity_score": 0.0,
                "overall_decision": "fail",
                "scores": {"relevance": 1, "structure": 3, "specificity": 1, "communication": 6, "problem_solving_approach": 2},
                "labels": {
                    "relevance": "Does not address system performance or measurable results",
                    "structure": "Basic narrative, lacks clear STAR structure",
                    "specificity": "No measurable outcomes provided",
                    "communication": "Clear but not relevant to the question",
                    "problem_solving_approach": "No relevant technical problem-solving demonstrated",
                },
                "feedback": {
                    "summary": "The answer is not relevant to the question about system performance.",
                    "strengths": [],
                    "key_issues": [
                        "The answer is not relevant to the question about system performance",
                        "No measurable results provided",
                        "No technical optimisation or constraints discussed",
                    ],
                    "improvements": [
                        "Focus on a real example involving system performance improvement",
                        "Include measurable metrics such as latency, throughput, or resource usage",
                        "Explain constraints and technical decisions",
                    ],
                },
                "follow_up": {
                    "question": "Can you describe a real example where you improved system performance under constraints with measurable results?",
                    "type": "relevance_gate",
                    "target_dimension": "relevance",
                },
                "memory_storage_allowed": False,
                "relevance_gate_applied": True,
                "topic_match": False,
            },
        )

        submit_answer()

    assert st.session_state["future_session_memory"] == [{"takeaway": "Keep it concise"}]
