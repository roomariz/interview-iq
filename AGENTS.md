# AGENTS.md - Rules for AI Agents

--------------------------------------------------------------------

## RULE SOURCES

This file is the primary control file.

Additional rules are defined in:
- /agents/general_rules.md
- /agents/project_rules.md

All rules must be applied together as a single system.

Precedence:
1. AGENTS.md
2. project_rules.md
3. general_rules.md

--------------------------------------------------------------------

## CRITICAL: Rules Before Every Run

For full rule definitions, refer to:
- /agents/general_rules.md
- /agents/project_rules.md

**Critical high-level rules:**

1. **NEVER modify or delete existing files** unless explicitly instructed by the user
2. **ALWAYS read existing files first** before making any changes
3. **NEVER commit secrets, API keys, or credentials** to git
4. **ALWAYS use environment variables** for sensitive data - never hardcode them
5. **ALWAYS verify changes** by running tests or linting commands when available
6. **ALWAYS ask for clarification** - if instructions are ambiguous, unclear, or incomplete: DO NOT guess or decide on your own
7. **NEVER assume libraries are available** - check existing imports and requirements first
8. **Before any commit, verify whether generated or temporary files should be committed; if not, update `.gitignore` instead of adding them so the files do not end up in the commit**
9. **KEEP responses concise** - answer directly without unnecessary preamble
10. **NEVER trust model output without validation**
11. **ALWAYS validate and sanitize inputs before sending to LLM**
12. **All files (Markdown and code) must not exceed 250 lines**
13. **Standardise to British English** across docs, prompts, and user-facing text, including `behavioural`

--------------------------------------------------------------------

## AUTHORITY & SCOPE

**Precedence Order:**
1. **User instruction** (highest) - Direct user commands always win, **unless they violate security constraints or system integrity rules**
2. **AGENTS.md** - This file's rules apply unless overridden by user
3. **Other docs** - Reference project docs only when rules don't cover the situation

**Agent Role:**
- Execute tasks as instructed by the user
- Do NOT introduce new features or change scope without confirmation
- You MAY fix minor issues (bugs, typos, inconsistencies) if clearly safe
- Do NOT make assumptions or decisions without asking
- Act as a tool, not a collaborator - wait for direction
- If unsure, ask - never guess

--------------------------------------------------------------------

## PROJECT INDEX - Quick Reference

**NOTE:** This section is for reference only. Rules above take precedence.

### DOC DEPENDENCY ORDER (read in this sequence)
```
PRD → Architecture → Features → Mockups
```

### ROOT FILES
| File | Purpose |
|------|---------|
| `115.md` | Sprint project requirements & task description |
| `AGENTS.md` | This file - rules for AI agents |
| `.gitignore` | Git ignore patterns |

### DOCUMENTATION (doc/product_requirement/)
| File | Purpose |
|------|---------|
| `PRODUCT_REQUIREMENT_DOCUMENT.md` | **PRIMARY SOURCE OF TRUTH** - Full product specification |
| `product-requirements.md` | Detailed requirements |
| `high-level-architecture.md` | System architecture design |
| `features.md` | Feature list |
| `minimum-viable-product-mvp.md` | MVP scope |
| `use-cases.md` | User scenarios |
| `user-interface--screens.md` | UI/UX specs |
| `user-pain-points.md` | Problem statements |
| `success-metrics.md` | KPIs |
| `edge-cases--security-considerations.md` | Security & edge cases |

### DOCUMENTATION - Mockups
| File | Purpose |
|------|---------|
| `mock_ups/1-welcome screen.md` | Welcome screen UI |
| `mock_ups/2-Set up screen.md` | Setup/interview config UI |
| `mock_ups/3-Question & Answer.md` | Q&A session UI |
| `mock_ups/4-Feedback.md` | AI feedback UI |
| `mock_ups/5-Sample Answer.md` | Sample answers UI |
| `mock_ups/6-Follow-Base-Exit.md` | Follow-up questions UI |
| `mock_ups/7-Session-Summary.md` | Session summary UI |

### DOCUMENTATION - Architecture Diagrams
| File | Purpose |
|------|---------|
| `architecture_&_flow_diagram/index.md` | Architecture overview |
| `architecture_&_flow_diagram/High_Level_Architecture.png` | System diagram |
| `architecture_&_flow_diagram/Navigation Flow.png` | User flow |
| `architecture_&_flow_diagram/CV_Extraction_&_Structuring.png` | CV processing |
| `architecture_&_flow_diagram/Gap_Analysis_&_Targeted_Questioning.png` | Gap analysis |
| `architecture_&_flow_diagram/Question_Generation_with_Distribution.png` | Question generation |

### CODE FILES (To Be Created)
| File | Purpose | Priority |
|------|---------|----------|
| `app.py` | Main Streamlit application | REQUIRED |
| `requirements.txt` | Python dependencies | REQUIRED |
| `.env` | Environment variables | REQUIRED |
| `.env.example` | Env template | REQUIRED |
| `prompts.py` | System prompts library | RECOMMENDED |
| `config.py` | Model settings | RECOMMENDED |
| `utils/api_client.py` | OpenRouter API wrapper | RECOMMENDED |
| `utils/security.py` | Input validation | RECOMMENDED |
| `utils/session_manager.py` | Session state | OPTIONAL |
| `utils/evaluator.py` | Scoring + parsing | OPTIONAL |
| `utils/report_generator.py` | PDF/JSON logic | OPTIONAL |
| `utils/error_handler.py` | Centralised error handling | OPTIONAL |
| `tests/test_app.py` | Unit tests | OPTIONAL |

--------------------------------------------------------------------

## AGENT HISTORY & DECISIONS LOG

**Purpose:** Track user preferences, decisions, and past warnings so agents avoid repeating mistakes.

### How to use:
- Before starting work, check this section for relevant past decisions
- If user says "don't do X again", document it here immediately
- Agents should reference this before taking action on similar tasks
- **Entries must be concise and factual**

### Current Log:

| Date | Category | Decision/Rule | Reason |
|------|----------|---------------|--------|
| 2026-04-24 | Dependencies | Use pinned stable versions (e.g., `streamlit==1.40.0`) instead of ranges | Consistent reproducible builds |
| 2026-04-24 | Architecture | Split AGENTS.md into layered structure: general_rules.md, project_rules.md | Modular reusable rules |
| 2026-04-24 | Files | All files (Markdown and code) must not exceed 250 lines | Maintainable file sizes |
| 2026-04-24 | UX | Standardise to British English across docs, prompts, and user-facing text | Consistent writing style |
| 2026-04-24 | Documentation | Maintain `doc/manual.md` for users and `doc/developer-manual.md` for implementation details; update both after every code change | Keep documentation aligned with current code |
| 2026-04-24 | Documentation | Maintain `doc/test-manual.md` for manual UI test steps; update after every code change | Keep manual testing aligned with current code |
| 2026-04-24 | Git | Before any commit, verify whether generated or temporary files should be committed; otherwise update `.gitignore` | Keep commits clean and intentional |
| 2026-04-26 | Trust model | Off-topic answers: `trust_level="low"`, `decision_confidence="high"`, `score_confidence=0.0` | Evaluation depth is low but decision is certain |
| 2026-04-26 | Validation | Removed nested `validation_warning.trust` - single trust object at root level only | Eliminates inconsistency risk and maintenance overhead |
| 2026-04-26 | Interpretation | Off-topic interpretation: "This answer is not relevant to the question, so detailed evaluation is not applicable." | Accurate signal - not partial evidence |
| 2026-04-26 | Off-topic path | Skip low-confidence adjustments for `failure_type=off_topic` in `apply_decision_adjustments` | Preserve correct off-topic signals |
| 2026-11-16 | architecture | Phase 1 only: health API and Ollama integration; no deployment, frontend API wiring, database or session migration | User-defined scope |
| 2026-11-16 | architecture | User selected direct xAI API for Grok; preserve Ollama/OpenRouter configurations and do not deploy | Explicit provider preference |
| 2026-11-16 | architecture | User switched to direct Google Gemini with a free-tier eligible model; retain other providers and no automatic paid fallback | Explicit provider preference |
| 2026-11-16 | architecture | Question requests must agree on exact count and schema; never return invalid fallback output or access Streamlit state from workers | User-defined validation constraints |

| 2026-11-16 | architecture | Assess relevance against the actual question substance; hypothetical technical answers need no STAR or historical metrics; preserve providers/frontend, no deployment | User relevance-fix constraints |

| 2026-11-16 | architecture | Ground feedback in current inputs, reconcile confidence aliases, withhold uncertain memory; retain screens/providers and stop after local tests | User evaluation reliability task |

| 2026-11-16 | architecture | Keep score-based performance verdict separate from evaluator uncertainty; trace risk reasons, preserve supported coaching and use concise decision probes | User confidence and feedback correction |

| 2026-11-16 | UX | Use InterviewIQ as the displayed app name, browser title and setup left-panel brand; align the text left beside the logo | User branding correction |
| 2026-11-16 | architecture | Phase 2 HTTP separation: keep Streamlit session ownership, screens, scoring and providers; authenticate API requests, mock live providers in tests, no database or deployment | User Phase 2 scope |

| 2026-11-16 | architecture | Phase 3A: aggregate deadlines, distributed quotas and backend-only Vercel preparation; preserve scoring/frontend/providers, mock LLMs, no deployment | User production-readiness scope |

| 2026-11-16 | architecture | Phase 3B uses the intentionally public roomariz/interview-iq repo; preserve visibility/features, require verified real free Upstash before Preview, stop for manual setup, no Production release | Explicit user clarification |

| 2026-11-16 | architecture | Prepare reviewed Phase 3A/3B local commit on codex/phase3b-preview; Frankfurt Redis/Vercel region; no push, cloud mutation, paid service or live LLM calls before approval | User Git publication scope |

| 2026-11-17 | security | Remediate dependency advisories on feat/streamlit-vercel-backend; preserve app/contracts/providers/config, compare against 12 baseline failures, no push/main merge/deployment/live inference | User security-review scope |

| 2026-11-17 | security | Resolve baseline tests and assess Redis, anonymous quotas and readiness; commit locally only, no push, deployment or live LLM calls; quota redesign requires approval | User final-verification scope |

| 2026-11-17 | architecture | Protected mocked Preview owner is roomas-projects (Hobby), confirmed from the user-supplied dashboard; never use astraut-solutions-projects; authorise connector access before creation/deployment; retain no-live-inference/free-tier restrictions | User deployment-owner correction |

| 2026-11-17 | architecture | Preview-first investigation is read-only: no deployment or cloud configuration changes; preserve personal Hobby owner, mock artifact and Preview secrets; report supported options and stop for approval | User investigation-only scope |

| 2026-11-17 | security | User permits one inert protected bootstrap record in the existing personal project after protection verification; keep InterviewIQ mock app Preview-only, no live inference/paid services, preserve Preview secrets | Conditional protected-bootstrap approval |

| 2026-11-17 | security | Phase 4A local only: signed anonymous quotas 10/minute and 100/day; global 30/minute and 1,000/day; distributed leases and private logging; mocked providers, no push/deploy/Production changes | User implementation scope and approved pilot limits |

| 2026-11-17 | security | Phase 4B preparation: review and commit Phase 4A locally; preserve protected personal Hobby Preview and inert Production bootstrap; present exact mocked update for approval before any push/deploy; no live inference or paid services | User preparation and approval boundary |

| 2026-11-17 | security | Phase 4B approved: publish only reviewed commits 53e5428/69e7d0c on the feature branch; add five Preview-only variables and deploy the exact permanent mock artifact to roomas-projects/interviewiq-api-preview; retain protection/bootstrap/quotas, no main/Production/live inference/paid changes | Explicit protected mocked deployment approval |

| 2026-11-18 | security | Phase 5 prioritises verified OpenRouter free Gemma, alternatively verified Gemini Free tier; zero paid inference/cash/credit purchase, no paid or Ollama fallback; separate approval before deployment/inference; if no suitable free model, skip to mocked Phase 6 | User revised Phase 5 constraints |

| 2026-11-18 | security | Phase 5 execution approved: OpenRouter google/gemma-4-31b-it:free only; one protected isolated Preview, three workflows, 12 total attempts including retries/concurrency, zero paid inference/cash; question first then evaluation; preserve mock Preview/bootstrap/quotas, stop after results | Explicit bounded free-model approval |

| 2026-11-18 | security | Correct Phase 5 Redis URL equivalence locally; preserve exact HTTPS endpoint/authentication and budgets; full suite/audits/scans and configured PING preflight; commit on feat/streamlit-vercel-backend only; replacement Preview requires approval, no push/deploy/inference | User guard-correction scope |

| 2026-11-18 | architecture | Use descriptive feature/workflow names for code, tests and documentation instead of numbered phase labels; retain historical deployment IDs and artifact provenance | User naming correction |

| 2026-11-18 | security | Approved one protected free-model replacement from cef29b8 and feature-branch push only; exact Gemma free model, three workflows/12 attempts, zero spend; stop on free-route failure and leave the next verification step for separate approval | User replacement-execution approval |

| 2026-11-18 | security | Prepare Community Cloud demonstration against the existing protected mocked Preview only; no live inference/provider changes, deployment, Production changes or paid services; require approval after the proposal | User Streamlit deployment preparation scope |

| 2026-11-18 | security | Investigate and fix question progression locally on feat/streamlit-vercel-backend; preserve adaptation/security, commit separately, prepare one mocked replacement for approval; no push/deploy/main merge/live inference/paid services | User Phase 6A scope |

| 2026-11-18 | security | Approved one exact a222d76 mocked Preview on roomas-projects; feature push only, 30 HTTP/15 admitted caps, no live inference or spend; user approved shared three-question prefix for five-question continuation; stop after bounded results, no Streamlit release | Explicit replacement approval and clarification |

| 2026-11-18 | security | Mock replacement stopped at 28 data-plane attempts/14 admissions: one Redis lease remained after timeout probes; five-question UI incomplete after harness interruption; no further remote action or Streamlit release | Bounded verification stop and unresolved control gate |

| 2026-11-18 | security | Investigate leases without assuming a defect; isolated local Redis lifecycle and full mocked workflow verification, smallest proven fix only; no scoring/model changes, push, deployment, main merge, paid resources or live providers; propose hosted checks for separate approval | User lease investigation and workflow verification scope |

| 2026-11-18 | security | Approved one isolated protected mocked workflow recovery Preview on roomas-projects; reviewed corrections commit and feature push only; maximum 14 admissions/26 verification HTTP attempts, zero spend/live inference; preserve old deployments/bootstrap/main and stop after report, no Streamlit release | Explicit hosted recovery execution approval |

| 2026-11-18 | security | Prepare Community Cloud frontend against verified dpl_3XLLkftWMZQx7U8bJwjXJG6NraRt/e247aba; private server secrets, demo-labelled UI/downloads, preserve quotas and leases; local tests/audits/scans and approval proposal only, no deploy/push/main/Production/live inference/paid infrastructure | User Community Cloud preparation scope |

| 2026-11-19 | security | Community Cloud execution approved only for reviewed 17-file candidate; private access before secrets, 12 admissions/16 HTTP attempts maximum, one mocked five-question workflow, zero spend/live inference; preserve main and all Vercel resources, stop after verification | User deployment approval |

| 2026-11-19 | security | Correct nested Streamlit imports locally, verify clean frontend-only startup without secrets and mocked workflows, commit separately on feature branch; no push/rebuild, credential installation, privacy changes, Vercel changes, live inference or paid services | User startup-correction scope |

| 2026-11-19 | security | Correct score presentation and recap locally; inspect hosted browser read-only, report header/WebSocket gaps, run mocked regressions/audits/scans and propose frontend update only; no push/deploy/main/Vercel/secrets/live inference/paid services | User final UI verification scope |

| 2026-11-19 | security | Publish exact reviewed nine-file summary correction on feature branch; preserve devcontainer/main/secrets/Vercel; mocked workflow and sanitised browser inspection only; stop on divergence or exposure | User private deployment verification scope |

| 2026-11-19 | security | Explicitly approved one reboot of the existing private Streamlit app to load published 12db45a; preserve secrets, access settings and Vercel resources | User reboot approval |

**Note:** MUST log any user correction or constraint in the table above.
Categories: `architecture`, `security`, `UX`, `performance`

--------------------------------------------------------------------

## QUICK COMMANDS

For detailed commands and testing, refer to `/agents/project_rules.md`.

```bash
# Install deps
pip install -r requirements.txt

# Run app
streamlit run app.py

# Set API key
export OPENROUTER_API_KEY="your-key"
```
