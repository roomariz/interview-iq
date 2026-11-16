import unittest  # noqa: F401
from time import sleep, time  # noqa: F401
from unittest.mock import patch  # noqa: F401
import sys  # noqa: F401
from concurrent.futures import Future  # noqa: F401

sys.path.append(r"D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main")

import streamlit as st  # noqa: F401
from unittest.mock import MagicMock  # noqa: F401

import interview_app_frontend.app as app_module  # noqa: F401
from interview_app_frontend.app import main  # noqa: F401
from interview_app_frontend.components.shell import SETUP_WIDGET_KEYS  # noqa: F401
from interview_app_frontend.state.question_generation_job import poll_question_generation  # noqa: F401
from interview_app_frontend.components.answer_evaluation_screen import render_answer_evaluation  # noqa: F401
from interview_app_frontend.components.question_screen import render_question_and_answer  # noqa: F401
from interview_app_frontend.state.session_manager import start_interview  # noqa: F401
from interview_app_backend.services.question_service import get_next_question_for_session  # noqa: F401


class QuestionLoopTestCase(unittest.TestCase):
    def setUp(self):
        st.session_state.clear()

    def _wait_for_generation(self, timeout: float = 1.0) -> None:
        deadline = time() + timeout
        while time() < deadline:
            if poll_question_generation(st.session_state):
                return
            sleep(0.01)

