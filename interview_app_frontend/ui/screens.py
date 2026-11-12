import streamlit as st

from interview_app_frontend.components.generating_question_screen import render_generating_question
from interview_app_frontend.components.answer_evaluation_screen import render_answer_evaluation
from interview_app_frontend.components.shell import render_question_and_answer, render_setup, render_welcome
from interview_app_frontend.components.feedback_screen import render_feedback
from interview_app_frontend.components.sample_answer_screen import render_sample_answer
from interview_app_frontend.components.session_summary_screen import render_session_summary
from interview_app_frontend.state.session_manager import DEFAULT_QUESTION
from interview_app_frontend.utils.feedback_model import has_structured_feedback


def render_screen() -> None:
    screen = st.session_state.get("current_screen", "welcome")
    session_complete = st.session_state.get("session_complete", False)

    if screen == "feedback":
        render_feedback()
        return

    if screen == "evaluating_answer":
        render_answer_evaluation()
        return

    if session_complete:
        render_session_summary()
        return

    if screen == "setup":
        render_setup()
    elif screen == "generating_question":
        render_generating_question()
    elif screen == "feedback":
        render_feedback()
    elif screen == "sample_answer":
        render_sample_answer()
    elif screen == "question":
        if not st.session_state.get("current_question"):
            base_questions = st.session_state.get("base_questions", []) or st.session_state.get("prepared_questions", []) or []
            if base_questions and isinstance(base_questions[0], dict):
                st.session_state.current_question = str(base_questions[0].get("question", "")).strip() or DEFAULT_QUESTION
            elif base_questions:
                st.session_state.current_question = str(base_questions[0]).strip() or DEFAULT_QUESTION
            else:
                st.session_state.current_question = DEFAULT_QUESTION
        st.session_state.has_active_session = True
        st.session_state.launch_question_view = False
        render_question_and_answer()
    else:
        render_welcome()
