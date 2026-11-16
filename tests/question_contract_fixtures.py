from interview_app_backend.llm.question_contract import QUESTION_TYPES, SCENARIO_TYPES


def valid_bundle():
    questions = [
        "Your application has a backend regression after a routine release. What evidence would you gather to isolate its cause?",
        "A user reports that your backend workflow becomes slow during busy periods. How would you measure and improve performance safely?",
        "Tell me about a time your backend team disagreed about delivery priorities. What did you do to resolve the conflict?",
        "A colleague asks you to design your application for a growing backend workload. Which trade-offs would guide your decision?",
        "Stakeholders report that your application cannot keep up with requests. How would you coordinate the backend team and scale the workflow?",
    ]
    return {
        "meta": {"total_questions": 5, "distribution": dict.fromkeys(QUESTION_TYPES, 1)},
        "questions": [{
            "sequence_order": index + 1, "question": question,
            "question_type": QUESTION_TYPES[index], "scenario_type": SCENARIO_TYPES[index],
            "focus_area": SCENARIO_TYPES[index], "difficulty_level": "Medium",
            "source_basis": {"cv_terms_used": [], "jd_terms_used": [], "gap_used": None},
            "what_interviewer_is_testing": [SCENARIO_TYPES[index]],
        } for index, question in enumerate(questions)],
    }
