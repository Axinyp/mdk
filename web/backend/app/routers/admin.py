from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.llm_config import LlmConfig
from ..models.session import ProtocolSubmission
from ..models.setting import Setting
from ..models.user import User
from ..schemas.admin import (
    LlmConfigCreate, LlmConfigResponse, LlmConfigUpdate,
    LlmListModelsRequest, LlmListModelsResponse,
    LlmTestRequest, LlmTestResponse,
    SettingResponse, SettingUpdate,
    UserCreate, UserUpdate,
)
from ..schemas.auth import UserResponse
from ..schemas.pagination import PagedResponse
from ..services.auth import hash_password_async, require_admin, get_current_user
from ..services.llm import (
    encrypt_api_key,
    list_available_models as llm_list_models,
    test_connection as llm_test_connection,
)
from ..services import protocol_ingestion
import httpx

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


@router.post("/llm/list-models", response_model=LlmListModelsResponse)
async def list_llm_models(req: LlmListModelsRequest, db: AsyncSession = Depends(get_db)):
    """Probe the provider's catalogue endpoint. Accepts either an existing
    ``config_id`` or an ad-hoc ``provider/api_base/api_key`` triple — the
    latter is what the create-form uses before the user has saved.
    """
    if req.config_id:
        cfg = await db.get(LlmConfig, req.config_id)
        if not cfg:
            raise HTTPException(status_code=404, detail="Config not found")
    else:
        cfg = LlmConfig(
            name="probe",
            provider=req.provider or "openai",
            model="probe",
            api_base=req.api_base,
            api_key=encrypt_api_key(req.api_key),
            is_default=False,
            is_active=True,
        )
    try:
        models = await llm_list_models(cfg)
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:200] if exc.response is not None else ""
        return LlmListModelsResponse(
            success=False, models=[],
            message=f"HTTP {exc.response.status_code if exc.response else '?'}: {body}",
        )
    except httpx.HTTPError as exc:
        return LlmListModelsResponse(
            success=False, models=[],
            message=f"网络错误: {type(exc).__name__}: {exc}",
        )
    except Exception as exc:
        return LlmListModelsResponse(
            success=False, models=[],
            message=f"{type(exc).__name__}: {exc}",
        )
    return LlmListModelsResponse(
        success=True, models=models,
        message=f"已获取 {len(models)} 个模型" if models else "未返回任何模型，请确认 API 地址",
    )


# ── Protocol Submission Review ────────────────────────────────────────────────

class ApproveRequest(BaseModel):
    edited_content: str | None = None


class RejectRequest(BaseModel):
    note: str = ""


def _sub_to_dict(s: ProtocolSubmission, include_content: bool = False) -> dict:
    d = {
        "id": s.id,
        "session_id": s.session_id,
        "submitter_id": s.submitter_id,
        "source_type": s.source_type,
        "filename": s.filename,
        "brand": s.brand,
        "model_name": s.model_name,
        "review_status": s.review_status,
        "reviewer_id": s.reviewer_id,
        "reviewer_note": s.reviewer_note,
        "approved_protocol_id": s.approved_protocol_id,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }
    if include_content:
        d["raw_content"] = s.raw_content
        d["extracted_protocol"] = s.extracted_protocol
    return d


@router.get("/protocol-submissions")
async def list_submissions(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(ProtocolSubmission).order_by(ProtocolSubmission.created_at.desc())
    if status:
        q = q.where(ProtocolSubmission.review_status == status)

    count_result = await db.execute(q)
    all_items = count_result.scalars().all()
    total = len(all_items)
    offset = (page - 1) * page_size
    items = all_items[offset: offset + page_size]

    return PagedResponse(
        items=[_sub_to_dict(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/protocol-submissions/{submission_id}")
async def get_submission(submission_id: str, db: AsyncSession = Depends(get_db)):
    sub = await db.get(ProtocolSubmission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return _sub_to_dict(sub, include_content=True)


@router.post("/protocol-submissions/{submission_id}/approve")
async def approve_submission(
    submission_id: str,
    req: ApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = await db.get(ProtocolSubmission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.review_status not in ("pending_review", "processing"):
        raise HTTPException(status_code=409, detail=f"Submission already {sub.review_status}")

    proto = await protocol_ingestion.approve(
        submission=sub,
        reviewer_id=current_user.id,
        edited_content=req.edited_content,
        db=db,
    )
    return {"status": "approved", "protocol_id": proto.id}


@router.post("/protocol-submissions/{submission_id}/reject")
async def reject_submission(
    submission_id: str,
    req: RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = await db.get(ProtocolSubmission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.review_status not in ("pending_review", "processing"):
        raise HTTPException(status_code=409, detail=f"Submission already {sub.review_status}")

    await protocol_ingestion.reject(
        submission=sub,
        reviewer_id=current_user.id,
        note=req.note,
        db=db,
    )
    return {"status": "rejected"}


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
    user = User(username=req.username, password=await hash_password_async(req.password), role=req.role)
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
