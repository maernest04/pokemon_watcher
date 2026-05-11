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
    ebay_app_id: str | None
    has_ebay_secret: bool
    is_admin: bool
    is_approved: bool


class MePatchBody(BaseModel):
    discord_channel_id: str | None = None
    ebay_app_id: str | None = None
    ebay_client_secret: str | None = None


class ChangePasswordBody(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class AdminChangePasswordBody(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    is_approved: bool
    is_admin: bool


@router.get("/me", response_model=UserMeResponse)
def read_me(user: User = Depends(get_current_user)):
    # Add virtual field for response
    user.has_ebay_secret = bool(user.ebay_client_secret)
    return user


@router.patch("/me", response_model=UserMeResponse)
def update_me(
    body: MePatchBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from services.encryption import encrypt_secret
    
    data = body.model_dump(exclude_unset=True)
    if "discord_channel_id" in data:
        user.discord_channel_id = data["discord_channel_id"]
    if "ebay_app_id" in data:
        user.ebay_app_id = data["ebay_app_id"]
    if "ebay_client_secret" in data:
        # Encrypt the secret before saving
        user.ebay_client_secret = encrypt_secret(data["ebay_client_secret"])
        
    db.add(user)
    db.commit()
    db.refresh(user)
    
    user.has_ebay_secret = bool(user.ebay_client_secret)
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


@router.get("/admin/users", response_model=list[AdminUserResponse])
def admin_list_users(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    from sqlalchemy import select
    return db.scalars(select(User).order_by(User.created_at.desc())).all()


@router.post("/admin/users/{target_id}/approve", response_model=AdminUserResponse)
def admin_approve_user(
    target_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    target = db.get(User, target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    target.is_approved = True
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.post("/admin/users/{target_id}/unapprove", response_model=AdminUserResponse)
def admin_unapprove_user(
    target_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    if target_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot unapprove yourself")
    
    target = db.get(User, target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    target.is_approved = False
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.post("/admin/users/{target_id}/toggle-admin", response_model=AdminUserResponse)
def admin_toggle_admin(
    target_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    if target_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote yourself")
    
    target = db.get(User, target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    target.is_admin = not target.is_admin
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.delete("/admin/users/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(
    target_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    if target_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    
    target = db.get(User, target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db.delete(target)
    db.commit()
    return None


@router.post("/admin/users/{target_id}/password", response_model=AdminUserResponse)
def admin_change_password(
    target_id: int,
    body: AdminChangePasswordBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    target = db.get(User, target_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    target.password_hash = hash_password(body.new_password)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target
