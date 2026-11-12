import sys
import unittest
from unittest.mock import patch

sys.path.append(r"D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main")

import streamlit as st

from interview_app_frontend.components.feedback_screen import render_feedback
from interview_app_frontend.ui.screens import render_screen
from interview_app_frontend.state.session_manager import advance_to_next_question, go_to_session_summary
from interview_app_frontend.utils.feedback_model import normalise_feedback_payload, score_band, score_bar
from interview_app_frontend.utils.feedback_view import (
    build_behaviour_aware_trust,
    build_follow_up,
    build_key_takeaway,
    build_score_consistency,
    prioritise_improvements,
    prioritise_strengths,
)


class TestFeedbackFormatting(unittest.TestCase):
    def setUp(self):
        st.session_state.clear()

    def test_score_display_mapping_uses_expected_bands(self):
        self.assertEqual(score_band(2), "Weak")
        self.assertEqual(score_band(5), "Needs improvement")
        self.assertEqual(score_band(8), "Strong")
        self.assertEqual(score_band(10), "Excellent")
        self.assertEqual(score_bar(7), "███████░░░")

    def test_feedback_payload_normalisation_keeps_scores_and_notes(self):
        payload = {
            "overall_decision": "borderline pass",
            "scores": {"relevance": 9, "structure": 3, "specificity": 5, "communication": 7, "problem_solving_approach": 8},
            "strengths": ["Clear answer"],
            "key_issues": ["Needs metrics"],
            "improvements": ["Add a measurable result"],
        }

        result = normalise_feedback_payload(payload)

        self.assertEqual(result["overall_decision"], "borderline pass")
        self.assertEqual(result["scores"]["relevance"], 9)
        self.assertEqual(result["scores"]["structure"], 3)
        self.assertEqual(result["strengths"], ["Clear answer"])
        self.assertEqual(result["key_issues"], ["Needs metrics"])
        self.assertEqual(result["improvements"], ["Add a measurable result"])

    def test_strengths_are_prioritised_by_signal_strength(self):
        payload = {
            "scores": {"relevance": 9, "structure": 4, "specificity": 8, "communication": 7, "problem_solving_approach": 6},
            "strengths": ["Clear and easy to follow", "Strong metrics and impact", "Explains trade-offs"],
        }

        result = prioritise_strengths(normalise_feedback_payload(payload))

        self.assertEqual(result[0], "Strong metrics and impact")

    def test_improvements_are_prioritised_by_issue_context(self):
        payload = normalise_feedback_payload(
            {
                "improvements": ["Explain technical decisions and trade-offs", "Add quantifiable results"],
                "key_issues": ["Trade-offs are only implied", "Missing specific metrics for improvement"],
            }
        )

        result = prioritise_improvements(payload)

        self.assertEqual(result[0], "Explain technical decisions and trade-offs")

    def test_follow_up_uses_issue_context(self):
        payload = normalise_feedback_payload(
            {
                "scores": {"relevance": 4, "structure": 3, "specificity": 3, "communication": 7, "problem_solving_approach": 5},
                "key_issues": ["Missing specific metrics for improvement", "Trade-offs are only implied"],
                "improvements": ["Add quantifiable results", "Explain technical decisions and trade-offs"],
                "validation_warning": {"reasoning_depth": "implicit"},
            }
        )

        follow_up = build_follow_up(payload)

        self.assertIn("metric", follow_up["question"].lower())
        self.assertEqual(follow_up["target_dimension"], "specificity")
        self.assertIn("alternative", follow_up["reasoning_action"].lower())
        self.assertIn("metrics", follow_up["context_note"].lower())
        self.assertEqual(follow_up["stage"], 1)

    def test_follow_up_stage_advances_with_memory(self):
        payload = normalise_feedback_payload(
            {
                "scores": {"relevance": 4, "structure": 3, "specificity": 3, "communication": 7, "problem_solving_approach": 5},
                "key_issues": ["Trade-offs are only implied"],
                "future_session_memory": [{"focus": "specificity"}],
                "validation_warning": {"reasoning_depth": "implicit"},
            }
        )

        follow_up = build_follow_up(payload)

        self.assertEqual(follow_up["stage"], 2)
        self.assertIn("next time", follow_up["question"].lower())

    def test_follow_up_for_irrelevant_answers_is_direct(self):
        payload = normalise_feedback_payload(
            {
                "overall_decision": "fail",
                "scores": {"relevance": 1, "structure": 3, "specificity": 1, "communication": 6, "problem_solving_approach": 2},
                "validation_warning": {"reasoning_depth": "not_applicable"},
                "topic_match": False,
                "relevance_gate_applied": True,
            }
        )

        follow_up = build_follow_up(payload)

        self.assertEqual(follow_up["type"], "relevance_gate")
        self.assertIn("system performance", follow_up["question"].lower())
        self.assertIn("directly", follow_up["reasoning_action"].lower())

    def test_score_consistency_helper_is_calm_and_specific(self):
        payload = normalise_feedback_payload(
            {
                "overall_decision": "pass",
                "overall_decision_detail": {"score_based_value": "fail", "trust_level": "low"},
                "scores": {"relevance": 3, "structure": 3, "specificity": 2, "communication": 3, "problem_solving_approach": 3},
            }
        )

        consistency = build_score_consistency(payload)
        takeaway = build_key_takeaway(payload)

        self.assertTrue(consistency["has_gap"])
        self.assertIn("trust cue", consistency["note"].lower())
        self.assertIn("key takeaway", takeaway.lower())


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
        ) as mock_columns, patch("interview_app_frontend.components.feedback_screen.st.button") as mock_button, patch(
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
        ) as mock_columns, patch("interview_app_frontend.components.feedback_screen.st.button"), patch(
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
