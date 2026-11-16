import streamlit as st

from interview_app_backend.llm.prompts.question_generation import TECH_STACK_OPTIONS
from interview_app_backend.llm.prompts.question_generation import infer_tech_stack_from_context
from interview_app_frontend.components.question_screen import render_question_and_answer as render_question_screen
from interview_app_frontend.components.topbar import render_shared_topbar
from interview_app_frontend.components.sidebar import render_interview_sidebar
from interview_app_frontend.state.session_manager import get_setup_validation_state, start_interview

SETUP_DEFAULTS = {
    "setup_role": "Backend Engineer",
    "setup_persona": "Friendly",
    "setup_cv_mode": "Paste Text",
    "setup_difficulty": "Easy",
    "setup_response_style": "Concise",
}

SETUP_WIDGET_KEYS = {
    "setup_role": "setup_role_tabs_v3",
    "setup_persona": "setup_persona_tabs_v3",
    "setup_cv_mode": "setup_cv_mode_tabs_v3",
    "setup_difficulty": "setup_difficulty_tabs_v3",
    "setup_response_style": "setup_response_style_tabs_v3",
    "setup_tech_stack": "setup_tech_stack_selection_v3",
}


def _set_screen(name: str) -> None:
    st.session_state.current_screen = name


def _setup_field_label(label: str, *, required: bool = False, is_valid: bool = True) -> None:
    marker = ' <span class="setup-required-marker">Required</span>' if required and not is_valid else ""
    required_asterisk = '<span class="setup-required-asterisk">*</span>' if required else ""
    st.markdown(
        f'<div class="setup-field-label">{label}{required_asterisk}{marker}</div>',
        unsafe_allow_html=True,
    )
def _stacked_segmented_control(label: str, options: list[str], key: str, *, required: bool = False, is_valid: bool = True) -> None:
    _setup_field_label(label, required=required, is_valid=is_valid)
    current_value = st.session_state.get(key)
    widget_key = SETUP_WIDGET_KEYS[key]
    st.segmented_control(
        label,
        options,
        key=widget_key,
        default=current_value if current_value in options else options[0], label_visibility="collapsed",
        on_change=_sync_widget_value,
        args=(widget_key, key),
    )
def _helper_text(text: str) -> None:
    st.markdown(f'<div class="setup-help-text">{text}</div>', unsafe_allow_html=True)


def _field_error(text: str) -> None:
    st.markdown(f'<div class="setup-field-error">{text}</div>', unsafe_allow_html=True)


def _sync_widget_value(widget_key: str, target_key: str) -> None:
    value = st.session_state.get(widget_key)
    if value is not None:
        st.session_state[target_key] = value


def _seed_setup_defaults() -> None:
    for key, value in SETUP_DEFAULTS.items():
        if not str(st.session_state.get(key, "")).strip():
            st.session_state[key] = value


def _estimate_card() -> None:
    st.markdown(
        """
        <div class="setup-estimate-card">
            <div class="setup-estimate-icon">◷</div>
            <div>
                <div class="setup-estimate-title">Estimated time: 15–20 minutes</div>
                <div class="setup-estimate-copy">This includes 5 main questions with possible follow-ups.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome() -> None:
    st.markdown(
        """
        <div class="welcome-card welcome-card--compact welcome-card--welcome">
            <div class="welcome-header">
                <div class="welcome-title">InterviewIQ</div>
            </div>
            <div class="welcome-body">
                <div class="hero-figure" aria-hidden="true">
                    <svg viewBox="0 0 360 220" class="hero-svg" role="img" aria-label="Interview practice illustration">
                        <defs>
                            <linearGradient id="cardGrad" x1="0" x2="0" y1="0" y2="1">
                                <stop offset="0%" stop-color="#eef4ff"/>
                                <stop offset="100%" stop-color="#ffffff"/>
                            </linearGradient>
                        </defs>
                        <ellipse cx="124" cy="148" rx="50" ry="14" fill="#dfe8ff" opacity="0.68"/>
                        <ellipse cx="254" cy="148" rx="48" ry="14" fill="#dfe8ff" opacity="0.52"/>
                        <path d="M94 152c-12-10-21-25-24-42 13 4 25 17 32 28 3-12 11-24 21-29-1 16-7 34-29 43z" fill="#d7e4ff"/>
                        <path d="M276 152c14-7 25-21 28-37-13 3-24 14-31 27-3-10-11-21-21-26 1 14 7 29 24 36z" fill="#d7e4ff"/>
                        <path d="M151 46h68v104h-68z" fill="url(#cardGrad)" stroke="#5966ff" stroke-width="5.5" rx="10"/>
                        <path d="M160 32h50v15h-50z" fill="#2f4aa8" rx="7"/>
                        <circle cx="185" cy="39" r="5.5" fill="#ffffff"/>
                        <path d="M160 67l7 7 12-14" fill="none" stroke="#5966ff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M180 67h22" stroke="#c5d2ff" stroke-width="3.5" stroke-linecap="round"/>
                        <path d="M180 88h22" stroke="#c5d2ff" stroke-width="3.5" stroke-linecap="round"/>
                        <path d="M180 109h18" stroke="#c5d2ff" stroke-width="3.5" stroke-linecap="round"/>
                        <path d="M160 89l7 7 12-14" fill="none" stroke="#5966ff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M160 111l7 7 12-14" fill="none" stroke="#5966ff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
                        <rect x="208" y="83" width="46" height="32" rx="11" fill="#6a77ff"/>
                        <circle cx="220" cy="99" r="3.3" fill="#ffffff"/>
                        <circle cx="234" cy="99" r="3.3" fill="#ffffff"/>
                        <circle cx="248" cy="99" r="3.3" fill="#ffffff"/>
                        <circle cx="251" cy="136" r="21" fill="#4b67e8"/>
                        <circle cx="251" cy="129" r="7.5" fill="#ffffff"/>
                        <path d="M238 149c4-10 10-15 13-15s9 5 13 15" fill="#ffffff"/>
                        <path d="M208 97l-11 8" stroke="#5966ff" stroke-width="3.3" stroke-linecap="round" stroke-dasharray="5 5"/>
                        <path d="M206 62c14 0 24 7 28 18" fill="none" stroke="#d1dbff" stroke-width="2.4" stroke-dasharray="6 6"/>
                    </svg>
                </div>
                <div class="welcome-copy">Prepare for technical and behavioural interviews through structured, adaptive practice sessions.</div>
                <div class="expectations-title">What you can expect:</div>
                <div class="expectations">
                    <div class="expectation-row"><span class="expectation-icon">👤</span><span>Role-specific interview questions</span></div>
                    <div class="expectation-row"><span class="expectation-icon">📊</span><span>Real-time evaluation and feedback</span></div>
                    <div class="expectation-row"><span class="expectation-icon">💬</span><span>Follow-up questions based on your responses</span></div>
                    <div class="expectation-row"><span class="expectation-icon">📄</span><span>Session summary with actionable insights</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left_cta, cta, right_cta = st.columns([1.35, 1, 1.35], gap="small")
    with cta:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.button(
            "Start Setup",
            type="primary",
            on_click=_set_screen,
            args=("setup",),
            use_container_width=True,
            key="welcome_start_setup",
            help="Go to setup",
        )
        st.markdown('<div class="helper-note" style="text-align:center;"><strong>Estimated time:</strong> 15–20 minutes</div>', unsafe_allow_html=True)
        st.markdown('<div class="helper-note" style="text-align:center;">You will configure role, difficulty, and preferences next</div>', unsafe_allow_html=True)


def render_setup() -> None:
    st.markdown('<div class="setup-shell">', unsafe_allow_html=True)
    st.markdown('<div class="setup-main-layout">', unsafe_allow_html=True)
    left, right = st.columns([0.72, 3.28], gap="small")
    with left:
        render_interview_sidebar(
            tech_stack=st.session_state.get("detected_tech_stack", st.session_state.get("setup_tech_stack", [])),
            focus_areas=st.session_state.get("focus_areas", []),
            question_type=st.session_state.get("question_type", "auto"),
        )

    with right:
        render_shared_topbar(
            title="Interview Setup",
            subtitle="Configure your preferences to personalise your interview practice session.",
            right_title="Your data is private",
            right_copy="and not stored.",
        )
        _seed_setup_defaults()
        detected_tech_stack = infer_tech_stack_from_context(
            st.session_state.get("setup_cv_content", ""),
            st.session_state.get("setup_job_description", ""),
        )
        validation_state = get_setup_validation_state()
        setup_left, setup_right = st.columns([1, 1], gap="large", vertical_alignment="top")
        with setup_left:
            _stacked_segmented_control(
                "Select Role",
                ["Backend Engineer", "Frontend Engineer", "Full Stack Engineer", "Data Engineer"],
                "setup_role",
                required=True,
                is_valid=validation_state["setup_role"],
            )
            _stacked_segmented_control("Select Interviewer Persona", ["Friendly", "Neutral", "Strict"], "setup_persona", required=True, is_valid=validation_state["setup_persona"])
            if not st.session_state.get("setup_persona"):
                _field_error("Interviewer persona is required.")
            _stacked_segmented_control("CV Input (Optional)", ["Upload PDF", "Paste Text"], "setup_cv_mode")
            if st.session_state.get("setup_cv_mode") == "Paste Text":
                st.text_area("Paste CV Content", placeholder="Paste your CV content here...", height=132, key="setup_cv_content", label_visibility="collapsed")
            _helper_text("Used to personalise questions based on your experience.")
            _setup_field_label("Model Temperature (Advanced)")
            _helper_text("Controls creativity and randomness in AI responses.")
            st.slider("Model Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1, label_visibility="collapsed", key="setup_temperature")
        with setup_right:
            _stacked_segmented_control("Select Difficulty", ["Easy", "Medium", "Hard"], "setup_difficulty", required=True, is_valid=validation_state["setup_difficulty"])
            if not st.session_state.get("setup_difficulty"):
                _field_error("Difficulty is required.")
            _stacked_segmented_control("Response Style", ["Concise", "Detailed"], "setup_response_style")
            _setup_field_label("Job Description (Optional)")
            st.text_area("Job Description (Optional)", placeholder="Paste the job description here...", height=116, label_visibility="collapsed", key="setup_job_description")
            _helper_text("Used to align questions with role requirements.")
            with st.expander("Advanced Configuration", expanded=False):
                st.caption(
                    "Detected tech stack is shown below. You can override it if the inference is incomplete or too broad."
                )
                st.caption("Detected Tech Stack: " + (", ".join(detected_tech_stack) if detected_tech_stack else "Not enough context yet"))
                tech_stack_key = SETUP_WIDGET_KEYS["setup_tech_stack"]
                st.multiselect(
                    "Override Tech Stack",
                    TECH_STACK_OPTIONS,
                    default=st.session_state.get(tech_stack_key, st.session_state.get("setup_tech_stack", detected_tech_stack)),
                    key=tech_stack_key,
                    on_change=_sync_widget_value,
                    args=(tech_stack_key, "setup_tech_stack"),
                    help="Optional controlled stack selector used to make question generation more precise.",
                )
                st.caption("Question type is controlled by the session flow and adaptation signals.")

        st.markdown('<div style="height: 0.55rem;"></div>', unsafe_allow_html=True)
        bottom_left, bottom_right = st.columns([1.7, 0.65], gap="large", vertical_alignment="center")
        with bottom_left:
            _estimate_card()
        with bottom_right:
            start_disabled = not all(validation_state.values())
            st.button(
                "Start Interview",
                type="primary",
                key="setup_start_interview",
                on_click=start_interview,
                use_container_width=True,
                disabled=start_disabled,
            )
            _helper_text("Select role, interviewer persona, and difficulty before starting.")

        setup_error = st.session_state.get("setup_error", "")
        if setup_error:
            st.error(setup_error)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_question_and_answer() -> None:
    render_question_screen()
