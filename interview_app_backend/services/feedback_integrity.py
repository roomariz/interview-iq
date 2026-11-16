"""Conservative checks for feedback and memory at the output boundary."""

from shared.feedback_guards import example_text, memory_is_allowed  # noqa: F401

import re
from collections.abc import Mapping

from interview_app_backend.services.question_validation import unsupported_technologies


def clean_feedback(data):
    """Remove demonstrably unsupported claims; never manufacture replacement advice."""
    result = dict(data)
    context = f"{data.get('question', '')} {data.get('answer', '')}".lower()
    scores = data.get("scores", {})
    non_behavioural = data.get("relevance_assessment", {}).get("question_type", "other") != "behavioural"
    previous = data.get("feedback_validation", {})
    removed = list(previous.get("removed_claims", []))
    issues = list(previous.get("issues", []))

    def clean(text):
        if not isinstance(text, str):
            return ""
        unsupported = unsupported_technologies(text, context)
        for concept in ("caching", "denormalisation", "denormalization", "asynchronous messaging",
                        "vertical scaling", "queue-based processing"):
            if concept in text.lower() and concept not in context:
                unsupported.append(concept)
        relevance_conflict = scores.get("relevance", 0) >= 6 and re.search(
            r"\b(irrelevant|off.topic|not relevant|does not address the question)\b", text, re.I)
        wrong_rubric = non_behavioural and re.search(
            r"\b(STAR|historical results|measurable results|quantifiable results)\b", text, re.I)
        invented_metrics = not re.search(r"\d", str(data.get("answer", ""))) and re.search(
            r"\b(strong metrics|metrics are present|measurable outcomes are present)\b", text, re.I)
        if unsupported or relevance_conflict or wrong_rubric or invented_metrics:
            removed.append(text)
            code = "unsupported_technology" if unsupported else "score_feedback_contradiction" if relevance_conflict else "unsupported_rubric" if wrong_rubric else "unsupported_metric_claim"
            issues.append({"code": code, "claim": text, "action": "removed"})
            return ""
        return text.strip()

    feedback = data.get("feedback", {})
    feedback = dict(feedback) if isinstance(feedback, Mapping) else {}
    feedback["summary"] = clean(feedback.get("summary", data.get("summary", "")))
    for key in ("strengths", "key_issues", "improvements"):
        items = feedback.get(key, data.get(key, []))
        feedback[key] = [value for item in items if (value := clean(item))] if isinstance(items, list) else []
        result[key] = feedback[key]
    result["feedback"] = feedback
    result["summary"] = result["overall_summary"] = feedback["summary"]
    for field in ("labels", "reasoning"):
        result[field] = {key: clean(value) for key, value in data.get(field, {}).items()}
    for dimension, label in list(result["labels"].items()):
        if scores.get(dimension, 0) >= 8 and re.search(r"\b(weak|lacks|needs improvement)\b", label, re.I):
            removed.append(label)
            issues.append({"code": "score_feedback_contradiction", "claim": label, "action": "removed"})
            result["labels"][dimension] = ""
    result["improvement_areas"] = feedback["improvements"]
    result["example_answer"] = example_text(data.get("example_answer"))
    result["feedback_validation"] = {
        **previous,
        "removed_claims": list(dict.fromkeys(removed)), "issues": issues,
        "status": "withheld_claims" if removed or issues else previous.get("status", "checked"),
        "method": "question_and_answer_constraints",
    }
    return result
