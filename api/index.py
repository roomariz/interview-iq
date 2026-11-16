from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.interview import router
from api.security import InterviewSecurity, error_response
from api.errors import provider_error

app = FastAPI(title="InterviewIQ API")
app.add_middleware(InterviewSecurity)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    return error_response(422, "validation", "Please check the interview inputs and their lengths.")


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    messages = {404: "Endpoint not found.", 405: "Method not allowed.",
                422: "Please check the interview inputs and question count.",
                502: "The provider returned an invalid result. Please try again."}
    return error_response(exc.status_code, "request_failed", messages.get(exc.status_code, "Request failed."))


@app.exception_handler(Exception)
@app.exception_handler(ValidationError)
@app.exception_handler(ResponseValidationError)
async def service_error(request, exc):
    return provider_error(exc)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
