"""Thin JSON cache over Redis, used by app.services.analytics_service to
avoid recomputing the same dashboard response on every request.

This is the first use of Redis as a cache in this codebase (elsewhere it's
only ever the Celery broker/result backend) — kept intentionally minimal:
get/set of JSON-serializable values with a TTL, and total silence on any
Redis failure (connection refused, timeout, whatever). Analytics must keep
working with no cache at all in local dev, where Redis often isn't running
(see every *_service.py's `_broker_reachable()` pre-check for the same
"Redis may simply not be there" assumption elsewhere in this codebase).
"""

import json
import logging
from typing import Any

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            get_settings().redis_url, socket_connect_timeout=0.5, socket_timeout=0.5
        )
    return _client


def get_json(key: str) -> Any | None:
    try:
        raw = _get_client().get(key)
    except redis.RedisError:
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        logger.warning("Cache key %s held non-JSON data — ignoring.", key)
        return None


def set_json(key: str, value: Any, *, ttl_seconds: int) -> None:
    try:
        _get_client().set(key, json.dumps(value), ex=ttl_seconds)
    except redis.RedisError:
        pass
