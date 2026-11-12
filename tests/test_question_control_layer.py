import unittest
from unittest.mock import patch

from interview_app_backend.llm.prompts.question_generation_prompt import build_question_generation_prompt
from interview_app_backend.services.question_generation_job import VALID_TRANSITIONS, update_status
from interview_app_backend.services.question_sequence import QUESTION_SEQUENCE
from interview_app_backend.services.question_sequence import build_question_prompt_context
from interview_app_backend.services.question_service import get_next_question_for_session
from interview_app_backend.services.question_service import same_question_pattern


class TestQuestionControlLayer(unittest.TestCase):
    def test_prompt_context_exposes_internal_focus_area(self):
        plan = build_question_prompt_context(
            role="Backend Engineer",
            difficulty="Medium",
            question_index=3,
            cv_context="Python APIs",
            jd_context="Fast APIs",
            previous_questions=["How would you handle a slow API?"],
            asked_topics=["API"],
            focus="",
            question_type="auto",
        )

        self.assertIn("focus_area", plan)
        self.assertIn("previous_questions", plan)
        self.assertTrue(plan["previous_questions"])

    def test_focus_area_sequence_matches_controlled_order(self):
        focus_area_sequence = [item["focus_area"] for item in QUESTION_SEQUENCE]
        self.assertEqual(focus_area_sequence, ["core", "experience", "jd_alignment", "gap", "deep_dive"])

    def test_same_question_pattern_detects_repeated_opening_style(self):
        first = "Describe a time you improved a slow API."
        second = "Describe a situation where you improved a slow API."
        third = "How would you improve a slow API?"
        self.assertTrue(same_question_pattern(first, second))
        self.assertFalse(same_question_pattern(first, third))

    def test_question_job_status_transitions_are_enforced(self):
        self.assertEqual(VALID_TRANSITIONS["pending"], ["running"])
        self.assertEqual(update_status("pending", "running"), "running")
        with self.assertRaises(AssertionError):
            update_status("running", "running")

    def test_prompt_includes_previous_questions_block(self):
        prompt = build_question_generation_prompt(
            role="Backend Engineer",
            difficulty="Medium",
            persona="Direct",
            response_style="Concise",
            temperature=0.5,
            cv_profile="Python APIs",
            job_description="Fast APIs",
            gap_analysis={"missing_skills": ["aws"]},
        )

        self.assertIn("TEMPERATURE: 0.5", prompt)
        self.assertIn("CV: Python APIs", prompt)
        self.assertIn("JOB_DESCRIPTION: Fast APIs", prompt)
        self.assertIn("GAP_ANALYSIS (for ONE question only): {\"missing_skills\": [\"aws\"]}", prompt)
        self.assertIn('"meta": {', prompt)
        self.assertIn('"sequence_order": 1-10', prompt)
        self.assertIn("Output (JSON only):", prompt)
        self.assertIn('"scenario_type": "debugging | performance | system_design | behavioural | scaling"', prompt)

    def test_cv_context_influences_fallback(self):
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
                focus="",
                cv_context="Python APIs",
                question_index=1,
                jd_context="",
                asked_topics=[],
                previous_questions=[],
            )

        self.assertIn("backend engineer", result.lower())
        self.assertIn("python", result.lower())
        self.assertTrue(result.endswith("?"))

    def test_variation_uses_previous_questions(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            mock_call_llm.side_effect = [
                "How would you apply your experience?",
                "How would you apply your experience?",
            ]

            first = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                focus="",
                cv_context="Python",
                question_index=1,
                jd_context="",
                asked_topics=[],
                previous_questions=[],
            )
            second = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                focus="",
                cv_context="Python",
                question_index=2,
                jd_context="",
                asked_topics=[],
                previous_questions=[first],
            )

        self.assertNotEqual(first, second)
        self.assertGreaterEqual(mock_call_llm.call_count, 2)
        self.assertIn("GAP_ANALYSIS (for ONE question only):", mock_call_llm.call_args.args[0])

    def test_fallback_parity_remains_scenario_based_without_client(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client", side_effect=ValueError("no key")), patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            result = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                focus="",
                cv_context="Python",
                question_index=1,
                jd_context="API performance",
                asked_topics=[],
                previous_questions=[],
            )

        self.assertIn("backend engineer", result.lower())
        self.assertTrue(any(keyword in result.lower() for keyword in ("python", "api", "performance")))
        self.assertTrue(result.endswith("?"))
        mock_call_llm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
