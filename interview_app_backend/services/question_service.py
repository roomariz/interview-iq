"""Question service interface; implementation is split by responsibility."""
import logging  # noqa: F401
import json  # noqa: F401
import random  # noqa: F401
from collections import Counter  # noqa: F401
from difflib import SequenceMatcher  # noqa: F401
from collections.abc import Callable  # noqa: F401
from interview_app_backend.llm.client import call_llm, get_openrouter_client  # noqa: F401
from interview_app_backend.llm.client import get_last_llm_call_metadata  # noqa: F401
from interview_app_backend.llm.client import clear_last_llm_call_metadata  # noqa: F401
from interview_app_backend.llm.provider_clients import get_google_client  # noqa: F401
from interview_app_backend.llm.provider_clients import get_grok_client  # noqa: F401
from interview_app_backend.llm.provider_fallback import CallLog  # noqa: F401
from interview_app_backend.llm.prompts.question_generation_prompt import build_question_generation_prompt  # noqa: F401
from interview_app_backend.llm.question_generation_parser import extract_question_generation_meta  # noqa: F401
from interview_app_backend.llm.question_generation_parser import parse_question_generation_response  # noqa: F401
from config.model_profiles import get_model_profile  # noqa: F401
from config.model_profiles import get_retry_limit  # noqa: F401
from interview_app_backend.llm.client_support import _is_permanent_error  # noqa: F401
from config.settings import MODEL_NAME  # noqa: F401
from interview_app_backend.services.question_sequence import build_question_prompt_context  # noqa: F401
from interview_app_backend.services.question_sequence import resolve_missing_context  # noqa: F401
from interview_app_backend.services.question_constants import (  # noqa: F401
    MAX_SCENARIO_TYPE_COUNT,
    ALLOWED_SCENARIO_TYPES,
    REQUIRED_SCENARIO_DIMENSIONS,
    DIMENSION_BY_SCENARIO_TYPE,
    QUESTION_TYPE_TO_SCENARIO_TYPE,
    PERFORMANCE_KEYWORDS,
    PERFORMANCE_TEMPLATES,
    QUESTION_TYPE_TEMPLATES,
    ROLE_FALLBACK_TEMPLATES,
    ROLE_KEYWORDS,
    FEW_SHOT_EXAMPLES,
    COMMON_TECH_TERMS,
    ROLE_ONLY_GROUNDING_TERMS,
    SEMANTIC_TECH_GROUPS,
    ROLE_BASELINE_GROUPS,
    TERM_TO_GROUP,
)
from interview_app_backend.services.question_context import (  # noqa: F401
    _build_context_block,
    _select_template,
    _select_question_type,
    _format_template,
    _extract_skill_from_context,
    _extract_role_keywords,
    _extract_context_keywords,
    _normalise_scenario_type,
)
from interview_app_backend.services.question_similarity import (  # noqa: F401
    _is_similar_to_previous,
    _question_similarity,
    is_semantically_duplicate,
    key_terms_overlap,
    _question_opening_style,
    same_question_pattern,
    _avoid_topics_line,
    _topic_tokens,
    derive_question_topics,
    normalise_topic,
    extract_topic,
)
from interview_app_backend.services.question_quality import (  # noqa: F401
    _soft_validate_question,
    is_valid_question,
    _is_generic_question,
    validate_question,
    _passes_generation_checks,
    _matches_context,
    _topic_relevance,
    _validate_single_question,
)
from interview_app_backend.services.question_prompt_helpers import (  # noqa: F401
    _build_strict_system_prompt,
    _build_few_shot_section,
    _build_template_guidance,
    _normalise_temperature,
    _question_prompt_style,
    _question_retry_limit,
    _question_strict_json,
    _build_question_plan,
)
from interview_app_backend.services.question_grounding import (  # noqa: F401
    _supported_terms_for_context,
    _expand_semantic_terms,
    _contextual_supported_terms,
    _context_mode,
    _source_terms,
    _classify_dimension,
    _has_allowed_term,
    _bundle_dimensions,
    _has_supported_grounding,
    _has_hallucinated_tech,
)
from interview_app_backend.services.question_bundle import (  # noqa: F401
    _question_text,
    _question_item,
    _filter_question_items,
    is_duplicate,
    deduplicate_questions,
    _validate_question_bundle,
    _raise_fallback_validation_error,
    _build_question_meta,
)
from interview_app_backend.services.question_fallback_templates import (  # noqa: F401
    _build_fallback_detail,
    _pick_template,
    generate_safe_fallback,
    generate_fallback_question,
)
from interview_app_backend.services.question_fallback import (  # noqa: F401
    _validated_fallback_bundle,
    _fallback_question_items,
    fallback_questions,
)
from interview_app_backend.services.question_retry import (  # noqa: F401
    _generate_with_retry,
)
from interview_app_backend.services.question_requests import (  # noqa: F401
    _get_client_or_none,
    build_question_prompt,
    build_role_based_question_prompt,
    get_next_question,
)
from interview_app_backend.services.question_session_requests import (  # noqa: F401
    get_role_based_question,
    get_next_question_for_session,
)

LOGGER = logging.getLogger(__name__)

class DuplicateQuestionError(RuntimeError):
    pass
