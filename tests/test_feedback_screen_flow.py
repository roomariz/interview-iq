import sys
import unittest
from unittest.mock import patch

sys.path.append(r"D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main")

import streamlit as st

from interview_app_frontend.components.feedback_screen import render_feedback
from interview_app_frontend.state.session_manager import advance_to_next_question


class TestFeedbackFlow(unittest.TestCase):
    def setUp(self):
        st.session_state.clear()

    def test_render_feedback_uses_mockup_aligned_defaults(self):
        st.session_state.current_screen = "feedback"
        st.session_state.feedback = {}
        st.session_state.job_description = "Added"
        st.session_state.cv_status = "Uploaded"

        def _columns_mock(*args, **kwargs):
            return (unittest.mock.MagicMock(), unittest.mock.MagicMock())

        with patch("interview_app_frontend.components.feedback_screen.st.markdown") as mock_markdown, patch(
            "interview_app_frontend.components.feedback_screen.st.columns", side_effect=_columns_mock
        ), patch("interview_app_frontend.components.feedback_screen.st.button") as mock_button, patch(
            "interview_app_frontend.components.feedback_screen.st.download_button"
        ) as mock_download, patch("interview_app_frontend.components.feedback_screen.st.expander") as mock_expander, patch(
            "interview_app_frontend.components.feedback_screen.st.code"
        ):
            mock_expander.return_value.__enter__.return_value = None
            mock_expander.return_value.__exit__.return_value = False
            render_feedback()

        rendered_html = " ".join(str(call.args[0]) for call in mock_markdown.call_args_list if call.args)
        self.assertIn("setup-sidebar-status", rendered_html)
        self.assertIn("setup-sidebar--active", rendered_html)
        self.assertIn("feedback-card__subtitle", rendered_html)
        self.assertIn("feedback-trust", rendered_html)
        self.assertIn("Continue Learning", rendered_html)
        self.assertIn("feedback-nudge", rendered_html)
        self.assertNotIn("Overall Outcome:", rendered_html)
        show_example_calls = [call for call in mock_button.call_args_list if call.args and call.args[0] == "Next"]
        self.assertTrue(show_example_calls)
        self.assertIs(show_example_calls[0].kwargs.get("on_click"), advance_to_next_question)
        self.assertEqual(show_example_calls[0].kwargs.get("type"), "primary")
        self.assertTrue(mock_expander.called)
        self.assertFalse(mock_expander.call_args.kwargs.get("expanded"))
        mock_download.assert_called_once()

    def test_render_feedback_shows_score_consistency_guard(self):
        st.session_state.current_screen = "feedback"
        st.session_state.feedback = {
            "overall_decision": "pass",
            "overall_decision_detail": {
                "value": "pass",
                "score_based_value": "fail",
                "trust_level": "low",
                "score_confidence": 0.31,
                "decision_confidence": "low",
                "gating_applied": True,
                "reason": "Decision should be reviewed because trust level is low",
            },
            "validation_warning": {
                "has_warning": True,
                "severity": "info",
                "trust_level": "low",
                "score_confidence": 0.31,
                "reasoning_depth": "implicit",
                "interpretation": "Treat the scores as provisional; the flags affect interpretation.",
            },
            "scores": {"relevance": 3, "structure": 3, "specificity": 2, "communication": 3, "problem_solving_approach": 3},
        }

        def _columns_mock(*args, **kwargs):
            return (unittest.mock.MagicMock(), unittest.mock.MagicMock())

        with patch("interview_app_frontend.components.feedback_screen.st.markdown") as mock_markdown, patch(
            "interview_app_frontend.components.feedback_screen.st.columns", side_effect=_columns_mock
        ), patch("interview_app_frontend.components.feedback_screen.st.button"), patch(
            "interview_app_frontend.components.feedback_screen.st.download_button"
        ), patch("interview_app_frontend.components.feedback_screen.st.expander") as mock_expander, patch(
            "interview_app_frontend.components.feedback_screen.st.code"
        ):
            mock_expander.return_value.__enter__.return_value = None
            mock_expander.return_value.__exit__.return_value = False
            render_feedback()

        rendered_html = " ".join(str(call.args[0]) for call in mock_markdown.call_args_list if call.args)
        self.assertIn("Score consistency check", rendered_html)
        self.assertIn("feedback-decision-confidence", rendered_html)

    def test_view_technical_breakdown_switches_to_summary(self):
        st.session_state.current_screen = "feedback"
        st.session_state.feedback = {}

        def _columns_mock(*args, **kwargs):
            return (unittest.mock.MagicMock(), unittest.mock.MagicMock())

        with patch("interview_app_frontend.components.feedback_screen.st.markdown"), patch(
            "interview_app_frontend.components.feedback_screen.st.columns", side_effect=_columns_mock
        ), patch("interview_app_frontend.components.feedback_screen.st.button") as mock_button, patch(
            "interview_app_frontend.components.feedback_screen.st.download_button"
        ), patch("interview_app_frontend.components.feedback_screen.st.expander") as mock_expander, patch(
            "interview_app_frontend.components.feedback_screen.st.code"
        ):
            mock_expander.return_value.__enter__.return_value = None
            mock_expander.return_value.__exit__.return_value = False
            render_feedback()

        breakdown_calls = [call for call in mock_button.call_args_list if call.args and call.args[0] == "Summary"]
        self.assertTrue(breakdown_calls)
        self.assertEqual(breakdown_calls[0].kwargs.get("on_click").__name__, "go_to_session_summary")

    def test_render_feedback_uses_summary_label_on_last_question(self):
        st.session_state.current_screen = "feedback"
        st.session_state.current_question_index = 5
        st.session_state.feedback = {}

        def _columns_mock(*args, **kwargs):
            return (unittest.mock.MagicMock(), unittest.mock.MagicMock())

        with patch("interview_app_frontend.components.feedback_screen.st.markdown"), patch(
            "interview_app_frontend.components.feedback_screen.st.columns", side_effect=_columns_mock
        ), patch("interview_app_frontend.components.feedback_screen.st.button") as mock_button, patch(
            "interview_app_frontend.components.feedback_screen.st.download_button"
        ), patch("interview_app_frontend.components.feedback_screen.st.expander") as mock_expander, patch(
            "interview_app_frontend.components.feedback_screen.st.code"
        ):
            mock_expander.return_value.__enter__.return_value = None
            mock_expander.return_value.__exit__.return_value = False
            render_feedback()

        next_calls = [call for call in mock_button.call_args_list if call.args and call.args[0] == "Next"]
        self.assertTrue(next_calls)

    def test_advance_next_question_moves_to_summary_after_fifth_question(self):
        st.session_state.current_question_index = 5

        advance_to_next_question()

        self.assertEqual(st.session_state.current_screen, "summary")
        self.assertTrue(st.session_state.session_complete)

    def test_render_feedback_shows_relevance_gate_nudge(self):
        st.session_state.current_screen = "feedback"
        st.session_state.feedback = {"failure_type": "off_topic", "validation_warning": {"interpretation": ""}}

        def _columns_mock(*args, **kwargs):
            return (unittest.mock.MagicMock(), unittest.mock.MagicMock())

        with patch("interview_app_frontend.components.feedback_screen.st.markdown") as mock_markdown, patch(
            "interview_app_frontend.components.feedback_screen.st.columns", side_effect=_columns_mock
        ), patch("interview_app_frontend.components.feedback_screen.st.button"), patch(
            "interview_app_frontend.components.feedback_screen.st.download_button"
        ), patch("interview_app_frontend.components.feedback_screen.st.expander") as mock_expander, patch(
            "interview_app_frontend.components.feedback_screen.st.code"
        ):
            mock_expander.return_value.__enter__.return_value = None
            mock_expander.return_value.__exit__.return_value = False
            render_feedback()

        rendered_html = " ".join(str(call.args[0]) for call in mock_markdown.call_args_list if call.args)
        self.assertIn("review the summary", rendered_html.lower())


if __name__ == "__main__":
    unittest.main()
