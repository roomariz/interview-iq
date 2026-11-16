from html import escape
from collections.abc import Callable

import streamlit as st


def _sidebar_value(value: object, fallback: str = "—") -> str:
    if isinstance(value, (list, tuple)):
        text = ", ".join(str(item).strip() for item in value if str(item).strip())
        value = text
    text = str(value).strip() if value not in (None, "") else ""
    return escape(text or fallback)


def _sidebar_item(label: str, value: object, icon_class: str, status: str | None = None, *, active: bool = False) -> str:
    raw = str(value).strip() if value not in (None, "") else ""
    badge = '<span class="setup-sidebar-status" aria-hidden="true"></span>' if status else ""
    item_class = "setup-sidebar-item setup-sidebar-item--active" if active else "setup-sidebar-item"
    return (
        f'<div class="{item_class}">'
        f'<span class="setup-sidebar-icon setup-sidebar-icon--{icon_class}" aria-hidden="true"></span>'
        f"<span>{escape(label)}</span>"
        f'<span class="setup-sidebar-value">{_sidebar_value(raw)}{badge}</span>'
        "</div>"
    )


def render_interview_sidebar(
    *,
    role: object = "Backend Engineer",
    difficulty: object = "Medium",
    persona: object = "Strict",
    response_style: object = "Detailed",
    job_description: object = "—",
    cv_status: object = "—",
    temperature: object = "0.7",
    tech_stack: object = "—",
    focus_areas: object = "—",
    question_type: object = "Auto",
    actions: tuple[str, str] = ("Start / Restart", "Exit Session"),
    disabled: bool = True,
    active: bool = False,
    on_restart: Callable[[], None] | None = None,
    on_exit: Callable[[], None] | None = None,
) -> None:
    raw_job_description = str(job_description).strip() if job_description not in (None, "") else ""
    raw_cv_status = str(cv_status).strip() if cv_status not in (None, "") else ""
    job_status = raw_job_description if raw_job_description in {"Added", "Uploaded"} else None
    cv_status_value = raw_cv_status if raw_cv_status in {"Added", "Uploaded"} else None
    sidebar_class = "setup-sidebar setup-sidebar--active" if active else "setup-sidebar"
    action_label_1, action_label_2 = actions
    st.markdown(
        f"""
        <aside class="{sidebar_class}">
            <div class="setup-sidebar-brand">
                <div class="setup-sidebar-logo" aria-hidden="true"></div>
                <div class="setup-sidebar-title">InterviewIQ</div>
            </div>
            <div class="setup-sidebar-section">Configuration</div>
            {_sidebar_item("Role", role, "briefcase", active=active)}
            {_sidebar_item("Difficulty", difficulty, "bars", active=active)}
            {_sidebar_item("Persona", persona, "user", active=active)}
            {_sidebar_item("Response Style", response_style, "chat", active=active)}
            {_sidebar_item("Detected Tech Stack", tech_stack, "doc", active=active)}
            {_sidebar_item("Focus Areas", focus_areas, "bars", active=active)}
            {_sidebar_item("Question Type", question_type, "play", active=active)}
            {_sidebar_item("Job Description", job_description, "doc", job_status, active=active)}
            {_sidebar_item("CV", cv_status, "doc", cv_status_value, active=active)}
            {_sidebar_item("Temperature", temperature, "temp", active=active)}
        </aside>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="setup-sidebar-section setup-sidebar-section--actions">Actions</div>', unsafe_allow_html=True)
    restart_disabled = disabled or on_restart is None
    exit_disabled = disabled or on_exit is None
    st.button(action_label_1, key="sidebar_restart", disabled=restart_disabled, on_click=on_restart, use_container_width=True)
    st.button(action_label_2, key="sidebar_exit", disabled=exit_disabled, on_click=on_exit, use_container_width=True)
