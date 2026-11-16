"""Deterministic question topic tracking, with no provider dependencies."""

def _topic_tokens(text: str) -> list[str]:
    cleaned = text.lower().replace("?", " ").replace(",", " ").replace("/", " ")
    return [token for token in cleaned.split() if len(token) > 3]


def derive_question_topics(question: str) -> list[str]:
    return list(dict.fromkeys(_topic_tokens(question)))


def normalise_topic(topic: str) -> str:
    return str(topic).lower().strip()


def extract_topic(question: str) -> str:
    topics = derive_question_topics(question)
    return normalise_topic(" ".join(topics[:3]))
