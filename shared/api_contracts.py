"""HTTP contracts shared without importing providers or Streamlit."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
QuestionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=6000)]
ContextText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=20000)]
TextList = Annotated[list[ShortText], Field(max_length=30)]


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @model_validator(mode="after")
    def reject_instructions(self):
        markers = ("ignore previous instructions", "ignore all previous instructions",
                   "disregard previous instructions", "override system", "system prompt",
                   "developer message", "prompt injection")

        def check(value, depth=0):
            if depth > 8:
                raise ValueError("Context is too deeply nested")
            if isinstance(value, str):
                if len(value) > 20000 or any(marker in value.lower() for marker in markers) or "\x00" in value:
                    raise ValueError("Unsupported instructions in input")
            elif isinstance(value, dict):
                if len(value) > 40:
                    raise ValueError("Too many context fields")
                for item in value.values():
                    check(item, depth + 1)
            elif isinstance(value, list):
                if len(value) > 40:
                    raise ValueError("Too many context items")
                for item in value:
                    check(item, depth + 1)

        check(self.model_dump())
        return self


class ContextRequest(RequestModel):
    role: Annotated[ShortText, Field(min_length=1)]
    cv_context: ContextText = ""
    jd_context: ContextText = ""
    question_type: ShortText = "auto"


class ContextResponse(BaseModel):
    tech_stack: list[str]
    competencies: list[str]
    question_type: str
    gap_analysis: dict[str, Any]
    model: str
    provider: str
    free_mode: bool
    session_question_limit: Annotated[int, Field(ge=1, le=10)]
    question_list_count: Annotated[int, Field(ge=1, le=5)]


class QuestionRequest(ContextRequest):
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    persona: Literal["Friendly", "Neutral", "Strict"] = "Neutral"
    response_style: Literal["Concise", "Detailed"] = "Detailed"
    focus: ShortText = ""
    temperature: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] = 0.7
    question_index: Annotated[int, Field(ge=1, le=10)] = 1
    question_list_count: Annotated[int, Field(ge=1, le=5)] = 1
    asked_topics: TextList = Field(default_factory=list)
    tech_stack: TextList = Field(default_factory=list)
    competencies: TextList = Field(default_factory=list)
    previous_questions: Annotated[list[QuestionText], Field(max_length=10)] = Field(default_factory=list)
    gap_analysis: dict[str, Any] = Field(default_factory=dict)


class QuestionItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    question: QuestionText


class QuestionResponse(BaseModel):
    questions: Annotated[list[QuestionItem], Field(min_length=1, max_length=5)]
    meta: dict[str, Any]
    llm_metadata: dict[str, str | int | None] = Field(default_factory=dict)


class EvaluationRequest(RequestModel):
    question: QuestionText
    answer: Annotated[str, StringConstraints(strip_whitespace=True, min_length=50, max_length=2000)]


class Scores(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    __pydantic_extra__: dict[str, Annotated[int, Field(ge=0, le=10)]] = Field(init=False)
    relevance: Annotated[int, Field(ge=0, le=10)]
    structure: Annotated[int, Field(ge=0, le=10)]
    specificity: Annotated[int, Field(ge=0, le=10)]
    communication: Annotated[int, Field(ge=0, le=10)]
    problem_solving_approach: Annotated[int, Field(ge=0, le=10)]


class EvaluationResponse(BaseModel):
    # Preserve all existing confidence, grounding and degraded-result fields.
    model_config = ConfigDict(extra="allow")
    question: QuestionText
    answer: str
    scores: Scores
    overall_decision: Literal["pass", "borderline pass", "borderline_pass", "borderline", "fail"]
    feedback: dict[str, Any]
    follow_up: dict[str, Any]


class ExampleRequest(RequestModel):
    answer: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ExampleResponse(BaseModel):
    text: Annotated[str, Field(max_length=12000)]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
