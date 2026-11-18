"""Standalone check of packaged provider transports; no real provider network."""

import json
import os
from pathlib import Path
import socket
import asyncio

os.environ.update(APP_ENV="test", LLM_PROVIDER="ollama", OLLAMA_MODEL="gemma4:cloud",
                  OLLAMA_HOST="https://ollama.com", OLLAMA_API_KEY="mock-only-not-a-real-provider-key",
                  OLLAMA_FALLBACK_TO_OPENROUTER="false", OPENROUTER_API_KEY="", GOOGLE_API_KEY="", XAI_API_KEY="",
                  BACKEND_API_SECRET="synthetic-artifact-secret", BACKEND_VISITOR_SIGNING_KEY="",
                  BACKEND_RATE_BACKEND="memory", BACKEND_RATE_LIMIT="1000", VERCEL_ENV="preview")
connect = socket.socket.connect


def guard(sock, address):
    if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
        return connect(sock, address)
    raise RuntimeError("External network prohibited")


socket.socket.connect = guard

from api.index import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
import mock_preview  # noqa: E402
import httpx  # noqa: E402
import requests  # noqa: E402

assert Path(mock_preview.__file__).parent == Path.cwd()
reply = mock_preview._output
attempts = []


def record(task, prompt):
    attempts.append(task)
    return reply(task, prompt)


mock_preview._output = record
headers = {"Authorization": "Bearer synthetic-artifact-secret"}
previous = []
with TestClient(app) as client:
    assert client.post("/api/interview/context", json={"role": "Backend Engineer"}).status_code == 401
    for index in range(1, 6):
        response = client.post("/api/interview/question", headers=headers, json={
            "role": "Backend Engineer", "question_index": index, "question_list_count": 5,
            "previous_questions": previous[-3:]})
        assert response.status_code == 200, response.text
        question = response.json()["questions"][0]["question"]
        assert question not in previous
        previous.append(question)
        response = client.post("/api/interview/evaluate", headers=headers, json={
            "question": question,
            "answer": "I would measure request latency, identify the bottleneck and verify the change with a representative test."})
        assert response.status_code == 200, response.text
        assert response.json()["follow_up"]["question"]
    assert client.post("/api/interview/example-answer", headers=headers, json={
        "answer": "I would measure request latency and verify the change with a representative test."}).status_code == 200

assert sum(task.startswith("question_generation.") for task in attempts) == 5
for url in ("https://ollama.com/api/chat", "https://openrouter.ai/api/v1/responses",
            "https://api.x.ai/v1/chat/completions", "https://generativelanguage.googleapis.com/v1/models"):
    for send in (lambda: requests.get(url), lambda: httpx.post(url)):
        try:
            send()
        except RuntimeError:
            pass
        else:
            raise AssertionError("External provider transport was not blocked")

async def check_async():
    async with httpx.AsyncClient(trust_env=False) as client:
        for url in ("https://ollama.com/api/chat", "https://openrouter.ai/api/v1/responses",
                    "https://api.x.ai/v1/chat/completions", "https://generativelanguage.googleapis.com/v1/models"):
            try:
                await client.post(url)
            except RuntimeError:
                pass
            else:
                raise AssertionError("Async provider transport was not blocked")
asyncio.run(check_async())
print(json.dumps({"questions": len(previous), "evaluations": 5, "questionAttempts": 5,
                  "exampleAnswer": True, "providerNetworkingBlocked": True}))
