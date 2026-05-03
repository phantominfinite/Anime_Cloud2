from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.services.auth import get_current_user
from app.services.jwt import create_access_token
from app.db.models import User

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/auth/login", response_model=Token)
async def login(
    user: User = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication failed")

    access_token = create_access_token(data={"sub": str(user.telegram_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "photo_url": user.photo_url,
        "is_admin": user.is_admin
    }
