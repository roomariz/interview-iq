"""Google's documented OpenAI-compatible Chat Completions transport."""

import json

from interview_app_backend.llm.question_contract import question_response_schema


def call_google_chat(client, request: dict, task: str) -> dict[str, str]:
    arguments = {
        "model": request["model"],
        "messages": [{"role": "user", "content": request["input"]}],
        "timeout": request["timeout"],
    }
    if "temperature" in request:
        arguments["temperature"] = request["temperature"]
    structured = task.startswith(("question_generation.", "evaluation.evidence_extraction", "evaluation.scoring"))
    if task.startswith("question_generation."):
        arguments["response_format"] = {"type": "json_schema", "json_schema": {
            "name": "interview_questions", "strict": True, "schema": question_response_schema(request["input"]),
        }}
    elif structured:
        arguments["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**arguments)
    if not response.choices:
        raise RuntimeError("Google Gemini returned no answer. Please try again.")
    choice = response.choices[0]
    text = choice.message.content
    if choice.finish_reason != "stop" or not isinstance(text, str) or not text.strip():
        raise RuntimeError("Google Gemini returned an empty, blocked or incomplete answer. Please try again.")
    if structured and not task.startswith("question_generation.") and not isinstance(json.loads(text), dict):
        raise ValueError("Google Gemini must return a JSON object")
    return {"output_text": text.strip()}
