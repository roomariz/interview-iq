import logging
import json
import random
from collections import Counter
from difflib import SequenceMatcher
from collections.abc import Callable

from interview_app_backend.llm.client import call_llm, get_openrouter_client
from interview_app_backend.llm.client import get_last_llm_call_metadata
from interview_app_backend.llm.provider_clients import get_google_client
from interview_app_backend.llm.provider_clients import get_grok_client
from interview_app_backend.llm.provider_fallback import CallLog
from interview_app_backend.llm.prompts.question_generation_prompt import build_question_generation_prompt
from interview_app_backend.llm.question_generation_parser import extract_question_generation_meta
from interview_app_backend.llm.question_generation_parser import parse_question_generation_response
from config.model_profiles import get_model_profile
from config.model_profiles import get_retry_limit
from config.settings import MODEL_NAME
from interview_app_backend.services.question_sequence import build_question_prompt_context
from interview_app_backend.services.question_sequence import resolve_missing_context


LOGGER = logging.getLogger(__name__)
MAX_SCENARIO_TYPE_COUNT = 2
ALLOWED_SCENARIO_TYPES = {"debugging", "performance", "system_design", "behavioural", "scaling"}
REQUIRED_SCENARIO_DIMENSIONS = ("debugging", "performance", "system_design", "behavioural", "scaling")
DIMENSION_BY_SCENARIO_TYPE = {
    "debugging": "debugging / regression recovery",
    "performance": "performance / trade-off decision-making",
    "system_design": "system design / scalability",
    "behavioural": "behavioural ownership / ambiguity handling",
    "scaling": "stakeholder communication / coordination",
}
QUESTION_TYPE_TO_SCENARIO_TYPE = {
    "cv_based": "debugging",
    "jd_based": "performance",
    "behavioural": "behavioural",
    "deep_dive": "system_design",
    "gap_targeted": "scaling",
}
class DuplicateQuestionError(RuntimeError):
    pass


PERFORMANCE_KEYWORDS = [
    "slow", "latency", "performance", "load time", "optimise", "optimize",
    "response time", "delay", "bottleneck", "inefficient", "speed",
]

PERFORMANCE_TEMPLATES = {
    "Easy": [
        "A user reports that a page in your application takes {duration} to load. What steps would you take to identify and improve the performance?",
        "Your API response time increased from {baseline} to {degraded}. What steps would you take to optimise it?",
        "A page in your app loads slowly due to backend data fetching. What would you check first?",
        "A colleague notices that a specific endpoint is slower than expected after a recent change. How would you investigate?",
    ],
    "Medium": [
        "Your application experiences intermittent slowdowns during peak usage. How would you diagnose and resolve this performance issue?",
        "A database query is taking unusually long to execute. Walk through your approach to identify and fix the bottleneck.",
    ],
    "Hard": [
        "Your system experiences latency spikes across multiple services. Design an approach to identify the root cause and implement a fix.",
        "Performance degrades significantly under load. How would you profile, identify constraints, and optimise the system?",
    ],
}

QUESTION_TYPE_TEMPLATES = {
    "cv_based": [
        "You have used {cv_skill} before in your {role} work. A production issue now affects your {role_focus}. How would you handle it?",
        "Your CV mentions {cv_skill}. A release has introduced a regression in your {role_focus} as a {role}. How would you apply that experience to fix it?",
    ],
    "jd_based": [
        "The job description emphasises {jd_requirement}. A production issue now affects your {role_focus} in your {role} role. How would you respond?",
        "This {role} role requires {jd_requirement}. How would you use that skill to handle a production issue in your {role_focus} safely?",
    ],
    "gap_targeted": [
        "You've demonstrated strength in {strength}, but have limited exposure to {gap}. A production issue now tests that gap in your {role_focus} as a {role}. How would you respond?",
        "To prepare for this {role} role, you'd need to improve in {gap}. How would you handle a real issue in your {role_focus} while closing that gap?",
    ],
    "behavioural": [
        "Tell me about a time when you {situation}. What was the outcome?",
        "Describe a challenging situation where you {action}. How did you handle it?",
    ],
}

ROLE_FALLBACK_TEMPLATES = {
    "backend": "You are working on a backend service where a recent change affects {detail}. How would you investigate the issue, decide on a fix, and keep the release stable?",
    "frontend": "You are working on a user interface where a recent change affects {detail}. How would you investigate the issue, decide on a fix, and keep the release stable?",
    "full stack": "You are working across the frontend and backend where a recent change affects {detail}. How would you investigate the issue, decide on a fix, and keep the release stable?",
    "data": "You are working on a data pipeline where a recent change affects {detail}. How would you investigate the issue, decide on a fix, and keep the release stable?",
    "devops": "You are working on a deployment pipeline where a recent change affects {detail}. How would you investigate the issue, decide on a fix, and keep the release stable?",
}

ROLE_KEYWORDS = {
    "backend": ["backend", "api", "database"],
    "frontend": ["frontend", "ui", "browser"],
    "full stack": ["frontend", "backend", "api"],
    "data": ["data", "pipeline", "query"],
    "devops": ["deployment", "infrastructure", "monitoring"],
    "platform": ["platform", "scale", "reliability"],
    "qa": ["testing", "regression", "release"],
}

FEW_SHOT_EXAMPLES = {
    ("Full Stack Engineer", "Easy", "Performance"): [
        {
            "Configuration": "Full Stack, Easy, Friendly, Performance",
            "Question": "A user reports that a page in your application takes 5 seconds to load. What steps would you take to identify and improve the performance?",
        },
        {
            "Configuration": "Full Stack, Easy, Friendly, Performance",
            "Question": "Your API endpoint is responding slowly after a recent change. How would you investigate and fix the issue?",
        },
    ],
}


def _build_context_block(role: str, cv_context: str, jd_context: str) -> str:
    return (
        f"Role: {role}\n"
        f"Candidate CV context: {cv_context.strip()}\n"
        f"Job Description context: {jd_context.strip()}\n"
    )


def _select_template(difficulty: str, focus: str) -> str:
    if focus.lower() == "performance":
        templates = PERFORMANCE_TEMPLATES.get(difficulty, PERFORMANCE_TEMPLATES["Easy"])
        return random.choice(templates)
    return None


def _select_question_type(cv_context: str, jd_context: str, asked_topics: list[str], question_index: int = 1) -> str:
    if cv_context.strip():
        return "technical"
    if jd_context.strip():
        return "technical"
    if asked_topics and len(asked_topics) >= 2:
        return "follow_up"
    return "technical"


def _format_template(template: str, role: str, difficulty: str, cv_context: str, jd_context: str) -> str:
    replacements = {
        "{duration}": random.choice(["5 seconds", "several seconds", "a few seconds"]),
        "{baseline}": random.choice(["200ms", "100ms", "150ms"]),
        "{degraded}": random.choice(["800ms", "1 second", "600ms"]),
        "{scenario}": random.choice(["a performance issue", "an API slowdown", "a loading problem"]),
        "{cv_skill}": _extract_skill_from_context(cv_context) or "your relevant experience",
        "{jd_requirement}": _extract_skill_from_context(jd_context) or "the required skill",
        "{gap}": "performance optimisation",
        "{strength}": "technical implementation",
        "{situation}": "you had to optimise something that was running slowly",
        "{action}": "improved the performance of a slow system",
    }
    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def _extract_skill_from_context(context: str) -> str | None:
    if not context.strip():
        return None
    keywords = ["react", "python", "javascript", "sql", "api", "database", "frontend", "backend", "node", "django", "spring", "spring boot"]
    context_lower = context.lower()
    for keyword in keywords:
        if keyword in context_lower:
            return keyword
    return None


def _extract_role_keywords(role: str) -> list[str]:
    role_lower = role.lower()
    for key, keywords in ROLE_KEYWORDS.items():
        if key in role_lower:
            return keywords[:3]
    if "platform" in role_lower or "infrastructure" in role_lower:
        return ["platform", "infrastructure"]
    if "qa" in role_lower or "test" in role_lower:
        return ["test", "regression"]
    return [role_lower] if role_lower else []


def _extract_context_keywords(context: str) -> list[str]:
    keywords = [
        "python",
        "java",
        "spring",
        "typescript",
        "javascript",
        "react",
        "angular",
        "fastapi",
        "django",
        "sql",
        "postgres",
        "api",
        "rest",
        "microservices",
        "database",
        "performance",
        "testing",
        "aws",
        "docker",
        "kubernetes",
        "monitoring",
        "scalability",
        "reliability",
        "communication",
        "leadership",
        "caching",
    ]
    lowered = context.lower()
    return [keyword for keyword in keywords if keyword in lowered][:3]


def _normalise_scenario_type(value: object, question_type: str = "") -> str:
    scenario_type = str(value or "").strip().lower().replace("-", "_")
    if scenario_type in ALLOWED_SCENARIO_TYPES:
        return scenario_type
    question_type_key = str(question_type or "").strip().lower().replace("-", "_")
    return QUESTION_TYPE_TO_SCENARIO_TYPE.get(question_type_key, "debugging")


COMMON_TECH_TERMS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "angular",
    "node",
    "sql",
    "postgres",
    "api",
    "database",
    "service",
    "frontend",
    "backend",
    "aws",
    "docker",
    "kubernetes",
    "monitoring",
    "scalability",
    "reliability",
    "performance",
    "testing",
    "fastapi",
    "django",
    "spring",
    "leadership",
    "communication",
    "redis",
    "kafka",
    "rabbitmq",
    "graphql",
    "rest",
    "microservices",
}

ROLE_ONLY_GROUNDING_TERMS = {
    "issue",
    "issues",
    "problem",
    "problems",
    "incident",
    "workflow",
    "team",
    "delivery",
    "production",
    "priority",
    "prioritise",
    "prioritize",
    "trade-off",
    "trade-offs",
    "ambiguity",
    "stakeholder",
    "stakeholders",
    "ownership",
    "communication",
    "coordination",
    "design",
    "scalability",
    "performance",
    "debugging",
    "regression",
}

SEMANTIC_TECH_GROUPS = {
    "backend": {"api", "backend", "service", "services", "endpoint", "rest", "microservices"},
    "frontend": {"frontend", "ui", "browser", "react", "angular", "component", "state", "render"},
    "database": {"database", "db", "sql", "postgres", "mysql", "schema", "query", "transaction", "migration"},
    "performance": {"performance", "latency", "throughput", "slow", "bottleneck", "optimise", "optimize", "load"},
    "system_design": {"design", "architect", "architecture", "scalable", "scalability", "distributed", "trade-off", "tradeoffs"},
    "behavioural": {"ownership", "communication", "stakeholder", "stakeholders", "ambiguity", "collaboration", "conflict", "leadership"},
    "scaling": {"scale", "scaling", "high-load", "load", "capacity", "growth", "resilience", "reliability"},
    "cloud": {"aws", "docker", "kubernetes", "deployment", "infrastructure", "monitoring", "observability", "pipeline"},
    "messaging": {"kafka", "rabbitmq", "queue", "queues", "event", "events"},
    "caching": {"redis", "cache", "caching", "memoization"},
    "testing": {"testing", "test", "regression", "qa", "quality"},
}

ROLE_BASELINE_GROUPS = {
    "backend": {"backend", "database", "performance", "system_design"},
    "frontend": {"frontend", "performance", "system_design"},
    "full stack": {"backend", "frontend", "database", "performance", "system_design"},
    "data": {"database", "performance", "system_design", "scaling"},
    "devops": {"cloud", "scaling", "system_design"},
    "platform": {"cloud", "scaling", "system_design", "performance"},
    "qa": {"testing", "behavioural", "debugging"},
    "product": {"behavioural", "system_design"},
}

TERM_TO_GROUP = {
    term: group
    for group, terms in SEMANTIC_TECH_GROUPS.items()
    for term in terms
}


def _is_similar_to_previous(question: str, previous_questions: list[str] | None) -> bool:
    previous = [item for item in previous_questions or [] if str(item).strip()]
    if not previous:
        return False
    if any(same_question_pattern(question, prior) for prior in previous):
        return True
    question_tokens = set(_topic_tokens(question))
    if not question_tokens:
        return False
    for prior in previous:
        prior_tokens = set(_topic_tokens(prior))
        if not prior_tokens:
            continue
        overlap = question_tokens & prior_tokens
        if len(overlap) >= 4 or len(overlap) / max(len(question_tokens), 1) >= 0.45:
            return True
    return False


def _question_similarity(question_a: str, question_b: str) -> float:
    a = " ".join(str(question_a).lower().split())
    b = " ".join(str(question_b).lower().split())
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def is_semantically_duplicate(question_a: str, question_b: str, threshold: float = 0.85) -> bool:
    return _question_similarity(question_a, question_b) >= threshold and key_terms_overlap(question_a, question_b) > 0.5


def key_terms_overlap(question_a: str, question_b: str) -> float:
    stop_words = {
        "how", "would", "you", "the", "and", "with", "your", "what", "when", "where", "why", "about",
        "time", "this", "that", "have", "been", "from", "under", "into", "over", "into", "does", "did",
        "using", "through", "describe", "tell", "me", "a", "an", "to", "of", "for", "in", "on", "at",
        "is", "are", "was", "were", "do", "does", "can", "could", "should",
    }

    def _terms(question: str) -> set[str]:
        tokens = [token.strip("?,.!:;()[]{}").lower() for token in str(question).split()]
        return {
            token
            for token in tokens
            if len(token) > 3 and token not in stop_words and not token.isdigit()
        }

    terms_a = _terms(question_a)
    terms_b = _terms(question_b)
    if not terms_a or not terms_b:
        return 0.0
    overlap = terms_a & terms_b
    return len(overlap) / max(min(len(terms_a), len(terms_b)), 1)


def _question_opening_style(question: str) -> str:
    opening = " ".join(str(question).lower().split())
    for prefix in ("how would you", "how do you", "what would you", "describe a", "tell me about", "walk me through", "give an example"):
        if opening.startswith(prefix):
            return prefix
    return " ".join(opening.split()[:4])


def same_question_pattern(question_a: str, question_b: str) -> bool:
    return _question_opening_style(question_a) == _question_opening_style(question_b)


def _soft_validate_question(question: str, role: str, cv_context: str, jd_context: str) -> bool:
    question_lower = question.lower()
    role_keywords = _extract_role_keywords(role)
    cv_keywords = _extract_context_keywords(cv_context)
    jd_keywords = _extract_context_keywords(jd_context)
    if role_keywords and not any(keyword in question_lower for keyword in role_keywords):
        return False
    if cv_context.strip() and cv_keywords and not any(keyword in question_lower for keyword in cv_keywords):
        return False
    if jd_context.strip() and jd_keywords and not any(keyword in question_lower for keyword in jd_keywords):
        return False
    return True


def is_valid_question(question: str) -> bool:
    if not isinstance(question, str) or len(question.strip()) < 20:
        return False
    if "?" not in question:
        return False
    return True


def _is_generic_question(question_lower: str) -> bool:
    return any(
        phrase in question_lower
        for phrase in (
            "how would you apply your experience",
            "how would you apply your relevant experience",
            "based on your experience",
            "your relevant experience",
            "explain your approach",
            "what would you do in general",
            "tell me about yourself",
            "describe yourself",
        )
    )


def validate_question(question: str, focus: str, question_type: str = "technical") -> tuple[bool, str]:
    if not question.strip():
        return False, "empty"

    question_lower = question.lower()

    if focus.lower() == "performance":
        has_performance_keyword = any(kw in question_lower for kw in PERFORMANCE_KEYWORDS)
        if not has_performance_keyword:
            return False, "missing_performance_keyword"

    if _is_generic_question(question_lower):
        return False, "abstract_question"

    if question_type == "behavioural":
        behavioural_indicators = ["tell me about", "describe a time", "walk me through", "give an example"]
        if not any(indicator in question_lower for indicator in behavioural_indicators):
            return False, "no_behavioural_scenario"
        return True, "valid"

    if question_type == "system_design":
        design_indicators = ["design", "architect", "scalable", "reliability", "trade-off", "load"]
        if not any(indicator in question_lower for indicator in design_indicators):
            return False, "no_system_design_scenario"
        return True, "valid"

    scenario_indicators = [
        "your application", "your api", "a page", "a user", "a colleague", "the system", "endpoint",
        "your data", "your database", "your pipeline", "your server", "your code", "your query",
    ]
    if not any(indicator in question_lower for indicator in scenario_indicators):
        return False, "no_scenario"

    return True, "valid"


def _passes_generation_checks(question: str, role: str, difficulty: str, focus: str, question_type: str) -> bool:
    return _soft_validate_question(question, role, focus, difficulty)


def _build_fallback_detail(question_plan: dict[str, object]) -> str:
    question_type = str(question_plan.get("question_type", "role_based"))
    role_keywords = list(question_plan.get("role_keywords", []) or [])
    cv_keywords = list(question_plan.get("cv_keywords", []) or [])
    jd_keywords = list(question_plan.get("jd_keywords", []) or [])
    focus_area = str(question_plan.get("focus_area", "")).strip()
    focus_label = str(question_plan.get("focus_label", "")).strip() or focus_area.replace("_", " ")
    if question_type == "cv_based":
        return cv_keywords[0] if cv_keywords else focus_label or "the experience highlighted in your CV"
    if question_type == "jd_based":
        return jd_keywords[0] if jd_keywords else focus_label or "the requirement in the job description"
    if question_type == "gap_targeted":
        return (jd_keywords[0] if jd_keywords else "") or (cv_keywords[0] if cv_keywords else "") or focus_label or "the weakest area"
    if question_type == "deep_dive":
        return " and ".join([item for item in [role_keywords[0] if role_keywords else "", jd_keywords[0] if jd_keywords else "", focus_label] if item]) or "the trade-off"
    return role_keywords[0] if role_keywords else focus_label or "the role"


def _pick_template(values: list[str], question_index: int, previous_questions: list[str] | None) -> str:
    offset = len(previous_questions or [])
    return values[offset % len(values)]


def generate_safe_fallback(
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str = "",
    jd_context: str = "",
    question_type: str = "behavioural",
    question_index: int = 1,
    previous_questions: list[str] | None = None,
    question_plan: dict[str, object] | None = None,
) -> str:
    if not cv_context.strip() and not jd_context.strip() and focus.lower() != "performance":
        templates = {
            "follow_up": [
                "A team has already investigated a production issue in your {role} work, but the root cause is still unclear. What additional evidence would you ask for, and how would it change your next step?",
                "A production incident in your {role} work has been reopened after an initial fix. What would you check next to avoid repeating the same mistake?",
                "Stakeholders are pressuring your {role} team for a quick fix. How would you maintain investigative rigour while managing expectations?",
                "Your fix in this {role} system caused a new regression. How would you diagnose whether it's related or a separate issue?",
                "The incident in your {role} work is escalating. How would you decide whether to roll back immediately or continue investigating?",
            ],
            "deep_dive": [
                "A recent release caused a production issue in your {role} work. How would you weigh the trade-offs, choose a safe fix, and keep delivery moving?",
                "A complex issue appears after a change goes live in your {role} system. How would you investigate, compare options, and choose the safest path forward?",
                "A critical bug surfaces mid-sprint in your {role} team. How would you balance fixing it properly versus meeting the deadline?",
                "A production incident recurs after a hotfix in your {role} work. What would you do differently to ensure a lasting solution?",
                "You're asked to ship an incomplete feature in your {role} role. How would you negotiate scope, quality, and timing to protect the release?",
            ],
            "cv_based": [
                "You have handled similar work before in your {role} role. A production issue now affects your application after a release. How would you apply that experience to diagnose and fix it?",
                "You have solved similar problems before as a {role}. How would you use that experience to recover a production regression in this role?",
                "Your past {role} project faced a similar incident. What would you do differently this time based on those lessons?",
                "You've seen this issue before in your {role} work. How would you apply your prior knowledge to prevent it from recurring?",
                "A past failure in your {role} work taught you a valuable lesson. How would you use that to handle this new production issue?",
            ],
            "jd_based": [
                "A production issue has appeared in your {role} application. How would you respond and keep the release stable?",
                "The {role} role requires strong problem-solving under pressure. How would you handle a real-world issue that tests that requirement?",
                "This {role} position demands incident management skills. How would you demonstrate those while handling this production crisis?",
                "Your {role} role involves maintaining system reliability. How would you address a critical issue while minimising user impact?",
                "Stakeholders depend on system uptime in this {role} team. How would you handle this incident and communicate progress effectively?",
            ],
            "gap_targeted": [
                "You need to strengthen a key skill in your {role} work. A production issue appears in your application. How would you handle it while closing that gap?",
                "A {role} project is exposing a gap in your experience. How would you close that gap and keep the work stable?",
                "Your weakness is incident response in your {role} role. How would you develop that skill while handling this real production issue?",
                "There's a gap between your {role} experience and the role requirements. How would you bridge it while managing this crisis?",
                "You lack deep experience in this {role} area. How would you compensate and still deliver a solid solution?",
            ],
        }
        template = _pick_template(templates.get(question_type, templates["deep_dive"]), question_index, previous_questions)
        return template.format(role=role.lower(), detail="the role", focus=focus.lower() or "the role")

    plan = question_plan or build_question_prompt_context(
        role=role,
        difficulty=difficulty,
        question_index=question_index,
        cv_context=cv_context,
        jd_context=jd_context,
        previous_questions=previous_questions,
        focus=focus,
        question_type=question_type,
    )
    role_lower = str(plan.get("role", role)).lower().strip() or "the team"
    question_type = str(plan.get("question_type", question_type))
    detail = _build_fallback_detail(plan)
    cv_hint = list(plan.get("cv_keywords", []) or [])
    jd_hint = list(plan.get("jd_keywords", []) or [])
    role_hint = list(plan.get("role_keywords", []) or [])
    role_focus = role_hint[0] if role_hint else (role_lower.split()[0] if role_lower else "application")
    previous = list(previous_questions or [])
    template = next(
        (value for key, value in ROLE_FALLBACK_TEMPLATES.items() if key in role_lower),
        "You are working on a {role} team where a recent change affects {detail}. How would you investigate the issue, decide on a fix, and keep the release stable?",
    )
    if focus.lower() == "performance":
        detail = detail if detail != "the role" else "performance"
        if difficulty.lower() == "easy":
            return f"A user reports that a page in your application takes several seconds to load. How would you investigate {detail} and improve performance without causing regressions?"
        return f"Your application is experiencing performance issues under load. How would you investigate {detail}, identify the bottleneck, and improve performance safely?"
    if question_type == "cv_based" and cv_context.strip():
        scenario = f"a realistic issue in a {role_lower} project"
        if jd_hint:
            scenario = f"{scenario} that also touches {jd_hint[0]}"
        template = _pick_template(QUESTION_TYPE_TEMPLATES["cv_based"], question_index, previous)
        return template.format(cv_skill=detail, scenario=scenario, role_focus=role_focus, role=role_lower)
    if question_type == "jd_based" and jd_context.strip():
        scenario = f"a release issue for a {role_lower} team"
        if cv_hint:
            scenario = f"{scenario} building on {cv_hint[0]}"
        template = _pick_template(QUESTION_TYPE_TEMPLATES["jd_based"], question_index, previous)
        return template.format(jd_requirement=detail, scenario=scenario, role_focus=role_focus, role=role_lower)
    if question_type == "gap_targeted":
        template = _pick_template(QUESTION_TYPE_TEMPLATES["gap_targeted"], question_index, previous)
        return template.format(strength=f"your {role_lower} experience", gap=detail, role_focus=role_focus, role=role_lower)
    if question_type == "deep_dive":
        question = template.format(role=role_lower, detail=detail)
        return question.replace("How would you investigate the issue, decide on a fix, and keep the release stable?", "How would you weigh the trade-offs, make the decision, and keep the release stable?")
    return template.format(role=role_lower, detail=detail)


def generate_fallback_question(
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str = "",
    jd_context: str = "",
    question_type: str = "behavioural",
    question_index: int = 1,
    previous_questions: list[str] | None = None,
    question_plan: dict[str, object] | None = None,
) -> str:
    return generate_safe_fallback(
        role=role,
        difficulty=difficulty,
        focus=focus,
        cv_context=cv_context,
        jd_context=jd_context,
        question_type=question_type,
        question_index=question_index,
        previous_questions=previous_questions,
        question_plan=question_plan,
    )


def _avoid_topics_line(asked_topics: list[str]) -> str:
    topics = [topic.strip() for topic in asked_topics if str(topic).strip()]
    if not topics:
        return ""
    return "Avoid repeating these topics: " + ", ".join(topics) + "\n"


def _topic_tokens(text: str) -> list[str]:
    cleaned = text.lower().replace("?", " ").replace(",", " ").replace("/", " ")
    return [token for token in cleaned.split() if len(token) > 3]


def derive_question_topics(question: str) -> list[str]:
    return list(dict.fromkeys(_topic_tokens(question)))


def normalise_topic(topic: str) -> str:
    return str(topic).lower().strip()


def extract_topic(question: str) -> str:
    topics = derive_question_topics(question)
    return normalise_topic(" ".join(topics[:3]))


def _matches_context(question: str, cv_context: str, jd_context: str) -> bool:
    question_text = question.lower()
    context_tokens = _topic_tokens(cv_context) + _topic_tokens(jd_context)
    generic_terms = {"system", "experience", "work", "role", "question"}
    context_hits = [token for token in context_tokens if token not in generic_terms and token in question_text]
    return bool(context_hits)


def _topic_relevance(question: str, cv_context: str, jd_context: str, question_type: str = "behavioural", focus: str = "") -> bool:
    question_lower = question.lower()
    focus_lower = (focus or "").lower()

    performance_terms = [
        "slow", "latency", "load time", "response time", "performance",
        "optimise", "optimize", "query", "api", "database", "frontend", "backend",
    ]

    if "performance" in focus_lower:
        if any(term in question_lower for term in performance_terms):
            return True

    combined_context = f"{cv_context} {jd_context}".strip().lower()
    if not combined_context:
        return True

    if question_type in ("cv_based", "jd_based", "gap_targeted"):
        context_tokens = set(_topic_tokens(cv_context) + _topic_tokens(jd_context))
        if not context_tokens:
            return True

        if _matches_context(question, cv_context, jd_context):
            return True

        topic = extract_topic(question)
        if not topic:
            return False
        topic_tokens = set(topic.split())
        if topic_tokens & context_tokens:
            return True
        return False

    return True


def _build_strict_system_prompt(role: str, difficulty: str, persona: str, focus: str) -> str:
    return (
        "You are a senior technical interviewer.\n\n"
        "Generate ONE interview question based on the configuration.\n\n"
        "STRICT RULES:\n"
        "- The question MUST reflect the selected role, difficulty, persona, and focus.\n"
        "- The question MUST follow the priority order: role first, then CV if provided, then job description.\n"
        "- The question MUST be concrete, not abstract.\n"
        "- The question MUST include a realistic scenario.\n"
        "- The question MUST be answerable in 2–4 minutes (for Easy difficulty).\n"
        "- The question MUST test applied thinking, not theory.\n\n"
        f"ROLE: {role}\n"
        f"DIFFICULTY: {difficulty}\n"
        f"PERSONA: {persona}\n"
        f"FOCUS: {focus}\n\n"
        "QUESTION DESIGN RULES:\n"
        "- For Easy: Use simple, relatable scenarios (e.g. slow API, UI lag, basic DB query). Avoid system design or large-scale architecture.\n"
        "- For Performance Optimisation: Must include a performance issue (latency, slow load, inefficient query, etc.)\n"
        "- For Full Stack: Should involve frontend + backend OR API + DB interaction\n\n"
        "- Vary the scenario and focus area each time to avoid repetition.\n"
        "OUTPUT FORMAT:\n"
        "Return ONLY the question.\n"
        "No explanation.\n"
    )


def _build_few_shot_section(role: str, difficulty: str, focus: str) -> str:
    key = (role, difficulty, focus)
    examples = FEW_SHOT_EXAMPLES.get(key, [])

    if not examples:
        return ""

    section = "\nExamples:\n"
    for example in examples:
        section += f"Configuration: {example['Configuration']}\n"
        section += f"Question:\n{example['Question']}\n\n"
    return section


def _build_template_guidance(role: str, difficulty: str, focus: str) -> str:
    template = _select_template(difficulty, focus)
    if template:
        return f"\nTemplate reference (use this structure):\n{template}\n"
    return ""


def _normalise_temperature(value: object | None) -> float:
    try:
        return float(value) if value is not None else 0.7
    except (TypeError, ValueError):
        return 0.7


def _question_prompt_style() -> str:
    return str(get_model_profile(MODEL_NAME).get("prompt_style", "strict"))


def _question_retry_limit() -> int:
    return get_retry_limit(MODEL_NAME)


def _question_strict_json(model_name: str | None = None) -> bool:
    profile = get_model_profile(model_name or MODEL_NAME)
    return bool(profile.get("strict_json", True))


def _question_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("question", "")).strip()
    return str(item).strip()


def _question_item(question: str, payload: dict[str, object]) -> dict[str, object]:
    scenario_type = _normalise_scenario_type(payload.get("scenario_type"), str(payload.get("question_type", "")))
    return {
        "question": question,
        "question_type": str(payload.get("question_type", "cv_based")).strip() or "cv_based",
        "scenario_type": scenario_type,
        "dimension": DIMENSION_BY_SCENARIO_TYPE.get(scenario_type, "debugging / regression recovery"),
        "focus_area": str(payload.get("focus_area", payload.get("focus", ""))).strip(),
        "source_basis": {
            "cv_terms_used": list(payload.get("cv_keywords", []) or []),
            "jd_terms_used": list(payload.get("jd_keywords", []) or []),
            "gap_used": payload.get("gap_used"),
        },
        "difficulty_level": str(payload.get("difficulty", "")).strip(),
        "what_interviewer_is_testing": [str(payload.get("purpose", "")).strip()] if str(payload.get("purpose", "")).strip() else [],
    }


def _filter_question_items(
    items: list[dict[str, object]],
    *,
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str,
    jd_context: str,
    question_type: str,
    previous_questions: list[str] | None,
    required_count: int,
) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in items:
        question = _question_text(item)
        if not is_valid_question(question):
            continue
        lowered = question.lower()
        if lowered in seen or _is_similar_to_previous(question, previous_questions):
            continue
        item_type = str(item.get("question_type", question_type)).strip() or question_type
        item_focus = str(item.get("focus_area", focus)).strip() or focus
        if not validate_question(question, item_focus or focus, item_type)[0]:
            continue
        if not _topic_relevance(question, cv_context, jd_context, item_type, focus):
            continue
        if not _soft_validate_question(question, role, cv_context, jd_context):
            continue
        if any(is_semantically_duplicate(question, existing["question"]) for existing in filtered if isinstance(existing, dict)):
            continue
        filtered.append(_question_item(question, {**item, "question_type": item_type, "focus_area": item_focus, "difficulty": difficulty, "purpose": item.get("what_interviewer_is_testing", [])[:1] if isinstance(item.get("what_interviewer_is_testing"), list) else ""}))
        seen.add(lowered)
        if len(filtered) >= required_count:
            break
    return filtered


def is_duplicate(question: dict[str, object], existing: dict[str, object]) -> bool:
    return is_semantically_duplicate(_question_text(question), _question_text(existing)) or same_question_pattern(_question_text(question), _question_text(existing))


def deduplicate_questions(questions: list[dict[str, object]]) -> list[dict[str, object]]:
    unique: list[dict[str, object]] = []
    scenario_counts: Counter[str] = Counter()
    for question in questions:
        if not isinstance(question, dict):
            continue
        scenario_type = _normalise_scenario_type(question.get("scenario_type"), str(question.get("question_type", "")))
        if scenario_counts[scenario_type] >= MAX_SCENARIO_TYPE_COUNT:
            continue
        if any(is_duplicate(question, existing) for existing in unique):
            continue
        unique.append({**question, "scenario_type": scenario_type, "dimension": DIMENSION_BY_SCENARIO_TYPE.get(scenario_type, "debugging / regression recovery")})
        scenario_counts[scenario_type] += 1
    if len(unique) < 5:
        raise DuplicateQuestionError("Generated question set collapsed below five unique questions")
    return unique


def _supported_terms_for_context(role: str, cv_context: str, jd_context: str) -> set[str]:
    context = resolve_missing_context(role, cv_context, jd_context)
    terms = set(context["role_keywords"]) | set(context["cv_keywords"]) | set(context["jd_keywords"])
    role_lower = " ".join(str(role).split()).lower()
    terms.add(role_lower)

    active_groups: set[str] = set()
    for term in terms:
        lowered = term.lower()
        group = TERM_TO_GROUP.get(lowered)
        if group:
            active_groups.add(group)
    for group_name, synonyms in ROLE_BASELINE_GROUPS.items():
        if group_name in role_lower:
            active_groups.update(synonyms)

    allowed_terms: set[str] = set()
    for group in active_groups:
        allowed_terms.update(SEMANTIC_TECH_GROUPS.get(group, set()))
    allowed_terms.update(terms)
    return {term for term in allowed_terms if term}


def _expand_semantic_terms(base_terms: set[str]) -> set[str]:
    expanded = set(base_terms)
    active_groups: set[str] = set()
    for term in base_terms:
        group = TERM_TO_GROUP.get(term)
        if group:
            active_groups.add(group)
    for group in active_groups:
        expanded.update(SEMANTIC_TECH_GROUPS.get(group, set()))
    return expanded


def _contextual_supported_terms(mode: str, role: str, cv_context: str, jd_context: str) -> set[str]:
    context = resolve_missing_context(role, cv_context, jd_context)
    base_terms = set(ROLE_ONLY_GROUNDING_TERMS) | set(context["role_keywords"])
    if mode in {"jd_only", "cv_jd"}:
        base_terms.update(context["jd_keywords"])
    if mode in {"cv_only", "cv_jd"}:
        base_terms.update(context["cv_keywords"])
    return _expand_semantic_terms(base_terms)


def _context_mode(cv_context: str, jd_context: str) -> str:
    has_cv = bool(" ".join(str(cv_context).split()).strip())
    has_jd = bool(" ".join(str(jd_context).split()).strip())
    if has_cv and has_jd:
        return "cv_jd"
    if has_jd:
        return "jd_only"
    if has_cv:
        return "cv_only"
    return "role_only"


def _source_terms(item: dict[str, object]) -> tuple[list[str], list[str]]:
    source_basis = item.get("source_basis") if isinstance(item.get("source_basis"), dict) else {}
    cv_terms = [str(term).strip().lower() for term in list(source_basis.get("cv_terms_used", []) or []) if str(term).strip()]
    jd_terms = [str(term).strip().lower() for term in list(source_basis.get("jd_terms_used", []) or []) if str(term).strip()]
    return cv_terms, jd_terms


def _classify_dimension(item: dict[str, object]) -> str:
    scenario_type = _normalise_scenario_type(item.get("scenario_type"), str(item.get("question_type", "")))
    return DIMENSION_BY_SCENARIO_TYPE.get(scenario_type, "debugging / regression recovery")


def _has_allowed_term(question: str, allowed_terms: set[str]) -> bool:
    lowered = question.lower()
    return any(term in lowered for term in allowed_terms)


def _bundle_dimensions(questions: list[dict[str, object]]) -> list[str]:
    return [_classify_dimension(question) for question in questions if isinstance(question, dict)]


def _has_supported_grounding(question: str, supported_terms: set[str]) -> bool:
    lowered = question.lower()
    return any(term in lowered for term in supported_terms)


def _has_hallucinated_tech(question: str, supported_terms: set[str]) -> bool:
    lowered = question.lower()
    for term in COMMON_TECH_TERMS:
        if term in lowered and term not in supported_terms:
            group = TERM_TO_GROUP.get(term)
            if group and any(alias in supported_terms for alias in SEMANTIC_TECH_GROUPS.get(group, set())):
                continue
            return True
    return False


def _validate_question_bundle(
    questions: list[dict[str, object]],
    *,
    role: str,
    cv_context: str,
    jd_context: str,
) -> tuple[bool, str]:
    if len(questions) < 1 or len(questions) > 10:
        return False, "invalid_question_count"

    scenario_types = [_normalise_scenario_type(item.get("scenario_type"), str(item.get("question_type", ""))) for item in questions if isinstance(item, dict)]
    if len(scenario_types) != len(set(scenario_types)):
        return False, "duplicate_scenario_classification"
    if len(questions) >= 5 and set(scenario_types) != set(REQUIRED_SCENARIO_DIMENSIONS):
        return False, "missing_dimension_coverage"

    context_mode = _context_mode(cv_context, jd_context)
    context_terms = resolve_missing_context(role, cv_context, jd_context)
    cv_keywords = set(context_terms["cv_keywords"])
    jd_keywords = set(context_terms["jd_keywords"])
    any_cv_grounding = False
    any_jd_grounding = False
    any_combined_grounding = False
    supported_terms = _contextual_supported_terms(context_mode, role, cv_context, jd_context)

    for item in questions:
        if not isinstance(item, dict):
            return False, "invalid_question_item"
        question = _question_text(item)
        cv_terms, jd_terms = _source_terms(item)
        dimension = _classify_dimension(item)
        if item.get("dimension") and str(item.get("dimension")).strip() != dimension:
            return False, "dimension_mismatch"
        if dimension not in DIMENSION_BY_SCENARIO_TYPE.values():
            return False, "invalid_dimension"
        if context_mode == "role_only":
            if any(term in question.lower() for term in COMMON_TECH_TERMS):
                return False, "scenario_a_contains_tech"
            if cv_terms or jd_terms:
                return False, "scenario_a_contains_source_terms"
        elif context_mode == "jd_only":
            if cv_terms:
                return False, "scenario_b_contains_cv_terms"
            if jd_keywords and not (jd_terms or _has_allowed_term(question, supported_terms)):
                return False, "scenario_b_missing_jd_grounding"
        elif context_mode == "cv_jd":
            has_cv_signal = bool(cv_terms) or _has_allowed_term(question, supported_terms | cv_keywords)
            has_jd_signal = bool(jd_terms) or _has_allowed_term(question, supported_terms | jd_keywords)
            any_cv_grounding = any_cv_grounding or has_cv_signal
            any_jd_grounding = any_jd_grounding or has_jd_signal
            any_combined_grounding = any_combined_grounding or (has_cv_signal and has_jd_signal)
        elif context_mode == "cv_only":
            if jd_terms:
                return False, "scenario_cv_only_contains_jd_terms"
        if len(questions) >= 5 and not _has_supported_grounding(question, supported_terms):
            return False, "ungrounded_question"
        if len(questions) >= 5 and _has_hallucinated_tech(question, supported_terms):
            return False, "hallucinated_tech"
        if dimension == "debugging / regression recovery" and "regression" not in question.lower() and "debug" not in question.lower():
            continue
    if context_mode == "cv_jd":
        if not any_cv_grounding:
            return False, "scenario_c_missing_cv_grounding"
        if not any_jd_grounding:
            return False, "scenario_c_missing_jd_grounding"
        if not any_combined_grounding:
            return False, "scenario_c_missing_alignment"
    return True, "valid"


def _raise_fallback_validation_error(reason: str) -> list[dict[str, object]]:
    LOGGER.error("Fallback generation failed validation: %s", reason)
    return []


def _validate_single_question(
    question: str,
    *,
    role: str,
    cv_context: str,
    jd_context: str,
    focus: str,
    question_type: str,
) -> tuple[bool, str]:
    if not is_valid_question(question):
        return False, "invalid_question"
    is_valid, reason = validate_question(question, focus, question_type)
    if not is_valid:
        return False, reason
    context_mode = _context_mode(cv_context, jd_context)
    supported_terms = _contextual_supported_terms(context_mode, role, cv_context, jd_context)
    if not _topic_relevance(question, cv_context, jd_context, question_type, focus):
        return False, "ungrounded_question"
    if not _soft_validate_question(question, role, cv_context, jd_context):
        return False, "missing_context_grounding"
    if _has_hallucinated_tech(question, supported_terms):
        return False, "hallucinated_tech"
    return True, "valid"


def _validated_fallback_bundle(
    *,
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str,
    jd_context: str,
    question_type: str,
    previous_questions: list[str] | None,
    question_plan: dict[str, object] | None,
    required_count: int,
) -> list[dict[str, object]]:
    fallback_items = _fallback_question_items(
        role=role,
        difficulty=difficulty,
        focus=focus,
        cv_context=cv_context,
        jd_context=jd_context,
        question_type=question_type,
        previous_questions=previous_questions,
        question_plan=question_plan,
        required_count=required_count,
    )
    valid, reason = _validate_question_bundle(fallback_items, role=role, cv_context=cv_context, jd_context=jd_context)
    if not valid:
        LOGGER.warning("Fallback validation warning: %s - returning generated items anyway", reason)
    return fallback_items


def _fallback_question_items(
    *,
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str,
    jd_context: str,
    question_type: str,
    previous_questions: list[str] | None,
    question_plan: dict[str, object] | None,
    required_count: int,
) -> list[dict[str, object]]:
    fallback: list[dict[str, object]] = []
    previous: list[str] = list(previous_questions or [])
    count = max(5, min(required_count or 5, 10))
    fallback_question_types = ["cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted"]
    base_plan = question_plan or _build_question_plan(
        role=role,
        difficulty=difficulty,
        question_index=1,
        cv_context=cv_context,
        jd_context=jd_context,
        asked_topics=[],
        focus=focus,
        question_type=question_type,
        previous_questions=previous_questions,
    )
    for index in range(1, count + 1):
        generated_question_type = fallback_question_types[(index - 1) % len(fallback_question_types)]
        item_plan = _build_question_plan(
            role=role,
            difficulty=difficulty,
            question_index=index,
            cv_context=cv_context,
            jd_context=jd_context,
            asked_topics=[],
            focus=focus,
            question_type=generated_question_type,
            previous_questions=previous,
        )
        item_plan = {**base_plan, **item_plan, "question_index": index, "question_type": generated_question_type}
        scenario_type = QUESTION_TYPE_TO_SCENARIO_TYPE.get(generated_question_type, "debugging")
        question = generate_safe_fallback(
            role=role,
            difficulty=difficulty,
            focus=focus,
            cv_context=cv_context,
            jd_context=jd_context,
            question_type=generated_question_type,
            question_index=index,
            previous_questions=previous,
            question_plan=item_plan,
        )
        if not question or question.lower() in {entry.lower() for entry in previous}:
            continue
        previous.append(question)
        fallback.append(_question_item(question, item_plan))
        fallback[-1]["scenario_type"] = scenario_type
    return fallback[:10]


def _build_question_meta(items: list[dict[str, object]] | None) -> dict[str, object]:
    distribution = {key: 0 for key in ("cv_based", "jd_based", "behavioural", "deep_dive", "gap_targeted")}
    questions = [item for item in items or [] if isinstance(item, dict)]
    for item in questions:
        question_type = str(item.get("question_type", "")).strip()
        if question_type in distribution:
            distribution[question_type] += 1
    return {"total_questions": len(questions), "distribution": distribution}


def _generate_with_retry(
    prompt: str,
    client: object,
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str,
    jd_context: str,
    question_type: str,
    question_index: int = 1,
    previous_questions: list[str] | None = None,
    question_plan: dict[str, object] | None = None,
    temperature: object | None = None,
    question_list_count: int = 1,
    retries: int | None = None,
    return_meta: bool = False,
    use_provider_fallback: bool = True,
    should_abort: Callable[[], bool] | None = None,
) -> str | list[dict[str, object]] | dict[str, object]:
    retries = _question_retry_limit() if retries is None else retries
    last_response = ""
    last_meta: dict[str, object] | None = None
    last_call_log: CallLog | None = None

    for attempt in range(retries + 1):
        try:
            task_name = f"question_generation.{question_type}"

            if use_provider_fallback:
                temp = _normalise_temperature(temperature)
                response = call_llm(
                    prompt,
                    client,
                    temperature=temp,
                    task=task_name,
                    provider="open-router",
                    should_abort=should_abort if callable(should_abort) else None,
                )
                metadata = get_last_llm_call_metadata()
                last_response = response or ""
                last_call_log = CallLog(
                    provider_used=str(metadata.get("provider", "open-router")).strip() or "open-router",
                    fallback_reason=None,
                    attempts=1,
                    response_valid=bool(last_response.strip()),
                    latency_ms=0.0,
                    error=None if last_response.strip() else "invalid_json",
                )
                LOGGER.info(
                    "Question generation call: provider=%s model=%s valid=%s",
                    last_call_log.provider_used,
                    str(metadata.get("model", "")).strip() or "unknown",
                    last_call_log.response_valid,
                )
            else:
                last_response = call_llm(prompt, client, temperature=_normalise_temperature(temperature), task=task_name)

        except (StopIteration, RuntimeError) as e:
            if "Free model limit reached" in str(e):
                raise
            LOGGER.warning(f"LLM call failed: {e}, using fallback")
            last_response = ""

        try:
            metadata_model = str(get_last_llm_call_metadata().get("model") or MODEL_NAME).strip() or MODEL_NAME
            parsed_items = parse_question_generation_response(last_response, strict=_question_strict_json(metadata_model))
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed_items = []

        if question_list_count > 1:
            filtered = _filter_question_items(
                parsed_items,
                role=role,
                difficulty=difficulty,
                focus=focus,
                cv_context=cv_context,
                jd_context=jd_context,
                question_type=question_type,
                previous_questions=previous_questions,
                required_count=question_list_count,
            )
            try:
                unique_questions = deduplicate_questions(filtered)
            except DuplicateQuestionError:
                unique_questions = []
            valid_bundle, validation_reason = _validate_question_bundle(
                unique_questions,
                role=role,
                cv_context=cv_context,
                jd_context=jd_context,
            )
            logger_payload = [_question_text(item) for item in unique_questions or filtered]
            LOGGER.warning("Generated questions: %s", logger_payload)
            if not valid_bundle:
                LOGGER.warning("Question bundle validation failed: %s", validation_reason)
            if valid_bundle:
                if last_response:
                    try:
                        last_meta = extract_question_generation_meta(last_response)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        last_meta = None
                if last_meta is None:
                    last_meta = _build_question_meta(unique_questions)
                return {"questions": unique_questions, "meta": last_meta} if return_meta else unique_questions
            LOGGER.warning(f"Invalid question list format, attempt {attempt + 1}")
            if attempt >= retries:
                break
            continue

        last_question = _question_text(parsed_items[0]) if parsed_items else ""
        if not is_valid_question(last_question):
            LOGGER.warning(f"Invalid question format, attempt {attempt + 1}")
            if attempt >= retries:
                break
            continue

        is_valid, validation_reason = validate_question(last_question, focus, question_type)
        if is_valid and _topic_relevance(last_question, cv_context, jd_context, question_type, focus) and not _is_similar_to_previous(last_question, previous_questions) and _soft_validate_question(last_question, role, cv_context, jd_context):
            if question_list_count > 1:
                meta = None
                if last_response:
                    try:
                        meta = extract_question_generation_meta(last_response)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        meta = None
                bundle = {"questions": [last_question], "meta": meta or _build_question_meta([{"question": last_question, "question_type": question_type}])}
                return bundle if return_meta else [last_question]
            return last_question
        LOGGER.warning(f"Validation failed: {validation_reason}, attempt {attempt + 1}")

        if attempt >= retries:
            break

    LOGGER.warning("Invalid LLM response after retries, fallback triggered")
    if question_list_count > 1:
        fallback_items = _validated_fallback_bundle(
            role=role,
            difficulty=difficulty,
            focus=focus,
            cv_context=cv_context,
            jd_context=jd_context,
            question_type=question_type,
            previous_questions=previous_questions,
            question_plan=question_plan,
            required_count=question_list_count,
        )
        bundle = {"questions": fallback_items, "meta": _build_question_meta(fallback_items)}
        return bundle if return_meta else fallback_items
    fallback_question = generate_safe_fallback(
        role=role,
        difficulty=difficulty,
        focus=focus,
        cv_context=cv_context,
        jd_context=jd_context,
        question_type=question_type,
        question_index=question_index,
        previous_questions=previous_questions,
        question_plan=question_plan,
    )
    valid, reason = _validate_single_question(
        fallback_question,
        role=role,
        cv_context=cv_context,
        jd_context=jd_context,
        focus=focus,
        question_type=question_type,
    )
    if not valid:
        LOGGER.warning("Single fallback validation warning: %s - returning generated item anyway", reason)
    return fallback_question


def _get_client_or_none() -> object | None:
    try:
        return get_openrouter_client()
    except Exception:
        LOGGER.warning("LLM client unavailable, using fallback question")
        return None


def _build_question_plan(
    role: str,
    difficulty: str,
    question_index: int,
    cv_context: str,
    jd_context: str,
    asked_topics: list[str] | None,
    focus: str,
    question_type: str | None,
    previous_questions: list[str] | None = None,
) -> dict[str, object]:
    return build_question_prompt_context(
        role=role,
        difficulty=difficulty,
        question_index=question_index,
        cv_context=cv_context,
        jd_context=jd_context,
        previous_questions=previous_questions,
        asked_topics=asked_topics,
        focus=focus,
        question_type=question_type or "auto",
    )


def fallback_questions(
    *,
    role: str,
    difficulty: str,
    focus: str,
    cv_context: str,
    jd_context: str,
    question_type: str,
    previous_questions: list[str] | None,
    question_plan: dict[str, object] | None,
    required_count: int = 5,
) -> list[dict[str, object]]:
    return _validated_fallback_bundle(
        role=role,
        difficulty=difficulty,
        focus=focus,
        cv_context=cv_context,
        jd_context=jd_context,
        question_type=question_type,
        previous_questions=previous_questions,
        question_plan=question_plan,
        required_count=required_count,
    )


def build_question_prompt(
    role: str,
    difficulty: str,
    persona: str,
    response_style: str,
    cv_context: str,
    question_index: int | None = None,
    jd_context: str = "",
    asked_topics: list[str] | None = None,
    focus: str = "General",
    tech_stack: list[str] | None = None,
    competencies: list[str] | None = None,
    question_type: str | None = None,
    previous_questions: list[str] | None = None,
    temperature: object | None = None,
    gap_analysis: object | None = None,
) -> str:
    plan = _build_question_plan(
        role=role,
        difficulty=difficulty,
        question_index=question_index or 1,
        cv_context=cv_context,
        jd_context=jd_context,
        asked_topics=asked_topics,
        focus=focus,
        question_type=question_type,
        previous_questions=previous_questions,
    )
    return build_question_generation_prompt(
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        persona=persona,
        response_style=response_style,
        temperature=temperature if temperature is not None else 0.7,
        cv_profile=str(plan["cv_context"]),
        job_description=str(plan["jd_context"]),
        gap_analysis=gap_analysis or {"focus": str(plan["focus"]), "focus_area": str(plan["focus_area"]), "question_type": str(plan["question_type"])},
        prompt_style=_question_prompt_style(),
    )


def get_next_question(
    role: str,
    difficulty: str,
    persona: str,
    response_style: str,
    cv_context: str,
    jd_context: str = "",
    asked_topics: list[str] | None = None,
    focus: str = "General",
    tech_stack: list[str] | None = None,
    competencies: list[str] | None = None,
    question_type: str | None = None,
    previous_questions: list[str] | None = None,
    temperature: object | None = None,
    gap_analysis: object | None = None,
    question_list_count: int = 1,
) -> str | list[dict[str, object]]:
    plan = _build_question_plan(
        role=role,
        difficulty=difficulty,
        question_index=1,
        cv_context=cv_context,
        jd_context=jd_context,
        asked_topics=asked_topics,
        focus=focus,
        question_type=question_type,
        previous_questions=previous_questions,
    )
    prompt = build_question_prompt(
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        persona=persona,
        response_style=response_style,
        cv_context=str(plan["cv_context"]),
        question_index=None,
        jd_context=str(plan["jd_context"]),
        asked_topics=list(plan["asked_topics"]),
        focus=str(plan["focus"]),
        tech_stack=tech_stack,
        competencies=competencies,
        question_type=str(plan["question_type"]),
        previous_questions=list(plan["previous_questions"]),
        temperature=temperature,
        gap_analysis=gap_analysis,
    )
    client = _get_client_or_none()
    if client is None:
        if question_list_count > 1:
            return _validated_fallback_bundle(
                role=str(plan["role"]),
                difficulty=str(plan["difficulty"]),
                focus=str(plan["focus"]),
                cv_context=str(plan["cv_context"]),
                jd_context=str(plan["jd_context"]),
                question_type=str(plan["question_type"]),
                previous_questions=list(plan["previous_questions"]),
                question_plan=plan,
                required_count=question_list_count,
            )
        fallback_question = generate_safe_fallback(
            role=str(plan["role"]),
            difficulty=str(plan["difficulty"]),
            focus=str(plan["focus"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            question_type=str(plan["question_type"]),
            question_index=1,
            previous_questions=list(plan["previous_questions"]),
            question_plan=plan,
        )
        valid, reason = _validate_single_question(
            fallback_question,
            role=str(plan["role"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            focus=str(plan["focus"]),
            question_type=str(plan["question_type"]),
        )
        if not valid:
            _raise_fallback_validation_error(reason)
        return fallback_question
    return _generate_with_retry(
        prompt=prompt,
        client=client,
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        focus=str(plan["focus"]),
        cv_context=str(plan["cv_context"]),
        jd_context=str(plan["jd_context"]),
        question_type=str(plan["question_type"]),
        question_index=1,
        previous_questions=list(plan["previous_questions"]),
        question_plan=plan,
        temperature=temperature,
        question_list_count=question_list_count,
        use_provider_fallback=True,
    )


def build_role_based_question_prompt(
    role: str,
    difficulty: str,
    persona: str,
    response_style: str,
    cv_context: str,
    jd_context: str = "",
    asked_topics: list[str] | None = None,
    focus: str = "General",
    tech_stack: list[str] | None = None,
    competencies: list[str] | None = None,
    question_type: str | None = None,
    previous_questions: list[str] | None = None,
    temperature: object | None = None,
    gap_analysis: object | None = None,
) -> str:
    plan = _build_question_plan(
        role=role,
        difficulty=difficulty,
        question_index=1,
        cv_context=cv_context,
        jd_context=jd_context,
        asked_topics=asked_topics,
        focus=focus,
        question_type=question_type,
        previous_questions=previous_questions,
    )
    return build_question_generation_prompt(
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        persona=persona,
        response_style=response_style,
        temperature=temperature if temperature is not None else 0.7,
        cv_profile=str(plan["cv_context"]),
        job_description=str(plan["jd_context"]),
        gap_analysis=gap_analysis or {"focus": str(plan["focus"]), "focus_area": str(plan["focus_area"]), "question_type": str(plan["question_type"])},
        prompt_style=_question_prompt_style(),
    )


def get_role_based_question(
    role: str,
    difficulty: str,
    persona: str,
    response_style: str,
    cv_context: str,
    jd_context: str = "",
    asked_topics: list[str] | None = None,
    focus: str = "General",
    tech_stack: list[str] | None = None,
    competencies: list[str] | None = None,
    question_type: str | None = None,
    previous_questions: list[str] | None = None,
    temperature: object | None = None,
    gap_analysis: object | None = None,
    question_list_count: int = 1,
) -> str | list[dict[str, object]]:
    plan = _build_question_plan(
        role=role,
        difficulty=difficulty,
        question_index=1,
        cv_context=cv_context,
        jd_context=jd_context,
        asked_topics=asked_topics,
        focus=focus,
        question_type=question_type,
        previous_questions=previous_questions,
    )
    prompt = build_role_based_question_prompt(
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        persona=persona,
        response_style=response_style,
        cv_context=str(plan["cv_context"]),
        jd_context=str(plan["jd_context"]),
        asked_topics=list(plan["asked_topics"]),
        focus=str(plan["focus"]),
        tech_stack=tech_stack,
        competencies=competencies,
        question_type=str(plan["question_type"]),
        previous_questions=list(plan["previous_questions"]),
        temperature=temperature,
        gap_analysis=gap_analysis,
    )
    client = _get_client_or_none()
    if client is None:
        if question_list_count > 1:
            return _validated_fallback_bundle(
                role=str(plan["role"]),
                difficulty=str(plan["difficulty"]),
                focus=str(plan["focus"]),
                cv_context=str(plan["cv_context"]),
                jd_context=str(plan["jd_context"]),
                question_type=str(plan["question_type"]),
                previous_questions=list(plan["previous_questions"]),
                question_plan=plan,
                required_count=question_list_count,
            )
        fallback_question = generate_safe_fallback(
            role=str(plan["role"]),
            difficulty=str(plan["difficulty"]),
            focus=str(plan["focus"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            question_type=str(plan["question_type"]),
            question_index=1,
            previous_questions=list(plan["previous_questions"]),
            question_plan=plan,
        )
        valid, reason = _validate_single_question(
            fallback_question,
            role=str(plan["role"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            focus=str(plan["focus"]),
            question_type=str(plan["question_type"]),
        )
        if not valid:
            _raise_fallback_validation_error(reason)
        return fallback_question
    return _generate_with_retry(
        prompt=prompt,
        client=client,
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        focus=str(plan["focus"]),
        cv_context=str(plan["cv_context"]),
        jd_context=str(plan["jd_context"]),
        question_type=str(plan["question_type"]),
        question_index=1,
        previous_questions=list(plan["previous_questions"]),
        question_plan=plan,
        temperature=temperature,
        question_list_count=question_list_count,
        use_provider_fallback=True,
    )


def get_next_question_for_session(
    role: str,
    difficulty: str,
    persona: str,
    response_style: str,
    focus: str,
    cv_context: str,
    question_index: int,
    jd_context: str = "",
    asked_topics: list[str] | None = None,
    tech_stack: list[str] | None = None,
    competencies: list[str] | None = None,
    question_type: str | None = None,
    previous_questions: list[str] | None = None,
    temperature: object | None = None,
    gap_analysis: object | None = None,
    question_list_count: int = 1,
    return_meta: bool = False,
    should_abort: Callable[[], bool] | None = None,
) -> str | list[dict[str, object]] | dict[str, object]:
    if not isinstance(question_index, int):
        raise ValueError("question_index must be int")
    if question_index < 1:
        raise ValueError("question_index must be at least 1")

    plan = _build_question_plan(
        role=role,
        difficulty=difficulty,
        question_index=question_index,
        cv_context=cv_context,
        jd_context=jd_context,
        asked_topics=asked_topics,
        focus=focus,
        question_type=question_type,
        previous_questions=previous_questions,
    )
    prompt = build_question_generation_prompt(
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        persona=persona,
        response_style=response_style,
        temperature=temperature if temperature is not None else 0.7,
        cv_profile=str(plan["cv_context"]),
        job_description=str(plan["jd_context"]),
        gap_analysis=gap_analysis or {"focus": str(plan["focus"]), "focus_area": str(plan["focus_area"]), "question_type": str(plan["question_type"])},
        prompt_style=_question_prompt_style(),
    )

    client = _get_client_or_none()
    if client is None:
        if question_list_count > 1:
            return _validated_fallback_bundle(
                role=str(plan["role"]),
                difficulty=str(plan["difficulty"]),
                focus=str(plan["focus"]),
                cv_context=str(plan["cv_context"]),
                jd_context=str(plan["jd_context"]),
                question_type=str(plan["question_type"]),
                previous_questions=list(plan["previous_questions"]),
                question_plan=plan,
                required_count=question_list_count,
            )
        fallback_question = generate_safe_fallback(
            role=str(plan["role"]),
            difficulty=str(plan["difficulty"]),
            focus=str(plan["focus"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            question_type=str(plan["question_type"]),
            question_index=question_index,
            previous_questions=list(plan["previous_questions"]),
            question_plan=plan,
        )
        valid, reason = _validate_single_question(
            fallback_question,
            role=str(plan["role"]),
            cv_context=str(plan["cv_context"]),
            jd_context=str(plan["jd_context"]),
            focus=str(plan["focus"]),
            question_type=str(plan["question_type"]),
        )
        if not valid:
            _raise_fallback_validation_error(reason)
        return fallback_question
    return _generate_with_retry(
        prompt=prompt,
        client=client,
        role=str(plan["role"]),
        difficulty=str(plan["difficulty"]),
        focus=str(plan["focus"]),
        cv_context=str(plan["cv_context"]),
        jd_context=str(plan["jd_context"]),
        question_type=str(plan["question_type"]),
        question_index=question_index,
        previous_questions=list(plan["previous_questions"]),
        question_plan=plan,
        temperature=temperature,
        question_list_count=question_list_count,
        return_meta=return_meta,
        use_provider_fallback=True,
        should_abort=should_abort,
    )
