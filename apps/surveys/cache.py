"""
Redis-based caching utilities for survey templates.
Maps to FR 3.2: Caching Strategy.
"""
from django.core.cache import cache

SURVEY_CACHE_PREFIX = "survey_template"
SURVEY_CACHE_TIMEOUT = 60 * 60  # 1 hour


def get_survey_cache_key(survey_id: str) -> str:
    """Generate cache key for a survey template."""
    return f"{SURVEY_CACHE_PREFIX}:{survey_id}"


def get_cached_survey(survey_id: str):
    """
    Retrieve cached survey template.
    Returns None if not cached.
    """
    return cache.get(get_survey_cache_key(survey_id))


def set_cached_survey(survey_id: str, survey_data: dict, timeout: int = SURVEY_CACHE_TIMEOUT):
    """Cache survey template data."""
    cache.set(get_survey_cache_key(survey_id), survey_data, timeout)


def invalidate_survey_cache(survey_id: str):
    """Remove survey from cache (call on update/delete)."""
    cache.delete(get_survey_cache_key(survey_id))


def invalidate_all_survey_caches():
    """Clear all survey caches (admin operation)."""
    cache.delete_pattern(f"{SURVEY_CACHE_PREFIX}:*")
