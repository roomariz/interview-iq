import unittest
import json
from unittest.mock import patch

from interview_app_backend.services.question_service import get_next_question_for_session


class TestQuestionSequenceProgression(unittest.TestCase):
    def test_question_index_one_falls_back_on_invalid_llm(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            client = object()
            mock_client_factory.return_value = client
            mock_call_llm.return_value = "How would you apply your experience?"

            result = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python",
                question_index=1,
                jd_context="",
                asked_topics=[],
                focus="",
            )

            self.assertNotEqual(result, "How would you apply your experience?")
            self.assertTrue(len(result.strip()) > 20, "Fallback should be a valid question")
            self.assertTrue(result.strip().endswith("?"), "Fallback should end with question mark")
            self.assertIn("backend engineer", result.lower())
            self.assertIn("python", result.lower())
            prompt, passed_client = mock_call_llm.call_args.args
            self.assertIn("CV: Python", prompt)
            self.assertIn("GAP_ANALYSIS (for ONE question only):", prompt)

    def test_invalid_llm_output_triggers_fallback(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            mock_call_llm.return_value = "How would you apply your experience?"

            result = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python APIs",
                question_index=1,
                jd_context="Fast APIs",
                asked_topics=[],
                focus="",
            )

        self.assertNotEqual(result, "How would you apply your experience?")
        self.assertTrue(len(result.strip()) > 20, "Fallback should be a valid question")
        self.assertTrue(result.strip().endswith("?"), "Fallback should end with question mark")
        self.assertIn("backend engineer", result.lower())
        self.assertIn("python", result.lower())
        self.assertTrue(any(keyword in result.lower() for keyword in ("api", "fast", "performance")))

    def test_non_relevant_llm_output_triggers_fallback_after_retry(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            mock_call_llm.side_effect = [
                "How would you apply your experience?",
                "How would you apply your experience?",
                "How would you apply your experience?",
            ]

            result = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python APIs",
                question_index=1,
                jd_context="Fast APIs",
                asked_topics=[],
                focus="",
            )

        self.assertNotEqual(result, "How would you apply your experience?")
        self.assertTrue(len(result.strip()) > 20, "Fallback should be a valid question")
        self.assertTrue(result.strip().endswith("?"), "Fallback should end with question mark")
        self.assertIn("backend engineer", result.lower())
        self.assertIn("python", result.lower())
        self.assertGreaterEqual(mock_call_llm.call_count, 1)

    def test_duplicate_topic_rejects_and_falls_back(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            mock_call_llm.side_effect = [
                "How would you apply your experience?",
                "How would you apply your experience?",
                "How would you apply your experience?",
            ]

            result = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python APIs",
                question_index=1,
                jd_context="API performance",
                asked_topics=[],
                focus="",
            )

        self.assertNotEqual(result, "How would you apply your experience?")
        self.assertTrue(len(result.strip()) > 20, "Fallback should be a valid question")
        self.assertTrue(result.strip().endswith("?"), "Fallback should end with question mark")
        self.assertIn("backend engineer", result.lower())
        self.assertIn("python", result.lower())

    def test_higher_question_index_uses_valid_llm_response(self):
        valid_question = "Your Python API response time increased from 200ms to 800ms in your application. How would you investigate and improve the performance?"
        with patch("interview_app_backend.services.question_service.get_openrouter_client", return_value=object()), patch(
            "interview_app_backend.services.question_service.call_llm",
            return_value=json.dumps([{"question": valid_question, "question_type": "cv_based", "focus_area": "performance"}]),
        ) as call:
            result = get_next_question_for_session("Backend Engineer", "Medium", "Direct", "Concise", focus="", cv_context="Python", question_index=3)
        self.assertEqual(result, valid_question)
        self.assertEqual(call.call_count, 1)

    def test_invalid_question_index_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "question_index must be at least 1"):
            get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python",
                question_index=0,
                jd_context="",
                asked_topics=[],
                focus="",
            )


if __name__ == "__main__":
    unittest.main()
