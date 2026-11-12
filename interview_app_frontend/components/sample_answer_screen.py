from html import escape

import streamlit as st

from interview_app_frontend.components.sidebar import render_interview_sidebar
from interview_app_frontend.state.session_manager import exit_session, restart_session, return_to_feedback, return_to_question


def _render_card(title: str, body: str, body_class: str = "sample-answer-card__body") -> str:
    return (
        '<section class="sample-answer-card">'
        '<div class="sample-answer-card__header">'
        '<span class="sample-answer-card__header-icon" aria-hidden="true"></span>'
        f"<h2>{escape(title)}</h2>"
        "</div>"
        f'<div class="{body_class}">{body}</div>'
        "</section>"
    )
def render_sample_answer() -> None:
    state = st.session_state
    left, right = st.columns([0.72, 3.28], gap="small")
    with left:
        render_interview_sidebar(
            role=state.get("role"),
            difficulty=state.get("difficulty"),
            persona=state.get("persona"),
            response_style=state.get("response_style"),
            job_description=state.get("job_description"),
            cv_status=state.get("cv_status"),
            temperature=state.get("temperature"),
            tech_stack=state.get("tech_stack", []),
            focus_areas=state.get("focus_areas", []),
            question_type=state.get("question_type", "auto"),
            actions=("Restart", "Exit Session"),
            disabled=False,
            active=True,
            on_restart=restart_session,
            on_exit=exit_session,
        )
    with right:
        st.markdown(
            """
            <style>
            .sample-answer-main { display: grid; gap: 1rem; }
            .sample-answer-card { border: 1px solid #cad4e5; border-radius: 10px; overflow: hidden; background: #fff; }
            .sample-answer-card__header { display: flex; align-items: center; gap: 0.95rem; min-height: 82px; padding: 0.95rem 1.25rem; background: #f3f6fe; border-bottom: 1px solid #cfd9ea; }
            .sample-answer-card__header-icon { width: 28px; height: 28px; border-radius: 7px; background: #2454c8; position: relative; flex: 0 0 auto; }
            .sample-answer-card__header-icon::before { content: "!"; position: absolute; inset: 0; display: grid; place-items: center; color: #fff; font-size: 0.95rem; font-weight: 800; }
            .sample-answer-card__header h2 { margin: 0; color: #2454c8; font-size: 1.58rem; line-height: 1.05; font-weight: 800; }
            .sample-answer-card__body { padding: 1.15rem 1.35rem 1.35rem; color: #1b2b54; font-size: 1.02rem; line-height: 1.55; }
            .sample-answer-answer { white-space: pre-wrap; overflow-wrap: anywhere; }
            .sample-answer-question { display: grid; gap: 0.4rem; }
            .sample-answer-question__label { color: #2454c8; font-size: 1rem; font-weight: 800; }
            .sample-answer-question__text { padding: 0.85rem 1rem; border-radius: 12px; background: #f7faff; border: 1px solid #d6e2ff; }
            .sample-answer-actions { display: flex; gap: 0.8rem; margin-top: 0.15rem; }
            .sample-answer-note { margin-top: 0.9rem; padding: 0.85rem 1rem; border-radius: 12px; background: #eef4ff; border: 1px solid #d6e2ff; color: #425379; font-size: 0.93rem; line-height: 1.45; }
            @media (max-width: 1080px) {
                .sample-answer-actions { flex-direction: column; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sample-answer-main">', unsafe_allow_html=True)
        st.markdown(
            _render_card(
                "Your Question",
                f'<div class="sample-answer-question"><div class="sample-answer-question__label">Question</div><div class="sample-answer-question__text">{escape(state.get("sample_answer_question") or state.get("current_question") or "")}</div></div>',
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _render_card(
                "Your Answer (submitted)",
                f'<div class="sample-answer-answer">{escape(state.get("sample_answer_source_answer") or state.get("answer") or "")}</div>',
                "sample-answer-card__body",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            _render_card(
                "Stronger Answer (Example)",
                f'<div class="sample-answer-answer">{escape(state.get("sample_answer") or "No example answer available.")}</div>',
                "sample-answer-card__body",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sample-answer-note">This is a learning reference, not the only right answer.</div>',
            unsafe_allow_html=True,
        )
        left_action, right_action = st.columns([1, 1], gap="small")
        with left_action:
            st.button("Next Question", key="sample_answer_next_question", on_click=return_to_question, use_container_width=True)
        with right_action:
            st.button("Back to Feedback", key="sample_answer_back_to_feedback", on_click=return_to_feedback, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
