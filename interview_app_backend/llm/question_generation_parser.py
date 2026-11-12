from __future__ import annotations

import json
import re
from collections.abc import Mapping
from collections import Counter


ALLOWED_QUESTION_TYPES = {"cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted"}
ALLOWED_SCENARIO_TYPES = {"debugging", "performance", "system_design", "behavioural", "scaling"}
QUESTION_TYPE_TO_SCENARIO_TYPE = {
    "cv_based": "debugging",
    "jd_based": "performance",
    "behavioural": "behavioural",
    "deep_dive": "system_design",
    "gap_targeted": "scaling",
}
EXPECTED_DISTRIBUTION_KEYS = ("cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted")
MIN_QUESTION_COUNT = 5
MAX_QUESTION_COUNT = 10


def _clean(value: object) -> str:
    return " ".join(str(value).split()).strip()


def _clean_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_clean(item) for item in value if _clean(item)]


def _clean_int(value: object) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _normalise_scenario_type(value: object, question_type: str) -> str:
    scenario_type = _clean(value).lower().replace("-", "_")
    if scenario_type in ALLOWED_SCENARIO_TYPES:
        return scenario_type
    question_type_key = _clean(question_type).lower().replace("-", "_")
    return QUESTION_TYPE_TO_SCENARIO_TYPE.get(question_type_key, "debugging")


def _strip_code_fences(payload: str) -> str:
    text = payload.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _question_text_from_item(item: object) -> str:
    if isinstance(item, Mapping):
        for key in ("question", "text", "prompt"):
            value = _clean(item.get(key, ""))
            if value:
                return value
    return _clean(item)


def extract_questions_with_regex(payload: object) -> list[str]:
    if not isinstance(payload, str):
        return []
    text = _strip_code_fences(payload)
    candidates: list[str] = []
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        match = re.match(r"^(?:[-*]|\d+[.)])\s*(.+)$", cleaned)
        if match:
            cleaned = match.group(1).strip()
        question_match = re.search(r"(.+?\?)", cleaned)
        if question_match:
            candidates.append(question_match.group(1).strip())
    return _clean_list(candidates)


def _normalise_meta(payload: object) -> dict[str, object] | None:
    if not isinstance(payload, Mapping):
        return None
    total_questions = _clean_int(payload.get("total_questions"))
    distribution = payload.get("distribution") if isinstance(payload.get("distribution"), Mapping) else None
    if total_questions is None or not (MIN_QUESTION_COUNT <= total_questions <= MAX_QUESTION_COUNT):
        return None
    if not distribution:
        return None

    normalised_distribution: dict[str, int] = {}
    for key in EXPECTED_DISTRIBUTION_KEYS:
        count = _clean_int(distribution.get(key))
        if count is None or count < 0:
            return None
        normalised_distribution[key] = count

    if sum(normalised_distribution.values()) != total_questions:
        return None

    return {"total_questions": total_questions, "distribution": normalised_distribution}


def extract_question_generation_meta(payload: object) -> dict[str, object] | None:
    raw: object = payload
    if isinstance(payload, str):
        text = _strip_code_fences(payload)
        raw = json.loads(text)
    if not isinstance(raw, Mapping):
        return None
    return _normalise_meta(raw.get("meta"))


def _infer_question_type(question: str) -> str:
    lowered = question.lower()
    if any(token in lowered for token in ("team", "stakeholder", "conflict", "collaborat", "communication")):
        return "behavioural"
    if any(token in lowered for token in ("design", "architecture", "scale", "scalability", "trade-off", "tradeoff")):
        return "deep_dive"
    if any(token in lowered for token in ("gap", "missing", "limited exposure", "close that gap")):
        return "gap_targeted"
    if any(token in lowered for token in ("job description", "role", "require", "expect")):
        return "jd_based"
    return "cv_based"


def _normalise_question_item(item: object, *, strict: bool = True, default_sequence_order: int | None = None) -> dict[str, object] | None:
    if not isinstance(item, Mapping):
        return None

    question = _question_text_from_item(item)
    if not question:
        return None
    question_type = _clean(item.get("question_type", item.get("type", "cv_based"))).lower().replace("-", "_")
    if question_type not in ALLOWED_QUESTION_TYPES:
        question_type = _infer_question_type(question)
    scenario_type = _normalise_scenario_type(item.get("scenario_type"), question_type)
    focus_area = _clean(item.get("focus_area", item.get("focus", "")))
    difficulty_level = _clean(item.get("difficulty_level", item.get("difficulty", "Medium")))
    what_interviewer_is_testing = _clean_list(item.get("what_interviewer_is_testing", item.get("testing", [])))
    sequence_order = _clean_int(item.get("sequence_order"))
    if sequence_order is None:
        sequence_order = default_sequence_order
    if strict and (not focus_area or not difficulty_level or not what_interviewer_is_testing or sequence_order is None):
        return None
    if not focus_area:
        focus_area = question_type.replace("_", " ")
    if not difficulty_level:
        difficulty_level = "Medium"
    if not what_interviewer_is_testing:
        what_interviewer_is_testing = [focus_area]
    if sequence_order is None:
        sequence_order = 1
    source_basis = item.get("source_basis") if isinstance(item.get("source_basis"), Mapping) else {}
    gap_used = source_basis.get("gap_used")
    if gap_used is None or gap_used == "":
        gap_used = None
    return {
        "question": question,
        "question_type": question_type,
        "scenario_type": scenario_type,
        "sequence_order": sequence_order,
        "focus_area": focus_area,
        "source_basis": {
            "cv_terms_used": _clean_list(source_basis.get("cv_terms_used", [])),
            "jd_terms_used": _clean_list(source_basis.get("jd_terms_used", [])),
            "gap_used": _clean(gap_used) if gap_used is not None else None,
        },
        "difficulty_level": difficulty_level,
        "what_interviewer_is_testing": what_interviewer_is_testing,
    }


def parse_question_generation_response(payload: object, *, strict: bool = True) -> list[dict[str, object]]:
    raw: object = payload
    meta: dict[str, object] | None = None
    if isinstance(payload, str):
        text = _strip_code_fences(payload)
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            if strict:
                return []
            raw = extract_questions_with_regex(text)
    if isinstance(raw, Mapping):
        meta = _normalise_meta(raw.get("meta"))
        if "questions" in raw:
            if strict and meta is None:
                return []
            raw = raw.get("questions", [])
        elif "meta" not in raw:
            raw = [raw]
        else:
            raw = []
            if strict and not raw:
                return []
    if not isinstance(raw, list):
        return []
    if strict and not (MIN_QUESTION_COUNT <= len(raw) <= MAX_QUESTION_COUNT):
        return []

    parsed: list[dict[str, object]] = []
    seen: set[str] = set()
    seen_orders: set[int] = set()
    for index, item in enumerate(raw, start=1):
        if isinstance(item, str) and not strict:
            item = {"question": item, "type": _infer_question_type(item), "focus": _infer_question_type(item)}
        question = _normalise_question_item(item, strict=strict, default_sequence_order=index)
        if not question:
            continue
        question_key = str(question["question"]).lower()
        sequence_order = int(question["sequence_order"])
        if question_key in seen or sequence_order in seen_orders:
            continue
        seen.add(question_key)
        seen_orders.add(sequence_order)
        parsed.append(question)

    if strict and len(parsed) < MIN_QUESTION_COUNT:
        return []

    parsed.sort(key=lambda item: int(item["sequence_order"]))

    if strict:
        sequence_orders = [int(item["sequence_order"]) for item in parsed]
        if sequence_orders != list(range(1, len(parsed) + 1)):
            return []
        if len(sequence_orders) != len(set(sequence_orders)):
            return []
        if meta is None:
            return []
        distribution = meta["distribution"]
        counts = Counter(str(item["question_type"]) for item in parsed)
        if len(parsed) != int(meta["total_questions"]):
            return []
        if any(int(distribution[key]) != counts.get(key, 0) for key in EXPECTED_DISTRIBUTION_KEYS):
            return []
    return parsed
