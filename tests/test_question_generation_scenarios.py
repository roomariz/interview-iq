import unittest
from unittest.mock import patch

from interview_app_backend.services.question_service import get_next_question_for_session
from interview_app_backend.services.question_service import _validate_question_bundle


class TestQuestionGenerationScenarios(unittest.TestCase):
    def test_role_only_bundle_rejects_tech_and_source_terms(self):
        questions = [
            {
                "question": "How would you investigate a production issue in the team workflow?",
                "question_type": "cv_based",
                "scenario_type": "debugging",
                "dimension": "debugging / regression recovery",
                "focus_area": "debugging",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Debugging"],
            },
            {
                "question": "How would you coordinate a delivery trade-off with the team?",
                "question_type": "jd_based",
                "scenario_type": "performance",
                "dimension": "performance / trade-off decision-making",
                "focus_area": "performance",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Trade-offs"],
            },
            {
                "question": "How would you handle ambiguity in a stakeholder conversation?",
                "question_type": "behavioural",
                "scenario_type": "behavioural",
                "dimension": "behavioural ownership / ambiguity handling",
                "focus_area": "communication",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Communication"],
            },
            {
                "question": "How would you coordinate the team when a priority changes unexpectedly?",
                "question_type": "deep_dive",
                "scenario_type": "scaling",
                "dimension": "stakeholder communication / coordination",
                "focus_area": "scaling",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
                "difficulty_level": "Hard",
                "what_interviewer_is_testing": ["Scalability"],
            },
            {
                "question": "How would you take ownership of an unclear issue and close it down?",
                "question_type": "gap_targeted",
                "scenario_type": "system_design",
                "dimension": "system design / scalability",
                "focus_area": "ownership",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
                "difficulty_level": "Hard",
                "what_interviewer_is_testing": ["Ownership"],
            },
        ]

        valid, reason = _validate_question_bundle(questions, role="Generalist", cv_context="", jd_context="")

        self.assertTrue(valid, reason)

    def test_jd_only_bundle_requires_jd_grounding(self):
        questions = [
            {
                "question": "How would you investigate a slow API query from the job description?",
                "question_type": "jd_based",
                "scenario_type": "performance",
                "dimension": "performance / trade-off decision-making",
                "focus_area": "performance",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": ["API"], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Performance"],
            },
            {
                "question": "How would you coordinate with stakeholders when a release slips?",
                "question_type": "behavioural",
                "scenario_type": "behavioural",
                "dimension": "behavioural ownership / ambiguity handling",
                "focus_area": "communication",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": ["stakeholders"], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Communication"],
            },
            {
                "question": "How would you design a safer rollout for a new requirement?",
                "question_type": "deep_dive",
                "scenario_type": "system_design",
                "dimension": "system design / scalability",
                "focus_area": "design",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": ["rollout"], "gap_used": None},
                "difficulty_level": "Hard",
                "what_interviewer_is_testing": ["Design"],
            },
            {
                "question": "How would you recover from a regression in the current release?",
                "question_type": "cv_based",
                "scenario_type": "debugging",
                "dimension": "debugging / regression recovery",
                "focus_area": "debugging",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": ["release"], "gap_used": None},
                "difficulty_level": "Medium",
                "what_interviewer_is_testing": ["Debugging"],
            },
            {
                "question": "How would you handle an ambiguous stakeholder handover?",
                "question_type": "gap_targeted",
                "scenario_type": "scaling",
                "dimension": "stakeholder communication / coordination",
                "focus_area": "ownership",
                "source_basis": {"cv_terms_used": [], "jd_terms_used": ["stakeholders"], "gap_used": None},
                "difficulty_level": "Hard",
                "what_interviewer_is_testing": ["Ownership"],
            },
        ]

        valid, reason = _validate_question_bundle(questions, role="Backend Engineer", cv_context="", jd_context="API rollout stakeholders")

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

    def test_role_only_fallback_bundle_is_scenario_complete_without_tech_terms(self):
        with patch("interview_app_backend.services.question_service.get_openrouter_client", return_value=object()), patch(
            "interview_app_backend.services.question_service.call_llm",
            side_effect=RuntimeError("forced failure"),
        ):
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

        questions = result["questions"]
        self.assertEqual(len(questions), 5)
        self.assertEqual({item["scenario_type"] for item in questions}, {"debugging", "performance", "system_design", "behavioural", "scaling"})
        self.assertTrue(all("?" in item["question"] for item in questions))
        self.assertTrue(all(not any(term in item["question"].lower() for term in ["aws", "rest", "microservices", "sql", "caching", "react", "api", "database"]) for item in questions))
        valid, reason = _validate_question_bundle(questions, role="Generalist", cv_context="", jd_context="")
        self.assertTrue(valid, reason)

    def test_jd_only_fallback_bundle_uses_job_description_terms(self):
        jd_context = "REST microservices SQL caching AWS rollout requirements"
        with patch("interview_app_backend.services.question_service.get_openrouter_client", return_value=object()), patch(
            "interview_app_backend.services.question_service.call_llm",
            side_effect=RuntimeError("forced failure"),
        ):
            result = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                focus="General",
                cv_context="",
                question_index=1,
                jd_context=jd_context,
                asked_topics=[],
                question_list_count=5,
                return_meta=True,
            )

        questions = result["questions"]
        question_texts = " | ".join(item["question"].lower() for item in questions)
        self.assertEqual(len(questions), 5)
        self.assertTrue(any(term in question_texts for term in ["rest", "microservices", "sql", "caching", "aws"]))
        self.assertFalse(any(term in question_texts for term in ["react", "angular", "graphql", "kafka", "redux"]))
        valid, reason = _validate_question_bundle(questions, role="Backend Engineer", cv_context="", jd_context=jd_context)
        self.assertTrue(valid, reason)

    def test_cv_jd_fallback_bundle_uses_cv_terms_and_gap_targeting(self):
        cv_context = "Python, React, API work"
        jd_context = "REST microservices SQL caching AWS rollout requirements"
        with patch("interview_app_backend.services.question_service.get_openrouter_client", return_value=object()), patch(
            "interview_app_backend.services.question_service.call_llm",
            side_effect=RuntimeError("forced failure"),
        ):
            result = get_next_question_for_session(
                role="Backend Engineer",
                difficulty="Medium",
                persona="Direct",
                response_style="Concise",
                focus="General",
                cv_context=cv_context,
                question_index=1,
                jd_context=jd_context,
                asked_topics=[],
                question_list_count=5,
                return_meta=True,
            )

        questions = result["questions"]
        question_texts = " | ".join(item["question"].lower() for item in questions)
        self.assertEqual(len(questions), 5)
        self.assertTrue(any(term in question_texts for term in ["python", "react", "api"]))
        self.assertTrue(any(item["question_type"] == "gap_targeted" for item in questions))
        valid, reason = _validate_question_bundle(questions, role="Backend Engineer", cv_context=cv_context, jd_context=jd_context)
        self.assertTrue(valid, reason)


if __name__ == "__main__":
    unittest.main()
