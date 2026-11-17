# Phase 4A local implementation

17 November 2026. Branch: `feat/streamlit-vercel-backend`.
No deployment, push, main merge, paid infrastructure or live provider calls.
The existing protected Preview and inert Production bootstrap were untouched.

## Architecture and identity

Streamlit owns an anonymous identity in its existing server-side session state.
The trusted frontend issues a 256-bit cryptographically random nonce, issue time
and HMAC-SHA256 signature using `BACKEND_VISITOR_SIGNING_KEY`. This key is separate
from `BACKEND_API_SECRET`; both servers must receive it through private settings.
The token remains on the server and is forwarded as `X-Interview-Visitor`.
There is no new browser cookie, browser storage, login screen or user database.

The backend checks bearer authentication first, then the exact token format,
signature, issue time and 24-hour lifetime. Future, expired, forged, missing and
malformed tokens fail with 401 before Redis access. Unsigned user IDs and forwarded
IP headers cannot choose the quota identity. Redis keys use a domain-separated
HMAC of the nonce; they contain no API secret, IP, CV, answer or raw token.
Workers receive a resolved client/token; they do not access Streamlit state.

This adapts the reviewed [original proposal](anonymous-rate-limit-proposal.md):
server-side session storage avoids custom cookie/bootstrap integration, browser
token exposure and a new public token-issuance endpoint. It identifies a Streamlit
connection, not a person or persistent browser. A reconnect/session reset can
obtain a fresh allowance. Token renewal after 24 hours is automatic.

## Approved pilot limits

| Control | Initial value | Accounting |
| --- | --- | --- |
| Visitor minute | 10 | Admitted API requests |
| Visitor day | 100 | Admitted API requests |
| Global minute | 30 | Admitted API requests |
| Global day | 1,000 | Admitted API requests |
| Global concurrency | 4 | Active admitted API requests |
| Authenticated ingress minute | 300 | Requests with valid visitor tokens, including invalid input |

Minute/day windows start on their first admitted request and expire after 60
seconds/24 hours; these are fixed windows, not sliding or calendar-day limits.
One Lua operation checks all four allowances, expires old lease members, checks
capacity, acquires an owned lease and commits counters atomically. Busy/quota
denials do not debit admitted-work allowances. Body size/encoding and schema
failures only consume ingress allowance. Provider failures after admission count.
Context requests count too; this is a conservative API request budget.
All multi-key admission keys share a namespace hash tag for Redis cluster use.
Quota records expire within 24 hours of the window opening; no identity registry
is retained. Changing the signing key invalidates tokens; global caps remain.
This uses [Redis's atomic scripting guarantee](https://redis.io/docs/latest/develop/interact/programmability/eval-intro/).

429 responses retain the existing error envelope and include `Retry-After` in
seconds, using the longest exhausted quota TTL or earliest available lease.
Redis outages, HTTP failures and malformed admission results fail closed with
503 and `Retry-After: 5`; no production memory fallback exists.
Local/test mode without a signing key retains legacy controls for compatibility.
Anonymous identity mode always requires Redis; production always requires identity.

## Distributed leases

Each request owns a random 256-bit sorted-set member. Redis TIME determines expiry.
Acquisition is atomic across instances; release removes only the owner's member.
Lease lifetime is 330 seconds, longer than the unchanged Vercel maximum duration
of 300 seconds and request deadline of 150 seconds. Active leases renew every
30 seconds. Normal completion awaits release; failure retains the lease until
expiry. Renewal failure cancels further deadline-aware provider work.

Timed-out synchronous SDK transports are tracked independently of HTTP responses.
Their lease is retained/renewed until the transport exits, then released. A crashed
or suspended invocation retains its lease until expiry. Old release/renew commands
cannot remove or resurrect another request's lease. No polling of Redis is needed:
normally one ingress call, one admission call and one release call per request,
plus one renewal per 30 seconds while active. Local transport checks use no Redis.

Lease safety assumes bounded execution or a running renewal task. Keep Vercel's
300-second maximum below the 330-second lease. On an unbounded local host, a stuck
transport combined with lost renewals could outlive the lease; this is not an
absolute bound on remote provider execution. Providers may continue processing
after a connection timeout. Do not describe API request concurrency as a cap on
individual model calls: existing fan-out/retries can perform multiple calls.

## Logging security

FastAPI now initialises the same private logging policy as Streamlit. The log
record factory retains reviewed static event templates and selected fixed error
categories, withholds interpolated values, replaces unreviewed messages and removes
exception/stack text. This covers HTTPX/HTTPCore/OpenAI logs before propagation,
including transport messages containing infrastructure URLs. Application logging
remains enabled. Owned handlers filter unapproved extra fields and emit event,
level, module, status code and duration; request paths/bodies/headers are omitted.
The reviewed event list must be updated when introducing new diagnostic messages.
Avoid alternative handlers that serialise unrestricted record extras or direct
stdout/print diagnostics. This policy does not control Vercel platform logs.
[HTTPX documents separate HTTPX/HTTPCore loggers](https://www.python-httpx.org/logging/);
both are covered by the policy.

## Files

- Added `shared/visitor_identity.py`, frontend `services/visitor.py`, backend
  `api/admission.py` and `api/admission_scripts.py`.
- Modified `api/configuration.py`, `api/security.py`, `api/rate_limit.py`,
  `api/index.py` and `interview_app_frontend/services/api_client.py`.
- Modified `interview_app_backend/llm/deadline.py`; added backend
  `utils/private_logging.py`, `utils/log_events.py`; modified `utils/logging_config.py`.
- Added `tests/test_phase4_identity_logging.py`, `tests/test_phase4_admission.py`,
  `tests/test_phase4_real_redis.py`, `tests/phase4_redis_support.py`.
- Modified `tests/test_question_fallback_ui.py`, `scripts/verify_managed_redis.py`,
  `.env.example`, `deployment/streamlit/secrets.example.toml`, `.gitignore`, `AGENTS.md`.
- Modified `doc/manual.md`, `doc/developer-manual.md`, `doc/test-manual.md`;
  added `doc/phase4a-report.md`, `doc/phase4a-verification.md`, `doc/phase4a-preview.md`.
  Pre-existing Phase 3B/proposal edits and untracked documents remain preserved.

## Remaining limitations and release recommendation

Anonymous resets, multiple tabs/connections, VPNs and distributed visitors can
evade visitor quotas. The global caps remain effective, but attackers can deny
service by exhausting them or the shared ingress allowance. No IP fingerprinting,
CAPTCHA, browser challenge or per-person guarantee is introduced. Keep deployment
protection while evaluating abuse controls. API counts are not token/spend caps;
retain provider spending limits and disabled paid fallback. Live Ollama Cloud
latency, cancellation and cost remain untested by design.

See [verification](phase4a-verification.md) and [exact proposed Preview changes](phase4a-preview.md).
Recommend a newly reviewed, protected, permanently mocked Preview under the
existing personal Hobby owner after approval. Rebuild the derived mock artifact
from these changes and verify its network guard before upload. Do not publish
publicly or enable live inference based solely on these local results.
