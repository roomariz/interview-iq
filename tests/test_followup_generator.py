import unittest

from interview_app_backend.services.followup_generator import (
    generate_adaptive_followup,
    get_followup_context_from_gaps,
    should_ask_followup,
)


class TestAdaptiveFollowup(unittest.TestCase):

    def test_generate_adaptive_followup_includes_previous_q_and_a(self):
        result = generate_adaptive_followup(
            "What is Python?",
            "Python is a programming language",
            "Skills: Python",
            "Required: Python",
        )
        self.assertIn("What is Python?", result)
        self.assertIn("Python is a programming language", result)

    def test_generate_adaptive_followup_uses_gap_context(self):
        result = generate_adaptive_followup(
            "What is Python?",
            "Python is a programming language",
            "Skills: Python",
            "Required: Python, Java, AWS",
        )
        self.assertIn("gap", result.lower())

    def test_generate_adaptive_followup_uses_weakness_for_low_score(self):
        result = generate_adaptive_followup(
            "What is Python?",
            "A programming language",
            "Skills: Python",
            "Required: Python",
            feedback_score=3,
        )
        self.assertIn("weakness", result.lower())

    def test_get_followup_context_from_gaps_returns_skills(self):
        gap_analysis = {"missing_skills": ["java", "aws", "docker"]}
        result = get_followup_context_from_gaps(gap_analysis)
        self.assertIn("java", result)

    def test_get_followup_context_from_gaps_empty_when_no_gaps(self):
        gap_analysis = {"missing_skills": []}
        result = get_followup_context_from_gaps(gap_analysis)
        self.assertEqual(result, "")

    def test_should_ask_followup_true_for_low_score(self):
        result = should_ask_followup(answer_quality_score=3, has_gaps=False)
        self.assertTrue(result)

    def test_should_ask_followup_true_for_gaps(self):
        result = should_ask_followup(answer_quality_score=None, has_gaps=True)
        self.assertTrue(result)

    def test_should_ask_followup_false_for_good_answer_no_gaps(self):
        result = should_ask_followup(answer_quality_score=7, has_gaps=False)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()