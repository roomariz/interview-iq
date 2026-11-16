import unittest
import json
from unittest.mock import patch

from interview_app_backend.services.question_service import build_role_based_question_prompt, get_role_based_question


class TestRoleBasedQuestionGeneration(unittest.TestCase):
    def test_build_role_based_question_prompt_mentions_role(self):
        prompt = build_role_based_question_prompt("Data Engineer", "Hard", "Strict", "Concise", "ETL experience")

        self.assertIn("Data Engineer", prompt)
        self.assertIn("DIFFICULTY: Hard", prompt)
        self.assertIn("PERSONA: Strict", prompt)
        self.assertIn("CV: ETL experience", prompt)
        self.assertIn("JOB_DESCRIPTION:", prompt)
        self.assertIn("GAP_ANALYSIS (for ONE question only):", prompt)

    def test_get_role_based_question_calls_llm_with_valid_scenario(self):
        question = "Your data pipeline performs ETL slowly after a release. How would you investigate and optimise its performance?"
        with patch("interview_app_backend.services.question_service.get_openrouter_client", return_value=object()), patch(
            "interview_app_backend.services.question_service.call_llm",
            return_value=json.dumps([{"question": question, "question_type": "cv_based", "focus_area": "performance"}]),
        ) as call:
            result = get_role_based_question("Data Engineer", "Hard", "Strict", "Concise", "ETL experience")
        self.assertEqual(result, question)
        self.assertEqual(call.call_count, 1)

    def test_get_role_based_question_rejects_invalid_fallback_when_llm_is_generic(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client", return_value=object()), patch(
            "interview_app_backend.services.question_service.call_llm", return_value=json.dumps({"questions": []})
        ), patch("interview_app_backend.services.question_service.generate_safe_fallback",
                 return_value="How would you apply your experience as a Data Engineer?"), self.assertRaisesRegex(RuntimeError, "Fallback generation failed validation"):
            get_role_based_question("Data Engineer", "Hard", "Strict", "Concise", "ETL experience")


if __name__ == "__main__":
    unittest.main()
