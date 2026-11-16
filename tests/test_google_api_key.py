import pytest
from config.settings import GOOGLE_API_KEY

pytestmark = pytest.mark.live


def test_google_api_key_is_set():
    """Test that Google API key is configured."""
    assert GOOGLE_API_KEY, "GOOGLE_API_KEY must be set in .env"
    assert len(GOOGLE_API_KEY) > 20, "GOOGLE_API_KEY seems too short"


def test_google_api_key_format():
    """Test that Google API key has expected format."""
    assert GOOGLE_API_KEY.startswith("AIzaSy"), "Google API key should start with AIzaSy"


def test_google_api_not_expired():
    """Test that Google API key is not expired (live test)."""
    pytest.importorskip("google.generativeai")
    import google.generativeai as genai

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    response = model.generate_content("Say OK")

    assert response.text, "Expected response text"
    assert "OK" in response.text.upper(), f"Expected OK in response, got: {response.text}"
