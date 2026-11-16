"""Atomic, expiring Redis quota. No identifiers from request headers are used."""

import hashlib
import math
from collections import deque
from time import monotonic

import httpx

from interview_app_backend.llm.deadline import remaining

# One atomic operation, including expiry: no INCR/EXPIRE race or client clock.
SCRIPT = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('PEXPIRE', KEYS[1], 60000) end
local ttl = redis.call('PTTL', KEYS[1])
if ttl < 0 then redis.call('PEXPIRE', KEYS[1], 60000); ttl = 60000 end
return {n, ttl}
"""


class RateLimiter:
    def __init__(self):
        self.arrivals = deque()

    async def retry_after(self, config, secret):
        if config.rate_backend == "memory":
            now = monotonic()
            while self.arrivals and now - self.arrivals[0] >= 60:
                self.arrivals.popleft()
            if len(self.arrivals) >= config.rate_limit:
                return max(1, math.ceil(60 - (now - self.arrivals[0])))
            self.arrivals.append(now)
            return 0
        digest = hashlib.sha256(secret.encode()).hexdigest()
        key = f"{config.namespace}:authenticated:{digest}"
        async with httpx.AsyncClient(timeout=remaining(3), follow_redirects=False, trust_env=False) as client:
            response = await client.post(config.redis_url.rstrip("/"),
                                         headers={"Authorization": f"Bearer {config.redis_token}"},
                                         json=["EVAL", SCRIPT, "1", key])
            response.raise_for_status()
            payload = response.json()
        count, ttl = payload["result"]
        if type(count) is not int or type(ttl) is not int or count < 1 or not 0 < ttl <= 60000:
            raise ValueError("Invalid shared quota response")
        return max(1, math.ceil(ttl / 1000)) if count > config.rate_limit else 0
