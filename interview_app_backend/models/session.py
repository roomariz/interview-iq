from dataclasses import dataclass, field


@dataclass(slots=True)
class Session:
    current_screen: str = "welcome"
    role: str = ""
    difficulty: str = ""
    persona: str = ""
    response_style: str = ""
    question_count: int = 0
    completed_questions: int = 0
    duration_minutes: int = 0
    scores: list[dict[str, int]] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    improvement_areas: list[str] = field(default_factory=list)
