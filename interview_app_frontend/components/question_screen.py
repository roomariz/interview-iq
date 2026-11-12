from html import escape

import streamlit as st
from interview_app_frontend.components.sidebar import render_interview_sidebar
from interview_app_frontend.components.loading_indicator import render_loading_indicator
from interview_app_frontend.components.prepared_questions_panel import render_prepared_questions_panel
from interview_app_frontend.components.question_panel import render_question_panel
from interview_app_frontend.components.topbar import render_shared_topbar
from interview_app_frontend.state.session_manager import (
    MAX_ANSWER_LENGTH,
    SECURITY_WARNING,
    clear_answer,
    exit_session,
    restart_session,
    submit_answer,
    return_to_setup,
    validate_answer,
)

DEFAULT_QUESTION = (
    "Describe a time you improved system performance under constraints. "
    "Include the challenge, your approach, and measurable results."
)
EVALUATION_NOTICE = "Evaluating your answer now. We are checking relevance, evidence, and scoring."


def _display_value(value: object, fallback: str) -> str:
    text = str(value).strip() if value not in (None, "") else ""
    return text or fallback


def _render_locked_submission_snapshot(current_question: str, current_answer: str, loading_text: str) -> None:
    st.markdown("### Question")
    st.write(current_question)
    with st.expander("Your Answer (submitted)", expanded=False):
        st.markdown(
            f'<div class="feedback-answer">{escape(current_answer or "No answer captured.")}</div>',
            unsafe_allow_html=True,
        )
    render_loading_indicator("Evaluation in progress", compact=True)


def render_question_and_answer(*, locked: bool = False, loading_message: str | None = None) -> None:
    state = st.session_state
    state.setdefault("current_question", DEFAULT_QUESTION)
    state.setdefault("prepared_questions", [])
    state.setdefault("base_questions", [])
    state.setdefault("follow_up_questions", [])
    state.setdefault("question_meta", {})
    question_index = max(int(state.get("current_question_index") or 1), 1)
    question_meta = state.get("question_meta", {}) if isinstance(state.get("question_meta", {}), dict) else {}
    total_questions = max(int(question_meta.get("total_questions", 0) or len(state.get("prepared_questions", []) or [])), 1)
    role_value = state.get("role")
    difficulty_value = state.get("difficulty")
    persona_value = state.get("persona")
    response_style_value = state.get("response_style")
    job_description_value = state.get("job_description")
    cv_status_value = state.get("cv_status")
    temperature_value = state.get("temperature")
    role = _display_value(role_value, "Backend Engineer")
    difficulty = _display_value(difficulty_value, "Medium")
    persona = _display_value(persona_value, "Strict")
    current_question = state.get("current_question", DEFAULT_QUESTION)
    current_answer = state.get("answer", "")
    answer_error = state.get("answer_submit_error", "")
    validation_error = validate_answer(current_answer)
    if current_answer.strip() and validation_error and validation_error != answer_error:
        state.answer_submit_error = validation_error
        answer_error = validation_error
    elif answer_error and not current_answer.strip():
        state.answer_submit_error = ""
        answer_error = ""
    banner_message = SECURITY_WARNING if not current_answer.strip() else (answer_error or validation_error or SECURITY_WARNING)
    submit_disabled = not current_answer.strip()

    left, right = st.columns([0.72, 3.28], gap="small")
    with left:
        render_interview_sidebar(
            role=role_value,
            difficulty=difficulty_value,
            persona=persona_value,
            response_style=response_style_value,
            job_description=job_description_value,
            cv_status=cv_status_value,
            temperature=temperature_value,
            tech_stack=state.get("tech_stack", []),
            focus_areas=state.get("focus_areas", []),
            question_type=state.get("question_type", "auto"),
            actions=("Restart", "Exit Session"),
            disabled=locked,
            active=True,
            on_restart=restart_session,
            on_exit=exit_session,
        )
    with right:
        if locked:
            st.markdown(
                """
                <style>
                .answer-evaluation-overlay {
                    position: fixed;
                    inset: 0;
                    z-index: 9998;
                    display: grid;
                    place-items: center;
                    background: rgba(15, 23, 42, 0.28);
                    backdrop-filter: blur(8px);
                }
                </style>
                <div class="answer-evaluation-overlay">
                """,
                unsafe_allow_html=True,
            )
            render_loading_indicator("Evaluation in progress", compact=True)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(f'<div class="question-main{" question-main--loading" if locked else ""}">', unsafe_allow_html=True)
        render_shared_topbar(
            title="Evaluating Your Answer" if locked else "Interview in Progress",
            subtitle="Preparing feedback from your submitted response." if locked else "Continue with the next question in the same session frame.",
            right_title=f"Question {question_index} of {total_questions}",
            right_copy="Feedback is being prepared." if locked else "Focus: Performance Optimisation",
            right_icon="⏱",
        )
        if locked:
            _render_locked_submission_snapshot(str(current_question), str(current_answer), "Evaluation in progress")
        else:
            notice = str(state.get("question_generation_notice", "")).strip()
            if notice:
                st.info(notice)
                state.question_generation_notice = ""
        st.markdown('<div class="question-warning" style="display:none;"></div>', unsafe_allow_html=True)
        if not locked:
            prepared_questions = state.get("prepared_questions", [])
            if len(prepared_questions or []) > 1:
                render_prepared_questions_panel(prepared_questions, question_meta=question_meta)
            render_question_panel(
                question_index=question_index,
                total_questions=total_questions,
                role=role,
                difficulty=difficulty,
                persona=persona,
                current_question=current_question,
                banner_message=banner_message,
                current_answer=current_answer,
                submit_disabled=submit_disabled or locked,
                input_disabled=locked,
                max_answer_length=MAX_ANSWER_LENGTH,
                on_back=return_to_setup,
                on_submit=submit_answer,
                on_clear=clear_answer,
            )
        st.markdown("</div>", unsafe_allow_html=True)
