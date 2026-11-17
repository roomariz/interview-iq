"""Short-lived, server-issued anonymous identities; no browser-selected IDs."""

import hashlib
import hmac
import re
import secrets
import time

TTL = 86400
TOKEN = re.compile(r"v1\.([0-9]{10})\.([0-9a-f]{64})\.([0-9a-f]{64})\Z")


def issue(key: str) -> str:
    payload = f"v1.{int(time.time())}.{secrets.token_hex(32)}"
    return payload + "." + hmac.new(key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def validate(token: str, key: str) -> str:
    match = TOKEN.fullmatch(token)
    if not match or not key:
        raise ValueError("Invalid visitor identity")
    issued, nonce, signature = match.groups()
    expected = hmac.new(key.encode(), token.rsplit(".", 1)[0].encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected) or not 0 <= time.time() - int(issued) < TTL:
        raise ValueError("Invalid visitor identity")
    return hmac.new(key.encode(), ("quota:" + nonce).encode(), hashlib.sha256).hexdigest()
