"""Additional Preview-only workflow gate; existing security remains inside it."""

import asyncio
import hmac
import json
import os

from deployment import free_model_budget as budget
from deployment.free_model_transport import CURRENT


class LiveVerificationGate:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] == "/api/health":
            return await self.app(scope, receive, send)
        from api.security import error_response
        from shared.visitor_identity import validate
        from shared.api_contracts import ContextRequest, EvaluationRequest, QuestionRequest

        path = scope["path"]
        schemas = {"/api/interview/context": ContextRequest, "/api/interview/question": QuestionRequest,
                   "/api/interview/evaluate": EvaluationRequest}
        if path not in schemas or scope["method"] != "POST":
            return await error_response(404, "live_verification_route", "Endpoint unavailable.")(scope, receive, send)
        headers = dict(scope["headers"])
        try:
            supplied = headers.get(b"authorization", b"")
            if not hmac.compare_digest(supplied, ("Bearer " + os.environ["BACKEND_API_SECRET"]).encode()):
                raise ValueError("authentication")
            validate(headers.get(b"x-interview-visitor", b"").decode(), os.environ["BACKEND_VISITOR_SIGNING_KEY"])
        except (ValueError, UnicodeError):
            return await error_response(401, "unauthorised", "Authentication failed.")(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 131072:
                return await error_response(413, "request_size", "Request too large.")(scope, receive, send)
            if not message.get("more_body", False):
                break
        try:
            request = schemas[path].model_validate_json(body)
            if isinstance(request, QuestionRequest) and request.question_list_count != 1:
                raise ValueError("count")
        except ValueError:
            return await error_response(422, "validation", "Please check the interview inputs.")(scope, receive, send)

        group = headers.get(b"x-live-verification-case", b"").decode("ascii", errors="ignore")
        token = None
        if path != "/api/interview/context":
            expected = "/api/interview/evaluate" if group == "evaluation" else "/api/interview/question"
            if group not in budget.CASE_LIMITS or path != expected:
                return await error_response(403, "live_verification_case", "Test case unavailable.")(scope, receive, send)
            try:
                owner = await asyncio.to_thread(budget.workflow, group)
                token = CURRENT.set((group, owner))
            except Exception:
                return await error_response(503, "live_verification_closed", "Verification is closed.")(scope, receive, send)

        delivered = False
        chunks = []
        status = 500

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        async def observed(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            if message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, replay, observed)
            if token:
                result = json.loads(b"".join(chunks))
                valid = status == 200
                if group != "evaluation":
                    meta = result.get("llm_metadata", {})
                    valid = valid and meta.get("status") == "success" and meta.get("model") == budget.MODEL
                await asyncio.to_thread(budget.command, "RPUSH", budget.keys()[2], json.dumps({
                    "event": "workflow", "case": group, "status": status, "valid": bool(valid)}))
                if not valid:
                    await asyncio.to_thread(budget.action, "close")
        except Exception:
            if token:
                await asyncio.to_thread(budget.action, "close")
            raise
        finally:
            if token:
                CURRENT.reset(token)
