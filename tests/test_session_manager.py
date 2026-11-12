import sys
from unittest.mock import Mock

sys.path.append(r'D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main')

import pytest
import streamlit as st
from interview_app_frontend.state.session_manager import clear_answer, ensure_session_state, exit_session, get_setup_validation_state, is_setup_valid, restart_session, return_to_feedback, return_to_setup, show_sample_answer, submit_answer, update_answer
from interview_app_frontend.state.state_schema import DEFAULT_SESSION_STATE


@pytest.fixture(autouse=True)
def reset_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()

# Enhanced session state initialization test including edge cases
def test_initialize_session_state():
    # Ensure the session state is initialized
    ensure_session_state()

    # Check default values in session state
    for key, value in DEFAULT_SESSION_STATE.items():
        assert key in st.session_state, f"Key {key} is not in session state"
        assert st.session_state[key] == value, f"Value for {key} is not as expected"

    # Additional checks for edge cases
    assert len(st.session_state) == len(DEFAULT_SESSION_STATE), "Session state should have the same number of keys as DEFAULT_SESSION_STATE"

# Test restart session functionality
def test_restart_session():
    # Set some values in the session state
    st.session_state["has_active_session"] = True
    st.session_state["current_question_index"] = 5
    st.session_state["answers"] = ["Answer 1", "Answer 2"]
    
    # Call restart_session
    restart_session()

    # Check that the session state is reset to defaults
    assert st.session_state["has_active_session"] == DEFAULT_SESSION_STATE["has_active_session"]
    assert st.session_state["current_question_index"] == DEFAULT_SESSION_STATE["current_question_index"]
    assert st.session_state["answers"] == DEFAULT_SESSION_STATE["answers"]

# Test exit session functionality
def test_exit_session():
    # Simulate starting a session
    st.session_state["has_active_session"] = True
    st.session_state["current_screen"] = "question"

    # Call exit_session
    exit_session()

    # Verify that the session state is reset to defaults
    assert st.session_state["has_active_session"] == DEFAULT_SESSION_STATE["has_active_session"]
    assert st.session_state["current_screen"] == "welcome"  # Ensure it resets to the welcome screen


def test_restart_session_resets_flow_state():
    st.session_state["current_screen"] = "feedback"
    st.session_state["has_active_session"] = True
    st.session_state["session_complete"] = True
    st.session_state["current_question_index"] = 3
    st.session_state["answers"] = ["First answer"]
    st.session_state["feedback"] = ["Helpful note"]
    st.session_state["summary"] = {"score": 4}
    st.session_state["future_session_memory"] = [{"takeaway": "Keep it concise"}]

    restart_session()

    assert st.session_state["current_screen"] == DEFAULT_SESSION_STATE["current_screen"]
    assert st.session_state["has_active_session"] == DEFAULT_SESSION_STATE["has_active_session"]
    assert st.session_state["session_complete"] == DEFAULT_SESSION_STATE["session_complete"]
    assert st.session_state["current_question_index"] == DEFAULT_SESSION_STATE["current_question_index"]
    assert st.session_state["current_question"] == DEFAULT_SESSION_STATE["current_question"]
    assert st.session_state["answers"] == DEFAULT_SESSION_STATE["answers"]
    assert st.session_state["feedback"] == DEFAULT_SESSION_STATE["feedback"]
    assert st.session_state["summary"] == DEFAULT_SESSION_STATE["summary"]
    assert st.session_state["future_session_memory"] == [{"takeaway": "Keep it concise"}]


def test_exit_session_returns_to_welcome_with_reset_state():
    st.session_state["current_screen"] = "summary"
    st.session_state["has_active_session"] = True
    st.session_state["session_complete"] = True
    st.session_state["current_question_index"] = 4
    st.session_state["answers"] = ["Answer"]
    st.session_state["feedback"] = ["Feedback"]

    exit_session()

    assert st.session_state["current_screen"] == "welcome"
    assert st.session_state["has_active_session"] == DEFAULT_SESSION_STATE["has_active_session"]
    assert st.session_state["session_complete"] == DEFAULT_SESSION_STATE["session_complete"]
    assert st.session_state["current_question_index"] == DEFAULT_SESSION_STATE["current_question_index"]
    assert st.session_state["current_question"] == DEFAULT_SESSION_STATE["current_question"]
    assert st.session_state["answers"] == DEFAULT_SESSION_STATE["answers"]
    assert st.session_state["feedback"] == DEFAULT_SESSION_STATE["feedback"]


def test_start_interview_toggles_loading_state():
    from interview_app_frontend.state.session_manager import start_interview

    st.session_state["setup_role"] = "Backend Engineer"
    st.session_state["setup_persona"] = "Strict"
    st.session_state["setup_difficulty"] = "Medium"
    st.session_state["setup_cv_mode"] = "Upload PDF"
    st.session_state["is_loading"] = False
    st.session_state["current_screen"] = "setup"
    st.session_state["has_active_session"] = False
    st.session_state["session_complete"] = False

    with pytest.MonkeyPatch.context() as monkeypatch:
        rerun_mock = Mock()
        monkeypatch.setattr("interview_app_frontend.state.session_manager.st.rerun", rerun_mock)
        start_interview()

    assert st.session_state["is_loading"] is True
    assert st.session_state["current_screen"] == "generating_question"
    assert st.session_state["has_active_session"] is True
    assert st.session_state["session_complete"] is False
    assert st.session_state["current_question_index"] == 1
    assert st.session_state["current_question"] == ""
    assert st.session_state["answer"] == ""
    assert st.session_state["job_description"] == "—"
    assert st.session_state["cv_status"] == "—"
    rerun_mock.assert_not_called()


def test_start_interview_uses_setup_values():
    from interview_app_frontend.state.session_manager import start_interview

    st.session_state["setup_role"] = "Data Engineer"
    st.session_state["setup_difficulty"] = "Hard"
    st.session_state["setup_persona"] = "Neutral"
    st.session_state["setup_response_style"] = "Concise"
    st.session_state["setup_temperature"] = 0.8
    st.session_state["setup_job_description"] = "Build reliable pipelines."
    st.session_state["setup_cv_mode"] = "Paste Text"
    st.session_state["setup_cv_content"] = "CV text"

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr("interview_app_frontend.state.session_manager.st.rerun", lambda: None)
        start_interview()

    assert st.session_state["role"] == "Data Engineer"
    assert st.session_state["difficulty"] == "Hard"
    assert st.session_state["persona"] == "Neutral"
    assert st.session_state["response_style"] == "Concise"
    assert st.session_state["temperature"] == "0.8"
    assert st.session_state["job_description"] == "Added"
    assert st.session_state["cv_status"] == "Uploaded"


def test_start_interview_requires_required_setup_fields():
    from interview_app_frontend.state.session_manager import start_interview

    st.session_state["setup_role"] = ""
    st.session_state["setup_persona"] = "Strict"
    st.session_state["setup_difficulty"] = "Medium"

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr("interview_app_frontend.state.session_manager.st.rerun", lambda: None)
        start_interview()

    assert st.session_state.get("current_screen", DEFAULT_SESSION_STATE["current_screen"]) == DEFAULT_SESSION_STATE["current_screen"]
    assert st.session_state.get("has_active_session", DEFAULT_SESSION_STATE["has_active_session"]) is False
    assert st.session_state["setup_error"] == "Please complete the required setup fields before starting the interview."
    assert st.session_state.get("current_question_index", DEFAULT_SESSION_STATE["current_question_index"]) == DEFAULT_SESSION_STATE["current_question_index"]
    assert st.session_state.get("answers", DEFAULT_SESSION_STATE["answers"]) == DEFAULT_SESSION_STATE["answers"]
    assert st.session_state.get("feedback", DEFAULT_SESSION_STATE["feedback"]) == DEFAULT_SESSION_STATE["feedback"]


def test_start_interview_clears_previous_setup_error_when_valid():
    from interview_app_frontend.state.session_manager import start_interview

    st.session_state["setup_role"] = "Backend Engineer"
    st.session_state["setup_persona"] = "Strict"
    st.session_state["setup_difficulty"] = "Medium"
    st.session_state["setup_error"] = "Please complete the required setup fields before starting the interview."

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr("interview_app_frontend.state.session_manager.st.rerun", lambda: None)
        start_interview()

    assert st.session_state["setup_error"] == ""


def test_is_setup_valid_requires_required_fields():
    st.session_state["setup_role"] = "Backend Engineer"
    st.session_state["setup_persona"] = "Strict"
    st.session_state["setup_difficulty"] = "Medium"

    assert is_setup_valid() is True

    validation_state = get_setup_validation_state()
    assert validation_state == {
        "setup_role": True,
        "setup_persona": True,
        "setup_difficulty": True,
    }


def test_is_setup_valid_rejects_missing_fields():
    st.session_state["setup_role"] = ""
    st.session_state["setup_persona"] = "Strict"
    st.session_state["setup_difficulty"] = "Medium"

    assert is_setup_valid() is False


def test_get_setup_validation_state_marks_missing_fields():
    st.session_state["setup_role"] = ""
    st.session_state["setup_persona"] = "Strict"
    st.session_state["setup_difficulty"] = ""

    assert get_setup_validation_state() == {
        "setup_role": False,
        "setup_persona": True,
        "setup_difficulty": False,
    }


def test_return_to_setup_preserves_setup_flow_values():
    st.session_state["current_screen"] = "question"
    st.session_state["has_active_session"] = True
    st.session_state["current_question_index"] = 2
    st.session_state["answer"] = "Draft"
    st.session_state["setup_role"] = "Data Engineer"

    return_to_setup()

    assert st.session_state["current_screen"] == "setup"
    assert st.session_state["has_active_session"] is False
    assert st.session_state["current_question_index"] == 0
    assert st.session_state["answer"] == ""
    assert st.session_state["setup_role"] == "Data Engineer"


def test_clear_and_submit_message_state_is_available():
    ensure_session_state()
    assert "answer" in st.session_state
    assert "current_question" in st.session_state


def test_submit_answer_sets_error_when_empty():
    st.session_state["answer"] = "   "
    st.session_state["answers"] = []
    st.session_state["answer_submit_error"] = ""

    submit_answer()

    assert st.session_state["answers"] == []
    assert st.session_state["answer_submit_error"] == "Please enter an answer before submitting."


def test_submit_answer_handles_evaluation_failures_without_crashing():
    st.session_state["answer"] = "Strong example answer with enough detail to pass the minimum length gate."
    st.session_state["answers"] = []
    st.session_state["answer_submit_error"] = ""
    st.session_state["current_question"] = "Describe a time you improved system performance under constraints."
    st.session_state["current_screen"] = "question"

    with pytest.MonkeyPatch.context() as monkeypatch:
        def raise_runtime_error(*_args, **_kwargs):
            raise RuntimeError("Authentication failed - please check your API key")

        monkeypatch.setattr(
            "interview_app_frontend.state.session_manager.evaluate_submission",
            raise_runtime_error,
        )

        submit_answer()

    assert st.session_state["answers"] == []
    assert st.session_state["current_screen"] == "question"
    assert st.session_state["answer_submit_error"] == "We could not evaluate your answer right now. Please try again in a few moments."


def test_clear_answer_resets_input():
    st.session_state["answer"] = "Draft answer"

    clear_answer()

    assert st.session_state["answer"] == ""


def test_update_answer_sets_current_value():
    update_answer("Updated draft")

    assert st.session_state["answer"] == "Updated draft"


def test_update_answer_sets_current_value_from_text_area_change():
    st.session_state["answer"] = "Old value"

    update_answer("New value")

    assert st.session_state["answer"] == "New value"


def test_show_sample_answer_stores_generated_example():
    st.session_state["answer"] = "I improved performance by profiling the bottleneck and simplifying the query path."
    st.session_state["current_question"] = "Describe a time you improved system performance under constraints."

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "interview_app_frontend.state.session_manager.generate_example_answer",
            lambda answer: f"Example: {answer}",
        )
        show_sample_answer()

    assert st.session_state["current_screen"] == "sample_answer"
    assert st.session_state["sample_answer"].startswith("Example:")
    assert st.session_state["sample_answer_question"] == "Describe a time you improved system performance under constraints."
    assert st.session_state["sample_answer_source_answer"].startswith("I improved performance")


def test_return_to_feedback_navigates_back():
    st.session_state["current_screen"] = "sample_answer"

    return_to_feedback()

    assert st.session_state["current_screen"] == "feedback"
