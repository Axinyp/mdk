import io
import json
import zipfile
from json import JSONDecodeError

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.session import GenSession
from ..models.user import User
from ..schemas.gen import (
    ConfirmRequest, MessageRequest, ParsedData, SessionCreate,
    SessionListItem, SessionMessageResponse, SessionResponse,
)
from ..services.auth import get_current_user
from ..services import conversation_service, orchestrator

router = APIRouter(prefix="/api/gen", tags=["generation"])


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    req: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await orchestrator.create_session(db, user.id, req.description)
    return await _enrich_session(db, session)


@router.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(GenSession)
        .where(GenSession.user_id == user.id)
        .order_by(GenSession.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_user_session(db, session_id, user.id)
    return await _enrich_session(db, session)


@router.get("/sessions/{session_id}/messages", response_model=list[SessionMessageResponse])
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_user_session(db, session_id, user.id)
    return await conversation_service.get_messages(db, session.id)


@router.post("/sessions/{session_id}/messages")
async def add_session_message(
    session_id: str,
    req: MessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = req.content.strip()
    session = await _get_user_session(db, session_id, user.id)
    try:
        await conversation_service.add_message(
            db, session.id, role="user", kind="answer", content=content,
        )
        messages = await conversation_service.get_messages(db, session.id)
        combined = conversation_service.build_parse_context(messages)
        session.description = combined
        await db.commit()
        parsed = await orchestrator.stage_parse(db, session.id, combined)
        refreshed = await _get_user_session(db, session_id, user.id)
        updated_messages = await conversation_service.get_messages(db, session.id)
        return {
            "status": refreshed.status,
            "parsed_data": parsed.model_dump(),
            "messages": [SessionMessageResponse.model_validate(m).model_dump() for m in updated_messages],
        }
    except JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM 返回了无法解析的 JSON: {e}")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Parse stage failed: {e}")


@router.post("/sessions/{session_id}/parse")
async def parse_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_user_session(db, session_id, user.id)
    try:
        parsed = await orchestrator.stage_parse(db, session.id, session.description)
        return {"status": "parsed", "parsed_data": parsed.model_dump()}
    except JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM 返回了无法解析的 JSON: {e}")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Parse stage failed: {e}")


@router.post("/sessions/{session_id}/confirm")
async def confirm_session(
    session_id: str,
    req: ConfirmRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_user_session(db, session_id, user.id)
    try:
        functions_with_joins = await orchestrator.stage_confirm(db, session.id, req.data)
        return {
            "status": "confirmed",
            "functions": [f.model_dump() for f in functions_with_joins],
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confirm stage failed: {e}")


@router.post("/sessions/{session_id}/generate")
async def generate_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_user_session(db, session_id, user.id)
    return StreamingResponse(
        orchestrator.stage_generate(db, session.id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions/{session_id}/result")
async def get_result(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_user_session(db, session_id, user.id)
    if session.status != "completed":
        raise HTTPException(status_code=400, detail=f"Not completed: {session.status}")
    return {
        "xml_content": session.xml_content,
        "cht_content": session.cht_content,
        "validation_report": json.loads(session.validation_report) if session.validation_report else None,
    }


@router.get("/sessions/{session_id}/download")
async def download_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await _get_user_session(db, session_id, user.id)
    if not session.xml_content or not session.cht_content:
        raise HTTPException(status_code=400, detail="No generated content")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Project.xml", session.xml_content)
        zf.writestr("output.cht", session.cht_content)
        if session.validation_report:
            zf.writestr("validation_report.json", session.validation_report)
    buf.seek(0)

    filename = f"mdk_{session_id[:8]}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _get_user_session(db: AsyncSession, session_id: str, user_id: int) -> GenSession:
    result = await db.execute(
        select(GenSession).where(GenSession.id == session_id, GenSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


async def _enrich_session(db: AsyncSession, session: GenSession) -> dict:
    latest = await conversation_service.get_latest_revision(db, session.id)
    payload = SessionResponse.model_validate(session).model_dump()
    payload["current_revision"] = latest.revision if latest else None
    return payload
