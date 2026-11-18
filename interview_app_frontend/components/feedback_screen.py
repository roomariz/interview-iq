import json
from html import escape

import streamlit as st

from interview_app_frontend.components.sidebar import render_interview_sidebar
from interview_app_frontend.state.session_manager import (
    advance_to_next_question,
    exit_session,
    restart_session,
    go_to_session_summary,
)
from interview_app_frontend.utils.feedback_model import FEEDBACK_DIMENSIONS, normalise_feedback_payload
from interview_app_frontend.utils.feedback_view import (
    build_behaviour_aware_trust,
    build_follow_up,
    build_key_takeaway,
    build_score_consistency,
    prioritise_improvements,
    prioritise_strengths,
)
from interview_app_frontend.utils.pipeline_view import build_reliability_card


def _render_read_only_card(title: str, body: str, body_class: str = "question-card__body") -> str:
    return (
        '<section class="question-card">'
        '<div class="question-card__header">'
        '<span class="question-card__header-icon" aria-hidden="true"></span>'
        f"<h1>{escape(title)}</h1>"
        "</div>"
        f'<div class="{body_class}"><div class="feedback-copy">{body}</div></div>'
        "</section>"
    )


def _render_collapsible_body(title: str, body: str, body_class: str = "question-card__body") -> None:
    with st.expander(title, expanded=False):
        st.markdown(
            f'<div class="{body_class}"><div class="feedback-copy">{body}</div></div>',
            unsafe_allow_html=True,
        )


def _render_list(items: list[str], empty_text: str, list_class: str = "feedback-list") -> str:
    if not items:
        return f'<div class="feedback-empty">{escape(empty_text)}</div>'
    return "<ul class='" + list_class + "'>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _render_pills(items: list[str], empty_text: str) -> str:
    if not items:
        return f'<div class="feedback-empty">{escape(empty_text)}</div>'
    return (
        '<div class="feedback-pill-list">'
        + "".join(f'<span class="feedback-pill">{escape(item)}</span>' for item in items)
        + "</div>"
    )


def _render_score_row(label: str, score: int) -> str:
    return f"""
    <div class="feedback-breakdown-row">
        <div class="feedback-breakdown-label">{escape(label)}</div>
        <div class="feedback-breakdown-track" aria-hidden="true">
            <div class="feedback-breakdown-fill" style="width: {score * 10}%"></div>
        </div>
        <div class="feedback-breakdown-score">{score}/10</div>
    </div>
    """


def _decision_display(decision: str) -> str:
    if decision == "pass":
        return "✓ PASS"
    if decision == "borderline pass":
        return "◐ BORDERLINE PASS"
    return "✕ FAIL"


def _confidence_class(level: str) -> str:
    confidence = level.strip().lower()
    if confidence in {"low", "high"}:
        return f"feedback-decision-confidence--{confidence}"
    return ""

def render_feedback() -> None:
    view_model = normalise_feedback_payload(st.session_state.get("feedback"))
    state = st.session_state
    decision_detail = view_model["overall_decision_detail"]
    validation_warning = view_model["validation_warning"]
    view_model["future_session_memory"] = state.get("future_session_memory", [])
    consistency = build_score_consistency(view_model)
    follow_up = build_follow_up(view_model)
    strengths = prioritise_strengths(view_model)
    improvements = prioritise_improvements(view_model)
    trust_display = build_behaviour_aware_trust(view_model)
    decision_confidence_class = _confidence_class(str(view_model.get("trust", {}).get("decision_confidence", "")))
    takeaway = build_key_takeaway(view_model)
    reliability_card = build_reliability_card(state.get("feedback"), view_model)
    display_model = dict(view_model)
    if state.get("_demonstration"):
        from interview_app_frontend.services.community_cloud import DEMONSTRATION_NOTICE
        display_model["demonstration"] = {"mocked": True, "notice": DEMONSTRATION_NOTICE}
    display_model["follow_up"] = follow_up
    display_model["score_consistency"] = consistency
    display_model["strengths"] = strengths
    display_model["improvements"] = improvements
    display_model["key_takeaway"] = takeaway
    display_model["trust_display"] = trust_display
    display_model["reliability_card"] = reliability_card
    subtitle = f"{escape(_decision_display(view_model['overall_decision']))} · {escape(trust_display['decision'])} · {escape(reliability_card['grounding'])} grounding"

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
        st.markdown('<div class="feedback-main">', unsafe_allow_html=True)
        _render_collapsible_body("Your Question", escape(view_model["question"]))
        _render_collapsible_body("Your Answer (submitted)", f'<div class="feedback-answer">{escape(view_model["answer"])}</div>', "answer-card__body")
        st.markdown(
            f"""
            <section class="feedback-card">
                <div class="feedback-card__header">
                    <span class="feedback-card__header-icon" aria-hidden="true"></span>
                    <h2>Diagnostic Feedback</h2>
                    <div class="feedback-card__subtitle">{subtitle}</div>
                </div>
                <div class="feedback-card__body">
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="feedback-reliability">
                <div class="feedback-reliability__title">{escape(reliability_card["title"])}</div>
                <div class="feedback-reliability__row"><span class="feedback-reliability__dot" style="background: {escape(reliability_card['dot_colour'])};"></span><strong>Confidence:</strong> {escape(reliability_card["confidence"])}</div>
                <div class="feedback-reliability__row"><strong>Grounding:</strong> {escape(reliability_card["grounding"])}</div>
                <div class="feedback-reliability__row"><strong>Assessment:</strong> {escape(reliability_card["assessment"])}</div>
                <div class="feedback-reliability__note">{escape(reliability_card["message"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="feedback-trust">
                <div class="feedback-trust__item"><strong>Trust:</strong> {escape(trust_display["summary"])}</div>
                <div class="feedback-trust__item">{escape(trust_display["detail"])}</div>
                <div class="feedback-trust__item"><span class="feedback-decision-confidence {decision_confidence_class}">{escape(trust_display["decision"])}</span></div>
                <div class="feedback-trust__item">{escape(trust_display["depth"])}</div>
                <div class="feedback-trust__note">{escape(validation_warning["interpretation"] or decision_detail["reason"] or "Scores are ready for review.")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if consistency["has_gap"]:
            st.markdown(
                f"""
                <div class="feedback-consistency">
                    <strong>Score consistency:</strong>
                    {escape(consistency["note"] or "Visible decision and score-based verdict differ.")} {'Adjusted labels: ' + ', '.join(consistency['issues']) + '.' if consistency['issues'] else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )
        nudge = "You can continue to the next question or review your session summary."
        if str(view_model.get("failure_type", "")).strip() == "off_topic":
            nudge = "This answer does not address the question. You can review the summary or try answering again."
        st.markdown(f'<div class="feedback-nudge">{escape(nudge)}</div>', unsafe_allow_html=True)
        st.markdown('<div class="feedback-section-title">Key Takeaway</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="feedback-key-takeaway">{escape(takeaway)}</div>', unsafe_allow_html=True)
        st.markdown('<div class="feedback-section-title">Suggested Follow-Up</div>', unsafe_allow_html=True)
        follow_up_body = (
            f"<p><strong>Stage:</strong> {follow_up.get('stage', 1)}/3</p>"
            f"<p><strong>Question:</strong> {escape(follow_up['question'])}</p>"
            f"<p><strong>Type:</strong> {escape(follow_up['type'] or 'general')}</p>"
            f"<p><strong>Target dimension:</strong> {escape(follow_up['target_dimension'] or 'problem_solving_approach')}</p>"
            f"<p><strong>Why this helps:</strong> {escape(follow_up.get('reasoning_action', ''))}</p>"
        )
        if follow_up.get("context_note"):
            follow_up_body += f"<p><strong>Context:</strong> {escape(follow_up['context_note'])}</p>"
        st.markdown(_render_read_only_card("Continue Learning", follow_up_body, "feedback-card__body"), unsafe_allow_html=True)
        st.markdown('<div class="feedback-section-title">Strengths</div>', unsafe_allow_html=True)
        st.markdown(_render_pills(strengths, "No strengths captured yet."), unsafe_allow_html=True)
        st.markdown('<div class="feedback-section-title">Prioritised Improvements</div>', unsafe_allow_html=True)
        st.markdown(_render_list(improvements, "No improvement notes captured yet."), unsafe_allow_html=True)
        st.markdown('<div class="feedback-section-title">Evaluation Breakdown</div>', unsafe_allow_html=True)
        st.markdown('<div class="feedback-breakdown">', unsafe_allow_html=True)
        for key, label in FEEDBACK_DIMENSIONS:
            st.markdown(_render_score_row(label, view_model["scores"][key]), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="feedback-section-title">What the Interviewer is Evaluating</div>', unsafe_allow_html=True)
        st.markdown(_render_list(view_model["criteria"], "No criteria recorded yet."), unsafe_allow_html=True)
        st.markdown("""<section class="feedback-panel"><h3>Weak Points</h3>""", unsafe_allow_html=True)
        st.markdown(_render_list(view_model["key_issues"], "No weak points captured yet."), unsafe_allow_html=True)
        st.markdown("</section>", unsafe_allow_html=True)
        st.markdown(
            f"""
                <div class="feedback-panel feedback-panel--reasoning">
                <h3>Problem-Solving Assessment</h3>
                <div class="feedback-reasoning">
                    <p><strong>Approach Quality:</strong> {view_model["scores"]["problem_solving_approach"]}/10</p>
                    <p>{escape(view_model["reasoning"]["clarity"])}</p>
                    <p><strong>Observations:</strong> {escape(view_model["reasoning"]["alternative_approaches"])}</p>
                    <p><strong>Trade-offs:</strong> {escape(view_model["reasoning"]["trade_off_awareness"])}</p>
                    <p><strong>Next action:</strong> {escape(follow_up.get("reasoning_action", ""))}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        left_button, right_button = st.columns([1, 1], gap="small")
        with left_button:
            st.button("Next", key="feedback_next_question", on_click=advance_to_next_question, use_container_width=True, type="primary")
        with right_button:
            st.button("Summary", key="feedback_view_summary", on_click=go_to_session_summary, use_container_width=True)
        st.download_button(
            "Download Evaluation Report",
            data=json.dumps(display_model, indent=2, ensure_ascii=True),
            file_name="evaluation-report.json",
            mime="application/json",
            use_container_width=True,
        )
        with st.expander("Technical Evaluation (JSON)", expanded=False):
            st.code(json.dumps(display_model, indent=2, ensure_ascii=True), language="json")
        st.markdown("</div></section></div></div>", unsafe_allow_html=True)
