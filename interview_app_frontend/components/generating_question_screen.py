from html import escape
from time import time
from typing import Any

import streamlit as st

from interview_app_backend.services.question_generation_job import begin_question_generation
from interview_app_backend.services.question_generation_job import poll_question_generation
from interview_app_frontend.components.sidebar import render_interview_sidebar
from interview_app_frontend.components.topbar import render_shared_topbar
from interview_app_frontend.state.session_manager import exit_session
from interview_app_frontend.state.session_manager import restart_session


_STYLES = """
<style>
.preparing-card { border: 1px solid #dbe3f0; border-radius: 16px; background: #ffffff; padding: 1rem 1.1rem; margin-top: 0.25rem; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04); }
.preparing-card__title { font-size: 1.2rem; font-weight: 800; color: #0f172a; margin-bottom: 0.35rem; }
.preparing-card__copy { color: #475569; font-size: 0.94rem; line-height: 1.45; margin-bottom: 0.75rem; }
.preparing-card__steps { display: grid; gap: 0.55rem; margin: 0.55rem 0 0.85rem; }
.preparing-step { display: flex; align-items: flex-start; gap: 0.65rem; color: #1e293b; font-size: 0.95rem; line-height: 1.35; }
.preparing-step__icon { width: 22px; height: 22px; border-radius: 999px; background: #e8efff; color: #1d4ed8; display: inline-grid; place-items: center; flex: 0 0 22px; font-size: 0.8rem; font-weight: 900; margin-top: 0.05rem; }
.preparing-step--active .preparing-step__icon { background: #1d4ed8; color: #ffffff; }
.preparing-step--active { font-weight: 700; color: #0f172a; }
.preparing-progress { margin-top: 0.15rem; }
.preparing-note { margin-top: 0.7rem; color: #64748b; font-size: 0.88rem; line-height: 1.35; }
.preparing-spinner { margin-top: 0.65rem; color: #1d4ed8; font-weight: 700; }
</style>
"""


def _display_value(value: object, fallback: str) -> str:
    text = str(value).strip() if value not in (None, "") else ""
    return text or fallback


_ROTATING_MESSAGES = [
    "Analysing your role responsibilities...",
    "Reviewing your experience...",
    "Matching job requirements...",
    "Generating a realistic interview scenario...",
]


def _build_step_rows(state: Any) -> list[str]:
    role = _display_value(state.get("role"), "selected role")
    has_cv = bool(str(state.get("setup_cv_content", "")).strip())
    has_jd = bool(str(state.get("setup_job_description", "")).strip())
    rows: list[str] = [f"Analysing selected role: {role}"]
    if has_cv:
        rows.append("Reviewing your CV and experience")
    if has_cv and has_jd:
        rows.append("Aligning with job description requirements")
    elif has_cv:
        rows.append("Personalising questions to your experience")
    elif has_jd:
        rows.append("Aligning with job description requirements")
    else:
        rows.append("Preparing relevant interview scenarios")
    return rows


def _progress_message(state: Any) -> tuple[str, int]:
    started_at = state.get("generation_start_time") or state.get("question_generation_started_at")
    elapsed = max(time() - float(started_at), 0.0) if started_at else 0.0
    index = int(elapsed // 1.5) % len(_ROTATING_MESSAGES)
    progress_map = [24, 52, 76, 92]
    return _ROTATING_MESSAGES[index], progress_map[index]


def _render_preparing_card(state: Any) -> None:
    message, progress = _progress_message(state)
    steps_html = "".join(
        f'<div class="preparing-step{" preparing-step--active" if index < 2 else ""}><span class="preparing-step__icon">✓</span><span>{escape(label)}</span></div>'
        for index, label in enumerate(_build_step_rows(state))
    )
    st.markdown(
        f"""
        <section class="preparing-card">
            <div class="preparing-card__title">We are preparing your interview questions.</div>
            <div class="preparing-card__copy">This uses your selected role first, then your CV, then the job description to shape the first question.</div>
            <div class="preparing-card__steps">{steps_html}</div>
            <div class="preparing-spinner">{escape(message)}</div>
            <div class="preparing-note">This usually takes a few seconds.</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.progress(progress)


@st.fragment(run_every="1s")
def render_generating_question() -> None:
    state = st.session_state
    job = state.get("question_job", {}) if isinstance(state.get("question_job", {}), dict) else {}
    if not state.get("question_generation_future") and job.get("status") not in {"failed", "timeout", "rate_limited"}:
        begin_question_generation(state)
    if poll_question_generation(state):
        st.rerun()

    left, right = st.columns([0.72, 3.28], gap="small")
    with left:
        render_interview_sidebar(
            role=state.get("role", "Backend Engineer"),
            difficulty=state.get("difficulty", "Medium"),
            persona=state.get("persona", "Strict"),
            response_style=state.get("response_style", "Detailed"),
            job_description=state.get("job_description", "—"),
            cv_status=state.get("cv_status", "—"),
            temperature=state.get("temperature", "0.7"),
            tech_stack=state.get("tech_stack", []),
            focus_areas=state.get("focus_areas", []),
            question_type="Preparing",
            actions=("Restart", "Exit Session"),
            disabled=False,
            active=True,
            on_restart=restart_session,
            on_exit=exit_session,
        )
    with right:
        st.markdown(_STYLES, unsafe_allow_html=True)
        render_shared_topbar(
            title="Preparing Your Interview",
            subtitle="We are preparing your interview questions before showing the first prompt.",
            right_title="Role → CV → JD",
            right_copy="Personalised generation in progress.",
            left_icon="⏳",
            right_icon="⚙",
        )
        _render_preparing_card(state)
        notice = str(state.get("question_generation_notice", "")).strip()
        if notice:
            st.info(notice)
