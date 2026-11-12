from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from interview_app_frontend.components.request_log_panel import render_request_log_panel
from interview_app_frontend.utils.request_log import get_log_summary


class _DummyExpander:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_render_request_log_panel_accepts_snake_case_summary_keys() -> None:
    summary = [
        {
            "time": "12:34:56",
            "task": "question_generation",
            "primary_model": "google/gemma-4-31b-it:free",
            "attempts": 2,
            "Final Status": "WARNING",
            "Reason": "temporary_rate_limit",
            "Latency": "1.2s",
        }
    ]

    columns = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

    with patch("interview_app_frontend.components.request_log_panel.has_request_logs", return_value=True), patch(
        "interview_app_frontend.components.request_log_panel.get_log_summary", return_value=summary
    ), patch(
        "interview_app_frontend.components.request_log_panel.get_status_counts",
        return_value={"OK": 0, "WARNING": 1, "FAIL": 0, "SWITCH": 0},
    ), patch(
        "interview_app_frontend.components.request_log_panel.clear_request_log"
    ), patch(
        "interview_app_frontend.components.request_log_panel.st.expander",
        return_value=_DummyExpander(),
    ), patch(
        "interview_app_frontend.components.request_log_panel.st.dataframe"
    ) as mock_dataframe, patch(
        "interview_app_frontend.components.request_log_panel.st.columns", return_value=columns
    ), patch(
        "interview_app_frontend.components.request_log_panel.st.button", return_value=False
    ):
        render_request_log_panel()

    styled_df = mock_dataframe.call_args.args[0]
    assert list(styled_df.data.columns) == [
        "Time",
        "Task",
        "Primary Model",
        "Attempts",
        "Fall back",
        "Final Status",
        "Reason",
        "Latency",
    ]


def test_running_request_logs_as_warning_summary() -> None:
    st.session_state.clear()
    st.session_state.request_log = [
        {
            "timestamp": 0,
            "task": "answer_evaluation",
            "provider": "open-router",
            "model": "google/gemma-4-31b-it:free",
            "attempts": 1,
            "fallback_reason": None,
            "status": "running",
            "error": "",
            "latency_ms": 0,
            "success": False,
        }
    ]

    summary = get_log_summary()

    assert summary[0]["Final Status"] == "WARNING"
    assert summary[0]["Reason"] == "in_progress"


def test_request_log_panel_auto_expands_for_running_requests() -> None:
    st.session_state.clear()
    st.session_state.request_log = [
        {
            "timestamp": 0,
            "task": "answer_evaluation",
            "provider": "open-router",
            "model": "google/gemma-4-31b-it:free",
            "attempts": 1,
            "fallback_reason": None,
            "status": "running",
            "error": "",
            "latency_ms": 0,
            "success": False,
        }
    ]

    with patch("interview_app_frontend.components.request_log_panel.has_request_logs", return_value=True), patch(
        "interview_app_frontend.components.request_log_panel.get_log_summary", return_value=[]
    ), patch(
        "interview_app_frontend.components.request_log_panel.get_status_counts",
        return_value={"OK": 0, "WARNING": 1, "FAIL": 0, "SWITCH": 0},
    ), patch(
        "interview_app_frontend.components.request_log_panel.clear_request_log"
    ), patch(
        "interview_app_frontend.components.request_log_panel.st.expander",
        return_value=_DummyExpander(),
    ) as mock_expander, patch(
        "interview_app_frontend.components.request_log_panel.st.dataframe"
    ), patch(
        "interview_app_frontend.components.request_log_panel.st.columns", return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    ), patch(
        "interview_app_frontend.components.request_log_panel.st.button", return_value=False
    ):
        render_request_log_panel()

    assert mock_expander.call_args.kwargs["expanded"] is True
