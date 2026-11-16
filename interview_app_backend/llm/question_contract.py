"""Shared request count, wire schema and local question-bundle validation."""

import json
from collections import Counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

QUESTION_TYPES = ("cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted")
SCENARIO_TYPES = ("debugging", "performance", "behavioural", "system_design", "scaling")
CONTRACT_PREFIX = "QUESTION_CONTRACT: "


class QuestionValidationError(ValueError):
    pass


def distribution_for(count: int, question_type: str = "cv_based") -> dict[str, int]:
    if count != 1 and not 5 <= count <= 10:
        raise ValueError("Question request count must be 1 or between 5 and 10")
    result = dict.fromkeys(QUESTION_TYPES, 0)
    if count == 1:
        result[question_type if question_type in result else "cv_based"] = 1
    else:
        for index in range(count):
            result[QUESTION_TYPES[index % len(QUESTION_TYPES)]] += 1
    return result


class SourceBasis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cv_terms_used: list[str]
    jd_terms_used: list[str]
    gap_used: str | None


class GeneratedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence_order: int = Field(ge=1, le=10)
    question: str = Field(min_length=20)
    question_type: Literal["cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted"]
    scenario_type: Literal["debugging", "performance", "behavioural", "system_design", "scaling"]
    focus_area: str = Field(min_length=1)
    source_basis: SourceBasis
    difficulty_level: str = Field(min_length=1)
    what_interviewer_is_testing: list[str] = Field(min_length=1)


class QuestionDistribution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cv_based: int = Field(ge=0)
    jd_based: int = Field(ge=0)
    behavioural: int = Field(ge=0)
    deep_dive: int = Field(ge=0)
    gap_targeted: int = Field(ge=0)


class QuestionMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_questions: int = Field(ge=1, le=10)
    distribution: QuestionDistribution


class QuestionBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meta: QuestionMeta
    questions: list[GeneratedQuestion] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def validate_bundle(self):
        count = len(self.questions)
        if self.meta.total_questions != count:
            raise ValueError("invalid_question_count: meta total does not match questions")
        if [item.sequence_order for item in self.questions] != list(range(1, count + 1)):
            raise ValueError("invalid_sequence_order")
        texts = [" ".join(item.question.lower().split()) for item in self.questions]
        if len(set(texts)) != count:
            raise ValueError("duplicate_question")
        counts = Counter(item.question_type for item in self.questions)
        if self.meta.distribution.model_dump() != {key: counts[key] for key in QUESTION_TYPES}:
            raise ValueError("invalid_distribution: meta does not match questions")
        return self


def contract_header(count: int, question_type: str = "cv_based") -> str:
    contract = {"count": count, "distribution": distribution_for(count, question_type)}
    return CONTRACT_PREFIX + json.dumps(contract, separators=(",", ":"))


def request_contract(prompt: str) -> dict:
    first_line = prompt.splitlines()[0] if prompt else ""
    if not first_line.startswith(CONTRACT_PREFIX):
        return {"count": 5, "distribution": distribution_for(5)}
    contract = json.loads(first_line[len(CONTRACT_PREFIX):])
    distribution_for(contract["count"])
    return contract


def question_response_schema(prompt: str) -> dict:
    contract = request_contract(prompt)
    count = contract["count"]
    schema = QuestionBundle.model_json_schema()
    schema["properties"]["questions"].update(minItems=count, maxItems=count)
    schema["$defs"]["QuestionMeta"]["properties"]["total_questions"].update(minimum=count, maximum=count)
    for key, value in contract["distribution"].items():
        schema["$defs"]["QuestionDistribution"]["properties"][key].update(minimum=value, maximum=value)
    return schema


def validate_question_response(payload: str, count: int, expected_distribution: dict | None = None) -> dict:
    try:
        raw = json.loads(payload)
    except (ValueError, TypeError) as exc:
        raise QuestionValidationError("invalid_json: return one complete JSON document") from exc
    actual = len(raw.get("questions", [])) if isinstance(raw, dict) and isinstance(raw.get("questions"), list) else 0
    if actual != count:
        raise QuestionValidationError(f"invalid_question_count: expected {count}, received {actual}")
    try:
        bundle = QuestionBundle.model_validate(raw)
    except ValidationError as exc:
        errors = "; ".join(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors(include_input=False))
        raise QuestionValidationError(f"invalid_question_schema: {errors}") from exc
    if expected_distribution is not None and bundle.meta.distribution.model_dump() != expected_distribution:
        raise QuestionValidationError(f"invalid_distribution: expected {json.dumps(expected_distribution)}")
    return bundle.model_dump()
