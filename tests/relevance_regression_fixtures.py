"""Verbatim incident inputs supplied by the user; scores are the reported failure."""

QUESTION = (
    "Your application has a regression after a release in your backend engineer team. "
    "What evidence would you gather to isolate the cause and recover safely?"
)
ANSWER = (
    "I would first assess the impact of the regression by checking error rates, response times, "
    "affected API endpoints and user reports. I would review application logs, monitoring metrics, "
    "deployment history and the code changes introduced in the latest release. I would also compare "
    "the behaviour with the previous stable version to help isolate the root cause.\n"
    "If the issue significantly affected users, I would coordinate with the team to roll back the "
    "release or disable the affected feature, provided this could be done safely. I would then "
    "reproduce the problem, implement a fix and verify it through unit, integration and regression tests.\n"
    "After redeployment, I would monitor the application to confirm recovery and document the root "
    "cause and preventive actions."
)
INCORRECT_EVALUATION = {
    "overall_decision": "fail",
    "scores": {"relevance": 1, "structure": 3, "specificity": 1, "communication": 6,
               "problem_solving_approach": 2},
    "topic_match": False, "relevance_gate_applied": True, "failure_type": "off_topic",
    "score_confidence": 0.0, "decision_confidence": "high",
    "summary": "The answer is not relevant to the question.",
    "follow_up": {"question": "Can you describe a real example where you improved system performance "
                              "under constraints with measurable results?"},
}


def verdict(question=QUESTION, answer=ANSWER, status="relevant", question_type="scenario_troubleshooting", confidence=0.96):
    return {"status": status, "confidence": confidence, "question_type": question_type,
            "reason": "The response addresses diagnostic evidence and safe recovery." if status == "relevant"
            else "The question asks for technical diagnosis while the response discusses a different subject.",
            "question_quote": question, "answer_quote": answer}
