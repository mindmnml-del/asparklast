"""Authentication endpoints — login, register, current user."""

import logging

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core import models, schemas, crud, auth
from core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

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
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_user_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


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
