import unittest
from unittest.mock import patch

import streamlit as st

from interview_app_frontend.components.session_summary_screen import render_session_summary


class TestSessionSummaryScreen(unittest.TestCase):
    def setUp(self) -> None:
        st.session_state.clear()
        st.session_state.summary = {
            "title": "Interview Session Complete!",
            "overall_performance": "50% (Needs Improvement)",
            "questions_completed": 1,
            "session_duration": "1 minutes",
            "average_scores": {"relevance": 5, "structure": 5, "specificity": 5, "communication": 5, "problem_solving_approach": 5},
            "strengths": [],
            "improvement_areas": [],
            "focus_areas": [],
            "recommended_next_steps": [],
            "evaluation_notice": "1 question evaluated with reduced confidence.",
        }
        st.session_state.feedback = {
            "strengths": ["Clear communication and easy to follow"],
            "improvements": ["Add one rejected alternative and one trade-off you accepted."],
        }
        st.session_state.answers = [
            {
                "question": "What would you do differently the next time you face the same gap?",
                "answer": "I would add one rejected alternative and one trade-off I accepted.",
                "overall_decision": "borderline pass",
                "summary": "Clear communication and easy to follow.",
                "strengths": ["Clear communication and easy to follow"],
                "improvements": ["Add one rejected alternative and one trade-off you accepted."],
                "scores": {"relevance": 5, "structure": 5, "specificity": 5, "communication": 5, "problem_solving_approach": 5},
                "trust": {"trust_level": "low"},
            }
        ]

    def test_render_session_summary_shows_evaluation_notice_once(self):
        def _columns(widths):
            count = widths if isinstance(widths, int) else len(widths)
            return tuple(unittest.mock.MagicMock() for _ in range(count))

        with patch("interview_app_frontend.components.session_summary_screen.inject_summary_styles"), patch(
            "interview_app_frontend.components.session_summary_screen.st.markdown"
        ) as mock_markdown, patch("interview_app_frontend.components.session_summary_screen.st.columns", side_effect=_columns), patch(
            "interview_app_frontend.components.session_summary_screen.st.button"
        ), patch("interview_app_frontend.components.session_summary_screen.st.info") as mock_info:
            render_session_summary()

        mock_info.assert_called_once_with("1 question evaluated with reduced confidence.")
        rendered_html = " ".join(str(call.args[0]) for call in mock_markdown.call_args_list if call.args)
        self.assertIn("Latest Question Recap", rendered_html)
        self.assertIn("What would you do differently the next time you face the same gap?", rendered_html)


if __name__ == "__main__":
    unittest.main()
