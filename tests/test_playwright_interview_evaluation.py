from __future__ import annotations

"""E2E browser tests.

These require local Chromium with sandbox support and will fail in restricted CI
or sandboxed environments.
"""

import os
import re
import subprocess
import sys
import textwrap
import time
import socket
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.e2e

ROOT = Path(__file__).resolve().parents[1]
QUESTION = (
    "Describe a time you improved system performance under constraints. "
    "Include the challenge, your approach, and measurable results."
)
CASES = [
    {
        "name": "out_of_scope",
        "answer": "In my previous role, I worked on improving team collaboration by introducing better documentation practices...",
        "outcome": "FAIL",
        "confidence": "Low",
        "assessment": "Off-topic answer",
        "must_contain": [],
        "must_not_contain": ["caching", "latency improvement", "trade-offs"],
    },
    {
        "name": "ok",
        "answer": "I worked on a backend service where performance was getting slower...",
        "outcome": "BORDERLINE PASS",
        "confidence": "Medium",
        "assessment": "Limited evidence",
        "must_contain": ["missing metrics", "weak structure"],
        "must_not_contain": ["strong metrics"],
    },
    {
        "name": "good",
        "answer": "I worked on a real-time transaction service where latency increased...",
        "outcome": "PASS",
        "confidence": "Medium",
        "assessment": "Limited evidence",
        "must_contain": [],
        "must_not_contain": ["off-topic", "fail"],
    },
    {
        "name": "best",
        "answer": "I worked on a backend service handling real-time transactions where latency increased from around 120ms to 400ms...",
        "outcome": "PASS",
        "confidence": "High",
        "assessment": "Strong evidence",
        "must_contain": [],
        "must_not_contain": ["borderline", "fail"],
    },
]

FULL_JOURNEY_CASES = [
    {
        "name": "out_of_scope",
        "answer": "I improved team collaboration by introducing better documentation practices and meeting cadences.",
        "outcome": "FAIL",
        "confidence": "Low",
        "assessment": "Off-topic answer",
        "label": "Off-topic",
        "must_contain": ["off-topic", "relevant to the question"],
        "must_not_contain": ["caching", "latency", "trade-off", "metrics"],
    },
    {
        "name": "weak",
        "answer": "I improved the backend service and made it faster, but I do not have the metrics to share.",
        "outcome": "BORDERLINE PASS",
        "confidence": "Medium",
        "assessment": "Limited evidence",
        "label": "Borderline",
        "must_contain": ["missing metrics", "weak structure"],
        "must_not_contain": ["caching", "120ms", "400ms"],
    },
    {
        "name": "good",
        "answer": "I worked on a real-time transaction service where latency increased. I profiled the system, narrowed the issue, and reduced response time.",
        "outcome": "PASS",
        "confidence": "Medium",
        "assessment": "Limited evidence",
        "label": "Pass",
        "must_contain": ["latency", "reasoning"],
        "must_not_contain": ["off-topic", "fail", "caching"],
    },
    {
        "name": "best",
        "answer": "I worked on a backend service handling real-time transactions where latency increased from around 120ms to 400ms. I profiled the system, found the bottleneck, and reduced the response time by 75%.",
        "outcome": "PASS",
        "confidence": "High",
        "assessment": "Strong evidence",
        "label": "Pass",
        "must_contain": ["120ms", "400ms", "trade-off"],
        "must_not_contain": ["borderline", "fail", "caching"],
    },
]


def _wait_for_server(base_url: str) -> None:
    deadline = time.monotonic() + 60
    for path in ("/_stcore/health", "/healthz", "/"):
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"{base_url}{path}", timeout=2) as response:
                    body = response.read().decode("utf-8", errors="ignore").lower()
                    if response.status < 500 and (path != "/" or "streamlit" in body or "ok" in body):
                        return
            except (urllib.error.URLError, OSError):
                time.sleep(1)
                continue
    raise RuntimeError("Streamlit app did not become ready in time.")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def app_server(tmp_path_factory):
    port = _free_port()
    sitecustomize_dir = tmp_path_factory.mktemp("sitecustomize")
    (sitecustomize_dir / "sitecustomize.py").write_text(
        "from tests.playwright_evaluation_mock import patch\npatch()\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(sitecustomize_dir), str(ROOT)])
    env.pop("OPENROUTER_API_KEY", None)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.headless",
            "true",
            "--server.address",
            "127.0.0.1",
            "--server.port",
            str(port),
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    _wait_for_server(base_url)
    yield base_url
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def page(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 1600})
    context.set_default_timeout(60000)
    page = context.new_page()
    yield page
    context.close()


def submit_answer(page, base_url: str, answer: str) -> None:
    page.set_default_timeout(10000)
    page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    page.goto(f"{base_url}/?screen=question", wait_until="domcontentloaded", timeout=30000)
    page.get_by_role("heading", name=re.compile("Question", re.IGNORECASE)).wait_for(state="visible", timeout=15000)
    answer_box = page.locator("textarea").first
    answer_box.wait_for(state="visible", timeout=15000)
    answer_box.fill(answer)
    answer_box.press("Tab")
    page.get_by_role("button", name="Submit Answer").click()
    page.get_by_text("Overall Outcome").wait_for(state="visible", timeout=15000)


def get_outcome(page) -> str:
    return page.locator(".feedback-outcome__value").inner_text().strip()


def get_reliability(page) -> dict[str, str]:
    text = page.locator(".feedback-reliability").inner_text().strip()
    return {
        "confidence": _extract(text, "Confidence"),
        "assessment": _extract(text, "Assessment"),
        "grounding": _extract(text, "Grounding"),
        "text": text,
    }


def get_feedback_text(page) -> str:
    parts = []
    for selector in (".feedback-card", ".feedback-trust", ".feedback-key-takeaway", ".feedback-consistency"):
        locator = page.locator(selector)
        if locator.count():
            parts.append(locator.first.inner_text())
    return "\n".join(parts).lower()


def get_reasoning_text(page) -> str:
    locator = page.locator(".feedback-panel--reasoning")
    return locator.first.inner_text().lower() if locator.count() else ""


def get_follow_up_text(page) -> str:
    locator = page.locator(".feedback-follow-up, .feedback-followup, .follow-up")
    return locator.first.inner_text().lower() if locator.count() else ""


def _extract(text: str, label: str) -> str:
    marker = f"{label}:"
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].splitlines()[0].strip()


@pytest.mark.e2e
@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_interview_evaluation_cases(page, app_server, case):
    submit_answer(page, app_server, case["answer"])
    outcome = get_outcome(page).upper()
    reliability = get_reliability(page)
    feedback_text = get_feedback_text(page)

    assert case["outcome"] in outcome
    assert case["confidence"].lower() in reliability["confidence"].lower()
    assert case["assessment"].lower() in reliability["assessment"].lower()
    for token in case["must_contain"]:
        assert token in feedback_text
    for token in case["must_not_contain"]:
        assert token not in feedback_text
    page.screenshot(path=str(ROOT / f"debug_{case['name']}.png"))
    if case["name"] in {"good", "best"}:
        reasoning_text = get_reasoning_text(page)
        assert "reason" in reasoning_text or "trade-off" in reasoning_text
        assert "latency" in reasoning_text or "ms" in reasoning_text
        if case["name"] == "best":
            assert "120ms" in reasoning_text
            assert "400ms" in reasoning_text


@pytest.mark.e2e
@pytest.mark.parametrize("case", FULL_JOURNEY_CASES, ids=[case["name"] for case in FULL_JOURNEY_CASES])
def test_full_journey_end_to_end(page, app_server, case):
    submit_answer(page, app_server, case["answer"])

    outcome = get_outcome(page).upper()
    reliability = get_reliability(page)
    feedback_text = get_feedback_text(page)
    reasoning_text = get_reasoning_text(page)
    follow_up_text = get_follow_up_text(page)

    assert case["outcome"] in outcome
    assert case["confidence"].lower() in reliability["confidence"].lower()
    assert case["assessment"].lower() in reliability["assessment"].lower()
    assert case["label"].lower() in page.locator("body").inner_text().lower()

    for token in case["must_contain"]:
        assert token in feedback_text or token in reasoning_text or token in follow_up_text

    for token in case["must_not_contain"]:
        assert token not in feedback_text
        assert token not in reasoning_text
        assert token not in follow_up_text
    page.screenshot(path=str(ROOT / f"debug_full_{case['name']}.png"))

    if case["name"] == "out_of_scope":
        assert "technical" not in feedback_text
        assert "caching" not in page.locator("body").inner_text().lower()
    if case["name"] == "weak":
        assert "borderline" in outcome.lower() or "weak" in reliability["assessment"].lower()
        assert "metric" in feedback_text
    if case["name"] == "good":
        assert "pass" in outcome.lower()
        assert "medium" in reliability["confidence"].lower()
    if case["name"] == "best":
        assert "high" in reliability["confidence"].lower()
        assert "trade-off" in reasoning_text or "trade off" in reasoning_text
        assert "caching" not in feedback_text
