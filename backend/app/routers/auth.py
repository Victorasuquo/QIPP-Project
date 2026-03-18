from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.config import settings
from app.schemas.auth import LoginRequest, TokenResponse, AccessTokenResponse, RefreshRequest, UserProfile
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    from app.models.user import User

    result = await db.execute(select(User).where(func.lower(User.email) == body.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if user.tenant_id else "",
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Update last_login (best-effort)
    try:
        from sqlalchemy import update
        await db.execute(update(User).where(User.id == user.id).values(last_login=datetime.utcnow()))
        await db.commit()
    except Exception:
        pass

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    from app.models.user import User

    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_id": str(user.tenant_id) if user.tenant_id else "",
    }
    access_token = create_access_token(token_data)
    return AccessTokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user=Depends(get_current_active_user)):
    return UserProfile.model_validate(current_user)


@router.post("/logout", status_code=204)
async def logout(current_user=Depends(get_current_active_user)):
    # JWT is stateless — client should discard tokens.
    # Future: add token blacklist in Redis if needed.
    return None
