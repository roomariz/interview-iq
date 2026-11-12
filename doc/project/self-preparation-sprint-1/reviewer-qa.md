# Likely Reviewer Questions and Answers

## 1. What problem does the app solve?

It helps users practise interview answers in a structured flow, then gives feedback, follow-up questions, and a session summary.

## 2. Why Streamlit instead of a heavier frontend?

This is a stateful single-user prototype. Streamlit gets me to a polished multi-screen UI quickly and keeps the app simpler to review.

## 3. Why OpenRouter?

OpenRouter gives one API for multiple model providers, which makes fallback routing and model experimentation much easier.

## 4. Which models are you using?

The repo defaults to a free Google model chain, with `openai/gpt-5-nano` as a fallback safety net. The exact model is controlled by `MODEL_NAME` in `.env`.

## 5. Is this few-shot prompting?

Not in the live path. The active question-generation prompt is structured zero-shot with hard constraints. There is few-shot scaffolding in the code, but it is not the main production path.

## 6. Is this chain-of-thought prompting?

Not explicitly. The prompts ask for reasoning, trade-offs, and evidence, but they do not ask the model to expose hidden step-by-step reasoning.

## 7. What are the key prompt techniques?

Priority ordering, structured role/CV/JD grounding, scenario constraints, output-only formatting, evidence extraction, and JSON-only scoring.

## 8. What makes the questions better than generic prompts?

They are grounded in role, CV, job description, previous questions, and a controlled question plan. That reduces repetition and improves relevance.

## 9. What security guards did you add?

Answer length checks, prompt-injection blocking, relevance gating, JSON repair and schema validation, duplicate filtering, and hallucinated-tech rejection.

## 10. How do you handle off-topic answers?

The app short-circuits them through a relevance gate and returns broad guidance instead of pretending it can give detailed technical feedback.

## 11. How does feedback work?

The app extracts evidence, scores five dimensions, grounds trust against the evidence context, then shows a readable feedback card and a JSON view.

## 12. What is the strongest part of the system?

The combination of structured prompts, fallback routing, and evaluation grounding. That is where most of the engineering value is.

## 13. What is the main trade-off you made?

I chose reliability and cost control over chasing the exact course-recommended model. That is why the repo uses a free model chain with a safety fallback.

## 14. What would you improve next?

I would replace any hard-coded filesystem references with repo-relative links, split `interview_app_backend/services/question_service.py` into smaller modules, and separate report generation from JSON/PDF export if the app were extended further.
