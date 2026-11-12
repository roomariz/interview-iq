import pytest
from unittest.mock import patch

from interview_app_backend.services.evaluation_service import evaluate_submission
from interview_app_frontend.utils.feedback_model import normalise_feedback_payload
from interview_app_frontend.utils.feedback_view import build_behaviour_aware_trust


QUESTION = "Describe a time you improved system performance under constraints."


@pytest.mark.parametrize(
    "answer",
    [
        "We improved teamwork by setting clearer meeting notes and helping the squad stay aligned.",
        "I wrote documentation for the release process and kept the project wiki up to date.",
        "I led the project planning, coordinated milestones, and managed stakeholder updates.",
        "I handled leadership duties and project management, but not system performance work.",
    ],
)
def test_relevance_gate_variants_fail(answer):
    with patch("interview_app_backend.services.evaluation_service.is_answer_relevant", return_value=False):
        result = evaluate_submission(QUESTION, answer)

    assert result["overall_decision"] == "fail"
    assert result["scores"]["relevance"] == 1
    assert result["scores"]["specificity"] == 1
    assert result["relevance_gate_applied"] is True
    assert result["follow_up"]["type"] == "relevance_gate"


def test_empty_trust_fallback_never_renders_blank_text():
    view_model = normalise_feedback_payload(
        {
            "question": QUESTION,
            "answer": "A relevant answer with no trust payload.",
            "scores": {"relevance": 8, "structure": 7, "specificity": 8, "communication": 8, "problem_solving_approach": 8},
            "overall_decision": "pass",
            "validation_warning": {
                "severity": "high",
                "interpretation": "Treat the scores as provisional; the flags affect interpretation.",
                "reasoning_depth": "implicit",
            },
            "overall_decision_detail": {"reason": "Decision should be reviewed because trust level is low"},
        }
    )

    trust_display = build_behaviour_aware_trust(view_model)

    assert trust_display["summary"].strip()
    assert trust_display["detail"].strip()
    assert trust_display["decision"].strip()
    assert trust_display["depth"].strip()


def test_exact_review_cue_matches_current_copy():
    view_model = normalise_feedback_payload(
        {
            "question": QUESTION,
            "answer": "A pass-level answer with a warning.",
            "scores": {"relevance": 8, "structure": 8, "specificity": 8, "communication": 8, "problem_solving_approach": 8},
            "overall_decision": "pass",
            "validation_warning": {
                "severity": "high",
                "interpretation": "Treat the scores as provisional; the flags affect interpretation.",
                "reasoning_depth": "implicit",
            },
            "overall_decision_detail": {"reason": "Decision should be reviewed because trust level is low"},
        }
    )

    trust_display = build_behaviour_aware_trust(view_model)

    assert "Read the scores as provisional." in trust_display["summary"]
