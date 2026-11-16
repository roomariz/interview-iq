from copy import deepcopy
import streamlit as st
from interview_app_frontend.state.state_schema import DEFAULT_SESSION_STATE
from interview_app_frontend.state.answer_evaluation_job import reset_answer_evaluation_state
from interview_app_frontend.state.question_generation_job import reset_question_generation_state
from interview_app_frontend.utils.session_summary_view import build_session_summary_view
from interview_app_frontend.services.settings import get_question_count, MODEL_NAME

def update_answer(value: str) -> None:
    st.session_state.answer = value


def clear_answer() -> None:
    st.session_state.answer = ""
    st.session_state.answer_submit_error = ""


def return_to_feedback() -> None:
    st.session_state.current_screen = "feedback"


def go_to_session_summary() -> None:
    state = st.session_state
    state.summary = build_session_summary_view(state)
    state.current_screen = "summary"
    state.launch_question_view = False
    st.session_state.session_complete = True


def return_to_question() -> None:
    state = st.session_state
    state.current_screen = "question"
    state.has_active_session = True
    state.launch_question_view = False
    state.session_complete = False
    state.answer = ""
    state.answer_submit_error = ""


def advance_to_next_question() -> None:
    state = st.session_state
    current_index = int(state.get("current_question_index") or 0)
    next_index = current_index + 1
    total_questions = int(state.get("session_question_limit") or get_question_count(MODEL_NAME) or 3)
    if next_index > total_questions:
        state.current_screen = "summary"
        state.session_complete = True
        state.launch_question_view = False
        return
    state.current_question_index = next_index
    state.current_screen = "generating_question"
    state.launch_question_view = False
    state.has_active_session = True
    state.session_complete = False
    state.answer = ""
    state.answer_submit_error = ""
    state.current_question = ""
    state.prepared_questions = []
    state.base_questions = []
    state.follow_up_questions = []
    state.question_generation_error = ""
    state.question_generation_notice = ""
    state.question_generation_ready = False
    state.question_generation_future = None
    state.question_job = {"status": "pending", "result": None, "error": None, "started_at": None}


def set_screen(name: str) -> None:
    st.session_state.current_screen = name


def restart_session() -> None:
    state = st.session_state
    memory = state.get("future_session_memory", [])
    for key, value in DEFAULT_SESSION_STATE.items():
        state[key] = deepcopy(value)
    state.future_session_memory = memory
    reset_answer_evaluation_state(state)
    reset_question_generation_state(state)


def exit_session() -> None:
    state = st.session_state
    memory = state.get("future_session_memory", [])
    for key, value in DEFAULT_SESSION_STATE.items():
        state[key] = deepcopy(value)
    state.future_session_memory = memory
    state.current_screen = "welcome"  # Reset state but keep relevant data if needed
    reset_answer_evaluation_state(state)
    reset_question_generation_state(state)


def return_to_setup() -> None:
    state = st.session_state
    state.current_screen = "setup"
    state.launch_question_view = False
    state.has_active_session = False
    state.session_complete = False
    state.current_question_index = 0
    state.current_question = ""
    state.answer = ""
    state.answer_submit_error = ""
    state.reference_answer = ""
    state.semantic_similarity_score = 0.0
    state.sample_answer = ""
    state.sample_answer_question = ""
    state.sample_answer_source_answer = ""
    state.answers = []
    state.feedback = []
    state.summary = {}
    state.is_loading = False
    state.prepared_questions = []
    state.base_questions = []
    state.follow_up_questions = []
    state.gap_analysis = {}
    reset_answer_evaluation_state(state)
    reset_question_generation_state(state)
