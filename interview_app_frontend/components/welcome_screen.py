import streamlit as st

def _set_screen(name):
    st.session_state.current_screen = name

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
