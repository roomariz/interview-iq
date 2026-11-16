"""Question generation similarity."""

from __future__ import annotations

from interview_app_backend.services import question_service as service
from shared.question_topics import _topic_tokens, derive_question_topics, normalise_topic, extract_topic  # noqa: F401


def _is_similar_to_previous(question: str, previous_questions: list[str] | None) -> bool:
    previous = [item for item in previous_questions or [] if str(item).strip()]
    if not previous:
        return False
    if any(service.same_question_pattern(question, prior) for prior in previous):
        return True
    question_tokens = set(service._topic_tokens(question))
    if not question_tokens:
        return False
    for prior in previous:
        prior_tokens = set(service._topic_tokens(prior))
        if not prior_tokens:
            continue
        overlap = question_tokens & prior_tokens
        if len(overlap) >= 4 or len(overlap) / max(len(question_tokens), 1) >= 0.45:
            return True
    return False


def _question_similarity(question_a: str, question_b: str) -> float:
    a = " ".join(str(question_a).lower().split())
    b = " ".join(str(question_b).lower().split())
    if not a or not b:
        return 0.0
    return service.SequenceMatcher(None, a, b).ratio()


def is_semantically_duplicate(question_a: str, question_b: str, threshold: float = 0.85) -> bool:
    return service._question_similarity(question_a, question_b) >= threshold and service.key_terms_overlap(question_a, question_b) > 0.5


def key_terms_overlap(question_a: str, question_b: str) -> float:
    stop_words = {
        "how", "would", "you", "the", "and", "with", "your", "what", "when", "where", "why", "about",
        "time", "this", "that", "have", "been", "from", "under", "into", "over", "into", "does", "did",
        "using", "through", "describe", "tell", "me", "a", "an", "to", "of", "for", "in", "on", "at",
        "is", "are", "was", "were", "do", "does", "can", "could", "should",
    }

    def _terms(question: str) -> set[str]:
        tokens = [token.strip("?,.!:;()[]{}").lower() for token in str(question).split()]
        return {
            token
            for token in tokens
            if len(token) > 3 and token not in stop_words and not token.isdigit()
        }

    terms_a = _terms(question_a)
    terms_b = _terms(question_b)
    if not terms_a or not terms_b:
        return 0.0
    overlap = terms_a & terms_b
    return len(overlap) / max(min(len(terms_a), len(terms_b)), 1)


def _question_opening_style(question: str) -> str:
    opening = " ".join(str(question).lower().split())
    for prefix in ("how would you", "how do you", "what would you", "describe a", "tell me about", "walk me through", "give an example"):
        if opening.startswith(prefix):
            return prefix
    return " ".join(opening.split()[:4])


def same_question_pattern(question_a: str, question_b: str) -> bool:
    return service._question_opening_style(question_a) == service._question_opening_style(question_b)


def _avoid_topics_line(asked_topics: list[str]) -> str:
    topics = [topic.strip() for topic in asked_topics if str(topic).strip()]
    if not topics:
        return ""
    return "Avoid repeating these topics: " + ", ".join(topics) + "\n"
