"""Read-only configured Redis preflight; no model or quota-writing requests."""

import asyncio
import json
import os
import secrets

import httpx


def verify():
    if not all(os.getenv(k) for k in ("UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN")):
        raise RuntimeError("Configured Redis credentials are required")
    # Only this short-lived process receives these synthetic provider settings.
    os.environ.update(APP_ENV="production", VERCEL_ENV="preview", LLM_PROVIDER="open-router",
                      IS_FREE_MODE="true", MODEL_NAME="google/gemma-4-31b-it:free",
                      OPENROUTER_API_KEY="synthetic-preflight-key", OLLAMA_API_KEY="", GOOGLE_API_KEY="", XAI_API_KEY="",
                      OLLAMA_FALLBACK_TO_OPENROUTER="false", BACKEND_RATE_BACKEND="redis",
                      BACKEND_RATE_NAMESPACE="interviewiq-mocked-preview", BACKEND_RATE_LIMIT="30",
                      BACKEND_GLOBAL_DAILY_LIMIT="1000", BACKEND_VISITOR_RATE_LIMIT="10",
                      BACKEND_VISITOR_DAILY_LIMIT="100", BACKEND_MAX_CONCURRENT="4",
                      BACKEND_INGRESS_RATE_LIMIT="300", LLM_TIMEOUT="60", BACKEND_REQUEST_DEADLINE="150",
                      BACKEND_API_SECRET=secrets.token_urlsafe(48), BACKEND_VISITOR_SIGNING_KEY=secrets.token_urlsafe(48))
    from deployment.phase5_redis import endpoint_url
    from deployment.phase5_transport import install
    install()
    root = endpoint_url()
    headers = {"Authorization": "Bearer " + os.environ["UPSTASH_REDIS_REST_TOKEN"]}
    statuses = []
    # Exercise both representations through the actual installed sync/async
    # guards. PING reads availability/authentication without changing Redis keys.
    with httpx.Client(timeout=10, trust_env=False, follow_redirects=False) as client:
        for url in (root.rstrip("/"), root):
            response = client.post(url, headers=headers, json=["PING"])
            response.raise_for_status()
            if response.json() != {"result": "PONG"}:
                raise RuntimeError("Redis preflight response refused")
            statuses.append(response.status_code)

    async def check_async():
        async with httpx.AsyncClient(timeout=10, trust_env=False, follow_redirects=False) as client:
            for url in (root.rstrip("/"), root):
                response = await client.post(url, headers=headers, json=["PING"])
                response.raise_for_status()
                if response.json() != {"result": "PONG"}:
                    raise RuntimeError("Redis preflight response refused")
                statuses.append(response.status_code)

    asyncio.run(check_async())
    return {"syncRootVariants": "passed", "asyncRootVariants": "passed", "httpStatuses": statuses,
            "requests": 4, "commands": "PING only", "modelCalls": 0, "quotaKeysChanged": False}


if __name__ == "__main__":
    try:
        print(json.dumps(verify()))
    except Exception as exc:
        # Exception strings from HTTP clients can contain the private Redis URL.
        print(json.dumps({"preflight": "failed", "errorType": type(exc).__name__}))
        raise SystemExit(1) from None
