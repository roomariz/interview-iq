import sys
import unittest

sys.path.append(r"D:\workspace\Turing_College\interview-practice-app\rrizwa-AE.1.5-main")

import streamlit as st

from interview_app_frontend.utils.feedback_model import normalise_feedback_payload, score_band, score_bar
from interview_app_frontend.utils.feedback_view import (
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

    def test_follow_up_uses_current_answer_decision(self):
        payload = normalise_feedback_payload(
            {
                "scores": {"relevance": 4, "structure": 3, "specificity": 3, "communication": 7, "problem_solving_approach": 5},
                "key_issues": ["Missing specific metrics for improvement", "Trade-offs are only implied"],
                "improvements": ["Add quantifiable results", "Explain technical decisions and trade-offs"],
                "question": "How would you diagnose a slow service?",
                "answer": "I would profile the database queries first.",
                "validation_warning": {"reasoning_depth": "implicit"},
            }
        )

        follow_up = build_follow_up(payload)

        self.assertIn("profile the database queries", follow_up["question"].lower())
        self.assertEqual(follow_up["target_dimension"], "problem_solving_approach")
        self.assertIn("evidence", follow_up["reasoning_action"].lower())
        self.assertIn("How would you diagnose a slow service?", follow_up["context_note"])
        self.assertNotIn("metric", follow_up["question"].lower())
        self.assertEqual(follow_up["stage"], 1)

    def test_follow_up_does_not_infer_repeated_gap_from_memory(self):
        payload = normalise_feedback_payload(
            {
                "scores": {"relevance": 4, "structure": 3, "specificity": 3, "communication": 7, "problem_solving_approach": 5},
                "key_issues": ["Trade-offs are only implied"],
                "future_session_memory": [{"focus": "specificity"}],
                "validation_warning": {"reasoning_depth": "implicit"},
            }
        )

        follow_up = build_follow_up(payload)

        self.assertEqual(follow_up["stage"], 1)
        self.assertEqual(follow_up["question"], "Which concrete step would you take first, and what evidence would support it?")
        self.assertNotIn("specificity", follow_up["question"].lower())

    def test_follow_up_for_irrelevant_answers_is_direct(self):
        payload = normalise_feedback_payload(
            {
                "question": "How would you improve system performance?",
                "answer": "I enjoy baking cakes.",
                "overall_decision": "fail",
                "scores": {"relevance": 1, "structure": 3, "specificity": 1, "communication": 6, "problem_solving_approach": 2},
                "validation_warning": {"reasoning_depth": "not_applicable"},
                "topic_match": False,
                "relevance_gate_applied": True,
            }
        )

        follow_up = build_follow_up(payload)

        self.assertEqual(follow_up["type"], "relevance_gate")
        self.assertEqual(follow_up["question"], "Which evidence or explanation directly addresses the original question?")
        self.assertEqual(follow_up["target_dimension"], "relevance")
        self.assertIn("system performance", follow_up["context_note"].lower())
        self.assertIn("baking cakes", follow_up["context_note"].lower())

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
