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
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            client = object()
            mock_client_factory.return_value = client
            valid_question = "Your Python API response time increased from 200ms to 800ms in your application. How would you investigate and improve the performance?"
            mock_call_llm.return_value = json.dumps(
                {
                    "meta": {
                        "total_questions": 7,
                        "distribution": {
                            "cv_based": 2,
                            "jd_based": 2,
                            "behavioural": 1,
                            "deep_dive": 1,
                            "gap_targeted": 1,
                        },
                    },
                    "questions": [
                        {
                            "sequence_order": 1,
                            "question": valid_question,
                            "question_type": "cv_based",
                            "focus_area": "performance",
                            "source_basis": {"cv_terms_used": ["Python"], "jd_terms_used": ["API"], "gap_used": None},
                            "difficulty_level": "Medium",
                            "what_interviewer_is_testing": ["Performance investigation"],
                        },
                        {
                            "sequence_order": 2,
                            "question": "Based on your Python experience, how would you handle a sudden regression in a service you already knew well?",
                            "question_type": "cv_based",
                            "focus_area": "experience",
                            "source_basis": {"cv_terms_used": ["Python"], "jd_terms_used": ["service"], "gap_used": None},
                            "difficulty_level": "Medium",
                            "what_interviewer_is_testing": ["Applied experience"],
                        },
                        {
                            "sequence_order": 3,
                            "question": "The job description emphasises API reliability. How would you stabilise an endpoint that now fails under load?",
                            "question_type": "jd_based",
                            "focus_area": "reliability",
                            "source_basis": {"cv_terms_used": ["Python"], "jd_terms_used": ["API"], "gap_used": None},
                            "difficulty_level": "Medium",
                            "what_interviewer_is_testing": ["Role alignment"],
                        },
                        {
                            "sequence_order": 4,
                            "question": "Tell me about a time you had to work with a product manager to resolve a production issue. What was your approach?",
                            "question_type": "behavioural",
                            "focus_area": "collaboration",
                            "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
                            "difficulty_level": "Medium",
                            "what_interviewer_is_testing": ["Communication"],
                        },
                        {
                            "sequence_order": 5,
                            "question": "Your service has a deep performance problem under peak load. How would you reason through the trade-offs before changing architecture?",
                            "question_type": "deep_dive",
                            "focus_area": "trade-offs",
                            "source_basis": {"cv_terms_used": ["Python"], "jd_terms_used": ["API"], "gap_used": None},
                            "difficulty_level": "Hard",
                            "what_interviewer_is_testing": ["Trade-off reasoning"],
                        },
                        {
                            "sequence_order": 6,
                            "question": "The job description asks for service reliability. How would you investigate another production issue without reusing the exact same fix?",
                            "question_type": "jd_based",
                            "focus_area": "investigation",
                            "source_basis": {"cv_terms_used": ["Python"], "jd_terms_used": ["service"], "gap_used": None},
                            "difficulty_level": "Medium",
                            "what_interviewer_is_testing": ["Varied scenario"],
                        },
                        {
                            "sequence_order": 7,
                            "question": "You have a gap in observability tooling. How would you close it while still handling a live API incident?",
                            "question_type": "gap_targeted",
                            "focus_area": "observability",
                            "source_basis": {"cv_terms_used": ["Python"], "jd_terms_used": ["observability"], "gap_used": "observability"},
                            "difficulty_level": "Medium",
                            "what_interviewer_is_testing": ["Gap closure plan"],
                        },
                    ]
                }
            )

            result = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                cv_context="Python",
                question_index=3,
                jd_context="",
                asked_topics=[],
                focus="",
            )

        self.assertEqual(result, valid_question)
        prompt, passed_client = mock_call_llm.call_args.args
        self.assertIn("ROLE: Backend Engineer", prompt)
        self.assertIn("CV: Python", prompt)
        self.assertIs(passed_client, client)

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
