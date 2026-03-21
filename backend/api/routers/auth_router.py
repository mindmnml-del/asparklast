"""Authentication endpoints — login, register, logout, current user."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from config import settings
from core import models, schemas, crud, auth
from core.auth import ACCESS_TOKEN_EXPIRE_MINUTES
from core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

# auto_error=False so we can fall back to cookie when header is absent
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

SESSION_COOKIE = "aispark_session"


async def get_current_user(
    request: Request,
    token_from_header: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Priority 1: httpOnly cookie
    token = request.cookies.get(SESSION_COOKIE)
    # Priority 2: Authorization header (B2B / API clients)
    if not token:
        token = token_from_header
    if not token:
        raise credentials_exception

    try:
        payload = auth.decode_access_token(token)
        if not payload:
            raise credentials_exception

        email = payload.get("sub")
        if not email:
            raise credentials_exception

        user = crud.get_user_by_email(db, email=email)
        if not user or not user.is_active:
            raise credentials_exception

        return user
    except Exception:
        raise credentials_exception


@router.post("/auth/token", response_model=schemas.Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_user_token(user.email)

    # Set httpOnly session cookie for browser clients
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=not settings.debug_mode,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    # Also return token in body for B2B / API key clients
    return {"access_token": token, "token_type": "bearer"}


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"message": "Logged out"}


@router.post("/auth/register", response_model=schemas.User)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = crud.create_user(db, user_data)
    if not user:
        raise HTTPException(status_code=500, detail="Registration failed")
    return user


@router.get("/users/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
