"""Evidence extraction and scoring instructions."""

EVIDENCE_EXTRACTION_PROMPT = (
    "Extract structured evidence from the candidate answer. Return ONLY valid JSON.\n\n"
    "JSON schema:\n"
    "{"
    '"has_metrics":false,'
    '"metrics":[{"type":"","before":"","after":"","change":""}],'
    '"has_structure":false,'
    '"has_reasoning":false,'
    '"has_tradeoffs":false,'
    '"has_alternatives":false,'
    '"confidence":{"metrics":0,"structure":0,"reasoning":0,"tradeoffs":0,"alternatives":0},'
    '"anomaly_flags":[]'
    "}\n\n"
    "Rules:\n"
    "- Set has_metrics true when the answer includes numbers, percentages, before/after values, time, cost, scale, throughput, latency, CPU, error rate, or other measurable impact.\n"
    "- Capture metrics even when they are phrased as ranges, approximations, or before/after comparisons.\n"
    "- Mark ambiguous, fake-looking, or non-impact numbers in anomaly_flags instead of treating them as strong metrics.\n"
    "- Flag negative or misleading metric phrasing when the number shape conflicts with the described outcome.\n"
    "- Set has_structure true when the answer has clear sections such as Challenge, Approach, Results, Situation, Task, Action, Result, or equivalent flow.\n"
    "- Set has_reasoning true when the answer explains why decisions were made.\n"
    "- Set has_tradeoffs true when the answer mentions trade-offs, risks, complexity, consistency, or budget constraints.\n"
    "- Set has_alternatives true when the answer mentions considered or rejected alternatives.\n"
    "- Do not invent evidence.\n"
    "- Return JSON only."
)

EVALUATION_PROMPT = (
    "Evaluate the candidate answer. Return ONLY valid JSON.\n\n"
    "JSON schema:\n"
    "{"
    '"evaluation":{"overall_decision":"pass|borderline pass|fail","scores":{"relevance":0,"structure":0,"specificity":0,"communication":0,"problem_solving_approach":0},"labels":{"relevance":"","structure":"","specificity":"","communication":"","problem_solving_approach":""}},'
    '"summary":"",'
    '"strengths":[],"criteria":[],'
    '"feedback_support":[{"claim":"","answer_quote":"","question_quote":""}],'
    '"key_issues":[],'
    '"improvements":[],'
    '"reasoning":{"clarity":"","alternative_approaches":"","trade_off_awareness":"","evidence":""},'
    '"follow_up":{"question":"","type":"","target_dimension":""},'
    '"topic_match":true,'
    '"relevance_gate_applied":false,'
    '"trust":{"trust_level":"","trust_definition":"","score_confidence":0,"decision_confidence":"","impact_strength":"","reason":""}'
    "}\n\n"
    "Feedback grounding: include feedback_support, an array of {claim, answer_quote, question_quote}.\n"
    "Every strength, issue and improvement must have an exact matching claim and verbatim excerpts\n"
    "from the current answer and question that support the assessment. Omit unsupported claims.\n"
    "Do not infer historical metrics from monitoring plans or invent weaknesses to fill a quota.\n"
    "Scoring rules:\n"
    "- Before identifying weaknesses, use the extracted evidence context as the source of truth.\n"
    "- Do not say a metric is missing if the answer includes numbers, percentages, before/after values, time, cost, scale, throughput, latency, CPU, error rate, or other measurable impact.\n"
    '- If measurable results are present but could be stronger, say: "Metrics are present, but could be tied more clearly to business or user impact."\n'
    "- Specificity rubric for behavioural examples requesting outcome evidence:\n"
    "  - 8-10: Multiple concrete measurable outcomes with clear before/after or percentage change.\n"
    "  - 5-7: Some metrics, but linkage or coverage is incomplete.\n"
    "  - 0-4: No concrete applicable evidence; metrics are only one form of specificity.\n"
    "  - Do not assign a score below 7 if multiple valid metrics are present.\n"
    "- Structure rubric:\n"
    "  - 8-10: Clear, coherent flow appropriate to the actual question type.\n"
    "  - 6-7: Partially organised explanation with some missing connections.\n"
    "  - 0-5: Disorganised.\n"
    "  - If Challenge, Approach, and Results are present, do not score structure below 6.\n"
    "- Problem-solving rubric:\n"
    "  - 8-10: Explains decisions, trade-offs, and alternatives.\n"
    "  - 5-7: Good approach but reasoning is implicit.\n"
    "  - 0-4: Steps listed without explanation.\n"
    "Inputs:\n"
    "- Question\n"
    "- Candidate Answer\n"
    "- Reference Answer (guideline only)\n"
    "- Semantic Similarity Score (0–1)\n\n"
    "Similarity (supporting only):\n"
    ">=0.75 strong, 0.4–0.74 partial, <0.4 weak\n"
    "- Do NOT rely only on similarity\n\n"
    "Rules:\n"
    "- Base evaluation ONLY on explicit evidence in the answer\n"
    "- Do NOT ignore metrics, results, or technical details present\n"
    "- Do NOT invent missing issues\n"
    "- Reference answer is NOT ground truth\n"
    "- Valid alternative approaches must not be penalised\n\n"
    "- Only refer to concepts explicitly present in the answer. Do NOT introduce technologies, techniques, or scenarios not mentioned.\n"
    "Prompt requirements:\n"
    "- Cross-check key issues and improvements against the extracted evidence context before finalising them.\n"
    "- Treat evaluation_context as structured support, not as a score override.\n"
    "- Treat evaluation_context as the source of truth for trust, confidence, and follow-up fields.\n"
    "- Surface contradiction flags and anomaly flags in the returned JSON when they are present.\n"
    "- Remove any issue that contradicts the answer content.\n"
    "- If the answer gives technical actions but limited reasoning, focus weaknesses on why each solution was chosen, trade-offs accepted, and alternatives considered and rejected.\n"
    "- technical_accuracy: correctness of solution\n"
    "- clarity: how clearly explained\n"
    "- structure: organisation and flow\n"
    "- relevance: alignment with question\n"
    "- problem_solving_approach: reasoning, trade-offs, justification\n\n"
    "Output:\n"
    "- strengths: supported concise points with matching feedback_support records\n"
    "- improvements: justified actionable points; empty key_issues are valid\n"
    "- overall_summary: 1–2 sentences\n\n"
    "- evaluation_version: short version tag for the evaluation contract\n"
    "- evaluation_trace: ordered steps showing how the result was interpreted\n"
    "- impact_strength: weak, moderate, or strong\n\n"
    "Return JSON only."
)
