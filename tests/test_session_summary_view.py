import unittest

from interview_app_frontend.utils.session_summary_view import (
    build_session_summary_view,
    _build_summary_from_raw,
    is_valid_answer,
    is_degraded_evaluation,
)


class TestSessionSummaryView(unittest.TestCase):
    def test_build_summary_from_raw_with_scores(self):
        answers = [
            {"scores": {"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7}},
            {"scores": {"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7}},
        ]
        result = _build_summary_from_raw(answers, 2, 15, ["Clear"], ["Add metrics"], [])
        self.assertEqual(result["questions_completed"], 2)
        self.assertEqual(result["session_duration"], "15 minutes")
        self.assertIn("overall_performance", result)
        self.assertIn("Good", result["overall_performance"])

    def test_build_summary_from_raw_empty(self):
        result = _build_summary_from_raw([], 0, 0, [], [], [])
        self.assertEqual(result["questions_completed"], 0)
        self.assertIn("Needs Improvement", result["overall_performance"])

    def test_build_summary_view_with_session_state(self):
        session_state = {
            "answers": [
                {"question": "Q1", "answer": "A1", "scores": {"relevance": 7, "structure": 6, "specificity": 5, "communication": 8, "problem_solving_approach": 6}},
            ],
            "current_question_index": 0,
            "session_duration_minutes": 10,
            "feedback": {"strengths": ["Clear"], "improvements": ["Add metrics"]},
            "summary": {},
        }
        result = build_session_summary_view(session_state)
        self.assertEqual(result["questions_completed"], 1)
        self.assertIn("Clear", result["strengths"])
        self.assertIn("Add metrics", result["improvement_areas"])

    def test_build_summary_view_counts_actual_answers(self):
        session_state = {
            "answers": [
                {"question": "Q1", "answer": "A1", "scores": {"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7}},
                {"question": "Q2", "answer": "A2", "scores": {"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7}},
            ],
            "current_question_index": 9,
            "session_duration_minutes": 12,
            "feedback": {"strengths": [], "improvements": []},
            "summary": {},
        }
        result = build_session_summary_view(session_state)
        self.assertEqual(result["questions_completed"], 2)
        self.assertEqual(result["overall_performance"], "70% (Good)")

    def test_build_summary_view_uses_existing_summary(self):
        session_state = {
            "summary": {
                "title": "Custom Title",
                "overall_performance": "85% (Excellent)",
                "questions_completed": 3,
                "session_duration": "20 minutes",
                "average_scores": {"relevance": 8.5},
                "strengths": ["Custom strength"],
                "improvement_areas": ["Custom improvement"],
                "recommended_next_steps": ["Step 1"],
            }
        }
        result = build_session_summary_view(session_state)
        self.assertEqual(result["title"], "Custom Title")
        self.assertEqual(result["overall_performance"], "85% (Excellent)")
        self.assertEqual(result["questions_completed"], 3)

    def test_build_summary_view_backfills_missing_sections_from_feedback(self):
        session_state = {
            "summary": {
                "title": "Interview Session Complete!",
                "overall_performance": "50% (Needs Improvement)",
                "questions_completed": 1,
                "session_duration": "1 minutes",
                "average_scores": {"relevance": 5},
                "strengths": [],
                "improvement_areas": [],
                "focus_areas": [],
                "recommended_next_steps": [],
                "evaluation_notice": "",
            },
            "feedback": {
                "strengths": ["Clear communication and easy to follow"],
                "improvements": ["Add one rejected alternative and one trade-off you accepted."],
                "key_issues": ["The evaluator could not complete a reliable pass across the free-model chain."],
            },
            "answers": [
                {
                    "question": "What would you do differently the next time you face the same gap?",
                    "answer": "I would add one rejected alternative and one trade-off I accepted.",
                    "scores": {"relevance": 5, "structure": 5, "specificity": 5, "communication": 5, "problem_solving_approach": 5},
                    "trust": {"trust_level": "low"},
                }
            ],
        }
        result = build_session_summary_view(session_state)
        self.assertIn("Clear communication and easy to follow", result["strengths"])
        self.assertIn("Add one rejected alternative and one trade-off you accepted.", result["improvement_areas"])
        self.assertIn("reduced confidence", result["evaluation_notice"])
        self.assertEqual(result["latest_question_recap"]["question"], "What would you do differently the next time you face the same gap?")
        self.assertIn("Clear communication and easy to follow", result["latest_question_recap"]["strengths"])

    def test_build_summary_view_uses_answer_history_when_live_feedback_is_missing(self):
        session_state = {
            "summary": {
                "title": "Interview Session Complete!",
                "overall_performance": "50% (Needs Improvement)",
                "questions_completed": 1,
                "session_duration": "1 minutes",
                "average_scores": {"relevance": 5, "structure": 5, "specificity": 5, "communication": 5, "problem_solving_approach": 5},
                "strengths": [],
                "improvement_areas": [],
                "focus_areas": [],
                "recommended_next_steps": [],
                "evaluation_notice": "",
            },
            "feedback": [],
            "answers": [
                {
                    "question": "What would you do differently the next time you face the same gap?",
                    "answer": "I would add one rejected alternative and one trade-off I accepted.",
                    "scores": {"relevance": 5, "structure": 5, "specificity": 5, "communication": 5, "problem_solving_approach": 5},
                    "trust": {"trust_level": "low"},
                    "strengths": ["Clear communication and easy to follow"],
                    "improvements": ["Add one rejected alternative and one trade-off you accepted."],
                    "key_issues": ["The evaluator could not complete a reliable pass across the free-model chain."],
                }
            ],
        }

        result = build_session_summary_view(session_state)

        self.assertIn("Clear communication and easy to follow", result["strengths"])
        self.assertIn("Add one rejected alternative and one trade-off you accepted.", result["improvement_areas"])
        self.assertIn("reduced confidence", result["evaluation_notice"])
        self.assertEqual(result["latest_question_recap"]["question"], "What would you do differently the next time you face the same gap?")
        self.assertIn("Clear communication and easy to follow", result["latest_question_recap"]["strengths"])

    def test_is_valid_answer_with_all_required_dimensions(self):
        answer = {"scores": {"relevance": 7, "structure": 6, "specificity": 5, "communication": 8, "problem_solving_approach": 6}}
        self.assertTrue(is_valid_answer(answer))

    def test_is_valid_answer_empty_scores(self):
        answer = {"scores": {}}
        self.assertFalse(is_valid_answer(answer))

    def test_is_valid_answer_partial_scores(self):
        answer = {"scores": {"relevance": 7}}
        self.assertFalse(is_valid_answer(answer))

    def test_is_valid_answer_missing_scores(self):
        answer = {"question": "Q1", "answer": "A1"}
        self.assertFalse(is_valid_answer(answer))

    def test_is_valid_answer_none_scores(self):
        answer = {"scores": None}
        self.assertFalse(is_valid_answer(answer))

    def test_is_degraded_evaluation_low_trust(self):
        answer = {"scores": {"relevance": 7, "structure": 6, "specificity": 5, "communication": 8, "problem_solving_approach": 6}, "trust": {"trust_level": "low"}}
        self.assertTrue(is_degraded_evaluation(answer))

    def test_is_degraded_evaluation_medium_trust(self):
        answer = {"scores": {"relevance": 7, "structure": 6, "specificity": 5, "communication": 8, "problem_solving_approach": 6}, "trust": {"trust_level": "medium"}}
        self.assertTrue(is_degraded_evaluation(answer))

    def test_is_degraded_evaluation_low_confidence(self):
        answer = {"scores": {"relevance": 7, "structure": 6, "specificity": 5, "communication": 8, "problem_solving_approach": 6}, "evaluation_confidence": {"overall": 0.3}}
        self.assertTrue(is_degraded_evaluation(answer))

    def test_is_degraded_evaluation_high_trust(self):
        answer = {"scores": {"relevance": 7, "structure": 6, "specificity": 5, "communication": 8, "problem_solving_approach": 6}, "trust": {"trust_level": "high"}}
        self.assertFalse(is_degraded_evaluation(answer))

    def test_build_summary_ignores_empty_scores(self):
        answers = [
            {"scores": {"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7}},
            {"scores": {}},
            {"scores": {"relevance": 8, "structure": 8, "specificity": 8, "communication": 8, "problem_solving_approach": 8}},
        ]
        result = _build_summary_from_raw(answers, 3, 15, [], [], [])
        self.assertEqual(result["questions_completed"], 3)
        self.assertIn("75", result["overall_performance"])
        self.assertIn("2/3", result["evaluation_notice"])

    def test_build_summary_ignores_partial_scores(self):
        answers = [
            {"scores": {"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7}},
            {"scores": {"relevance": 7}},
            {"scores": {"relevance": 8, "structure": 8, "specificity": 8, "communication": 8, "problem_solving_approach": 8}},
        ]
        result = _build_summary_from_raw(answers, 3, 15, [], [], [])
        self.assertEqual(result["questions_completed"], 3)
        self.assertIn("75", result["overall_performance"])
        self.assertIn("2/3", result["evaluation_notice"])

    def test_build_summary_flags_degraded_evaluations(self):
        answers = [
            {"scores": {"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7}, "trust": {"trust_level": "high"}},
            {"scores": {"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7}, "trust": {"trust_level": "low"}},
        ]
        result = _build_summary_from_raw(answers, 2, 15, [], [], [])
        self.assertIn("reduced confidence", result["evaluation_notice"])

    def test_build_summary_uses_singular_wording_for_one_degraded_answer(self):
        answers = [
            {"scores": {"relevance": 7, "structure": 7, "specificity": 7, "communication": 7, "problem_solving_approach": 7}, "trust": {"trust_level": "low"}},
        ]
        result = _build_summary_from_raw(answers, 1, 15, [], [], [])
        self.assertEqual(result["evaluation_notice"], "1 question evaluated with reduced confidence.")

    def test_build_summary_all_invalid(self):
        answers = [
            {"scores": {}},
            {"scores": {"relevance": 7}},
        ]
        result = _build_summary_from_raw(answers, 2, 15, [], [], [])
        self.assertIn("could not be evaluated", result["evaluation_notice"])
        self.assertIn("Needs Improvement", result["overall_performance"])


if __name__ == "__main__":
    unittest.main()
