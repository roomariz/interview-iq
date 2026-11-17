"""Server-to-server HTTP only; no provider credentials or automatic POST retries."""

import os
from typing import TypeVar
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ValidationError

from shared.api_contracts import (
    ContextRequest, ContextResponse, EvaluationRequest, EvaluationResponse,
    ExampleRequest, ExampleResponse, QuestionRequest, QuestionResponse,
)

Response = TypeVar("Response", bound=BaseModel)


class BackendError(RuntimeError):
    """Contains only safe, frontend-owned messages."""


def _setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value
    # Streamlit secrets are read on the script thread when constructing the client.
    try:
        import streamlit as st
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, RuntimeError):
        return default


class InterviewAPIClient:
    def __init__(self, base_url=None, secret=None, timeout=None, transport=None):
        self.base_url = (base_url or _setting("BACKEND_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.secret = secret if secret is not None else _setting("BACKEND_API_SECRET")
        parsed = urlsplit(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise BackendError("The backend address is not configured correctly.")
        if parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise BackendError("The remote backend requires HTTPS.")
        self.timeout = float(timeout if timeout is not None else _setting("BACKEND_API_TIMEOUT", "180"))
        self.transport = transport
        self.preview_bypass = _setting("VERCEL_AUTOMATION_BYPASS_SECRET")
        from interview_app_frontend.services.visitor import session_token
        self.visitor = session_token(_setting("BACKEND_VISITOR_SIGNING_KEY"))

    def _post(self, path: str, payload: BaseModel, response: type[Response]) -> Response:
        if not self.secret:
            raise BackendError("The interview service connection is not configured.")
        headers = {"Authorization": f"Bearer {self.secret}"}
        if self.visitor:
            headers["X-Interview-Visitor"] = self.visitor
        if self.preview_bypass:
            headers["x-vercel-protection-bypass"] = self.preview_bypass
        try:
            with httpx.Client(base_url=self.base_url, timeout=httpx.Timeout(self.timeout, connect=5),
                              transport=self.transport, follow_redirects=False, trust_env=False) as client:
                result = client.post(path, json=payload.model_dump(), headers=headers)
            if result.status_code != 200:
                messages = {
                    401: "The interview service connection is not authorised.",
                    413: "The interview context is too large. Please shorten your CV or job description.",
                    422: "Please check the interview inputs and their lengths.",
                    429: "Please wait before trying again.",
                    503: "The interview service is busy or unavailable. Please try again later.",
                    504: "The provider took too long. Please try again.",
                }
                raise BackendError(messages.get(result.status_code, "Interview service unavailable. Please try again."))
            if len(result.content) > 1048576:
                raise BackendError("The interview service returned an invalid response.")
            return response.model_validate(result.json())
        except httpx.TimeoutException:
            raise BackendError("The interview service took too long. Please try again.") from None
        except httpx.RequestError:
            raise BackendError("Cannot connect to the interview service. Please try again shortly.") from None
        except (ValidationError, ValueError):
            raise BackendError("The interview service returned an invalid response.") from None

    def context(self, **kwargs) -> dict:
        return self._post("/api/interview/context", ContextRequest(**kwargs), ContextResponse).model_dump()

    def question(self, **kwargs) -> dict:
        request = QuestionRequest(**kwargs)
        result = self._post("/api/interview/question", request, QuestionResponse)
        if len(result.questions) != request.question_list_count:
            raise BackendError("The interview service returned an incomplete questionnaire.")
        return result.model_dump()

    def evaluate(self, question: str, answer: str) -> dict:
        return self._post("/api/interview/evaluate", EvaluationRequest(question=question, answer=answer),
                          EvaluationResponse).model_dump()

    def example(self, answer: str) -> str:
        return self._post("/api/interview/example-answer", ExampleRequest(answer=answer), ExampleResponse).text


def evaluate_submission(question: str, answer: str) -> dict:
    return InterviewAPIClient().evaluate(question, answer)


def generate_example_answer(answer: str) -> str:
    return InterviewAPIClient().example(answer)
