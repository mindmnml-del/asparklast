"""
API Key Authentication for B2B Tenants
Provides FastAPI dependency for X-API-Key header validation.
"""

import hashlib
import secrets
import logging
from datetime import datetime, UTC
from typing import Optional, Tuple

from fastapi import Security, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from core.database import get_db
from core import models

logger = logging.getLogger(__name__)

# Header extractor — auto_error=False so we return a clean 401 ourselves
api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    """Return SHA-256 hex digest of the raw API key (64 lowercase hex chars)."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_api_key() -> Tuple[str, str, str]:
    """
    Generate a new API key triplet.

    Returns:
        raw_key  — the full secret to hand to the tenant once (never stored)
        key_hash — SHA-256 hex digest stored in the database
        prefix   — 'aispark_' + first 8 URL-safe chars, stored for display
    """
    raw_key = secrets.token_urlsafe(32)
    key_hash = hash_api_key(raw_key)
    prefix = "aispark_" + raw_key[:8]
    return raw_key, key_hash, prefix


def get_api_key_tenant(
    api_key: Optional[str] = Security(api_key_header_scheme),
    db: Session = Depends(get_db),
) -> models.Tenant:
    """
    FastAPI dependency that validates an X-API-Key header and returns
    the associated Tenant.

    Raises HTTP 401 on: missing header, unknown key, revoked key,
    expired key, or inactive tenant.
    """
    if not api_key:
        logger.warning("B2B request with no X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required for API access",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    try:
        key_hash = hash_api_key(api_key)
        api_key_record = (
            db.query(models.ApiKey)
            .filter(models.ApiKey.key_hash == key_hash)
            .first()
        )

        if not api_key_record:
            logger.warning("B2B authentication failed: key not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        if not api_key_record.is_active:
            logger.warning(f"B2B authentication failed: key '{api_key_record.prefix}' is inactive")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        if api_key_record.expires_at is not None:
            expires = api_key_record.expires_at
            # SQLite stores naive datetimes — make comparison timezone-safe
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            if datetime.now(UTC) > expires:
                logger.warning(f"B2B authentication failed: key '{api_key_record.prefix}' expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired",
                    headers={"WWW-Authenticate": "ApiKey"},
                )

        tenant = api_key_record.tenant
        if not tenant or not tenant.is_active:
            logger.warning(f"B2B authentication failed: tenant inactive for key '{api_key_record.prefix}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Associated tenant is inactive",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        logger.debug(f"B2B auth successful: tenant '{tenant.name}' via key '{api_key_record.prefix}'")
        return tenant

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"B2B authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key validation failed",
            headers={"WWW-Authenticate": "ApiKey"},
        )
