import hmac
import hashlib
import json
import logging
from urllib.parse import parse_qsl
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.config import settings
from app.db.session import get_db
from app.db.models import User

logger = logging.getLogger(__name__)

def validate_telegram_data(init_data: str, bot_token: str) -> bool:
    """
    Validates the data received from the Telegram Web App.
    Source: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
        if "hash" not in parsed_data:
            return False

        hash_ = parsed_data.pop("hash")
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        return calculated_hash == hash_
    except Exception as e:
        logger.error(f"Auth Validation Error: {e}")
        return False

async def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency that validates Telegram data and returns the User object.
    Creates the user if they don't exist.
    """
    if not x_telegram_init_data:
        # Allow anonymous access for public endpoints. Use require_user
        # dependency for protected routes.
        return None

    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN is not configured")

    if not validate_telegram_data(x_telegram_init_data, settings.BOT_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

    try:
        parsed_data = dict(parse_qsl(x_telegram_init_data))
        user_data = json.loads(parsed_data.get("user", "{}"))
        telegram_id = int(user_data.get("id"))
        
        # Check if user exists
        result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
        user = result.scalars().first()
        
        if not user:
            # Create new user
            user = User(
                telegram_id=telegram_id,
                username=user_data.get("username"),
                first_name=user_data.get("first_name"),
                photo_url=user_data.get("photo_url"),
                is_admin=False # Default
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # Update info if changed
            if user.first_name != user_data.get("first_name") or user.photo_url != user_data.get("photo_url"):
                user.first_name = user_data.get("first_name")
                user.photo_url = user_data.get("photo_url")
                user.username = user_data.get("username")
                await db.commit()
        
        return user

    except Exception as e:
        logger.error(f"Auth Dependency Error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def require_user(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Dependency that enforces authentication."""
    if not user:
        raise HTTPException(status_code=401, detail="Missing Telegram init data")
    return user
