import streamlit as st

from interview_app_frontend.state.session_manager import exit_session, restart_session
from interview_app_frontend.utils.session_summary_view import build_session_summary_view
from interview_app_frontend.utils.styles import inject_summary_styles


def render_session_summary() -> None:
    inject_summary_styles()
    summary = build_session_summary_view(st.session_state)
    _render_header()
    _render_performance_overview(summary)
    _render_latest_question_recap(summary)
    _render_score_breakdown(summary)
    _render_strengths_and_improvements(summary)
    _render_next_steps(summary)
    _render_actions()


def _render_header() -> None:
    st.markdown(
        """
        <div class="summary-header">
            <h1>Interview Session Complete!</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_performance_overview(summary: dict) -> None:
    performance = summary.get("overall_performance", "0%")
    questions = summary.get("questions_completed", 0)
    duration = summary.get("session_duration", "0 minutes")
    st.markdown(
        f"""
        <div class="summary-overview">
            <div class="overview-item">
                <span class="overview-label">Overall Performance</span>
                <span class="overview-value">{performance}</span>
            </div>
            <div class="overview-item">
                <span class="overview-label">Questions Completed</span>
                <span class="overview-value">{questions}</span>
            </div>
            <div class="overview-item">
                <span class="overview-label">Session Duration</span>
                <span class="overview-value">{duration}</span>
            </div>
        </div>
        <hr class="summary-divider"/>
        """,
        unsafe_allow_html=True,
    )
    _render_evaluation_notice(summary)


def _render_evaluation_notice(summary: dict) -> None:
    notice = summary.get("evaluation_notice", "")
    if notice:
        st.info(notice)


def _render_latest_question_recap(summary: dict) -> None:
    recap = summary.get("latest_question_recap", {})
    if not isinstance(recap, dict) or not recap:
        return
    strengths = recap.get("strengths", [])
    improvements = recap.get("improvement_areas", [])
    question = recap.get("question", "").strip()
    decision = recap.get("decision", "").strip()
    st.markdown("### Latest Question Recap")
    st.markdown(
        f"""
        <div class="summary-recap">
            <div class="summary-recap__row"><strong>Question:</strong> {question or 'Not available'}</div>
            <div class="summary-recap__row"><strong>Outcome:</strong> {decision or 'Not available'}</div>
            <div class="summary-recap__row"><strong>Key takeaway:</strong> {recap.get('summary', '').strip() or 'No recap captured.'}</div>
            <div class="summary-recap__row"><strong>Strengths:</strong> {', '.join(str(item) for item in strengths) or 'None recorded.'}</div>
            <div class="summary-recap__row"><strong>Improvement areas:</strong> {', '.join(str(item) for item in improvements) or 'None recorded.'}</div>
        </div>
        <hr class="summary-divider"/>
        """,
        unsafe_allow_html=True,
    )


def _render_score_breakdown(summary: dict) -> None:
    scores = summary.get("average_scores", {})
    st.markdown("### Performance Breakdown")
    dimension_labels = {
        "relevance": "Relevance",
        "structure": "Structure",
        "specificity": "Specificity",
        "communication": "Communication",
        "problem_solving_approach": "Problem-Solving Approach",
    }
    score_bands = {0: "Needs Work", 4: "Needs Work", 7: "Good", 9: "Excellent"}
    html_parts = ['<div class="score-breakdown">']
    for dim, label in dimension_labels.items():
        value = scores.get(dim, 0)
        band = next((b for threshold, b in score_bands.items() if value >= threshold), "Needs Work")
        bar_width = int(value / 10 * 20)
        bar = "█" * bar_width + "░" * (20 - bar_width)
        html_parts.append(
            f'<div class="score-row"><span class="score-label">{label}</span>'
            f'<span class="score-bar">{bar}</span>'
            f'<span class="score-value">{value}/10 ({band})</span></div>'
        )
    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)
    st.markdown('<hr class="summary-divider"/>', unsafe_allow_html=True)


def _render_strengths_and_improvements(summary: dict) -> None:
    strengths = summary.get("strengths", [])
    improvements = summary.get("improvement_areas", [])
    focus_areas = summary.get("focus_areas", [])
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Key Strengths")
        if strengths:
            for s in strengths:
                st.markdown(f"- {s}")
        else:
            st.markdown("_No specific strengths identified._")
    with col2:
        st.markdown("### Areas for Improvement")
        if improvements:
            for i in improvements:
                st.markdown(f"- {i}")
        else:
            st.markdown("_No specific improvements identified._")
    if focus_areas:
        st.markdown("### Focus Areas")
        for area in focus_areas:
            st.markdown(f"- {area}")
    st.markdown('<hr class="summary-divider"/>', unsafe_allow_html=True)


def _render_next_steps(summary: dict) -> None:
    steps = summary.get("recommended_next_steps", [])
    st.markdown("### Recommended Next Steps")
    for i, step in enumerate(steps, 1):
        st.markdown(f"{i}. {step}")
    st.markdown('<hr class="summary-divider"/>', unsafe_allow_html=True)


def _render_actions() -> None:
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        st.button("Start New Session", on_click=restart_session, type="primary")
    with col4:
        st.button("Exit", on_click=exit_session)
