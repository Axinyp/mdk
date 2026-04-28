from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.auth import (
    LoginRequest, PasswordChangeRequest, RegisterRequest, TokenResponse, UserResponse,
)
from ..services.auth import (
    create_token, get_current_user, hash_password_async, require_admin, verify_password_async,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not await verify_password_async(req.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    token = create_token(user.id, user.username, user.role)
    return TokenResponse(access_token=token, must_change_password=user.must_change_password)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    existing = await db.execute(select(User).where(User.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=req.username.strip(),
        password=await hash_password_async(req.password),
        role=req.role,
        must_change_password=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.put("/password")
async def change_password(
    req: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await verify_password_async(req.old_password, user.password):
        raise HTTPException(status_code=400, detail="Old password incorrect")
    user.password = await hash_password_async(req.new_password)
    user.must_change_password = False
    await db.commit()
    return {"message": "Password changed"}
