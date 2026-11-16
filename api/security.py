"""Bounded requests and instance-local abuse controls; no interview storage."""

import hmac
import os
from collections import deque
from time import monotonic

from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = 131072


def error_response(status: int, code: str, message: str, headers=None):
    return JSONResponse({"error": {"code": code, "message": message}},
                        status_code=status, headers=headers)


class InterviewSecurity:
    def __init__(self, app):
        self.app = app
        self.arrivals = deque()
        self.active = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/interview/"):
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        secret = os.getenv("BACKEND_API_SECRET", "")
        supplied = headers.get(b"authorization", b"")
        if not secret:
            return await error_response(503, "configuration", "Interview service is not configured.")(scope, receive, send)
        if not hmac.compare_digest(supplied, f"Bearer {secret}".encode()):
            return await error_response(401, "unauthorised", "Backend authentication failed.",
                                        {"WWW-Authenticate": "Bearer"})(scope, receive, send)
        now = monotonic()
        while self.arrivals and now - self.arrivals[0] >= 60:
            self.arrivals.popleft()
        if len(self.arrivals) >= int(os.getenv("BACKEND_RATE_LIMIT", "30")):
            return await error_response(429, "rate_limit", "Please wait before trying again.",
                                        {"Retry-After": "60"})(scope, receive, send)
        if self.active >= int(os.getenv("BACKEND_MAX_CONCURRENT", "4")):
            return await error_response(503, "busy", "Interview service is busy. Please try again.",
                                        {"Retry-After": "5"})(scope, receive, send)
        if headers.get(b"content-encoding", b"identity") != b"identity":
            return await error_response(415, "encoding", "Unsupported content encoding.")(scope, receive, send)
        try:
            declared_size = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await error_response(400, "request_size", "Invalid request size.")(scope, receive, send)
        if declared_size < 0 or declared_size > MAX_REQUEST_BYTES:
            return await error_response(413, "request_size", "Request is too large.")(scope, receive, send)
        # Buffer only up to the cap, including chunked requests without Content-Length.
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > MAX_REQUEST_BYTES:
                return await error_response(413, "request_size", "Request is too large.")(scope, receive, send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        self.arrivals.append(now)
        self.active += 1
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = [*message.get("headers", []), (b"cache-control", b"no-store")]
            await send(message)

        try:
            await self.app(scope, bounded_receive, private_send)
        finally:
            self.active -= 1
