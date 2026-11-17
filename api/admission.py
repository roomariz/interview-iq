"""Atomic anonymous/global quotas and owned distributed work leases."""

import asyncio
import logging
import math
import secrets

import httpx

from api.admission_scripts import ADMIT, RELEASE, RENEW
from interview_app_backend.llm.deadline import current_deadline

LOGGER = logging.getLogger("interview.security")
LEASE_MS = 330000  # Longer than Vercel's configured 300-second function lifetime.
_cleanup = set()


async def command(config, script, keys, args):
    async with httpx.AsyncClient(timeout=3, follow_redirects=False, trust_env=False) as client:
        response = await client.post(config.redis_url.rstrip("/"),
                                     headers={"Authorization": f"Bearer {config.redis_token}"},
                                     json=["EVAL", script, str(len(keys)), *keys, *map(str, args)])
        response.raise_for_status()
        return response.json()["result"]


class Admission:
    def __init__(self, config, visitor):
        self.config = config
        self.owner = secrets.token_hex(32)
        prefix = "{" + config.namespace + "}:v4:"
        self.keys = [prefix + visitor + ":minute", prefix + visitor + ":day",
                     prefix + "global:minute", prefix + "global:day", prefix + "leases"]
        self.heartbeat = None
        self.deadline = current_deadline.get()

    async def acquire(self):
        c = self.config
        result = await command(c, ADMIT, self.keys,
                               [c.visitor_rate, c.visitor_day, c.rate_limit, c.global_day,
                                c.max_concurrent, LEASE_MS, self.owner])
        if (not isinstance(result, list) or len(result) != 2
                or any(type(v) is not int for v in result) or result[0] not in (0, 1, 2)
                or not 0 <= result[1] <= 86400000 or (result[0] == 0) != (result[1] == 0)):
            raise ValueError("Invalid admission response")
        if result[0] == 0:
            self.heartbeat = asyncio.create_task(self.renew())
        return result[0], max(1, math.ceil(result[1] / 1000))

    async def renew(self):
        while True:
            await asyncio.sleep(30)
            try:
                renewed = await command(self.config, RENEW, [self.keys[4]], [self.owner, LEASE_MS])
                if type(renewed) is not int or renewed != 1:
                    if self.deadline:
                        self.deadline.cancelled.set()
                    return
            except Exception:
                if self.deadline:
                    self.deadline.cancelled.set()
                LOGGER.warning("lease_renewal_failed")
                return  # Retain the existing lease until expiry; never release on uncertainty.

    async def finish(self, deadline):
        if not deadline.has_transports():
            await self.release_when_idle(deadline)
            return
        task = asyncio.create_task(self.release_when_idle(deadline))
        _cleanup.add(task)
        task.add_done_callback(_cleanup.discard)

    async def release_when_idle(self, deadline):
        # HTTP cancellation does not stop a synchronous provider transport.
        while deadline.has_transports():
            await asyncio.sleep(0.1)
        self.heartbeat.cancel()
        try:
            await command(self.config, RELEASE, [self.keys[4]], [self.owner])
        except Exception:
            LOGGER.warning("lease_release_failed")
