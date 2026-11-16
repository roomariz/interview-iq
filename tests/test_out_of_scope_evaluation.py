import json
import unittest
from unittest.mock import patch

from interview_app_backend.services.evaluation_service import evaluate_submission
from tests.relevance_regression_fixtures import verdict


class TestOutOfScopeEvaluation(unittest.TestCase):
    def test_out_of_scope_answer_returns_hard_fail_without_full_pipeline(self) -> None:
        question = "Describe a time you improved system performance under constraints."
        answer = "I documented the rollout plan and coordinated weekly status meetings with the team."

        with patch("interview_app_backend.llm.client.call_llm", return_value=json.dumps(verdict(question, answer, "off_topic", "behavioural"))) as mock_call, patch(
            "interview_app_backend.services.evaluation_rules.get_openrouter_client"
        ) as mock_client, patch(
            "interview_app_backend.services.evaluation_service.generate_reference_answer"
        ) as mock_reference, patch(
            "interview_app_backend.services.evaluation_service.calculate_semantic_similarity"
        ) as mock_similarity:
            result = evaluate_submission(question, answer)

        self.assertEqual(result["overall_decision"], "fail")
        self.assertLessEqual(result["scores"]["relevance"], 2)
        self.assertEqual(result["scores"]["structure"], 3)
        self.assertEqual(result["scores"]["specificity"], 1)
        self.assertEqual(result["scores"]["communication"], 6)
        self.assertEqual(result["scores"]["problem_solving_approach"], 2)
        self.assertTrue(result["relevance_gate_applied"])
        self.assertFalse(result["topic_match"])
        self.assertFalse(result["memory_storage_allowed"])
        self.assertEqual(result["validation_warning"]["trust_level"], "low")
        self.assertIn("not relevant to the question", result["validation_warning"]["interpretation"].lower())
        self.assertEqual(result["follow_up"]["type"], "relevance_gate")
        self.assertIn("system performance", result["follow_up"]["question"].lower())
        self.assertIn("not relevant to the question", result["feedback"]["summary"].lower())
        self.assertNotIn("caching", " | ".join(result["feedback"]["improvements"]).lower())
        self.assertEqual(result["reference_answer"], "")
        self.assertEqual(result["semantic_similarity_score"], 0.0)
        mock_reference.assert_not_called()
        mock_similarity.assert_not_called()
        mock_client.assert_called_once()
        self.assertEqual(mock_call.call_count, 1)


if __name__ == "__main__":
    unittest.main()
