"""Opt-in real Redis verification using two independent backend processes.

Requires securely configured UPSTASH_REDIS_REST_URL and TOKEN in the environment.
Makes synthetic context requests only; never invokes an LLM. Quota keys expire.
"""

import concurrent.futures
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import uuid

import httpx


ROOT = Path(__file__).resolve().parents[1]


def unused_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def start_backend(environment):
    port = unused_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.index:app", "--host", "127.0.0.1", "--port", str(port),
         "--no-access-log", "--log-level", "critical"], cwd=ROOT, env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError("Verification backend did not start")
            try:
                if httpx.get(url + "/api/health", timeout=0.5, trust_env=False).status_code == 200:
                    return process, url
            except httpx.RequestError:
                pass
            time.sleep(0.1)
        raise RuntimeError("Verification backend startup timed out")
    except BaseException:
        stop_backend(process)
        raise


def stop_backend(process):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def verify():
    url = os.getenv("UPSTASH_REDIS_REST_URL", "")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
    if not url or not token:
        raise RuntimeError("Configure Redis REST URL and token securely before verification")
    # Do not pass the parent's provider keys, private .env or unrelated secrets.
    environment = {key: value for key, value in os.environ.items()
                   if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "HOME", "USERPROFILE"}}
    secret = secrets.token_urlsafe(48)
    environment.update(APP_ENV="production", LLM_PROVIDER="ollama", OLLAMA_API_KEY="unused-verification-key",
                       BACKEND_API_SECRET=secret, BACKEND_RATE_BACKEND="redis", BACKEND_RATE_LIMIT="4",
                       BACKEND_RATE_NAMESPACE="iqverify-" + uuid.uuid4().hex, BACKEND_REQUEST_DEADLINE="10",
                       UPSTASH_REDIS_REST_URL=url, UPSTASH_REDIS_REST_TOKEN=token)
    processes = []
    try:
        for _ in range(2):
            processes.append(start_backend(environment))
        urls = [item[1] for item in processes]

        def context_request(index, authenticated=True):
            headers = {"Authorization": f"Bearer {secret}"} if authenticated else {}
            return httpx.post(urls[index % 2] + "/api/interview/context", json={"role": "Backend Engineer"},
                              headers=headers, timeout=15, trust_env=False)

        unauthorised = context_request(0, False)
        assert unauthorised.status_code == 401, "Authentication check failed"
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(context_request, range(8)))
        statuses = sorted(response.status_code for response in responses)
        assert statuses == [200] * 4 + [429] * 4, "Combined quota or Redis connectivity failed"
        assert all(1 <= int(response.headers["Retry-After"]) <= 60 for response in responses
                   if response.status_code == 429), "Retry-After check failed"
        assert all(secret not in response.text and token not in response.text for response in responses)
        outage = dict(environment, UPSTASH_REDIS_REST_URL=f"https://127.0.0.1:{unused_port()}",
                      UPSTASH_REDIS_REST_TOKEN="unused-outage-token")
        process, outage_url = start_backend(outage)
        processes.append((process, outage_url))
        response = httpx.post(outage_url + "/api/interview/context", json={"role": "Backend Engineer"},
                              headers={"Authorization": f"Bearer {secret}"}, timeout=15, trust_env=False)
        assert response.status_code == 503, "Redis outage did not fail closed"
        print("PASS: two processes; 4 admitted, 4 rate-limited; Retry-After, auth and outage checks passed")
        print("No LLM calls. Synthetic quota key expires within 60 seconds.")
    finally:
        for process, _ in processes:
            stop_backend(process)


if __name__ == "__main__":
    try:
        verify()
    except Exception as exc:
        # Neither tracebacks nor upstream exception strings may expose credentials.
        print(f"Redis verification failed ({type(exc).__name__}); check configuration and connectivity.")
        sys.exit(1)
