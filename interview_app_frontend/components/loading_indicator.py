from html import escape

import streamlit as st


_LOADING_STYLES = """
<style>
.evaluation-loader {
    width: min(360px, 100%);
    margin: 1rem auto 0;
    display: grid;
    gap: 0.65rem;
    justify-items: center;
    text-align: center;
}
.evaluation-loader--compact {
    width: min(280px, 100%);
    margin-top: 0;
}
.evaluation-loader__ring {
    width: 42px;
    height: 42px;
    border-radius: 999px;
    border: 4px solid rgba(29, 78, 216, 0.14);
    border-top-color: #1d4ed8;
    animation: evaluation-spin 0.9s linear infinite;
}
.evaluation-loader__dots {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
}
.evaluation-loader__dots span {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #1d4ed8;
    opacity: 0.35;
    animation: evaluation-pulse 1.1s infinite ease-in-out;
}
.evaluation-loader__dots span:nth-child(2) { animation-delay: 0.15s; }
.evaluation-loader__dots span:nth-child(3) { animation-delay: 0.3s; }
.evaluation-loader__status {
    color: #1d4ed8;
    font-weight: 800;
    line-height: 1.35;
}
.evaluation-loader__bar {
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: linear-gradient(90deg, #dbeafe 0%, #bfdbfe 45%, #dbeafe 100%);
    overflow: hidden;
}
.evaluation-loader__bar::after {
    content: "";
    display: block;
    height: 100%;
    width: 40%;
    border-radius: inherit;
    background: linear-gradient(90deg, rgba(29, 78, 216, 0.2), rgba(29, 78, 216, 0.9), rgba(29, 78, 216, 0.2));
    animation: evaluation-slide 1.4s ease-in-out infinite;
}
.evaluation-loader--panel {
    padding: 0.95rem 1rem;
    border-radius: 16px;
    border: 1px solid #dbe3f0;
    background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
}
@keyframes evaluation-spin {
    to { transform: rotate(360deg); }
}
@keyframes evaluation-pulse {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.35; }
    40% { transform: translateY(-4px); opacity: 1; }
}
@keyframes evaluation-slide {
    0% { transform: translateX(-55%); }
    50% { transform: translateX(75%); }
    100% { transform: translateX(155%); }
}
</style>
"""


def render_loading_indicator(message: str, *, compact: bool = False, panel: bool = False) -> None:
    classes = ["evaluation-loader"]
    if compact:
        classes.append("evaluation-loader--compact")
    if panel:
        classes.append("evaluation-loader--panel")
    st.markdown(_LOADING_STYLES, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="{' '.join(classes)}" aria-label="Loading evaluation in progress">
            <div class="evaluation-loader__ring" aria-hidden="true"></div>
            <div class="evaluation-loader__dots" aria-hidden="true"><span></span><span></span><span></span></div>
            <div class="evaluation-loader__status">{escape(message)}</div>
            <div class="evaluation-loader__bar" aria-hidden="true"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
