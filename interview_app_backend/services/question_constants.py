"""Existing question categories, vocabulary and template constants."""

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
