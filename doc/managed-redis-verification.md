# Managed Redis verification results

Verified on 16 November 2026 against the user's existing free Upstash database.
No database was provisioned, no paid service was enabled and no LLM was invoked.

## Credential handling

The two REST values were found in the ignored private local `.env` file. Only
`UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` were loaded into the
verification process environment. No credentials were copied into tracked files,
arguments, output, test results or cloud configuration.
The endpoint was validated as an Upstash HTTPS REST hostname before the main run.
Child backends received only required operating-system values, Redis settings,
a generated temporary backend secret and an unused dummy provider key.
Production configuration still requires environment variables and ignores dotenv.

## Observed results

| Check | Result |
| --- | --- |
| Actual managed REST connectivity | Passed; authenticated EVAL calls succeeded |
| Production rate limiter | Existing httpx REST integration; unchanged Lua script |
| Independent backend processes | Two separate local Uvicorn processes |
| Concurrent admission | Eight parallel authenticated requests across both processes |
| Combined atomic quota | Exactly four HTTP 200 and four HTTP 429 responses |
| Retry information | Every 429 had numeric Retry-After between 1 and 60 seconds |
| Invalid backend authentication | HTTP 401 before consuming the legitimate quota |
| Simulated unavailable Redis | Separate backend returned HTTP 503; no local fallback |
| Invalid managed Redis REST token | Managed service rejected an intentionally invalid token |
| Backend with invalid Redis token | HTTP 503 with sanitised body; no model call |
| Response privacy | Temporary backend secret/token absent from tested response bodies |
| LLM calls | Zero |

The main run executed `scripts/verify_managed_redis.py` and exited successfully.
Its sanitised output was:

```text
PASS: two processes; 4 admitted, 4 rate-limited; Retry-After, auth and outage checks passed
No LLM calls. Synthetic quota key expires within 60 seconds.
```

An additional authentication check sent an intentionally invalid token to the
same managed REST endpoint and confirmed rejection (401/403 accepted). A separate
backend process configured with that invalid token returned sanitised HTTP 503
for an otherwise valid, authenticated synthetic context request. It exited cleanly.

Only short-lived quota counters were written remotely. The main test used a
random verification namespace; expiry is set atomically to 60 seconds by EVAL.
All three main-run backends and the extra invalid-token backend were stopped.
No endpoints, tokens, keys or personal interview data appear in this report.

## Scope and remaining gates

This proves the observed quota behaviour across independent local backend
processes using a real managed Redis service. It does not replace testing the
deployed Vercel instances, production traffic or long-running load.
The outage was simulated through an unreachable endpoint, not by taking down
the user's real database. No hosted performance or inference costs were measured.

The Redis prerequisite for Preview preparation is now satisfied. The existing
[deployment proposal](protected-preview-proposal.md) has been reviewed against the current
source and connected accounts. Remaining steps are publishing an exact reviewed
source revision through authorised Git access, approving/configuring the Preview
project, securely setting its environment variables and checking the actual build.
No Vercel project, deployment or Streamlit test app has been created.
Production and live inference remain separately gated.
