from pathlib import Path
import sys
from unittest.mock import patch

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from interview_app_frontend.app import main


def test_main_injects_paste_fix_on_question_screen() -> None:
    st.session_state.clear()
    st.session_state.current_screen = "question"

    with patch("interview_app_frontend.app.st.set_page_config"), patch(
        "interview_app_frontend.app.ensure_session_state"
    ), patch("interview_app_frontend.app.inject_styles"), patch(
        "interview_app_frontend.app.render_screen"
    ), patch(
        "interview_app_frontend.app.components.html"
    ) as mock_html:
        main()

    mock_html.assert_called_once()


def test_main_skips_paste_fix_off_question_screen() -> None:
    st.session_state.clear()
    st.session_state.current_screen = "welcome"

    with patch("interview_app_frontend.app.st.set_page_config"), patch(
        "interview_app_frontend.app.ensure_session_state"
    ), patch("interview_app_frontend.app.inject_styles"), patch(
        "interview_app_frontend.app.render_screen"
    ), patch(
        "interview_app_frontend.app.components.html"
    ) as mock_html:
        main()

    mock_html.assert_not_called()
