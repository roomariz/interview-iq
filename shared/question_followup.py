"""Concise probes anchored to an actual answer decision, without inferring a deficit."""

import re


def question_bound_followup(question: str, answer: str, assessment: dict, feedback=None) -> dict:
    question_type = assessment.get("question_type", "other")
    feedback = feedback or {}
    off_topic = assessment.get("status") == "off_topic"
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", answer) if part.strip()]
    focus = " ".join(feedback.get("improvements", []) + feedback.get("key_issues", [])).lower()
    tokens = set(re.findall(r"\b[a-z]{5,}\b", focus))
    anchor = max(sentences, key=lambda part: sum(token in part.lower() for token in tokens), default="")
    excerpt = " ".join(anchor.split()[:24])
    if off_topic:
        text = "Which evidence or explanation directly addresses the original question?"
    elif "roll" in answer.lower() and "back" in answer.lower() and "disabl" in answer.lower():
        text = "What evidence would make you choose a rollback rather than disabling the affected feature?"
    elif question_type == "technical_knowledge" and excerpt:
        text = f'How would you demonstrate “{excerpt}” with a small example and an edge case?'
    elif question_type == "behavioural" and excerpt:
        text = f'You said “{excerpt}”. What did you personally decide, and what informed that choice?'
    elif excerpt:
        text = f'For “{excerpt}”, what evidence would justify that decision over an alternative?'
    else:
        text = "Which concrete step would you take first, and what evidence would support it?"
    return {
        "question": text, "type": "relevance_gate" if off_topic else "depth_probe",
        "target_dimension": "relevance" if off_topic else "problem_solving_approach",
        "reasoning_action": "Explain the evidence supporting this decision.",
        "context_note": f"Original question: {question}\nSubmitted response: {answer}",
        "stage": 1,
    }
