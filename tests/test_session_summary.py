import unittest

from interview_app_backend.services.report_service import summarise_performance


class TestSessionSummary(unittest.TestCase):
    def test_summarise_performance_returns_mockup_aligned_summary(self):
        session_data = {
            "scores": [
                {"technical_accuracy": 8, "clarity": 7, "structure": 6, "relevance": 7},
                {"technical_accuracy": 7, "clarity": 8, "structure": 5, "relevance": 8},
            ],
            "completed_questions": 5,
            "duration_minutes": 18,
            "strengths": ["Clear communication of ideas"],
            "improvement_areas": ["Add specific metrics"],
        }

        result = summarise_performance(session_data)

        self.assertEqual(result["title"], "Interview Session Complete!")
        self.assertEqual(result["overall_performance"], "70% (Good)")
        self.assertEqual(result["questions_completed"], 5)
        self.assertEqual(result["session_duration"], "18 minutes")
        self.assertEqual(result["average_scores"], {"technical_accuracy": 7.5, "clarity": 7.5, "structure": 5.5, "relevance": 7.5})
        self.assertIn("Practice STAR framework (Situation, Task, Action, Result)", result["recommended_next_steps"])


if __name__ == "__main__":
    unittest.main()
