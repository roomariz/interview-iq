# Dependency security review — 17 November 2026

Completed locally on `feat/streamlit-vercel-backend`, based on merge `622e11d`.
No push, merge into main, deployment, paid service or live inference was performed.
The original findings remain in [the advisory inventory](dependency-advisory-inventory.md)
and [the publication-time report](preview-publication-plan.md); they were not erased.

## Original five affected packages

| Package | Originally installed | Selected patched pin | Deployed scope |
| --- | --- | --- | --- |
| python-dotenv | 1.0.1 | 1.2.2 | Backend; local config loading |
| requests | 2.32.3 | 2.33.0 | Backend Ollama transport; frontend transitive |
| Starlette | 0.41.3 | 1.3.1 | Backend; also required by upgraded Streamlit |
| Streamlit | 1.40.0 | 1.67.0 | Frontend, excluded from Vercel backend |
| Pillow | 11.3.0 | 13.0.0 | Frontend/local rendering, excluded from Vercel backend |

The original audit contained 100 records, or 71 distinct package/advisory-ID pairs.
These are five affected packages, not five individual vulnerabilities. The complete
71-ID table retains CVE/GHSA aliases and upstream patched versions, including
59 Pillow IDs. Alias overlap means ID counts need not equal unique vulnerabilities.

## Exposure and patched versions

- **python-dotenv:** CVE-2026-28684 / GHSA-mf9w-mj56-hr94, patched in 1.2.2.
  It affects symlink handling in set_key/unset_key. This application only reads
  dotenv and production/test mode ignores it, so the affected write API is unused.
  The package was still upgraded rather than relying on that reduced exposure.
  [Maintainer advisory](https://github.com/theskumar/python-dotenv/security/advisories/GHSA-mf9w-mj56-hr94).
- **Requests:** CVE-2024-47081 / GHSA-9hjg-9r4m-mvj7, patched in 2.32.4;
  CVE-2026-25645 / GHSA-gc5v-m9x4-r6x2, patched in 2.33.0. These concern netrc
  credentials with malformed URLs and insecure temporary extraction. Ollama uses
  a fixed validated HTTPS host and disables redirects; extract_zipped_paths is
  not called. Pin 2.33.0 fixes both findings.
  [Maintainer advisory](https://github.com/psf/requests/security/advisories/GHSA-gc5v-m9x4-r6x2).
- **Starlette:** CVE-2025-54121 (multipart blocking; fixed 0.47.2),
  CVE-2025-62727 (file Range DoS; 0.49.1), CVE-2026-48710 (Host URL parsing;
  1.0.1), CVE-2026-48818 (Windows static-file SSRF; 1.1.0), CVE-2026-48817
  (HTTPEndpoint method dispatch; 1.1.0), CVE-2026-54282 (path URL parsing;
  1.3.0) and CVE-2026-54283 (form limits; 1.3.1). The API uses JSON, explicit
  FastAPI methods and raw ASGI paths for authentication. It has no StaticFiles,
  FileResponse, form or HTTPEndpoint handlers. These facts reduce specific attack
  paths but do not excuse keeping the vulnerable dependency. All seven are patched.
  [Release notes](https://starlette.dev/release-notes/).
- **Streamlit:** CVE-2026-33682 / GHSA-7p48-42j8-8846 affects Windows UNC path
  handling and NTLM exposure; fixed 1.54.0. CVE-2026-10804 / GHSA-vqwp-45wm-r9r5
  concerns local cache hashing; upstream lists 1.53.1 as patched. Linux Community
  Cloud is outside the Windows vector, but local development runs on Windows.
  [Maintainer advisory](https://github.com/streamlit/streamlit/security/advisories/GHSA-7p48-42j8-8846).
- **Pillow:** reported fixes span 12.1.1 through 13.0.0, including crafted-image
  CPU/memory exhaustion, codec memory-safety problems and PDF/font/image parser
  issues. The application offers text CV input and no user image upload, lowering
  direct exposure. Version 13.0.0 clears the complete reported set.
  [Pillow 13 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html).

## Compatible dependency changes

FastAPI 0.115.6 constrained Starlette below 0.42. FastAPI is now **0.135.0**,
whose official metadata accepts the patched Starlette while retaining Pydantic
2.10.0. Streamlit **1.67.0** is selected because preceding releases constrain
Pillow below 13; its metadata permits Pillow 13. Both are compatible with Python
3.12. New pins are synchronised across root, backend/frontend and pyproject files.
Frontend pandas is pinned to the existing local 2.2.0 version: unrestricted pandas
3 would remove the Styler.applymap API used by the current request-log panel.
[FastAPI metadata](https://pypi.org/pypi/fastapi/0.135.0/json),
[Streamlit metadata](https://pypi.org/pypi/streamlit/1.67.0/json).

The installed-environment audit found vulnerable transitives that a plain pip
install had retained because they satisfied broad ranges. These are explicitly
pinned in both runtime manifests and local requirements:

| Package | Previously installed | New pin | Reason |
| --- | --- | --- | --- |
| anyio | 4.13.0 | 4.16.0 | TLS IDNA handling and process-worker stderr findings |
| certifi | 2026.4.22 | 2026.10.23 | Remove compromised certificate trust |
| idna | 3.13 | 3.20 | Reported IDNA validation finding |
| urllib3 | 2.6.3 | 2.8.0 | Redirect credentials, streaming and proxy TLS findings |

The separate development audit also found fpdf2 2.7.8 (CVE-2026-114609 and
CVE-2026-114610), now **2.8.8**, and pytest 8.4.2 (CVE-2025-71176), now
**9.0.3**. Neither is deployed. The legacy report helper is not exposed as an API
and does not render attacker-controlled SVG/HTML. Pytest's issue concerns shared
Unix temporary directories, relevant to development/CI rather than Vercel.
pytest-playwright moved **0.7.0 → 0.7.2** because the old plugin prohibited pytest 9.
[Plugin release notes](https://github.com/microsoft/playwright-pytest/releases/tag/v0.7.2).

Legacy GitPython 3.1.47, Tornado 6.5.5 and pip 24.2 were still installed locally
although the upgraded manifests do not require those first two libraries. They
were patched in the existing environment to **3.2.1**, **6.6.1** and **26.3**
respectively; no unnecessary application dependencies were added for them.
All additional identifiers/fixes are in [the additional inventory](dependency-additional-advisories.md).

## Verification

| Check | Result |
| --- | --- |
| Complete automated suite | 587 passed, 12 failed, 11 deselected; 60.99 seconds |
| Failure identities vs established merge baseline | Exactly the same 12; no new regressions |
| Backend/frontend manifest audit | 49 resolved packages; zero known findings; no skips |
| Full development manifest audit | 82 resolved packages; zero known findings; no skips |
| Actual installed environment audit | 96 packages; zero known findings; no skips |
| Dependency compatibility | pip check: no broken requirements |
| OpenAPI before/after | Entire generated document identical, including paths/components |
| Changed Python test lint | Passed |
| Whole-repository lint | Same 42 existing findings; no new lint identities |
| Backend-only installation and startup | Passed; Streamlit/Pillow absent; health/auth verified with dummy keys |
| Frontend-only installation/render | Passed welcome render, pandas styling and real local headless server health; FastAPI/OpenAI absent |
| Secret/artefact scan | Tracked/untracked candidate tree scanned for known patterns and configured secret values; no findings |

Streamlit changed AppTest relative paths to resolve against the calling test file.
The single compatibility edit uses an absolute path to the same cloud entrypoint.
Welcome-screen assertions remain unchanged. No tests were weakened or removed.
Application code, scoring, prompts, wire models, provider SDK pins/rankings,
session logic, Vercel entrypoint, region, duration and deployment gates are unchanged.

Reproduce with dummy provider keys, APP_ENV=test and LLM_PROVIDER=open-router:
`python -m pytest -q --tb=short`. Runtime audit:
`python -m pip_audit -r requirements-backend.txt -r requirements-frontend.txt`.
Development audit: `python -m pip_audit -r requirements-dev.txt`.
Installed audit: `python -m pip_audit --path .venv/Lib/site-packages`.
Audit tooling was isolated under ignored `.pytest_cache/audit-env`.
JSON/text results and before/after OpenAPI snapshots are ignored local artefacts
under `.pytest_cache/security-*`; no credentials are included in the inventories.

## Remaining risks and mitigations

No unresolved known Python-package findings remain in the audited sets. The
historical findings are retained with their relevance and patched versions above.
Audits are point-in-time advisory checks, not proof against undisclosed issues,
OS/browser/native dependency vulnerabilities or a future changed resolution.
Rebuild environments from the manifests and rerun audits before each deployment;
do not assume an existing environment upgrades unpinned transitives automatically.

The 12 pre-existing functional test failures and 42 lint findings remain visible.
They still need separate release assessment; dependency remediation does not
resolve evaluation/coaching/session-memory concerns. Hosted routing, cold starts,
provider latency/cost and multi-user behaviour remain unverified.
Live/e2e-marked tests were excluded as in the established baseline; no inference
traffic ran. Linux deployment builds and browser binaries still need their own
authorised checks before release. Preserve HTTPS, bearer auth, body/deadline
limits and Redis fail-closed admission; keep provider spending/ingress controls.
Starlette currently warns that its httpx-based test client is deprecated; it still
passes the contract suite. No warning was suppressed to make the review pass.
