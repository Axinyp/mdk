from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.llm_config import LlmConfig
from ..models.setting import Setting
from ..models.user import User
from ..schemas.admin import (
    LlmConfigCreate, LlmConfigResponse, LlmConfigUpdate,
    LlmTestRequest, LlmTestResponse,
    SettingResponse, SettingUpdate,
    UserCreate, UserUpdate,
)
from ..schemas.auth import UserResponse
from ..services.auth import hash_password, require_admin, get_current_user
from ..services.llm import encrypt_api_key, test_connection as llm_test_connection

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# --- LLM Config ---

@router.get("/llm/config", response_model=list[LlmConfigResponse])
async def list_llm_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LlmConfig).order_by(LlmConfig.id))
    configs = result.scalars().all()
    return [
        LlmConfigResponse(
            **{c: getattr(cfg, c) for c in ("id", "name", "provider", "model", "api_base", "is_default", "is_active", "created_at")},
            api_key_set=bool(cfg.api_key),
        )
        for cfg in configs
    ]


@router.post("/llm/config", response_model=LlmConfigResponse, status_code=201)
async def create_llm_config(req: LlmConfigCreate, db: AsyncSession = Depends(get_db)):
    if req.is_default:
        await _clear_default(db)
    data = req.model_dump()
    data["api_key"] = encrypt_api_key(data.get("api_key"))
    cfg = LlmConfig(**data)
    db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
    return LlmConfigResponse(
        **{c: getattr(cfg, c) for c in ("id", "name", "provider", "model", "api_base", "is_default", "is_active", "created_at")},
        api_key_set=bool(cfg.api_key),
    )


@router.put("/llm/config/{config_id}", response_model=LlmConfigResponse)
async def update_llm_config(config_id: int, req: LlmConfigUpdate, db: AsyncSession = Depends(get_db)):
    cfg = await db.get(LlmConfig, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="Config not found")
    updates = req.model_dump(exclude_unset=True)
    if updates.get("is_default"):
        await _clear_default(db)
    if "api_key" in updates:
        updates["api_key"] = encrypt_api_key(updates["api_key"])
    for k, v in updates.items():
        setattr(cfg, k, v)
    await db.commit()
    await db.refresh(cfg)
    return LlmConfigResponse(
        **{c: getattr(cfg, c) for c in ("id", "name", "provider", "model", "api_base", "is_default", "is_active", "created_at")},
        api_key_set=bool(cfg.api_key),
    )


@router.delete("/llm/config/{config_id}")
async def delete_llm_config(config_id: int, db: AsyncSession = Depends(get_db)):
    cfg = await db.get(LlmConfig, config_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="Config not found")
    await db.delete(cfg)
    await db.commit()
    return {"message": "Deleted"}


@router.post("/llm/test", response_model=LlmTestResponse)
async def test_llm(req: LlmTestRequest, db: AsyncSession = Depends(get_db)):
    if req.config_id:
        cfg = await db.get(LlmConfig, req.config_id)
        if not cfg:
            raise HTTPException(status_code=404, detail="Config not found")
    elif req.provider and req.model:
        cfg = LlmConfig(
            name="test", provider=req.provider, model=req.model,
            api_base=req.api_base, api_key=encrypt_api_key(req.api_key),
            is_default=False, is_active=True,
        )
    else:
        raise HTTPException(status_code=400, detail="Provide config_id or provider+model")
    ok, msg = await llm_test_connection(cfg)
    return LlmTestResponse(success=ok, message=msg, model=cfg.model)


async def _clear_default(db: AsyncSession):
    result = await db.execute(select(LlmConfig).where(LlmConfig.is_default.is_(True)))
    for cfg in result.scalars():
        cfg.is_default = False


# --- Users ---

@router.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(req: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username exists")
    user = User(username=req.username, password=hash_password(req.password), role=req.role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, req: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}")
async def disable_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot disable yourself")
    user.status = "disabled"
    await db.commit()
    return {"message": "User disabled"}


# --- Settings ---

@router.get("/settings", response_model=list[SettingResponse])
async def list_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting).order_by(Setting.key))
    return result.scalars().all()


@router.put("/settings/{key}", response_model=SettingResponse)
async def update_setting(key: str, req: SettingUpdate, db: AsyncSession = Depends(get_db)):
    setting = await db.get(Setting, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    setting.value = req.value
    await db.commit()
    await db.refresh(setting)
    return setting
