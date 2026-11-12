from enum import Enum


class QuestionType(Enum):
    TECHNICAL = "technical"
    BEHAVIOURAL = "behavioural"
    ROLE_SPECIFIC = "role_specific"
    GAP_FOCUSED = "gap_focused"
    FOLLOW_UP = "follow_up"


QUESTION_DISTRIBUTION = {
    QuestionType.TECHNICAL: 0.30,
    QuestionType.BEHAVIOURAL: 0.25,
    QuestionType.ROLE_SPECIFIC: 0.25,
    QuestionType.GAP_FOCUSED: 0.15,
    QuestionType.FOLLOW_UP: 0.05,
}


def get_weighted_distribution() -> dict:
    return QUESTION_DISTRIBUTION.copy()


def get_question_type_for_index(index: int, has_gaps: bool = False) -> QuestionType:
    if has_gaps and index > 1:
        distribution = _adjust_for_gaps(QUESTION_DISTRIBUTION)
    else:
        distribution = QUESTION_DISTRIBUTION

    normalized_index = (index - 1) % len(distribution)
    types = list(distribution.keys())
    return types[normalized_index]


def _adjust_for_gaps(base_distribution: dict) -> dict:
    adjusted = base_distribution.copy()
    current_gap = adjusted.get(QuestionType.GAP_FOCUSED, 0.15)
    adjusted[QuestionType.GAP_FOCUSED] = min(current_gap + 0.15, 0.40)
    return adjusted


def get_question_type_prompt(type: QuestionType) -> str:
    prompts = {
        QuestionType.TECHNICAL: "Ask a technical question specific to the role.",
        QuestionType.BEHAVIOURAL: "Ask a behavioural question about teamwork and communication.",
        QuestionType.ROLE_SPECIFIC: "Ask a role-specific scenario question.",
        QuestionType.GAP_FOCUSED: "Ask a question targeting the candidate's skill gaps.",
        QuestionType.FOLLOW_UP: "Ask a follow-up question to explore their previous answer.",
    }
    return prompts.get(type, "")