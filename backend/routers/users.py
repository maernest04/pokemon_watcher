from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from auth import get_current_user, hash_password, verify_password
from database import get_db
from models import User

router = APIRouter(prefix="/api/users", tags=["users"])


class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    discord_channel_id: str | None


class MePatchBody(BaseModel):
    discord_channel_id: str | None = None


class ChangePasswordBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=128)


@router.get("/me", response_model=UserMeResponse)
def read_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserMeResponse)
def update_me(
    body: MePatchBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = body.model_dump(exclude_unset=True)
    if "discord_channel_id" in data:
        user.discord_channel_id = data["discord_channel_id"]
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.password_hash = hash_password(body.new_password)
    db.add(user)
    db.commit()
    return None
