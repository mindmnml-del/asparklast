"""
Async-safe B2B usage tracking.

Called from FastAPI BackgroundTasks so API usage is recorded after the
response is sent, without blocking the client.
"""

import logging
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from core.database import SessionLocal
from core.models import ApiUsage

logger = logging.getLogger(__name__)


def log_b2b_usage(
    *,
    tenant_id: int,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    user_id: Optional[int] = None,
) -> None:
    """
    Persist a single API-usage record for a B2B request.

    Creates its own DB session so it can safely run inside a BackgroundTask
    (where the request-scoped session is already closed).
    Any database error is logged and swallowed.
    """
    db = SessionLocal()
    try:
        record = ApiUsage(
            user_id=user_id,
            tenant_id=tenant_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message,
        )
        db.add(record)
        db.commit()
        logger.debug(
            "B2B usage logged: tenant=%s endpoint=%s status=%s time=%sms",
            tenant_id, endpoint, status_code, response_time_ms,
        )
    except SQLAlchemyError:
        db.rollback()
        logger.error(
            "Failed to log B2B usage for tenant=%s endpoint=%s",
            tenant_id, endpoint, exc_info=True,
        )
    except Exception:
        db.rollback()
        logger.error(
            "Unexpected error logging B2B usage for tenant=%s endpoint=%s",
            tenant_id, endpoint, exc_info=True,
        )
    finally:
        db.close()
