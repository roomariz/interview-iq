"""Deterministic, request-aware questions for the isolated mocked Preview only."""

from contextvars import ContextVar
from functools import wraps

from interview_app_backend.llm.question_contract import QUESTION_TYPES, SCENARIO_TYPES, distribution_for

REQUEST = ContextVar("mock_question_request", default=None)

QUESTIONS = (
    (
        "Your application has a backend regression after a routine release. What evidence would you gather to isolate its cause?",
        "An API endpoint intermittently returns empty records although storage contains them. Which checks distinguish routing errors from faulty filtering?",
        "During deployment, service startup fails only when configuration comes from the environment. How can you isolate the offending setting?",
        "A colleague reports that cancelled API transactions still trigger notifications. Where can you inspect event ordering to identify the incorrect boundary?",
        "Your server crashes when two API updates arrive together. What experiment could reveal unsafe access to shared state?",
    ),
    (
        "A user reports that your backend workflow becomes slow during busy periods. How would you measure and improve performance safely?",
        "Your API endpoint spends most of its response time waiting for a connection. Which measurements distinguish saturation from a slow query?",
        "The service becomes slow as a cache fills. What profiling experiment can separate eviction overhead from computation?",
        "A colleague notices slow database throughput during backups. How can you compare competing workloads before adjusting schedules?",
        "Your API upload takes minutes even for small files. Which timings can locate buffering or transfer delays?",
    ),
    (
        "Tell me about a time your backend team disagreed about delivery priorities. What did you do to resolve the conflict?",
        "Describe a time you explained an API reliability risk to a nontechnical stakeholder. How did the discussion affect their decision?",
        "Walk me through an occasion when a service incident exposed a communication gap. Which action helped colleagues coordinate recovery?",
        "Give an example of mentoring someone who struggled with database troubleshooting. What adjustment made the guidance useful?",
        "Tell me about receiving difficult feedback on an API proposal. How did you decide what to revise?",
    ),
    (
        "A colleague asks you to design your application for a growing backend workload. Which trade-offs would guide your decision?",
        "Design an API contract for a client that must work offline. How can synchronisation handle conflicting edits?",
        "Architect a service that processes jobs after the caller disconnects. Which reliability guarantees belong at each boundary?",
        "Your database serves tenants with different isolation requirements. What design balances separation with operational effort?",
        "An API must evolve without breaking older clients. Which versioning trade-offs guide a safe migration?",
    ),
    (
        "Stakeholders report that your application cannot keep up with requests. How would you coordinate the backend team and scale the workflow?",
        "Your API cannot accept a sudden surge of imports. What capacity controls can protect interactive traffic while workers catch up?",
        "A service outage affects one region while demand grows elsewhere. How can you distribute work without losing queued tasks?",
        "Your database cannot fit a growing archive on one machine. Which partition boundaries support expansion and predictable retrieval?",
        "Your API consumer overwhelms shared capacity during a campaign. How can admission policies keep other customers responsive?",
    ),
)


def bind_request(generate):
    @wraps(generate)
    def bound(*args, **kwargs):
        token = REQUEST.set(kwargs)
        try:
            return generate(*args, **kwargs)
        finally:
            REQUEST.reset(token)
    return bound


def question_bundle(request):
    if request is None:
        raise RuntimeError("Mock questions require an explicit request context")
    count = request.get("question_list_count", 1)
    index = request.get("question_index", 1) - 1
    if count not in {1, 5} or not 0 <= index < 5:
        raise RuntimeError("The mocked demonstration supports five interview steps")
    from interview_app_backend.services import question_service as service

    role = request.get("role", "Backend Engineer")
    cv, jd = request.get("cv_context", ""), request.get("jd_context", "")
    context = service.resolve_missing_context(role, cv, jd)
    terms = [min(service._extract_role_keywords(role), key=len)]
    for text in (cv, jd):
        keywords = service._extract_context_keywords(text)
        if keywords:
            terms.append(keywords[0])
    context_hint = " / ".join(dict.fromkeys(terms))
    distribution = distribution_for(count, request.get("question_type", "cv_based"))
    kinds = list(QUESTION_TYPES) if count == 5 else [next(key for key,value in distribution.items() if value)]
    items = []
    for order, kind in enumerate(kinds, 1):
        scenario = SCENARIO_TYPES[QUESTION_TYPES.index(kind)]
        text = QUESTIONS[SCENARIO_TYPES.index(scenario)][index]
        items.append({"sequence_order": order, "question": text[:-1] + " for " + context_hint + "?",
                      "question_type": kind, "scenario_type": scenario, "focus_area": scenario,
                      "difficulty_level": request.get("difficulty", "Medium"),
                      "source_basis": {"cv_terms_used": context["cv_keywords"],
                                       "jd_terms_used": context["jd_keywords"], "gap_used": None},
                      "what_interviewer_is_testing": [scenario]})
    return {"meta": {"total_questions": count, "distribution": distribution}, "questions": items}
