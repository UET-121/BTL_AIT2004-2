from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from shared.db.database import get_db
from shared.models import User
from jose import jwt, JWTError
from .jwt_ import oauth2_scheme, get_password_hash, ALGORITHM, SECRET_KEY


async def _verify_token_and_get_user(token: str, db: AsyncSession) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin (Token không hợp lệ hoặc đã hết hạn)",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    return await _verify_token_and_get_user(token, db)


async def get_user_from_url_token(
    token: Optional[str] = Query(None, alias="token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu mã token bảo mật trên đường dẫn tải ảnh (Missing token)",
        )
    return await _verify_token_and_get_user(token, db)


async def init_default_users(db: AsyncSession):
    default_users = [
        {"username": "admin", "role": "admin"},
        {"username": "manager", "role": "manager"},
        {"username": "viewer", "role": "viewer"},
    ]

    for u_data in default_users:
        result = await db.execute(
            select(User).where(User.username == u_data["username"])
        )
        user = result.scalar_one_or_none()
        if user:
            if user.role != u_data["role"]:
                user.role = u_data["role"]
        else:
            new_user = User(
                username=u_data["username"],
                hashed_password=get_password_hash(u_data["username"]),
                role=u_data["role"],
            )
            db.add(new_user)

    await db.commit()


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.role_hierarchy = ["viewer", "manager", "admin"]
        self.allowed_roles = allowed_roles

    def _get_role_level(self, role: str) -> int:
        try:
            return self.role_hierarchy.index(role)
        except ValueError:
            return -1

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        user_level = self._get_role_level(current_user.role)

        min_required_level = min([self._get_role_level(r) for r in self.allowed_roles])

        if user_level < min_required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quyền hạn của bạn ({current_user.role}) không đủ để thực hiện hành động này.",
            )

        return current_user


admin_required = RoleChecker(["admin"])

manager_required = RoleChecker(["manager", "admin"])

viewer_required = RoleChecker(["viewer", "manager", "admin"])
