"""Resolve a server-only anonymous token on the Streamlit script thread."""

from shared.visitor_identity import issue, validate


def session_token(key):
    if not key:
        return ""  # Legacy local/test mode only; production requires a key.
    import streamlit as st
    token = st.session_state.get("_anonymous_visitor_token", "")
    try:
        validate(token, key)
    except ValueError:
        token = issue(key)
        st.session_state["_anonymous_visitor_token"] = token
    return token
