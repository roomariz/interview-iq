from dataclasses import dataclass, field


CORE_EVALUATION_DIMENSIONS = (
    "relevance",
    "structure",
    "specificity",
    "communication",
    "problem_solving_approach",
)


@dataclass(slots=True)
class Evaluation:
    scores: dict[str, int] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    feedback: dict[str, object] = field(default_factory=dict)
    reasoning: dict[str, str] = field(default_factory=dict)
    follow_up: dict[str, str] = field(default_factory=dict)
    example_answer: str = ""
