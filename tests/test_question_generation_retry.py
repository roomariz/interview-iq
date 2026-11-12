import json
import unittest
from unittest.mock import patch

from interview_app_backend.services.question_service import DuplicateQuestionError
from interview_app_backend.services.question_service import deduplicate_questions
from interview_app_backend.services.question_service import get_next_question_for_session
from interview_app_backend.services.question_service import _validate_question_bundle


class TestQuestionGenerationRetry(unittest.TestCase):
    def test_deduplicate_questions_enforces_scenario_type_caps(self):
        questions = [
            {"question": f"Question {index}?", "question_type": "cv_based", "scenario_type": "debugging"}
            for index in range(1, 6)
        ]

        with self.assertRaises(DuplicateQuestionError):
            deduplicate_questions(questions)

    def test_multi_question_generation_retries_then_falls_back_on_collapse(self):
        payload = json.dumps(
            {
                "meta": {
                    "total_questions": 5,
                    "distribution": {
                        "cv_based": 2,
                        "jd_based": 2,
                        "behavioural": 1,
                        "deep_dive": 0,
                        "gap_targeted": 0,
                    },
                },
                "questions": [
                    {
                        "sequence_order": index,
                        "question": f"How would you improve API performance in scenario {index}?",
                        "question_type": "cv_based",
                        "scenario_type": "debugging",
                        "focus_area": "performance",
                        "source_basis": {"cv_terms_used": ["API"], "jd_terms_used": ["performance"], "gap_used": None},
                        "difficulty_level": "Medium",
                        "what_interviewer_is_testing": ["Performance"],
                    }
                    for index in range(1, 6)
                ],
            }
        )

        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            mock_call_llm.side_effect = [payload, payload, payload]

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
                question_list_count=5,
                return_meta=True,
            )

        self.assertEqual(mock_call_llm.call_count, 3)
        self.assertEqual(len(result["questions"]), 5)
        self.assertEqual(len({item["question"] for item in result["questions"]}), 5)
        self.assertTrue(all("scenario_type" in item for item in result["questions"]))

    def test_hallucinated_tech_is_rejected_by_output_validation(self):
        payload = json.dumps(
            {
                "meta": {
                    "total_questions": 5,
                    "distribution": {
                        "cv_based": 2,
                        "jd_based": 2,
                        "behavioural": 1,
                        "deep_dive": 0,
                        "gap_targeted": 0,
                    },
                },
                "questions": [
                    {
                        "sequence_order": index,
                        "question": f"How would you optimise Redis caching in scenario {index}?",
                        "question_type": "jd_based",
                        "scenario_type": "performance",
                        "focus_area": "performance",
                        "source_basis": {"cv_terms_used": ["Python"], "jd_terms_used": ["API"], "gap_used": None},
                        "difficulty_level": "Medium",
                        "what_interviewer_is_testing": ["Performance"],
                    }
                    for index in range(1, 6)
                ],
            }
        )

        with patch("interview_app_backend.services.question_service.get_openrouter_client") as mock_client_factory, patch(
            "interview_app_backend.services.question_service.call_llm"
        ) as mock_call_llm:
            mock_client_factory.return_value = object()
            mock_call_llm.side_effect = [payload, payload, payload]

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
                question_list_count=5,
                return_meta=True,
            )

        self.assertEqual(mock_call_llm.call_count, 3)
        self.assertTrue(all("redis" not in item["question"].lower() for item in result["questions"]))

    def test_forced_llm_failure_uses_validated_fallback_bundle(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client", return_value=object()), patch(
            "interview_app_backend.services.question_service.call_llm",
            side_effect=RuntimeError("forced failure"),
        ) as mock_call_llm:
            result = get_next_question_for_session(
                role="Generalist",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                focus="General",
                cv_context="",
                question_index=1,
                jd_context="",
                asked_topics=[],
                question_list_count=5,
                return_meta=True,
            )

        self.assertEqual(mock_call_llm.call_count, 3)
        self.assertEqual(len(result["questions"]), 5)
        self.assertTrue(all(item["question"].strip() for item in result["questions"]))
        scenario_types = [item["scenario_type"] for item in result["questions"]]
        dimensions = [item["dimension"] for item in result["questions"]]
        self.assertEqual(set(scenario_types), {"debugging", "performance", "system_design", "behavioural", "scaling"})
        self.assertEqual(set(dimensions), {"debugging / regression recovery", "performance / trade-off decision-making", "system design / scalability", "behavioural ownership / ambiguity handling", "stakeholder communication / coordination"})
        valid, reason = _validate_question_bundle(result["questions"], role="Generalist", cv_context="", jd_context="")
        self.assertTrue(valid, reason)

    def test_duplicate_classification_is_rejected(self):
        questions = [
            {
                "question": "How would you debug a regression in your React work?",
                "question_type": "cv_based",
                "scenario_type": "debugging",
                "dimension": "debugging / regression recovery",
                "focus_area": "debugging",
                "source_basis": {"cv_terms_used": ["React"], "jd_terms_used": [], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Debugging"],
            },
            {
                "question": "How would you investigate another regression in your React work?",
                "question_type": "cv_based",
                "scenario_type": "debugging",
                "dimension": "debugging / regression recovery",
                "focus_area": "debugging",
                "source_basis": {"cv_terms_used": ["React"], "jd_terms_used": [], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Debugging"],
            },
            {
                "question": "How would you improve a slow API in the JD?",
                "question_type": "jd_based",
                "scenario_type": "performance",
                "dimension": "performance / trade-off decision-making",
                "focus_area": "performance",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": ["API"], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Performance"],
            },
            {
                "question": "How would you explain a production issue to stakeholders?",
                "question_type": "behavioural",
                "scenario_type": "behavioural",
                "dimension": "behavioural ownership / ambiguity handling",
                "focus_area": "communication",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": ["stakeholders"], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Communication"],
            },
            {
                "question": "How would you design a safer rollout for an existing service?",
                "question_type": "deep_dive",
                "scenario_type": "system_design",
                "dimension": "system design / scalability",
                "focus_area": "design",
                "source_basis": {"cv_terms_used": ["React"], "jd_terms_used": ["service"], "gap_used": None},
                "difficulty_level": "Hard",
                "what_interviewer_is_testing": ["Design"],
            },
        ]

        valid, reason = _validate_question_bundle(questions, role="Backend Engineer", cv_context="React", jd_context="API stakeholders")

        self.assertFalse(valid, reason)


if __name__ == "__main__":
    unittest.main()
