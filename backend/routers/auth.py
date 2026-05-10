from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import create_access_token, hash_password, verify_password
from database import get_db
from models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterBody(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    message: str | None = None


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterBody, db: Session = Depends(get_db)):
    existing = db.scalars(select(User).where(User.username == body.username)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Auto-approve and make admin if this is the very first user
    user_count = db.query(User).count()
    is_first_user = user_count == 0

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        is_approved=is_first_user,
        is_admin=is_first_user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if is_first_user:
        token = create_access_token(subject=user.username, user_id=user.id)
        return TokenResponse(access_token=token, message="First user created as Admin and Approved!")
    
    return TokenResponse(message="Account created successfully. Please wait for an admin to approve your account.")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginBody, db: Session = Depends(get_db)):
    from auth import login_attempts, MAX_LOGIN_ATTEMPTS
    
    attempts = login_attempts.get(body.username, 0)
    if attempts >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please contact an administrator."
        )

    user = db.scalars(select(User).where(User.username == body.username)).first()
    if user is None or not verify_password(body.password, user.password_hash):
        login_attempts[body.username] = attempts + 1
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval by an administrator.",
        )

    # Success, reset attempts
    login_attempts[body.username] = 0
    
    token = create_access_token(subject=user.username, user_id=user.id)
    return TokenResponse(access_token=token)
