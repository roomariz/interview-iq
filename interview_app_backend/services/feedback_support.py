"""Validate claim provenance without confusing absent citations with hallucination."""

import unicodedata

from pydantic import BaseModel, Field, ValidationError


def _normalise(text):
    return " ".join(unicodedata.normalize("NFKC", text).replace("’", "'").split()).casefold().rstrip(".")


class FeedbackSupport(BaseModel):
    claim: str = Field(min_length=1)
    answer_quote: str = Field(min_length=8)
    question_quote: str = Field(min_length=8)


def validate_feedback_support(evaluation, raw, question, answer):
    supported = set()
    previous = evaluation.get("feedback_validation", {})
    issues = list(previous.get("issues", []))
    items = raw.get("feedback_support", []) if isinstance(raw, dict) else []
    for item in items if isinstance(items, list) else []:
        try:
            support = FeedbackSupport.model_validate(item)
        except ValidationError:
            issues.append({"code": "malformed_support"})
            continue
        if _normalise(support.answer_quote) in _normalise(answer) and _normalise(support.question_quote) in _normalise(question):
            supported.add(_normalise(support.claim))
        else:
            issues.append({"code": "source_quote_mismatch", "claim": support.claim})
    feedback = dict(evaluation.get("feedback", {}))
    withheld = list(previous.get("removed_claims", []))
    accepted = 0
    for key in ("strengths", "key_issues", "improvements"):
        values = feedback.get(key, [])
        kept = []
        for value in values:
            if _normalise(value) in supported:
                kept.append(value)
                accepted += 1
            else:
                withheld.append(value)
                issues.append({"code": "missing_claim_support", "claim": value})
        feedback[key] = evaluation[key] = kept
    evaluation["feedback"] = feedback
    evaluation["improvement_areas"] = feedback["improvements"]
    evaluation["feedback_validation"] = {
        "removed_claims": withheld, "issues": issues, "accepted_claims": accepted,
        "status": "withheld_claims" if withheld or issues else "checked",
        "method": "source_quotes_and_question_constraints",
    }
    return evaluation
