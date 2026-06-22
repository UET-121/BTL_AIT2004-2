from fastapi import Depends, APIRouter, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.database import get_db
from shared.models import User
from shared.config.logger import log

from ..security.jwt_ import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from ..middleware.rate_limit import limiter

router = APIRouter(prefix="/api/user", tags=["Login/Logout/Signin"])


@router.post("/login", summary="Login for JWT Token")
@limiter.limit("15/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):

    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
        },
        expires_delta=access_token_expires,
    )
    log.info(f"User '{user.username}' đã đăng nhập thành công.")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
    }
