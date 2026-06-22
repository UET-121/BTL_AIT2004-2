from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.db.database import get_db
from shared.models import User
from shared.config.logger import log
from shared.schemas.user import UserCreateRequest, UserRoleUpdateRequest

from ..security.jwt_ import get_password_hash
from ..security.user_manage import admin_required, manager_required
from ..middleware.rate_limit import limiter

router = APIRouter(prefix="/api/users", tags=["User Management"])

VALID_ROLES = ["viewer", "manager", "admin"]

# ─── GET /api/users/list ───
@router.get("/list", summary="Lấy danh sách tất cả users")
@limiter.limit("60/minute")
async def get_users_list(
    request: Request,
    current_user: User = Depends(manager_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]


# ─── POST /api/users/create ───
@router.post("/create", summary="Tạo user mới")
@limiter.limit("10/minute")
async def create_user(
    request: Request,
    payload: UserCreateRequest,
    current_user: User = Depends(manager_required),
    db: AsyncSession = Depends(get_db),
):
    # Validate role
    if payload.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role không hợp lệ. Chỉ chấp nhận: {', '.join(VALID_ROLES)}",
        )

    # Manager chỉ được tạo user với role viewer
    if current_user.role == "manager" and payload.role != "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager chỉ có thể tạo tài khoản với quyền 'viewer'.",
        )

    # Kiểm tra trùng username
    result = await db.execute(select(User).where(User.username == payload.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tên đăng nhập '{payload.username}' đã tồn tại.",
        )

    new_user = User(
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    log.info(f"User '{current_user.username}' đã tạo tài khoản mới: '{new_user.username}' (role: {new_user.role})")
    return {"id": new_user.id, "username": new_user.username, "role": new_user.role}


# ─── DELETE /api/users/delete/{user_id} ───
@router.delete("/delete/{user_id}", summary="Xóa user")
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(manager_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy user.")

    # Không được tự xóa chính mình
    if target_user.username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể tự xóa tài khoản của mình.",
        )

    # Manager chỉ được xóa user có role viewer
    if current_user.role == "manager" and target_user.role != "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager chỉ có thể xóa tài khoản có quyền 'viewer'.",
        )

    # Bảo vệ: không cho xóa admin cuối cùng
    if target_user.role == "admin":
        admin_count_result = await db.execute(select(User).where(User.role == "admin"))
        admins = admin_count_result.scalars().all()
        if len(admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa tài khoản Admin duy nhất của hệ thống.",
            )

    log.info(f"User '{current_user.username}' đã xóa tài khoản: '{target_user.username}'")
    await db.delete(target_user)
    await db.commit()
    return {"message": f"Đã xóa tài khoản '{target_user.username}' thành công."}


# ─── PUT /api/users/update-role/{user_id} ───
@router.put("/update-role/{user_id}", summary="Cập nhật role của user (Admin only)")
@limiter.limit("10/minute")
async def update_user_role(
    request: Request,
    user_id: int,
    payload: UserRoleUpdateRequest,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    if payload.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role không hợp lệ. Chỉ chấp nhận: {', '.join(VALID_ROLES)}",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy user.")

    # Không được tự đổi role chính mình (tránh mất quyền admin)
    if target_user.username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể thay đổi role của chính mình.",
        )

    # Bảo vệ: không cho hạ cấp admin cuối cùng
    if target_user.role == "admin" and payload.role != "admin":
        admin_count_result = await db.execute(select(User).where(User.role == "admin"))
        admins = admin_count_result.scalars().all()
        if len(admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể hạ quyền Admin duy nhất của hệ thống.",
            )

    old_role = target_user.role
    target_user.role = payload.role
    await db.commit()

    log.info(f"Admin '{current_user.username}' đã đổi role của '{target_user.username}': {old_role} → {payload.role}")
    return {"id": target_user.id, "username": target_user.username, "role": target_user.role}
