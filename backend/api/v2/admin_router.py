"""
B2B Admin API (V2) — Tenant & API Key Management
Protected by a dedicated admin Bearer token, separate from sandbox auth.
"""

import logging
import secrets
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import settings
from core import models, schemas
from core.database import get_db
from core.api_key_auth import generate_api_key

logger = logging.getLogger(__name__)

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)


async def verify_admin_key(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    Validate the Bearer token against the static admin API key.
    Returns the validated key string on success.
    """
    configured_key = settings.admin_api_key
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "admin_not_configured",
                "message": "Admin API is not configured on this server.",
            },
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_credentials",
                "message": "Authorization header with Bearer token is required.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not secrets.compare_digest(credentials.credentials, configured_key):
        logger.warning("Admin auth failed: invalid Bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid admin API key.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


@router.post(
    "/tenants",
    response_model=schemas.TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
)
async def create_tenant(
    request: schemas.TenantCreate,
    _key: str = Depends(verify_admin_key),
    db: Session = Depends(get_db),
):
    """Create a new B2B tenant organization."""
    try:
        tenant = models.Tenant(name=request.name)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "duplicate_tenant",
                "message": "A tenant with this name already exists.",
            },
        )
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.error("Admin /tenants error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred while creating the tenant.",
            },
        )


@router.post(
    "/tenants/{tenant_id}/api-keys",
    response_model=schemas.ApiKeyResponseWithRaw,
    status_code=status.HTTP_201_CREATED,
    summary="Generate an API key for a tenant",
)
async def create_api_key(
    tenant_id: int,
    request: schemas.ApiKeyCreate,
    _key: str = Depends(verify_admin_key),
    db: Session = Depends(get_db),
):
    """
    Generate a new API key for the specified tenant.
    The raw_key is returned ONCE in the response and is never stored or retrievable again.
    """
    # Verify tenant exists
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "tenant_not_found",
                "message": f"Tenant with id {tenant_id} not found.",
            },
        )

    try:
        raw_key, key_hash, prefix = generate_api_key()

        api_key = models.ApiKey(
            key_hash=key_hash,
            prefix=prefix,
            tenant_id=tenant_id,
            name=request.name,
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        # Build response with raw_key injected (NOT from DB)
        return schemas.ApiKeyResponseWithRaw(
            id=api_key.id,
            prefix=api_key.prefix,
            name=api_key.name,
            tenant_id=api_key.tenant_id,
            created_at=api_key.created_at,
            raw_key=raw_key,
        )

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.error("Admin /api-keys error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred while generating the API key.",
            },
        )


@router.get(
    "/tenants/{tenant_id}/api-keys",
    response_model=List[schemas.ApiKeyResponse],
    summary="List API keys for a tenant",
)
async def list_tenant_api_keys(
    tenant_id: int,
    _key: str = Depends(verify_admin_key),
    db: Session = Depends(get_db),
):
    """List all API keys for the specified tenant (no sensitive fields exposed)."""
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "tenant_not_found",
                "message": f"Tenant with id {tenant_id} not found.",
            },
        )

    try:
        keys = (
            db.query(models.ApiKey)
            .filter(models.ApiKey.tenant_id == tenant_id)
            .all()
        )
        return keys

    except HTTPException:
        raise
    except Exception:
        logger.error("Admin GET /api-keys error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred while listing API keys.",
            },
        )
