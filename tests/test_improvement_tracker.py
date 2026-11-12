import unittest
import os
import json
from unittest.mock import patch, mock_open

from interview_app_backend.services.improvement_tracker import ImprovementTracker


class TestImprovementTracker(unittest.TestCase):

    def setUp(self):
        self.test_file = "test_history.json"
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_record_session_stores_data(self):
        tracker = ImprovementTracker(self.test_file)
        session_data = {
            "session_id": "test-1",
            "scores": [{"relevance": 7, "structure": 8}, {"relevance": 8, "structure": 9}],
            "questions_completed": 2,
            "role": "Backend Engineer",
            "difficulty": "Medium",
        }

        tracker.record_session(session_data)

        history = tracker._load_history()
        self.assertIn("test-1", history)

    def test_record_session_calculates_average(self):
        tracker = ImprovementTracker(self.test_file)
        session_data = {
            "session_id": "test-2",
            "scores": [{"score": 6}, {"score": 8}],
            "questions_completed": 2,
        }

        tracker.record_session(session_data)

        history = tracker._load_history()
        self.assertEqual(history["test-2"]["average_score"], 7.0)

    def test_get_trend_returns_session_list(self):
        tracker = ImprovementTracker(self.test_file)
        tracker.record_session({"session_id": "s1", "scores": [{"score": 6}], "questions_completed": 1})
        tracker.record_session({"session_id": "s2", "scores": [{"score": 8}], "questions_completed": 1})

        trend = tracker.get_trend()

        self.assertEqual(len(trend), 2)

    def test_calculate_improvement_returns_insufficient_data_for_one_session(self):
        tracker = ImprovementTracker(self.test_file)
        tracker.record_session({"session_id": "s1", "scores": [{"score": 7}], "questions_completed": 1})

        improvement = tracker.calculate_improvement()

        self.assertEqual(improvement["trend"], "insufficient_data")
        self.assertEqual(improvement["sessions_tracked"], 1)

    def test_calculate_improvement_detects_improvement(self):
        tracker = ImprovementTracker(self.test_file)
        tracker.record_session({"session_id": "s1", "scores": [{"score": 6}], "questions_completed": 1})
        tracker.record_session({"session_id": "s2", "scores": [{"score": 9}], "questions_completed": 1})

        improvement = tracker.calculate_improvement()

        self.assertEqual(improvement["trend"], "improving")
        self.assertGreater(improvement["overall_change"], 0)

    def test_get_trend_with_dimension_filter(self):
        tracker = ImprovementTracker(self.test_file)
        tracker.record_session({"session_id": "s1", "scores": [{"relevance": 6, "structure": 8}], "questions_completed": 1})
        tracker.record_session({"session_id": "s2", "scores": [{"relevance": 8, "structure": 9}], "questions_completed": 1})

        trend = tracker.get_trend("relevance")

        self.assertGreater(len(trend), 0)

    def test_get_best_session_returns_highest_score(self):
        tracker = ImprovementTracker(self.test_file)
        tracker.record_session({"session_id": "s1", "scores": [{"score": 5}], "questions_completed": 1})
        tracker.record_session({"session_id": "s2", "scores": [{"score": 9}], "questions_completed": 1})

        best = tracker.get_best_session()

        self.assertEqual(best["session_id"], "s2")

    def test_clear_history_removes_all_data(self):
        tracker = ImprovementTracker(self.test_file)
        tracker.record_session({"session_id": "s1", "scores": [{"score": 7}], "questions_completed": 1})

        tracker.clear_history()

        history = tracker._load_history()
        self.assertEqual(history, {})


if __name__ == "__main__":
    unittest.main()