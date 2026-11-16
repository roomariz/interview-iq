import json
from unittest.mock import Mock

import pytest

from interview_app_backend.llm.question_contract import (
    QuestionValidationError, question_response_schema, request_contract, validate_question_response,
)
from interview_app_backend.llm.prompts.question_generation_prompt import build_question_generation_prompt
from interview_app_backend.services import question_service as service
from question_contract_fixtures import valid_bundle


def prompt():
    return build_question_generation_prompt("Backend Engineer", "Medium", "Friendly", "Concise", 0.7, "", "", {})


def generate(monkeypatch, responses):
    monkeypatch.setattr(service, "MODEL_NAME", "gemini-3.5-flash-lite")
    call = Mock(side_effect=responses)
    monkeypatch.setattr(service, "call_llm", call)
    result = service._generate_with_retry(
        prompt(), object(), "Backend Engineer", "Medium", "General", "", "", "role_based",
        question_list_count=5, retries=len(responses) - 1, return_meta=True,
    )
    return result, call


def test_prompt_has_one_unambiguous_exact_count():
    text = prompt()
    assert text.splitlines()[0].startswith("QUESTION_CONTRACT:")
    assert "Generate exactly 5" in text
    assert "Generate 5–10" not in text
    assert "For simpler models" not in text
    assert request_contract(text)["distribution"] == dict.fromkeys(valid_bundle()["meta"]["distribution"], 1)


@pytest.mark.parametrize("count", [0, 1, 2, 4, 6])
def test_partial_or_extra_response_is_rejected_with_exact_count(count):
    bundle = valid_bundle()
    bundle["questions"] = (bundle["questions"] * 2)[:count]
    with pytest.raises(QuestionValidationError, match=f"expected 5, received {count}"):
        validate_question_response(json.dumps(bundle), 5)


def test_schema_enforces_requested_count_and_distribution():
    schema = question_response_schema(prompt())
    assert schema["properties"]["questions"]["minItems"] == schema["properties"]["questions"]["maxItems"] == 5
    assert schema["$defs"]["QuestionMeta"]["properties"]["total_questions"]["minimum"] == 5
    assert schema["$defs"]["QuestionMeta"]["properties"]["total_questions"]["maximum"] == 5
    assert all(value["minimum"] == value["maximum"] == 1 for value in schema["$defs"]["QuestionDistribution"]["properties"].values())


@pytest.mark.parametrize("bad", ["{", "```json\n{}", "[]"])
def test_malformed_json_or_shape_is_rejected(bad):
    with pytest.raises(QuestionValidationError):
        validate_question_response(bad, 5)


def test_retry_requests_corrected_complete_bundle(monkeypatch):
    partial = valid_bundle()
    partial["questions"] = partial["questions"][:1]
    result, calls = generate(monkeypatch, [json.dumps(partial), json.dumps(valid_bundle())])
    assert len(result["questions"]) == 5
    corrected = calls.call_args_list[1].args[0]
    assert "invalid_question_count" in corrected
    assert "expected 5, received 1" in corrected
    assert "complete replacement" in corrected


def test_malformed_json_retry_keeps_reason(monkeypatch):
    result, calls = generate(monkeypatch, ["{", json.dumps(valid_bundle())])
    assert len(result["questions"]) == 5
    assert "invalid_json" in calls.call_args_list[1].args[0]


def test_role_only_allows_role_vocabulary_but_rejects_invented_tools():
    questions = valid_bundle()["questions"]
    assert service._validate_question_bundle(questions, role="Backend Engineer", cv_context="", jd_context="")[0]
    questions[0]["question"] += " Use Kubernetes?"
    assert service._validate_question_bundle(questions, role="Backend Engineer", cv_context="", jd_context="")[1] == "scenario_a_contains_tech"


def test_fallback_rejects_invalid_bundle_instead_of_returning_it(monkeypatch):
    questions = valid_bundle()["questions"]
    questions[0]["question"] += " Use Kubernetes?"
    monkeypatch.setattr(service, "_fallback_question_items", Mock(return_value=questions))
    with pytest.raises(RuntimeError, match="Fallback generation failed validation"):
        service.fallback_questions(role="Backend Engineer", difficulty="Medium", focus="General", cv_context="",
                                   jd_context="", question_type="role_based", previous_questions=[], question_plan=None)


def test_wrong_distribution_and_duplicates_do_not_pass():
    bundle = valid_bundle()
    bundle["questions"][1]["question"] = bundle["questions"][0]["question"]
    with pytest.raises(QuestionValidationError, match="duplicate_question"):
        validate_question_response(json.dumps(bundle), 5)

    bundle = valid_bundle()
    bundle["meta"]["distribution"]["cv_based"] = 2
    with pytest.raises(QuestionValidationError, match="invalid_distribution"):
        validate_question_response(json.dumps(bundle), 5)


def test_valid_existing_fallback_candidates_use_the_same_checks(monkeypatch):
    monkeypatch.setattr(service, "_fallback_question_items", Mock(return_value=valid_bundle()["questions"]))
    items = service.fallback_questions(role="Backend Engineer", difficulty="Medium", focus="General", cv_context="",
                                       jd_context="", question_type="role_based", previous_questions=[], question_plan=None)
    assert len(items) == 5
    assert [item["sequence_order"] for item in items] == list(range(1, 6))


def test_role_irrelevance_is_not_accepted(monkeypatch):
    bundle = valid_bundle()
    bundle["questions"][0]["question"] = "A user asks about a garden's flower colours. How would you pick a bouquet for the display?"
    monkeypatch.setattr(service, "_fallback_question_items", Mock(return_value=[]))
    with pytest.raises(RuntimeError):
        generate(monkeypatch, [json.dumps(bundle)])


def test_single_request_has_a_single_question_contract(monkeypatch):
    monkeypatch.setattr(service, "MODEL_NAME", "gemini-3.5-flash-lite")
    text = service.build_question_prompt("Backend Engineer", "Medium", "Friendly", "Concise", "", question_count=1)
    assert request_contract(text)["count"] == 1
    assert "Generate exactly 1" in text


def test_candidate_source_metadata_is_not_lost_in_filter(monkeypatch):
    item = valid_bundle()["questions"][0]
    item["source_basis"]["cv_terms_used"] = ["Python"]
    item["question"] = "Your Python backend API has a regression in your application. How would you investigate the root cause?"
    filtered = service._filter_question_items([item], role="Backend Engineer", difficulty="Medium", focus="General",
                                             cv_context="Python", jd_context="", question_type="cv_based", previous_questions=[], required_count=1)
    assert filtered[0]["source_basis"] == item["source_basis"]


def test_missing_question_fields_are_reported_precisely():
    bundle = valid_bundle()
    del bundle["questions"][0]["source_basis"]
    with pytest.raises(QuestionValidationError, match="questions.0.source_basis"):
        validate_question_response(json.dumps(bundle), 5)


def test_source_terms_must_exist_in_the_provided_document():
    questions = valid_bundle()["questions"]
    questions[0]["source_basis"]["jd_terms_used"] = ["Kubernetes"]
    valid, reason = service._validate_question_bundle(questions, role="Backend Engineer", cv_context="", jd_context="API work")
    assert valid is False
    assert reason == "unsupported_jd_source_terms"
