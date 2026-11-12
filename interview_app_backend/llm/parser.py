import json
import logging
from collections.abc import Mapping

from pydantic import BaseModel, Field, field_validator, model_validator

from interview_app_backend.llm.json_utils import repair_json_payload
from interview_app_backend.llm.prompt_contract import parse_prompt_contract


LOGGER = logging.getLogger(__name__)
SCORE_KEYS = (
    "technical_accuracy",
    "clarity",
    "structure",
    "relevance",
    "problem_solving_approach",
    "specificity",
    "communication",
)
def _normalise_score_value(value: object) -> object:
    if isinstance(value, bool):
        return value
    try:
        numeric = float(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return value
    return int(max(0, min(10, round(numeric))))


class ScoreSchema(BaseModel):
    technical_accuracy: int = Field(ge=0, le=10)
    clarity: int = Field(ge=0, le=10)
    relevance: int = Field(ge=0, le=10)
    structure: int = Field(ge=0, le=10)
    specificity: int = Field(ge=0, le=10)
    communication: int = Field(ge=0, le=10)
    problem_solving_approach: int = Field(ge=0, le=10)


class LabelSchema(BaseModel):
    relevance: str = ""
    structure: str = ""
    specificity: str = ""
    communication: str = ""
    problem_solving_approach: str = ""


class FeedbackSchema(BaseModel):
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    key_issues: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)

    @field_validator("strengths", "key_issues", "improvements")
    @classmethod
    def _strip_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class ReasoningSchema(BaseModel):
    clarity: str = ""
    alternative_approaches: str = ""
    trade_off_awareness: str = ""
    evidence: str = ""


class EvidenceSchema(BaseModel):
    metrics: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    reasoning: str = ""

    @field_validator("metrics", "actions")
    @classmethod
    def _strip_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class MetricDetailSchema(BaseModel):
    type: str = ""
    before: str = ""
    after: str = ""
    change: str = ""


class ConfidenceSchema(BaseModel):
    metrics: float = Field(default=0.0, ge=0.0, le=1.0)
    structure: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: float = Field(default=0.0, ge=0.0, le=1.0)
    tradeoffs: float = Field(default=0.0, ge=0.0, le=1.0)
    alternatives: float = Field(default=0.0, ge=0.0, le=1.0)


class EvidenceContextSchema(BaseModel):
    has_metrics: bool = False
    metrics: list[MetricDetailSchema] = Field(default_factory=list)
    has_structure: bool = False
    has_reasoning: bool = False
    has_tradeoffs: bool = False
    has_alternatives: bool = False
    confidence: ConfidenceSchema = Field(default_factory=ConfidenceSchema)
    contradiction_flags: list[str] = Field(default_factory=list)
    anomaly_flags: list[str] = Field(default_factory=list)
    numeric_signals: list[str] = Field(default_factory=list)


class FollowUpSchema(BaseModel):
    question: str = ""
    type: str = ""
    target_dimension: str = ""


class EvaluationSchema(BaseModel):
    evidence: EvidenceSchema = Field(default_factory=EvidenceSchema)
    scores: ScoreSchema
    labels: LabelSchema
    feedback: FeedbackSchema = Field(default_factory=FeedbackSchema)
    reasoning: ReasoningSchema = Field(default_factory=ReasoningSchema)
    follow_up: FollowUpSchema = Field(default_factory=FollowUpSchema)
    example_answer: dict[str, str] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    overall_summary: str = ""
    evaluation_version: str = ""
    evaluation_trace: list[str] = Field(default_factory=list)
    impact_strength: str = ""

    @model_validator(mode="before")
    @classmethod
    def _coerce_payload(cls, value: object) -> object:
        if not isinstance(value, Mapping):
            return value

        data = dict(value)
        nested = data.get("evaluation") if isinstance(data.get("evaluation"), Mapping) else {}
        evidence = data.get("evidence") if isinstance(data.get("evidence"), Mapping) else {}
        feedback = data.get("feedback") if isinstance(data.get("feedback"), Mapping) else {}
        reasoning = data.get("reasoning") if isinstance(data.get("reasoning"), Mapping) else {}
        if not reasoning:
            legacy_reasoning = data.get("reasoning_feedback")
            if isinstance(legacy_reasoning, Mapping):
                reasoning = dict(legacy_reasoning)
            else:
                legacy_assessment = data.get("reasoning_assessment")
                if isinstance(legacy_assessment, Mapping):
                    reasoning = dict(legacy_assessment)

        follow_up = data.get("follow_up") if isinstance(data.get("follow_up"), Mapping) else {}
        example_answer = data.get("example_answer") if isinstance(data.get("example_answer"), Mapping) else {}

        scores_source = data.get("scores") if isinstance(data.get("scores"), Mapping) else {}
        labels_source = data.get("labels") if isinstance(data.get("labels"), Mapping) else {}
        if not evidence:
            evidence = {
                "metrics": data.get("metrics", []),
                "actions": data.get("actions", []),
                "reasoning": str(data.get("reasoning_text", data.get("reasoning", ""))).strip(),
            }
        if not scores_source and isinstance(nested, Mapping):
            scores_source = nested.get("scores") if isinstance(nested.get("scores"), Mapping) else {}
        if not labels_source and isinstance(nested, Mapping):
            labels_source = nested.get("labels") if isinstance(nested.get("labels"), Mapping) else {}

        scores_source = dict(scores_source)
        if "technical_accuracy" not in scores_source and "specificity" in scores_source:
            scores_source["technical_accuracy"] = scores_source["specificity"]
        if "clarity" not in scores_source and "communication" in scores_source:
            scores_source["clarity"] = scores_source["communication"]
        if "specificity" not in scores_source and "technical_accuracy" in scores_source:
            scores_source["specificity"] = scores_source["technical_accuracy"]
        if "communication" not in scores_source and "clarity" in scores_source:
            scores_source["communication"] = scores_source["clarity"]
        scores_source = {key: _normalise_score_value(value) for key, value in scores_source.items()}

        if not feedback:
            feedback = {
                "summary": str(data.get("overall_summary", "")).strip(),
                "strengths": data.get("strengths", []),
                "key_issues": data.get("key_issues", data.get("weak_points", [])),
                "improvements": data.get("improvements", data.get("improvement_areas", [])),
            }

        if not follow_up:
            follow_up = {
                "question": str(data.get("follow_up_question", "")).strip(),
                "type": str(data.get("follow_up_type", "")).strip(),
                "target_dimension": str(data.get("target_dimension", "")).strip(),
            }

        strengths = data.get("strengths", feedback.get("strengths", []))
        improvement_areas = data.get("improvement_areas", feedback.get("improvements", []))
        data["scores"] = scores_source
        data["labels"] = labels_source
        data["evidence"] = evidence
        data["feedback"] = feedback
        data["reasoning"] = reasoning or {
            "clarity": str(data.get("clarity", "")).strip(),
            "alternative_approaches": str(data.get("alternative_approaches", "")).strip(),
            "trade_off_awareness": str(data.get("trade_off_awareness", "")).strip(),
            "evidence": str(evidence.get("reasoning", data.get("evidence", ""))).strip(),
        }
        data["follow_up"] = follow_up
        data["example_answer"] = example_answer
        data["strengths"] = strengths
        data["improvement_areas"] = improvement_areas
        future_session_memory = data.get("future_session_memory")
        data["future_session_memory"] = list(future_session_memory) if isinstance(future_session_memory, list) else []
        data["overall_summary"] = str(data.get("overall_summary", feedback.get("summary", ""))).strip()
        return data


def _log_validation_event(*, model: str | None, provider: str | None, task: str | None, validation: str, fallback_triggered: bool, reason: str) -> None:
    LOGGER.info(
        "evaluation_model=%s provider=%s task=%s validation=%s fallback_triggered=%s reason=%s",
        model or "",
        provider or "",
        task or "",
        validation,
        fallback_triggered,
        reason,
    )


def parse_json_response(payload: str, *, model: str | None = None, provider: str | None = None, task: str | None = None) -> dict:
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError:
        repaired = repair_json_payload(payload)
        if repaired is None:
            _log_validation_event(model=model, provider=provider, task=task, validation="failed", fallback_triggered=True, reason="invalid_json")
            schema = EvaluationSchema.model_validate_json(payload)
            return schema.model_dump()
        _log_validation_event(model=model, provider=provider, task=task, validation="repaired", fallback_triggered=False, reason="malformed_json")
        raw = json.loads(repaired)
    if isinstance(raw, Mapping) and isinstance(raw.get("evaluation"), Mapping):
        return parse_prompt_contract(raw)
    try:
        schema = EvaluationSchema.model_validate(raw)
    except Exception:
        _log_validation_event(model=model, provider=provider, task=task, validation="failed", fallback_triggered=True, reason="invalid_schema")
        raise
    return schema.model_dump()


def parse_evidence_response(payload: str) -> dict:
    schema = EvidenceContextSchema.model_validate_json(payload)
    return schema.model_dump()
