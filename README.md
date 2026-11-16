# **InterviewIQ**

InterviewIQ is an AI-assisted interview practice application that turns a candidate's target role, experience, and optional CV and job description into personalised questions and structured feedback. It combines a Streamlit interface with Python services, OpenRouter model routing, and an evidence-aware evaluation pipeline.

This technical overview distinguishes implemented capabilities, intended benefits, and product targets from measured results.

## Problem it solves

Candidates need repeated, relevant practice and clear explanations of how to improve their answers. Human mock interviews require access to an interviewer and scheduling; static question banks provide limited feedback on a candidate's own reasoning and experience.

InterviewIQ provides a self-paced loop of scenario questions, written answers, structured assessment, and targeted improvement guidance. It aims to reduce dependence on scheduled coaching and help candidates explain their actions, decisions, trade-offs, and outcomes more clearly. Cost savings and improved interview outcomes require validation with users.

## Intended users

| User group | Preparation need |
| --- | --- |
| Students and graduates | Practise internship and entry-level interviews and explain project experience. |
| Career changers | Connect previous experience to a new role and identify preparation gaps. |
| Technical candidates | Explain implementation decisions, constraints, and technical trade-offs. |
| Experienced professionals | Strengthen evidence, ownership, communication, and decision-making in answers. |

Universities, training providers, and career programmes are potential future organisational users. Accounts, cohort administration, and team licensing belong to the product vision rather than established deployment capabilities.

## User workflow and outputs

1. **Configure:** select role, difficulty, interviewer persona, and response style; provide optional CV and job-description context.
2. **Practise:** receive a scenario question and submit a written answer. The frontend submission validator accepts answers of 50–2,000 characters.
3. **Review:** inspect scores, strengths, issues, improvement guidance, reasoning feedback, and reliability indicators.
4. **Refine:** view an example answer, continue with a follow-up, or move to another base question.
5. **Summarise:** review session performance and retain available JSON report downloads.

The model profile configures three base questions for free models and five for paid models. Question-generation bundles have separate validation rules; these counts are not a universal session length.

Answer evaluation scores five dimensions from 0 to 10:

| Dimension | Assessment focus |
| --- | --- |
| Relevance | Does the answer address the question? |
| Structure | Does the response follow a coherent sequence? |
| Specificity | Are claims supported by concrete actions, details, and outcomes? |
| Communication | Is the explanation clear and understandable? |
| Problem-solving approach | Are decisions, alternatives, and trade-offs explained? |

Scores and pass/borderline/fail decisions are practice feedback, not validated predictions of hiring success.

## Scale: money, people, and locations

| Area | Current evidence and operating implications |
| --- | --- |
| Money | No verified project budget, revenue, operating spend, or cost per completed session is reported in the repository. Costs depend on hosting, model choice, token usage, retries, and provider billing. |
| Free-model operation | Free mode is enabled by default. Evaluation uses a free-model chain; generation also has a configured paid fallback. A free primary model does not establish zero total cost. |
| People | No verified active-user count, customer count, pilot cohort size, or measured concurrent-user capacity is reported. Streamlit maintains separate user session state. |
| Locations | The browser interface permits remote access when hosted, but no verified deployment regions, countries served, or geographic adoption figures are reported. |
| Technical capacity | Generation and evaluation each use a background executor configured with one worker. Provider quotas, process memory, and queued work constrain throughput. Production capacity requires load testing. |
| Storage | In-memory session state replaces a persistent user/session database. Long-term progress tracking remains a future capability. |

To establish deployment scale, measure completed sessions, concurrent users, queue time, latency, token usage, hosting spend, and provider charges. Use these measurements to calculate cost per completed session before making growth claims.

## Results and success criteria

**Implemented outputs:** personalised questions, structured answer evaluation, evidence and confidence signals, example-answer views, follow-up guidance, session summaries, and JSON reporting. Automated tests cover these areas and failure cases such as malformed responses, irrelevant answers, and provider errors.

**Measured impact:** the repository does not establish improvements in job offers, interview pass rates, confidence, coaching costs, or adoption. Tests of application behaviour are distinct from evidence of learning or commercial impact.

The [success-metrics specification](doc/product_requirement/success-metrics.md) defines targets, rather than achieved results:

| Metric | Documented target |
| --- | --- |
| Session completion | More than 80% for the specified five-question flow. |
| Feedback satisfaction | More than 4.5/5. |
| Return rate | More than 40%. |
| API response time | Less than 10 seconds per call. |
| Failed evaluations | Less than 1%. |
| Availability | 99% uptime. |

The specification also proposes a 10–15% score improvement between the first and final question. These targets need a measured pilot, an agreed session definition, and a consistent assessment method.

## Technical architecture

Frontend and backend are separate Python packages within one modular Streamlit application. They are not independently deployed frontend and API services.

```text
Browser
  -> Streamlit screens and per-user session state
  -> Backend services and background jobs
  -> Prompt construction and OpenRouter model client
  -> Response parsing, schema validation, and evaluation rules
  -> Feedback, follow-ups, session summary, and JSON report
```

| Component | Responsibility |
| --- | --- |
| `app.py` | Root launcher. |
| `interview_app_frontend/` | Screens, components, navigation, job interaction, and session state. |
| `interview_app_backend/services/` | Questions, CV/JD processing, evaluation, follow-ups, and reporting. |
| `interview_app_backend/llm/` | Provider clients, prompts, parsers, retries, and model fallbacks. |
| `interview_app_backend/models/` | Structured application and report models. |
| `config/` | Environment loading, runtime settings, and model profiles. |
| `shared/` | Common constants, enums, and types. |
| `tests/` | Unit, service, integration-style, and browser tests. |

### Evaluation and reliability

The pipeline combines input checks, relevance classification, model-assisted assessment, evidence grounding, and decision adjustments. Pydantic models and parser rules validate structured responses before display. Confidence and anomaly signals distinguish answer quality from assessment reliability.

Off-topic answers receive a dedicated relevance-gate result instead of detailed assessment unsupported by the answer. Provider or parsing failures can produce controlled degraded feedback. Question generation validates structure, grounding, coverage, and duplication, with retries and fallback questions when needed.

Background jobs separate generation and evaluation from screen rendering. Timeouts, transient-error retries, model/provider metadata, and request logs support diagnosis. These mechanisms do not establish a measured service-level guarantee.

## Technology stack

Versions below come from [requirements.txt](requirements.txt).

| Technology | Version | Use |
| --- | --- | --- |
| Python | 3.x | Application and service language. |
| Streamlit | 1.40.0 | Interactive UI and session state. |
| OpenAI Python SDK | 1.55.3 | OpenAI-compatible client for OpenRouter requests. |
| OpenRouter | Hosted API | Model routing via `https://openrouter.ai/api/v1`. |
| Pydantic | 2.10.0 | Structured data and response validation. |
| python-dotenv | 1.0.1 | Local environment configuration. |
| Requests | 2.32.3 | HTTP integration support. |
| google-generativeai | 0.8.4 | Optional Google provider integration. |
| pandas | 2.2.0 | Tabular data utilities. |
| fpdf2 | 2.7.8 | PDF reporting dependency; JSON is the baseline export documented here. |
| Playwright / pytest-playwright | 1.53.0 / 0.7.0 | Browser automation and testing. |

### Model configuration

The checked-in configuration selects `google/gemma-4-31b-it:free` by default, followed by `google/gemma-3-12b-it:free`. Generation additionally includes `openai/gpt-5-nano` as a safety net. Evaluation stays within its free-model chain and degrades when necessary.

These are configured identifiers, not a guarantee of current provider availability. See [settings](config/settings.py) and [model profiles](config/model_profiles.py). `IS_FREE_MODE=true` overrides `MODEL_NAME` with the default free model; set it to `false` to use a configured alternative.

## Innovation and design choices

- **Context-aware practice:** role, CV, job description, and observed weak areas inform questions and follow-ups.
- **Evidence-aware scoring:** relevance, grounding, contradictions, and confidence influence how scores are interpreted.
- **Inspectable feedback:** structured JSON and reliability indicators expose assessment details beyond a conversational response.
- **Controlled generation:** schema checks, duplication controls, grounding rules, and fallback bundles constrain model output.
- **Session-based design:** in-memory state supports initial practice without account or database infrastructure.

The innovation is the application-level combination of personalisation, structured evaluation, and reliability controls. The project integrates existing language models; it does not claim a novel foundation model or proven superiority over other coaching tools.

## Privacy, security, and limitations

CV and interview state are held in the current application session. Relevant content is transmitted to external model providers, so session-only application storage does not imply that data stays on the device or that providers retain nothing.

Keep credentials in environment variables or a local `.env` file. Length checks, basic prompt-injection filtering, relevance checks, and response validation provide safeguards, but cannot eliminate injection, hallucinations, bias, or scoring errors.

The current design does not establish production-grade authentication, persistent history, multi-region availability, or audited privacy compliance. A PDF builder exists, but PDF export requires separate verification before being treated as supported. Learning outcomes and large-scale operation also require validation.

## Run locally

Create and activate a Python virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Copy [.env.example](.env.example) to `.env` and set your own `OPENROUTER_API_KEY`. Google and xAI credentials are optional and apply to their respective integrations. Do not commit credentials.

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit.

## Verification and further documentation

Run a focused offline check of input validation, model configuration, and JSON reporting:

```bash
python -m pytest tests/test_validation.py tests/test_client_configuration.py tests/test_report_service.py
```

The wider suite includes browser and live-provider checks with additional runtime or credential requirements. Consult the manuals before running those checks.

- [User manual](doc/manual.md): workflow and user-facing behaviour.
- [Developer manual](doc/developer-manual.md): implementation details.
- [Manual test guide](doc/test-manual.md): UI verification steps.
- [Product requirements](doc/product_requirement/PRODUCT_REQUIREMENT_DOCUMENT.md): scope and phased vision.
- [Architecture specification](doc/product_requirement/high-level-architecture.md): design context and planned extensions.
