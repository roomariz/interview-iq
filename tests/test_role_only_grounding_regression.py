"""No-document sessions must reject invented tools, not ordinary scenario words."""

import json
from unittest.mock import Mock

import pytest

from interview_app_backend.services import question_service as service
from interview_app_backend.services.question_validation import validate_generated_items
from interview_app_backend.llm.question_contract import QuestionValidationError
from question_contract_fixtures import valid_bundle


@pytest.mark.parametrize("word", ["monitoring", "testing", "leadership", "restore", "reaction"])
def test_role_only_generic_vocabulary_is_not_invented_technology(word):
    items = valid_bundle()["questions"]
    items[0]["question"] += f" What {word} evidence would help?"
    validate_generated_items(items, count=5, role="Backend Engineer", cv_context="", jd_context="")


def test_named_tool_rejection_identifies_question_and_term():
    items = valid_bundle()["questions"]
    items[1]["question"] += " Would Kubernetes help?"
    with pytest.raises(QuestionValidationError, match=r"question\[2\].*kubernetes"):
        validate_generated_items(items, count=5, role="Backend Engineer", cv_context="", jd_context="")


def test_single_question_cannot_infer_redis_from_generic_backend_role():
    valid, reason = service._validate_single_question(
        "Your application backend regression involves Redis. How would you isolate the cause?",
        role="Backend Engineer", cv_context="", jd_context="", focus="General", question_type="technical",
    )
    assert not valid
    assert reason == "hallucinated_tech"


@pytest.mark.parametrize("difficulty", ["Easy", "Medium", "Hard"])
@pytest.mark.parametrize("role", ["Backend Engineer", "Frontend Developer", "Data Engineer", "DevOps Engineer"])
@pytest.mark.parametrize("count", [5, 10])
def test_real_role_only_fallback_satisfies_full_contract(role, difficulty, count):
    items = service.fallback_questions(
        role=role, difficulty=difficulty, focus="General", cv_context="", jd_context="",
        question_type="role_based", previous_questions=[], question_plan=None, required_count=count,
    )
    assert len(items) == count
    assert not any(item["source_basis"]["cv_terms_used"] or item["source_basis"]["jd_terms_used"] for item in items)
    assert service.validate_question(items[1]["question"], "performance", "jd_based")[0]
    assert service.validate_question(items[2]["question"], "General", "behavioural")[0]


def test_supplied_named_tool_is_allowed():
    valid, reason = service._validate_single_question(
        "Your application backend regression involves Python. How would you isolate the cause?",
        role="Backend Engineer", cv_context="Python", jd_context="", focus="General", question_type="technical",
    )
    assert valid, reason


def test_repeated_fallback_does_not_bypass_previous_question_detection():
    items = service.fallback_questions(
        role="Backend Engineer", difficulty="Medium", focus="General", cv_context="", jd_context="",
        question_type="role_based", previous_questions=[], question_plan=None,
    )
    with pytest.raises(RuntimeError, match="Fallback generation failed validation"):
        service.fallback_questions(
            role="Backend Engineer", difficulty="Medium", focus="General", cv_context="", jd_context="",
            question_type="role_based", previous_questions=[item["question"] for item in items], question_plan=None,
        )


def test_retry_names_unsupported_tool_and_recovers(monkeypatch):
    bad = valid_bundle()
    bad["questions"][0]["question"] += " Use Redis?"
    call = Mock(side_effect=[json.dumps(bad), json.dumps(valid_bundle())])
    monkeypatch.setattr(service, "call_llm", call)
    monkeypatch.setattr(service, "MODEL_NAME", "gemini-3.5-flash-lite")
    result = service._generate_with_retry(
        "Generate questions", object(), "Backend Engineer", "Medium", "General", "", "", "role_based",
        question_list_count=5, retries=1, return_meta=True,
    )
    assert len(result["questions"]) == 5
    assert "question[1]" in call.call_args_list[1].args[0]
    assert "redis" in call.call_args_list[1].args[0]
