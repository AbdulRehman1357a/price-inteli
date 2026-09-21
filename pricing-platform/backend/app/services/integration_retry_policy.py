import logging
import time
from collections.abc import Callable
from typing import TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Transient network/rate-limit failures worth a short exponential backoff.
# A 4xx that isn't 429 (bad credentials, malformed request, not found) is a
# permanent error — retrying it wastes the backoff window without any
# chance of success, so only httpx.HTTPStatusError with status 429 and
# generic transport failures (DNS, connection reset, timeout) qualify.
_RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


def is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _RETRYABLE_STATUS_CODES
    return isinstance(exc, httpx.TransportError)


def with_retry(fn: Callable[[], T], *, max_attempts: int = 3, base_delay_seconds: float = 1.0) -> T:
    """Synchronous exponential-backoff wrapper applied at the adapter-call
    boundary (integration_sync_service._run(), around fetch_records/
    push_records) — deliberately NOT a Celery autoretry, which would
    re-run the whole job and re-process every already-applied record, not
    just retry the one HTTP call that failed. Distinct from
    IntegrationSyncJob.retry_count, which only increments on a
    user/schedule-triggered whole-job retry_job() call.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — re-raised below once retries are exhausted
            if attempt >= max_attempts or not is_retryable(exc):
                raise
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning("Retrying after transient error (attempt %s/%s): %s", attempt, max_attempts, exc)
            time.sleep(delay)
