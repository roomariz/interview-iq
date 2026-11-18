"""Permanent test-only transport injection for the isolated Preview artifact."""

from contextvars import ContextVar
import json
import os
from deployment.mock_questions import REQUEST, bind_request, question_bundle
from urllib.parse import urlsplit

import httpx
import requests

ACTIVE = ContextVar("preview_fixture_task", default="")
INSTALLED = False


def _inputs(prompt):
    if "\nInput:\n" in prompt:
        data = json.loads(prompt.rsplit("\nInput:\n", 1)[1])
        return data.get("question", ""), data.get("answer", "")
    return (prompt.rsplit("\nQuestion:\n", 1)[1].split("\n\nAnswer:\n", 1)[0],
            prompt.rsplit("\nAnswer:\n", 1)[1])


def _output(task, prompt):
    if task.startswith("question_generation."):
        return question_bundle(REQUEST.get())
    if task == "evaluation.relevance_check":
        question, answer = _inputs(prompt)
        return {"status": "relevant", "confidence": .95, "question_type": "scenario_troubleshooting",
                "reason": "Synthetic fixture for diagnostic evidence and verification.",
                "question_quote": question, "answer_quote": answer}
    if task == "evaluation.evidence_extraction":
        return {"has_metrics": False, "has_structure": True, "has_reasoning": True,
                "has_tradeoffs": False, "has_alternatives": False,
                "confidence": {"metrics": .1, "structure": .9, "reasoning": .9,
                               "tradeoffs": .1, "alternatives": .1}, "anomaly_flags": []}
    if task in {"evaluation.scoring", "evaluation.feedback_repair"}:
        question, answer = _inputs(prompt)
        claim = "You identify diagnostic evidence and verify the change."
        output = {"feedback": {"summary": "Synthetic coaching based on the submitted diagnostic plan.",
                               "strengths": [claim], "key_issues": [], "improvements": []},
                  "feedback_support": [{"claim": claim, "question_quote": question, "answer_quote": answer}]}
        if task == "evaluation.scoring":
            output.update(scores=dict.fromkeys(("technical_accuracy", "clarity", "relevance", "structure",
                                                "specificity", "communication", "problem_solving_approach"), 7),
                          evidence={"metrics": [], "actions": ["identify the bottleneck"],
                                    "reasoning": "verify the change"})
        return output
    if task == "evaluation.reference_answer":
        return "Measure latency, identify the bottleneck and verify the change with a representative test."
    if task == "evaluation.semantic_similarity":
        return "0.88"
    if task == "evaluation.example_answer":
        return prompt.rsplit("Original answer:\n", 1)[1].strip()
    raise RuntimeError("Unsupported synthetic fixture task")


def _post(url, **kwargs):
    if url != "https://ollama.com/api/chat":
        raise RuntimeError("External provider networking is disabled in this fixture")
    task = ACTIVE.get()
    prompt = kwargs["json"]["messages"][-1]["content"]
    if "PREVIEW_DEADLINE_CHECK" in prompt:
        from interview_app_backend.llm.deadline import pause
        pause(151)
    if "PREVIEW_PROVIDER_ERROR" in prompt:
        # Preserve real provider retry/error handling while returning a synthetic outage.
        status, data = 503, {"error": "Synthetic provider outage"}
    else:
        value = _output(task, prompt)
        text = value if isinstance(value, str) else json.dumps(value)
        status, data = 200, {"message": {"content": text}, "done": True}
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(data).encode()
    return response


def install():
    global INSTALLED
    if INSTALLED:
        return
    if os.getenv("VERCEL_ENV") not in {None, "preview"}:
        raise RuntimeError("This artifact is restricted to Preview")
    # A valid provider key would be unnecessary exposure in a synthetic build.
    if os.getenv("OLLAMA_API_KEY") != "mock-only-not-a-real-provider-key":
        raise RuntimeError("The mocked artifact requires its dummy provider key")
    if any(os.getenv(key) for key in ("OPENROUTER_API_KEY", "XAI_API_KEY", "GOOGLE_API_KEY")):
        raise RuntimeError("Live provider keys are forbidden in this artifact")
    if os.getenv("LLM_PROVIDER") != "ollama" or os.getenv("OLLAMA_FALLBACK_TO_OPENROUTER") != "false":
        raise RuntimeError("The mocked artifact requires Ollama selection without fallback")
    allowed = urlsplit(os.getenv("UPSTASH_REDIS_REST_URL", ""))
    origin = (allowed.scheme, allowed.hostname, allowed.port or 443)

    def check(request):
        url = request.url
        if (url.scheme, url.host, url.port or 443) != origin or request.method != "POST":
            raise RuntimeError("Outbound HTTP is restricted to the configured Redis service")

    sync = httpx.HTTPTransport.handle_request
    asynchronous = httpx.AsyncHTTPTransport.handle_async_request

    def guarded_sync(transport, request):
        check(request)
        return sync(transport, request)

    async def guarded_async(transport, request):
        check(request)
        return await asynchronous(transport, request)

    def blocked(*args, **kwargs):
        raise RuntimeError("External provider networking is disabled in this fixture")

    httpx.HTTPTransport.handle_request = guarded_sync
    httpx.AsyncHTTPTransport.handle_async_request = guarded_async
    requests.sessions.Session.request = blocked
    requests.post = _post
    from interview_app_backend.llm.ollama_client import OllamaCloudClient
    original = OllamaCloudClient.call

    def call(client, prompt, temperature, task, should_abort=None):
        token = ACTIVE.set(task or "general")
        try:
            return original(client, prompt, temperature, task, should_abort)
        finally:
            ACTIVE.reset(token)

    OllamaCloudClient.call = call
    from interview_app_backend.services import question_service
    question_service.get_next_question_for_session = bind_request(question_service.get_next_question_for_session)
    INSTALLED = True
