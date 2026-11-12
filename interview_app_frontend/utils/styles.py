import streamlit as st
from interview_app_frontend.utils.feedback_styles import FEEDBACK_STYLES
from interview_app_frontend.utils.question_styles import QUESTION_STYLES


def inject_styles() -> None:
    css = inject_summary_styles()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def inject_summary_styles() -> None:
    css = """
        .block-container { padding-top: 0.6rem; padding-bottom: 0.9rem; padding-left: 1rem; padding-right: 1rem; }
        [data-testid="stHeader"] { display: none; }
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stButton"] > button {
            position: relative;
            width: 100%;
            border-radius: 14px;
            border: 1px solid #1d4ed8;
            background: #1d4ed8;
            color: white;
            font-weight: 700;
            padding: 0.9rem 1.25rem;
        }
        .cta-arrow [data-testid="stButton"] > button::after {
            content: "›";
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.7rem;
            line-height: 1;
        }
        [data-testid="stButton"] > button:hover { border-color: #1e40af; background: #1e40af; }
        .welcome-card { border: 1px solid #d6deef; border-radius: 16px; background: #ffffff; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04); overflow: hidden; }
        .welcome-card--compact { max-height: calc(100vh - 120px); }
        .welcome-card--welcome { max-width: 900px; margin: 0 auto; }
        .welcome-header { border-bottom: 1px solid #e6ebf5; padding: 1.1rem 1.5rem; text-align: center; }
        .welcome-title { font-size: 2rem; font-weight: 800; color: #0f172a; margin: 0; }
        .welcome-body { padding: 0.95rem 1.5rem 0.65rem; text-align: center; }
        .hero-figure { width: 230px; height: 146px; margin: 0 auto 0.3rem; }
        .hero-figure--small { display: none; }
        .hero-svg { width: 100%; height: 100%; display: block; }
        .welcome-copy { max-width: 560px; margin: 0 auto; color: #334155; font-size: 0.96rem; line-height: 1.34; }
        .expectations-title { margin: 0.7rem 0 0.5rem; font-size: 1.08rem; font-weight: 800; color: #0f172a; }
        .expectations { max-width: 620px; margin: 0 auto 0.55rem; text-align: left; }
        .expectation-row { display: flex; align-items: center; gap: 0.8rem; margin: 0.42rem 0; color: #0f172a; font-size: 0.94rem; }
        .expectation-icon { width: 36px; height: 36px; border-radius: 999px; background: #e8efff; color: #2756d8; display: inline-flex; align-items: center; justify-content: center; flex: 0 0 36px; font-size: 0.95rem; font-weight: 800; }
        .cta-wrap { max-width: 360px; margin: 0 auto; }
        .welcome-cta-spacer { height: 0.55rem; }
        .helper-note { color: #64748b; margin-top: 0.12rem; font-size: 0.86rem; }
        .helper-note strong { color: #475569; }
        .active-actions { display: flex; gap: 0.75rem; justify-content: center; max-width: 520px; margin: 1.25rem auto 0; }
        .active-actions [data-testid="stButton"] { flex: 1; }
        .disabled-welcome-button { pointer-events: none; opacity: 0.65; }
        .setup-topbar, .setup-estimate-card { border: 1px solid #dbe3f0; border-radius: 16px; background: #f8fbff; }
        .setup-topbar { display: flex; justify-content: space-between; align-items: center; gap: 0.8rem; padding: 0.75rem 0.9rem 0.75rem 0.95rem; margin-bottom: 0.65rem; }
        .setup-topbar, .question-card-inline { animation: screenFadeIn 180ms ease-out; }
        .setup-topbar-left, .setup-estimate-card { display: flex; align-items: center; gap: 0.9rem; }
        .setup-topbar-icon, .setup-topbar-privacy-icon { width: 48px; height: 48px; border-radius: 14px; background: #eef4ff; color: #1d4ed8; display: flex; align-items: center; justify-content: center; flex: 0 0 auto; font-size: 1.45rem; }
        .setup-estimate-icon { width: 44px; height: 44px; border-radius: 12px; background: #e9f0ff; color: #1d4ed8; display: flex; align-items: center; justify-content: center; flex: 0 0 auto; font-size: 1.2rem; }
        .setup-topbar-title { font-size: 1.6rem; font-weight: 800; color: #0f172a; line-height: 1.05; }
        .setup-topbar-subtitle, .setup-help-text, .setup-estimate-copy { color: #64748b; font-size: 0.82rem; line-height: 1.3; }
        .setup-topbar-privacy { display: flex; align-items: center; gap: 0.7rem; padding: 0.7rem 0.85rem; background: #eef4ff; border-radius: 14px; color: #1d4ed8; text-align: center; font-size: 0.84rem; }
        .setup-estimate-title { font-weight: 700; color: #0f172a; }
        .setup-shell { display: block; width: 100%; min-height: 0; padding-top: 0; }
        .setup-main-layout { display: block; width: 100%; min-height: 0; }
        .setup-section { margin-top: 0.25rem; padding: 0.25rem 0.55rem 0.05rem; border: 1px solid #e8eef8; border-radius: 12px; background: #ffffff; }
        .setup-section--advanced { padding-bottom: 0.5rem; }
        .setup-section--actions { padding-bottom: 0.35rem; }
        .setup-main-layout > div { width: 100%; max-width: 100%; }
        .setup-main-layout > [data-testid="column"] { min-height: 0; width: 100%; }
        .setup-sidebar { border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.3rem 0.4rem 0.2rem; background: #fafbfc; color: #94a3b8; opacity: 0.62; min-height: auto; width: 100%; max-width: 100%; box-sizing: border-box; }
        .setup-sidebar--active { opacity: 1; background: #ffffff; color: #16224a; }
        .setup-sidebar-brand { display: flex; align-items: centre; gap: 0.55rem; padding: 0.08rem 0 0.28rem; border-bottom: 1px solid rgba(148, 163, 184, 0.22); margin-bottom: 0.3rem; }
        .setup-sidebar-logo { width: 34px; height: 34px; border-radius: 8px; background: #1d4ed8; position: relative; flex: 0 0 34px; }
        .setup-sidebar-logo::after { content: ""; position: absolute; inset: 7px; border: 2px solid #ffffff; border-radius: 4px; }
        .setup-sidebar-logo::before { content: ""; position: absolute; left: 12px; top: 10px; width: 10px; height: 10px; border: 2px solid #ffffff; border-radius: 999px; background: transparent; }
        .setup-sidebar-title { font-size: 0.86rem; font-weight: 700; color: #111827; line-height: 1.08; }
        .setup-sidebar--active .setup-sidebar-title { color: #12244b; }
        .setup-sidebar-section { font-size: 0.64rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.18rem; margin-bottom: 0.1rem; color: #9ca3af; }
        .setup-sidebar--active .setup-sidebar-section { color: #5d6d84; }
        .setup-sidebar-section--actions { margin-top: 0.2rem; }
        .setup-sidebar-item, .setup-sidebar-action { display: flex; align-items: center; gap: 0.4rem; font-size: 0.76rem; padding: 0.08rem 0; border-bottom: 1px solid rgba(148, 163, 184, 0.1); margin: 0.55rem 0 0.72rem; }
        .setup-sidebar--active .setup-sidebar-item { margin: 0.55rem 0 0.72rem; }
        .setup-sidebar-icon { width: 18px; height: 18px; flex: 0 0 18px; opacity: 0.85; position: relative; }
        .setup-sidebar-icon::before, .setup-sidebar-icon::after { content: ""; position: absolute; background: #94a3b8; }
        .setup-sidebar-icon--briefcase::before { left: 2px; right: 2px; top: 6px; height: 8px; border: 1.5px solid #94a3b8; background: transparent; border-radius: 3px; }
        .setup-sidebar-icon--briefcase::after { left: 6px; top: 3px; width: 6px; height: 3px; border-radius: 2px 2px 0 0; }
        .setup-sidebar-icon--bars::before { left: 3px; right: 3px; top: 4px; height: 2px; box-shadow: 0 5px 0 #94a3b8, 0 10px 0 #94a3b8; }
        .setup-sidebar-icon--user::before { left: 5px; top: 2px; width: 8px; height: 8px; border: 1.5px solid #94a3b8; border-radius: 999px; background: transparent; }
        .setup-sidebar-icon--user::after { left: 3px; bottom: 2px; width: 12px; height: 5px; border: 1.5px solid #94a3b8; border-top: 0; border-radius: 0 0 8px 8px; background: transparent; }
        .setup-sidebar-icon--doc::before { left: 4px; top: 2px; width: 10px; height: 13px; border: 1.5px solid #94a3b8; border-radius: 2px; background: transparent; }
        .setup-sidebar-icon--doc::after { right: 5px; top: 2px; width: 4px; height: 4px; transform: rotate(45deg); background: #94a3b8; }
        .setup-sidebar-icon--chat::before { left: 3px; top: 4px; width: 12px; height: 9px; border: 1.5px solid #94a3b8; border-radius: 4px; background: transparent; }
        .setup-sidebar-icon--chat::after { left: 6px; bottom: 2px; width: 5px; height: 5px; transform: rotate(45deg); background: transparent; border-left: 1.5px solid #94a3b8; border-bottom: 1.5px solid #94a3b8; }
        .setup-sidebar-icon--temp::before { left: 7px; top: 1px; width: 4px; height: 12px; border: 1.5px solid #94a3b8; border-radius: 3px; background: transparent; }
        .setup-sidebar-icon--temp::after { left: 5px; bottom: 1px; width: 8px; height: 8px; border-radius: 999px; border: 1.5px solid #94a3b8; background: transparent; }
        .setup-sidebar-icon--play::before { left: 5px; top: 4px; width: 0; height: 0; border-left: 8px solid #94a3b8; border-top: 5px solid transparent; border-bottom: 5px solid transparent; background: transparent; }
        .setup-sidebar-icon--exit::before { left: 3px; top: 4px; width: 10px; height: 8px; border: 1.5px solid #94a3b8; border-left: 0; background: transparent; }
        .setup-sidebar-icon--exit::after { right: 2px; top: 5px; width: 7px; height: 2px; transform: rotate(45deg); background: #94a3b8; box-shadow: 0 3px 0 #94a3b8; }
        .setup-sidebar-item span:nth-child(2), .setup-sidebar-button span:nth-child(2) { flex: 1 1 auto; }
        .setup-sidebar-action, .setup-sidebar-button { color: #94a3b8; }
        .setup-sidebar-button { display: flex; align-items: center; gap: 0.4rem; padding: 0.55rem 0.8rem; border-radius: 7px; border-bottom: 1px solid rgba(148, 163, 184, 0.1); font-size: 0.92rem; background: #eef2f7; color: #9ca3af; min-height: 44px; margin: 0.45rem 0; }
        .setup-sidebar--active .setup-sidebar-button { background: #f7f9fd; color: #16224a; border: 1px solid #dbe2ed; opacity: 1; min-height: 44px; padding: 0.55rem 0.8rem; border-radius: 8px; font-size: 0.92rem; margin: 0.45rem 0; }
        .setup-sidebar-button--disabled { opacity: 1; }
        .setup-sidebar-item span:last-child { color: #cbd5e1; }
        .setup-sidebar--active .setup-sidebar-item span:last-child { color: #152446; }
        .setup-sidebar--active .setup-sidebar-value { display: flex; align-items: center; gap: 0.35rem; }
        .setup-sidebar-item:last-of-type, .setup-sidebar-action:last-of-type { border-bottom: 0; }
        .setup-sidebar * { user-select: none; }
        [data-testid="stElementContainer"].st-key-sidebar_restart,
        [data-testid="stElementContainer"].st-key-sidebar_exit { margin: 0.62rem 0; }
        [data-testid="stElementContainer"].st-key-sidebar_restart button,
        [data-testid="stElementContainer"].st-key-sidebar_exit button {
            justify-content: flex-start;
            min-height: 44px;
            padding: 0.55rem 0.8rem;
            border: 1px solid #dbe2ed;
            border-radius: 8px;
            background: #f7f9fd;
            color: #16224a;
            font-size: 0.92rem;
            font-weight: 700;
            box-shadow: none;
        }
        [data-testid="stElementContainer"].st-key-sidebar_restart button:disabled,
        [data-testid="stElementContainer"].st-key-sidebar_exit button:disabled { opacity: 0.65; }
        .setup-shell .stButton { max-width: 100%; }
        .setup-shell [data-testid="stElementContainer"].st-key-setup_start_interview { display: flex !important; justify-content: flex-end !important; width: 100% !important; margin: 0.35rem auto 0 !important; }
        .setup-shell [data-testid="stElementContainer"].st-key-setup_start_interview [data-testid="stButton"] { width: min(100%, 320px) !important; margin-left: auto; }
        .setup-sidebar .setup-sidebar-item, .setup-sidebar .setup-sidebar-action { padding-left: 0.1rem; padding-right: 0.1rem; }
        [data-testid="stButtonGroup"] { width: 100%; }
        [data-testid="stButtonGroup"] [data-baseweb="button-group"] {
            display: flex;
            gap: 0;
            width: 100%;
            border: 1px solid #d7dfee;
            border-radius: 12px;
            overflow: hidden;
            background: #ffffff;
        }
        .setup-shell [data-testid="stButtonGroup"] [data-baseweb="button-group"] > button[data-testid="stBaseButton-segmented_control"],
        .setup-shell [data-testid="stButtonGroup"] [data-baseweb="button-group"] > button[data-testid="stBaseButton-segmented_controlActive"] {
            padding: 0.68rem 0.9rem !important;
            min-height: 44px !important;
            box-shadow: none !important;
            border-radius: 0 !important;
        }
        .setup-shell [data-testid="stButtonGroup"] [data-baseweb="button-group"] > button[data-testid="stBaseButton-segmented_control"] {
            background: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #d7dfee !important;
        }
        .setup-shell [data-testid="stButtonGroup"] [data-baseweb="button-group"] > button[data-testid="stBaseButton-segmented_controlActive"] {
            background: #eef4ff !important;
            color: #1d4ed8 !important;
            border: 1px solid #1d4ed8 !important;
        }
        .setup-shell .stTextArea textarea { min-height: 96px; }
        .setup-shell .stTextInput input, .setup-shell .stSelectbox div[data-baseweb="select"], .setup-shell .stTextArea textarea, .setup-shell .stSlider { width: 100%; }
        .setup-shell [data-baseweb="select"] { min-height: 48px; }
        .setup-shell [data-baseweb="select"] > div { min-height: 48px; }
        .setup-shell [data-baseweb="select"] input { padding-top: 7px; padding-bottom: 7px; }
        .setup-shell [data-baseweb="select"] svg { color: #64748b; }
        .setup-shell .stSlider [role="slider"] { background: #1d4ed8 !important; }
        .setup-shell .stSlider [data-baseweb="slider"] { padding-top: 0.12rem; padding-bottom: 0.42rem; }
        .setup-shell [data-baseweb="slider"] > div { height: 6px; border-radius: 999px; background: #dbe3ee !important; }
        .setup-shell [data-baseweb="slider"] > div > div { background: #1d4ed8 !important; }
        [data-testid="stTextArea"] textarea[aria-label="Write your answer here..."] { min-height: 160px !important; }
        {QUESTION_STYLES}
        {FEEDBACK_STYLES}
        .setup-panel .stCaption { color: #64748b; margin-top: 0.08rem; }
        .setup-field-label { font-size: 0.9rem; font-weight: 700; color: #1e293b; margin: 0 0 0.35rem; }
        .setup-field-label--side { margin-bottom: 0; white-space: nowrap; }
        .setup-required-asterisk { margin-left: 0.18rem; color: #1d4ed8; }
        .setup-required-marker { display: inline-flex; align-items: center; margin-left: 0.4rem; padding: 0.14rem 0.42rem; border-radius: 999px; background: #fff1f2; color: #be123c; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
        .setup-field-error { margin: 0.3rem 0 0.55rem; padding: 0.45rem 0.7rem; border: 1px solid #fecaca; border-radius: 10px; background: #fef2f2; color: #b91c1c; font-size: 0.82rem; line-height: 1.35; }
        .setup-disabled-hint { margin-top: 0.35rem; color: #64748b; font-size: 0.8rem; line-height: 1.3; }
        .setup-shell [data-testid="stButtonGroup"] [data-baseweb="button-group"] > button[data-testid="stBaseButton-segmented_control"]:has(input[value=""]),
        .setup-shell [data-testid="stButtonGroup"] [data-baseweb="button-group"] > button[data-testid="stBaseButton-segmented_control"]:has([aria-pressed="false"]) {
            border-color: #fca5a5 !important;
            box-shadow: inset 0 0 0 1px #fca5a5 !important;
        }
        .setup-shell [data-testid="stButtonGroup"] [data-baseweb="button-group"] > button[data-testid="stBaseButton-segmented_controlActive"]:has([aria-pressed="true"]) {
            border-color: #1d4ed8 !important;
        }
        .setup-shell [data-baseweb="select"]:has(input[value=""]),
        .setup-shell [data-baseweb="select"]:has(button[aria-label="Select a role"]),
        .setup-shell [data-baseweb="select"]:has(button[aria-label="Select an option"]) {
            border-color: #fca5a5 !important;
            box-shadow: inset 0 0 0 1px #fca5a5 !important;
        }
        [data-testid="stRadio"] label { padding: 0; }
        @media (min-width: 901px) {
            .setup-main-layout > [data-testid="column"]:first-child { flex: 0 0 clamp(240px, 14vw, 285px); max-width: clamp(240px, 14vw, 285px); }
            .setup-main-layout > [data-testid="column"]:last-child { flex: 1 1 auto; max-width: calc(100% - clamp(240px, 14vw, 285px)); }
            .setup-sidebar { min-height: auto; }
        }
        @media (min-width: 1400px) {
            .setup-panel { width: min(100%, 1540px); }
            .setup-main-layout > [data-testid="column"]:first-child { flex-basis: clamp(240px, 14vw, 285px); max-width: clamp(240px, 14vw, 285px); }
            .setup-main-layout > [data-testid="column"]:last-child { max-width: calc(100% - clamp(240px, 14vw, 285px)); }
            .setup-start-wrap { max-width: 360px; }
        .setup-shell .stTextArea textarea { min-height: 124px; }
        }
        @keyframes screenFadeIn { from { opacity: 0.92; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        @media (max-width: 900px) {
            .setup-shell { min-height: 0; padding-top: 0; }
            .setup-main-layout > [data-testid="column"] { min-height: 0; }
            .setup-sidebar { min-height: auto; }
        }
    """.replace("{QUESTION_STYLES}", QUESTION_STYLES).replace("{FEEDBACK_STYLES}", FEEDBACK_STYLES)
    return css
