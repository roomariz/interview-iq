# Review Script

Use this as a one-page speaking script in a project review.

## Opening

This is a Streamlit interview-practice app with a layered frontend/backend design, OpenRouter-based model routing, and a strong set of evaluation guardrails. The core idea is to help a user practise interview answers, get feedback, and adapt the next questions based on their CV, job description, and previous answers.

## What I Built

The app has a welcome screen, setup screen, question screen, locked evaluation state, feedback screen, improved-answer view, and session summary. The flow is:
welcome -> setup -> question generation -> answer submission -> evaluation -> feedback -> next question or summary.

## Why These Technologies

- Streamlit: fast to build, stateful, suitable for a single-user interactive prototype.
- OpenRouter: one API for multiple model providers, with fallback support.
- OpenAI client: used as the integration layer for OpenRouter.
- Pydantic: strict JSON parsing and schema validation.
- fpdf2: JSON and PDF report generation.
- pytest and Playwright: regression and UI coverage.

## Prompting Approach

The live question-generation path is mostly structured zero-shot prompting with hard constraints.

- It uses a priority order: role first, then CV, then job description.
- It includes a question plan with type, purpose, focus, and previous questions.
- It uses explicit guardrails so the model returns one concrete scenario, not a vague prompt.
- The prompt is not a classic few-shot prompt in the live path. There is few-shot scaffolding in the code, but the active prompt is effectively zero-shot plus constraints.
- It is also not explicit chain-of-thought prompting. Instead, it asks for reasoning, trade-offs, and evidence without exposing hidden reasoning.

## Evaluation Approach

Answer evaluation is evidence-first.

- First, the app extracts structured evidence from the answer.
- Then it scores relevance, structure, specificity, communication, and problem-solving approach.
- It uses a relevance gate so off-topic answers are handled separately.
- It grounds trust and confidence against the evidence context.
- It generates a follow-up question based on weak areas.

## Guardrails

The app validates answer length and blocks obvious prompt-injection phrases. It also repairs malformed JSON, validates model outputs, and rejects unsupported or hallucinated tech in generated questions. That gives the app a safer trust boundary than a plain LLM chat demo.

## Model Choices

The repo defaults to a free Google model chain with `openai/gpt-5-nano` as a fallback safety net. That choice is pragmatic because the app needs structured JSON and reliable fallback behaviour. It is slightly different from the course brief, which recommended GPT-5 mini/nano/5, so I would explain that as a cost and reliability trade-off.

## Feature Highlights

- CV and job-description personalisation
- Adaptive question sequencing
- Real-time answer evaluation
- Improved-answer reference view
- Session summary and downloadable reports
- Request log for LLM calls

## Closing Line

Overall, this is a review-ready interview practice tool that combines prompt engineering, structured outputs, fallback routing, and UI state management in a single workflow.
