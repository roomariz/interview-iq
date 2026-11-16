"""Sanitised API errors, handled before server exception logging."""

from fastapi.routing import APIRoute
from fastapi import HTTPException
from pydantic import ValidationError
from httpx import TimeoutException
from openai import APITimeoutError, RateLimitError
from requests.exceptions import Timeout as RequestsTimeout

from api.security import error_response
from interview_app_backend.llm.deadline import check


def provider_error(exc):
    cause = exc
    seen = set()
    while cause is not None and id(cause) not in seen:
        seen.add(id(cause))
        if isinstance(cause, (TimeoutError, APITimeoutError, TimeoutException, RequestsTimeout)):
            return error_response(504, "timeout", "The provider took too long. Please try again.")
        if isinstance(cause, RateLimitError):
            return error_response(503, "provider_busy", "The provider is busy. Please try again later.")
        cause = cause.__cause__
    return error_response(502, "provider_failure", "Interview service unavailable. Please try again; no scores were recorded.")


class SafeRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request):
            try:
                result = await handler(request)
                check()
                return result
            except (HTTPException, ValidationError):
                raise
            except Exception as exc:
                # RequestValidationError belongs to FastAPI, not Pydantic ValidationError.
                from fastapi.exceptions import RequestValidationError
                if isinstance(exc, RequestValidationError):
                    raise
                return provider_error(exc)

        return safe_handler
