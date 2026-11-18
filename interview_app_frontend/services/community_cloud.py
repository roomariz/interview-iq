"""Configuration gate for the permanent mocked Community Cloud demonstration."""

from interview_app_frontend.services.api_client import _setting


MOCK_BACKEND_URL = "https://interviewiq-api-preview-28ndht991-roomas-projects.vercel.app"
DEMONSTRATION_NOTICE = (
    "Demonstration only — model responses are mocked. Questions, scores, feedback, "
    "confidence, follow-ups, sample answers and session summaries are illustrative, "
    "not a verified live AI assessment of your abilities. Use synthetic interview data."
)


def validate_configuration() -> None:
    if _setting("BACKEND_API_URL").rstrip("/") != MOCK_BACKEND_URL:
        raise ValueError("The demonstration requires the approved mocked Preview backend.")
    names = ("BACKEND_API_SECRET", "BACKEND_VISITOR_SIGNING_KEY", "VERCEL_AUTOMATION_BYPASS_SECRET")
    values = [_setting(name) for name in names]
    if any(not value or value.startswith("REPLACE_") for value in values):
        raise ValueError("The demonstration service connection is not configured.")
    if min(len(value.encode()) for value in values[:2]) < 32 or values[0] == values[1]:
        raise ValueError("The demonstration requires separate strong authentication secrets.")
