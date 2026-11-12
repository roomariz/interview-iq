from html import escape

import streamlit as st


def render_shared_topbar(
    *,
    title: str,
    subtitle: str,
    right_title: str,
    right_copy: str,
    left_icon: str = "⚙",
    right_icon: str = "🛡",
) -> None:
    st.markdown(
        f"""
        <div class="setup-topbar">
            <div class="setup-topbar-left">
                <div class="setup-topbar-icon">{escape(left_icon)}</div>
                <div>
                    <div class="setup-topbar-title">{escape(title)}</div>
                    <div class="setup-topbar-subtitle">{escape(subtitle)}</div>
                </div>
            </div>
            <div class="setup-topbar-privacy">
                <div class="setup-topbar-privacy-icon">{escape(right_icon)}</div>
                <div>{escape(right_title)}<br/>{escape(right_copy)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
