import pandas as pd
import streamlit as st

from interview_app_frontend.utils.request_log import (
    get_log_summary,
    has_request_logs,
    clear_request_log,
    get_status_counts,
)


def render_request_log_panel() -> None:
    if not has_request_logs():
        return

    active_request = any(log.get("status") in ("pending", "running") for log in st.session_state.get("request_log", []))

    with st.expander("Request Log", expanded=active_request):
        summary = get_log_summary()

        if not summary:
            st.write("No requests logged.")
            return

        df = pd.DataFrame(summary)
        columns = ["Time", "Task", "Primary Model", "Attempts", "Fall back", "Final Status", "Reason", "Latency"]
        column_aliases = {
            "time": "Time",
            "task": "Task",
            "primary_model": "Primary Model",
            "attempts": "Attempts",
            "Fall back": "Fall back",
            "fallback": "Fall back",
            "Final Status": "Final Status",
            "final_status": "Final Status",
            "Reason": "Reason",
            "reason": "Reason",
            "Latency": "Latency",
            "latency": "Latency",
        }
        display_df = df.rename(columns=column_aliases).reindex(columns=columns).copy()

        def style_status(val: str) -> str:
            if val == "OK":
                return "color: green"
            if val == "FAIL":
                return "color: red"
            if val == "WARNING":
                return "color: orange"
            if val == "SWITCH":
                return "color: blue"
            return ""

        styled = display_df.style.applymap(style_status, subset=["Final Status"])

        st.dataframe(styled, use_container_width=True, hide_index=True)

        counts = get_status_counts()
        cols = st.columns(4)
        for i, (status, count) in enumerate(counts.items()):
            cols[i].markdown(f"**{status}**: {count}")

        if st.button("Clear Log", key="clear_request_log"):
            clear_request_log()
            st.rerun()


def render_request_log_summary() -> str:
    if not has_request_logs():
        return ""

    counts = get_status_counts()
    total = sum(counts.values())
    failures = counts["FAIL"]

    if failures > 0:
        return f"⚠️ {failures}/{total} requests failed"
    if counts["WARNING"] > 0:
        return f"⚡ {counts['WARNING']} retries"
    return f"✓ {total} requests OK"
