# Phase 3B: free Upstash setup and verification

Status: the user created the free database and real verification passed on
16 November 2026. See [results](phase3b-redis-verification.md). No Vercel project
or deployment has been created. Do not paste credentials into chat or Git.

## Compatibility confirmed by inspection

`api/rate_limit.py` uses httpx HTTPS POST, not a Redis TCP client. Its JSON request
is `["EVAL", script, "1", key]` with `Authorization: Bearer <REST token>`.
Upstash documents this REST command format and EVAL scripting. No redis-py client,
TCP connection string, extra SDK or interview database is required.
The existing Lua script atomically increments and expires the quota counter.
Its 429/Retry-After behaviour and fail-closed 503 handling are preserved.

Sources: [REST API](https://upstash.com/docs/redis/features/restapi),
[EVAL](https://upstash.com/docs/redis/sdks/py/commands/scripts/eval).
Protocol compatibility was first established by inspection; the subsequent
real-service verification is recorded separately in the results linked above.

## Create the free database manually

1. Sign in to the [Upstash console](https://console.upstash.com/) using your own
   account. Complete any login or consent yourself.
2. Select Redis, then Create Database. Proposed name: `interviewiq-preview`.
3. Select the explicit **Free / $0** plan. Do not select Pay as You Go, a fixed
   paid plan, Prod Pack, extra replicas or paid add-ons. If the account has no
   available free database, stop and report that limitation.
4. Select a single primary region near the intended Vercel function region.
   Record the actual region before selecting a matching Vercel region.
5. Confirm the summary still shows $0 before creating the database. The official
   [pricing page](https://upstash.com/pricing/redis), checked 16 November 2026,
   advertises 500K monthly commands and 10 GB bandwidth for Free. Check current
   console limits; do not assume one HTTP request equals one billed Redis command.
6. Open the database details and find the REST API credentials. Copy the HTTPS
   REST URL and the **write-capable REST token**, not the read-only token or
   `redis://`/`rediss://` connection URL. EVAL/INCR/PEXPIRE require write access.
7. Keep both values in your password manager or the secure environment settings.
   Never put them into tracked templates, screenshots, logs or terminal commands.

Official [getting-started instructions](https://upstash.com/docs/redis/overall/getstarted).
Do not use an anonymous three-day database as a persistent Preview dependency.

## Verify before any Preview deployment

The repository includes `scripts/verify_managed_redis.py`. It starts two independent
local Uvicorn processes with a shared, unique Redis quota namespace. It sends eight
parallel synthetic context requests and expects four 200 responses and four 429s.
It checks Retry-After, invalid-authentication rejection and a separate simulated
Redis outage returning 503. The quota key expires in 60 seconds.
No LLM endpoints are requested and real provider credentials are excluded from
child processes. Redis is the only real external service this verifier contacts.

In PowerShell, configure values interactively so the token is not stored as a
literal command in shell history:

```powershell
$env:UPSTASH_REDIS_REST_URL = Read-Host 'Upstash HTTPS REST URL'
$redisToken = Read-Host 'Upstash REST token' -AsSecureString
$env:UPSTASH_REDIS_REST_TOKEN = [System.Net.NetworkCredential]::new('', $redisToken).Password
try {
    .venv/Scripts/python.exe scripts/verify_managed_redis.py
} finally {
    Remove-Item Env:UPSTASH_REDIS_REST_URL -ErrorAction SilentlyContinue
    Remove-Item Env:UPSTASH_REDIS_REST_TOKEN -ErrorAction SilentlyContinue
    Remove-Variable redisToken -ErrorAction SilentlyContinue
}
```

The token exists in process memory during the test, as required for authentication;
it is not written to a file, passed as an argument or printed. Only share the
sanitised PASS/failure result. If the test fails, stop; do not deploy or enable
in-memory quotas in production to work around it.

## Add Redis credentials to Vercel after the verification gate

The proposed Vercel configuration is in [the deployment proposal](phase3b-proposal.md).
Obtain approval for that configuration before creating/configuring the project.

1. In the approved Vercel project, open Settings → Environment Variables.
2. Add `UPSTASH_REDIS_REST_URL` using the database's HTTPS REST URL.
3. Add `UPSTASH_REDIS_REST_TOKEN` using its write-capable REST token; use the
   sensitive/encrypted setting available in the dashboard.
4. Select **Preview only**, scoped to the approved branch where supported.
   Do not select Production. Add no credentials to the public repository.
5. Add `BACKEND_RATE_BACKEND=redis`, `BACKEND_RATE_NAMESPACE=interviewiq-preview`,
   `BACKEND_RATE_LIMIT=30` and `APP_ENV=production` for Preview. APP_ENV controls
   strict security checks; it does not select a Vercel Production deployment.
6. Add the remaining backend variables from
   `deployment/vercel-preview.env.example`, replacing placeholders in the dashboard.
   Generate one strong random backend secret shared only with the Streamlit server.
7. Deploy only the approved non-production branch to Preview. Inspect the build
   and repeat authentication, quota and outage checks against the actual service.
   Use an isolated test namespace for verification so tests do not exhaust app quota.

Redis/provider credentials belong only on Vercel. Streamlit receives the backend
URL, backend authentication secret, client timeout and, for a protected Preview,
the optional Vercel automation bypass secret. No credentials have been configured
by this work. Production release and live inference each require separate approval.
