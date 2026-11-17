"""Environment-specific configuration; production never uses local quotas."""

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class BackendConfig:
    environment: str
    deadline: float
    rate_backend: str
    rate_limit: int
    max_concurrent: int
    redis_url: str
    redis_token: str
    namespace: str
    visitor_key: str = ""
    visitor_rate: int = 10
    visitor_day: int = 100
    global_day: int = 1000
    ingress_rate: int = 300

    @classmethod
    def load(cls):
        environment = os.getenv("APP_ENV", "production" if os.getenv("VERCEL") else "local")
        if os.getenv("VERCEL") and environment != "production":
            raise ValueError("Vercel requires production controls")
        if environment not in {"local", "test", "production"}:
            raise ValueError("Invalid APP_ENV")
        backend = os.getenv("BACKEND_RATE_BACKEND", "redis" if environment == "production" else "memory")
        deadline = float(os.getenv("BACKEND_REQUEST_DEADLINE", "150"))
        rate = int(os.getenv("BACKEND_RATE_LIMIT", "30"))
        concurrent = int(os.getenv("BACKEND_MAX_CONCURRENT", "4"))
        visitor_key = os.getenv("BACKEND_VISITOR_SIGNING_KEY", "")
        visitor_rate = int(os.getenv("BACKEND_VISITOR_RATE_LIMIT", "10"))
        visitor_day = int(os.getenv("BACKEND_VISITOR_DAILY_LIMIT", "100"))
        global_day = int(os.getenv("BACKEND_GLOBAL_DAILY_LIMIT", "1000"))
        ingress_rate = int(os.getenv("BACKEND_INGRESS_RATE_LIMIT", "300"))
        if min(visitor_rate, visitor_day, global_day, ingress_rate) < 1:
            raise ValueError("Invalid anonymous limits")
        if visitor_key and (len(visitor_key.encode()) < 32 or visitor_key == os.getenv("BACKEND_API_SECRET")):
            raise ValueError("A separate strong visitor signing key is required")
        if not 0 < deadline <= 270 or rate < 1 or concurrent < 1:
            raise ValueError("Invalid backend limits")
        if backend not in {"memory", "redis"} or (environment == "production" and backend != "redis"):
            raise ValueError("Production requires shared rate limiting")
        if visitor_key and backend != "redis":
            raise ValueError("Anonymous quotas require Redis")
        url = os.getenv("UPSTASH_REDIS_REST_URL", "")
        token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
        namespace = os.getenv("BACKEND_RATE_NAMESPACE", "interviewiq")
        if not namespace or len(namespace) > 64 or not all(c.isalnum() or c in "-_" for c in namespace):
            raise ValueError("Invalid rate namespace")
        if backend == "redis":
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or not token:
                raise ValueError("Shared rate service configuration required")
        if environment == "production":
            if not visitor_key:
                raise ValueError("Production requires anonymous identities")
            if len(os.getenv("BACKEND_API_SECRET", "").encode()) < 32:
                raise ValueError("Production requires a strong backend secret")
            from config import settings
            keys = {"ollama": settings.OLLAMA_API_KEY, "open-router": settings.OPENROUTER_API_KEY,
                    "google": settings.GOOGLE_API_KEY, "grok": settings.XAI_API_KEY}
            if not keys[settings.LLM_PROVIDER] or settings.LLM_TIMEOUT <= 0:
                raise ValueError("Provider configuration required")
            if settings.OLLAMA_FALLBACK_TO_OPENROUTER and not settings.OPENROUTER_API_KEY:
                raise ValueError("Fallback provider configuration required")
        return cls(environment, deadline, backend, rate, concurrent, url, token, namespace,
                   visitor_key, visitor_rate, visitor_day, global_day, ingress_rate)
