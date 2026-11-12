import unittest
import json
from unittest.mock import patch

from interview_app_backend.llm.prompts.question_generation_prompt import build_question_generation_prompt
from interview_app_backend.llm.question_generation_parser import parse_question_generation_response
from interview_app_backend.services.question_service import is_semantically_duplicate
from interview_app_backend.services.question_service import key_terms_overlap
from interview_app_backend.services.question_service import build_question_prompt, get_next_question


def _build_question_generation_payload() -> str:
    return json.dumps(
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
                    "question": "Your API response time increased from 200ms to 800ms in your application. How would you investigate and improve the performance of the React frontend?",
                    "question_type": "jd_based",
                    "scenario_type": "performance",
                    "focus_area": "performance",
                    "source_basis": {"cv_terms_used": ["React"], "jd_terms_used": ["API"], "gap_used": None},
                    "difficulty_level": "Easy",
                    "what_interviewer_is_testing": ["Performance investigation"],
                },
                {
                    "sequence_order": 2,
                    "question": "Based on your React experience, how would you handle a sudden slowdown caused by a changed component tree?",
                    "question_type": "cv_based",
                    "scenario_type": "debugging",
                    "focus_area": "front-end performance",
                    "source_basis": {"cv_terms_used": ["React"], "jd_terms_used": ["frontend"], "gap_used": None},
                    "difficulty_level": "Easy",
                    "what_interviewer_is_testing": ["Applied CV experience"],
                },
                {
                    "sequence_order": 3,
                    "question": "The job description asks for API reliability. How would you investigate and stabilise a slow endpoint after a release?",
                    "question_type": "jd_based",
                    "scenario_type": "performance",
                    "focus_area": "API reliability",
                    "source_basis": {"cv_terms_used": ["React"], "jd_terms_used": ["API"], "gap_used": None},
                    "difficulty_level": "Medium",
                    "what_interviewer_is_testing": ["Role alignment"],
                },
                {
                    "sequence_order": 4,
                    "question": "Tell me about a time you had to collaborate across teams to resolve a production issue. What was your approach?",
                    "question_type": "behavioural",
                    "scenario_type": "behavioural",
                    "focus_area": "collaboration",
                    "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
                    "difficulty_level": "Medium",
                    "what_interviewer_is_testing": ["Ownership and communication"],
                },
                {
                    "sequence_order": 5,
                    "question": "Your application has a performance issue under peak load. How would you design the investigation and weigh the trade-offs before changing the release?",
                    "question_type": "deep_dive",
                    "scenario_type": "scaling",
                    "focus_area": "trade-offs",
                    "source_basis": {"cv_terms_used": ["React"], "jd_terms_used": ["API"], "gap_used": None},
                    "difficulty_level": "Hard",
                    "what_interviewer_is_testing": ["Trade-off reasoning"],
                },
                {
                    "sequence_order": 6,
                    "question": "Based on your React experience, how would you diagnose a production regression without reusing the same fix you applied last time?",
                    "question_type": "cv_based",
                    "scenario_type": "debugging",
                    "focus_area": "regression handling",
                    "source_basis": {"cv_terms_used": ["React"], "jd_terms_used": ["frontend"], "gap_used": None},
                    "difficulty_level": "Medium",
                    "what_interviewer_is_testing": ["Transfer of experience"],
                },
                {
                    "sequence_order": 7,
                    "question": "You have limited exposure to observability. How would you close that gap while still handling a real API performance incident?",
                    "question_type": "gap_targeted",
                    "scenario_type": "scaling",
                    "focus_area": "observability",
                    "source_basis": {"cv_terms_used": ["React"], "jd_terms_used": ["observability"], "gap_used": "observability"},
                    "difficulty_level": "Hard",
                    "what_interviewer_is_testing": ["Gap closure plan"],
                },
            ],
        }
    )


class TestQuestionGeneration(unittest.TestCase):
    def test_build_question_prompt_includes_context(self):
        prompt = build_question_prompt("Backend Engineer", "Medium", "Direct", "Concise", "Python CV")

        self.assertIn("ROLE: Backend Engineer", prompt)
        self.assertIn("DIFFICULTY: Medium", prompt)
        self.assertIn("PERSONA: Direct", prompt)
        self.assertIn("RESPONSE_STYLE: Concise", prompt)
        self.assertIn("CV: Python CV", prompt)
        self.assertIn("JOB_DESCRIPTION:", prompt)
        self.assertIn("GAP_ANALYSIS (for ONE question only):", prompt)
        self.assertIn("Generate 5–10 high-quality, non-repetitive interview questions", prompt)
        self.assertIn('"questions": [', prompt)

    def test_build_question_generation_prompt_includes_structured_fields(self):
        prompt = build_question_generation_prompt(
            role="Backend Engineer",
            difficulty="Medium",
            persona="Direct",
            response_style="Concise",
            temperature=0.7,
            cv_profile="Python CV",
            job_description="PostgreSQL role",
            gap_analysis={"missing_skills": ["aws"], "gap_summary": "Missing: aws"},
        )

        self.assertIn("TEMPERATURE: 0.7", prompt)
        self.assertIn("CV: Python CV", prompt)
        self.assertIn("JOB_DESCRIPTION: PostgreSQL role", prompt)
        self.assertIn("GAP_ANALYSIS (for ONE question only): {\"missing_skills\": [\"aws\"], \"gap_summary\": \"Missing: aws\"}", prompt)
        self.assertIn("Context Handling (MANDATORY)", prompt)
        self.assertIn("SCENARIO A: ROLE ONLY", prompt)
        self.assertIn("SCENARIO B: ROLE + JOB DESCRIPTION", prompt)
        self.assertIn("SCENARIO C: ROLE + JOB DESCRIPTION + CV", prompt)
        self.assertIn("You MUST determine the active scenario (A, B, or C) before generating questions.", prompt)
        self.assertIn("You MUST follow only the rules for that scenario.", prompt)
        self.assertIn("Source Priority (CRITICAL)", prompt)
        self.assertIn("Anti-Hallucination Rules", prompt)
        self.assertIn("Before finalising:", prompt)
        self.assertIn("Check that each question aligns with a different required dimension.", prompt)
        self.assertIn("Check that no unsupported technologies are introduced.", prompt)
        self.assertIn("Check that grounding follows the active scenario rules.", prompt)
        self.assertIn("If any check fails, revise before output.", prompt)
        self.assertIn('"meta": {', prompt)
        self.assertIn('"sequence_order": 1-10', prompt)
        self.assertIn("Output (JSON only):", prompt)
        self.assertIn('"question_type": "cv_based | jd_based | behavioural | deep_dive | gap_targeted"', prompt)
        self.assertIn('"scenario_type": "debugging | performance | system_design | behavioural | scaling"', prompt)
        self.assertIn("For a 5-question set, cover five different capability dimensions", prompt)
        self.assertIn("Do NOT repeat the same verb pattern or frame", prompt)
        self.assertIn("Do NOT write coaching or meta questions", prompt)

    def test_get_next_question_with_valid_scenario_passes_validation(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            client = object()
            mock_client_factory.return_value = client
            mock_call_llm.return_value = _build_question_generation_payload()
            result = get_next_question("Full Stack Engineer", "Easy", "Friendly", "Concise", "React experience")

            self.assertIn("your application", result.lower())
            self.assertIn("react", result.lower())
            mock_client_factory.assert_called_once_with()
            mock_call_llm.assert_called_once()
            prompt, passed_client = mock_call_llm.call_args.args
            self.assertIn("ROLE: Full Stack Engineer", prompt)
            self.assertIs(passed_client, client)
            self.assertEqual(mock_call_llm.call_args.kwargs["task"], "question_generation.cv_based")

    def test_parse_question_generation_response_requires_strict_structure(self):
        parsed = parse_question_generation_response(_build_question_generation_payload())

        self.assertEqual(len(parsed), 7)
        self.assertEqual([item["sequence_order"] for item in parsed], [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual([item["question_type"] for item in parsed], ["jd_based", "cv_based", "jd_based", "behavioural", "deep_dive", "cv_based", "gap_targeted"])

    def test_semantic_duplicate_guard_detects_paraphrases(self):
        first = "How would you improve API performance under load?"
        second = "How would you improve performance of the API under load?"
        third = "Tell me about a time you handled conflict in a team."

        self.assertTrue(is_semantically_duplicate(first, second))
        self.assertFalse(is_semantically_duplicate(first, third))
        self.assertGreater(key_terms_overlap(first, second), 0.5)

    def test_get_next_question_falls_back_without_openrouter_key(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client", side_effect=ValueError("OPENROUTER_API_KEY is not set")), patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            result = get_next_question("Backend Engineer", "Medium", "Direct", "Concise", "Python CV")

        self.assertIn("python", result.lower())
        self.assertIn("api", result.lower())
        self.assertIn("production issue", result.lower())
        mock_call_llm.assert_not_called()

    def test_get_next_question_falls_back_when_client_creation_fails(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client", side_effect=TypeError("OpenAI() takes no arguments")), patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            result = get_next_question("Backend Engineer", "Medium", "Direct", "Concise", "Python CV")

        self.assertIn("python", result.lower())
        self.assertIn("api", result.lower())
        mock_call_llm.assert_not_called()

    def test_get_next_question_personalises_from_spring_cv_keyword(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client", side_effect=ValueError("OPENROUTER_API_KEY is not set")), patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            result = get_next_question("Backend Engineer", "Medium", "Direct", "Concise", "Spring Boot")

        self.assertIn("spring", result.lower())
        self.assertIn("api", result.lower())
        mock_call_llm.assert_not_called()

    def test_get_next_question_uses_previous_questions_to_change_template(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client", side_effect=ValueError("OPENROUTER_API_KEY is not set")), patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            first = get_next_question(
                "Backend Engineer",
                "Medium",
                "Direct",
                "Concise",
                "Spring Boot",
                previous_questions=[],
            )
            second = get_next_question(
                "Backend Engineer",
                "Medium",
                "Direct",
                "Concise",
                "Spring Boot",
                previous_questions=[first],
            )

        self.assertNotEqual(first, second)
        self.assertNotEqual(first.split("?")[0], second.split("?")[0])
        self.assertIn("spring", first.lower())
        self.assertIn("spring", second.lower())
        mock_call_llm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
