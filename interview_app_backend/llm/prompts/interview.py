WELCOME_PROMPT = ""

EXAMPLE_ANSWER_PROMPT = (
    "Rewrite the answer to improve clarity, structure, and reasoning.\n\n"
    "Constraints:\n"
    "- 1-2 paragraphs, max 2000 chars\n"
    "- Preserve all facts\n"
    "- Do NOT add new metrics, trade-offs, or experiences\n\n"
    "Improve:\n"
    "- make reasoning explicit (why)\n"
    "- improve flow (context -> action -> reasoning -> outcome)\n\n"
    "If missing metrics, trade-offs, or alternatives: do NOT invent.\n\n"
    "Style:\n"
    "- concise, direct, professional\n"
    "- focus on reasoning over listing"
)


def build_example_answer_prompt(answer: str) -> str:
    clean_answer = answer.strip()
    return f"{EXAMPLE_ANSWER_PROMPT}\n\nOriginal answer:\n{clean_answer}"


REFERENCE_ANSWER_PROMPT = (
    "Generate a concise, high-quality reference answer to the question.\n"
    "- 1-2 paragraphs\n"
    "- No invented personal details or metrics\n"
    "- Focus on clear reasoning and structure"
)


SEMANTIC_SIMILARITY_PROMPT = (
    "Compare meaning of two answers. Return ONLY a number (0-1).\n\n"
    "Scale:\n"
    "1.0 same meaning\n"
    "0.7-0.9 mostly aligned\n"
    "0.4-0.6 partial\n"
    "<0.4 incorrect/unrelated\n\n"
    "Focus on:\n"
    "- correctness of ideas\n"
    "- reasoning alignment\n"
    "- coverage of key concepts\n\n"
    "Ignore wording differences."
)


def build_reference_answer_prompt(question: str) -> str:
    return f"{REFERENCE_ANSWER_PROMPT}\n\nQuestion:\n{question.strip()}"


def build_semantic_similarity_prompt(reference_answer: str, user_answer: str) -> str:
    return (
        f"{SEMANTIC_SIMILARITY_PROMPT}\n\n"
        f"Reference answer:\n{reference_answer.strip()}\n\n"
        f"User answer:\n{user_answer.strip()}"
    )
