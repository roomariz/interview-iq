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
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            client = object()
            mock_client_factory.return_value = client
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
                            "question": "Your data pipeline is taking longer than expected to process recent data. How would you investigate and optimise the performance?",
                            "question_type": "jd_based",
                            "focus_area": "data pipeline performance",
                            "source_basis": {"cv_terms_used": ["ETL"], "jd_terms_used": ["pipeline"], "gap_used": None},
                            "difficulty_level": "Hard",
                            "what_interviewer_is_testing": ["Performance investigation"],
                        },
                        {
                            "sequence_order": 2,
                            "question": "Based on your ETL experience, how would you respond when a familiar pipeline starts running slowly after a deployment?",
                            "question_type": "cv_based",
                            "focus_area": "ETL experience",
                            "source_basis": {"cv_terms_used": ["ETL"], "jd_terms_used": ["pipeline"], "gap_used": None},
                            "difficulty_level": "Hard",
                            "what_interviewer_is_testing": ["Applied experience"],
                        },
                        {
                            "sequence_order": 3,
                            "question": "The job description emphasises pipeline reliability. How would you stabilise a job that now fails intermittently?",
                            "question_type": "jd_based",
                            "focus_area": "pipeline reliability",
                            "source_basis": {"cv_terms_used": ["ETL"], "jd_terms_used": ["pipeline"], "gap_used": None},
                            "difficulty_level": "Hard",
                            "what_interviewer_is_testing": ["Role alignment"],
                        },
                        {
                            "sequence_order": 4,
                            "question": "Tell me about a time you had to coordinate with another team to resolve a delivery problem. What did you do?",
                            "question_type": "behavioural",
                            "focus_area": "coordination",
                            "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
                            "difficulty_level": "Medium",
                            "what_interviewer_is_testing": ["Communication"],
                        },
                        {
                            "sequence_order": 5,
                            "question": "Your data platform has a recurring performance issue. How would you reason through the trade-offs before choosing a fix?",
                            "question_type": "deep_dive",
                            "focus_area": "trade-offs",
                            "source_basis": {"cv_terms_used": ["ETL"], "jd_terms_used": ["pipeline"], "gap_used": None},
                            "difficulty_level": "Hard",
                            "what_interviewer_is_testing": ["Deep reasoning"],
                        },
                        {
                            "sequence_order": 6,
                            "question": "Based on your ETL experience, how would you tackle a fresh regression without repeating the same diagnosis approach twice?",
                            "question_type": "cv_based",
                            "focus_area": "regression handling",
                            "source_basis": {"cv_terms_used": ["ETL"], "jd_terms_used": ["pipeline"], "gap_used": None},
                            "difficulty_level": "Hard",
                            "what_interviewer_is_testing": ["Transfer of experience"],
                        },
                        {
                            "sequence_order": 7,
                            "question": "You have only limited experience with observability. How would you close that gap while handling a live pipeline issue?",
                            "question_type": "gap_targeted",
                            "focus_area": "observability",
                            "source_basis": {"cv_terms_used": ["ETL"], "jd_terms_used": ["observability"], "gap_used": "observability"},
                            "difficulty_level": "Hard",
                            "what_interviewer_is_testing": ["Gap closure plan"],
                        },
                    ]
                }
            )

            result = get_role_based_question("Data Engineer", "Hard", "Strict", "Concise", "ETL experience")

            self.assertEqual(result, "Your data pipeline is taking longer than expected to process recent data. How would you investigate and optimise the performance?")
            prompt, passed_client = mock_call_llm.call_args.args
            self.assertIn("Data Engineer", prompt)
            self.assertIs(passed_client, client)

    def test_get_role_based_question_falls_back_to_scenario_when_llm_is_generic(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            mock_call_llm.return_value = json.dumps({"questions": []})

            result = get_role_based_question("Data Engineer", "Hard", "Strict", "Concise", "ETL experience")

        self.assertTrue(result.endswith("?"))
        self.assertIn("data", result.lower())
        self.assertTrue(
            any(keyword in result.lower() for keyword in ("etl", "pipeline", "experience", "project")),
            "Fallback should stay scenario-based and reflect the supplied context",
        )


if __name__ == "__main__":
    unittest.main()
