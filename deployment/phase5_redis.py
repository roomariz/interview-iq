"""Canonical identity for the configured HTTPS Redis REST root, never aliases."""

import os
import re
from urllib.parse import urlsplit


def normalise_endpoint(value):
    if (not isinstance(value, str) or not value or any(ord(c) <= 32 or ord(c) == 127 for c in value)
            or "?" in value or "#" in value):
        raise ValueError("Invalid Redis REST endpoint")
    parsed = urlsplit(value)
    host = parsed.hostname or ""
    port = parsed.port
    labels = host.split(".")
    if (parsed.scheme != "https" or parsed.username is not None or parsed.password is not None
            or not host or len(host) > 253 or parsed.netloc.endswith(":")
            or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels)
            or port is not None and not 1 <= port <= 65535 or parsed.path not in ("", "/")):
        raise ValueError("Invalid Redis REST endpoint")
    return parsed.scheme, host, port or 443, "/"


def configured_endpoint():
    try:
        return normalise_endpoint(os.environ["UPSTASH_REDIS_REST_URL"])
    except (KeyError, ValueError):
        raise RuntimeError("Phase 5 Redis endpoint configuration refused") from None


def endpoint_url():
    scheme, host, port, path = configured_endpoint()
    return f"{scheme}://{host}{':' + str(port) if port != 443 else ''}{path}"


def allows_redis_request(request):
    configured = configured_endpoint()
    if request.method != "POST":
        return False
    try:
        return normalise_endpoint(str(request.url)) == configured
    except ValueError:
        return False


async def guarded_async_send(original, client, request, **kwargs):
    if not allows_redis_request(request):
        raise RuntimeError("Phase 5 alternative transport denied")
    return await original(client, request, **{**kwargs, "follow_redirects": False})
