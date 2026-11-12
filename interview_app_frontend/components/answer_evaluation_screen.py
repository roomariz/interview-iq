import streamlit as st

from interview_app_frontend.components.loading_indicator import render_loading_indicator
from interview_app_frontend.components.sidebar import render_interview_sidebar
from interview_app_frontend.components.topbar import render_shared_topbar
from interview_app_frontend.state.answer_evaluation_job import consume_answer_evaluation
from interview_app_frontend.state.session_manager import finalise_answer_submission


_EVALUATION_LAYOUT_STYLES = """
<style>
.answer-evaluation-shell {
    display: block;
    width: 100%;
}
.answer-evaluation-layout {
    display: block;
    width: 100%;
    min-height: 0;
}
.answer-evaluation-layout > div {
    width: 100%;
    max-width: 100%;
}
.answer-evaluation-main {
    display: grid;
    gap: 0.85rem;
    align-content: start;
    padding: 0.05rem 0 0.3rem;
}
.answer-evaluation-stage {
    width: 100%;
    display: flex;
    justify-content: center;
}
.answer-evaluation-stage__card {
    width: min(100%, 280px);
}
</style>
"""


@st.fragment(run_every="1s")
def render_answer_evaluation() -> None:
    state = st.session_state
    result = consume_answer_evaluation(state)
    if isinstance(result, dict) and result.get("error"):
        state.current_screen = "question"
        state.is_loading = False
        state.answer_submit_error = "We could not evaluate your answer right now. Please try again in a few moments."
        st.rerun()
    if isinstance(result, dict) and result:
        finalise_answer_submission(state.get("current_question", ""), state.get("answer", "").strip(), result)
        st.rerun()

    st.markdown(_EVALUATION_LAYOUT_STYLES, unsafe_allow_html=True)
    st.markdown('<div class="answer-evaluation-shell"><div class="answer-evaluation-layout">', unsafe_allow_html=True)
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
            question_type=state.get("question_type", "Preparing"),
            actions=("Restart", "Exit Session"),
            disabled=True,
            active=True,
        )
    with right:
        st.markdown('<div class="answer-evaluation-main">', unsafe_allow_html=True)
        render_shared_topbar(
            title="Evaluating Your Answer",
            subtitle="We are checking relevance, evidence, and scoring before showing feedback.",
            right_title="Evaluation in progress",
            right_copy="Please wait a moment.",
            left_icon="⏱",
            right_icon="⚙",
        )
        st.markdown('<div class="answer-evaluation-stage"><div class="answer-evaluation-stage__card">', unsafe_allow_html=True)
        render_loading_indicator("Evaluation in progress", compact=True, panel=True)
        st.markdown("</div></div></div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)
