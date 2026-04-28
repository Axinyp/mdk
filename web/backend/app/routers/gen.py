import io

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.gen import (
    ConfirmRequest, MessageRequest, SessionCreate,
    SessionListItem, SessionMessageResponse, SessionResponse,
)
from ..services import session_service
from ..services.auth import get_current_user

router = APIRouter(prefix="/api/gen", tags=["generation"])


class ParseRequest(BaseModel):
    answer: str | None = None
    description: str | None = None


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    req: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await session_service.create_session(db, user.id, req.description)


@router.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await session_service.list_user_sessions(db, user.id)


@router.get("/sessions/{session_id}/messages", response_model=list[SessionMessageResponse])
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await session_service.list_messages(db, session_id, user.id)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await session_service.get_user_session(db, session_id, user.id)
    return await session_service.enrich_session(db, session)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await session_service.delete_session(db, session_id, user.id)
    return None


_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


@router.post("/sessions/{session_id}/messages")
async def add_session_message(
    session_id: str,
    req: MessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stream = session_service.stream_process_message(
        db, session_id, user.id, req.content.strip(),
    )
    return StreamingResponse(stream, media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/sessions/{session_id}/parse")
async def parse_session(
    session_id: str,
    req: ParseRequest = ParseRequest(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stream = session_service.stream_parse_session(
        db, session_id, user.id, answer=req.answer, description=req.description,
    )
    return StreamingResponse(stream, media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/sessions/{session_id}/confirm")
async def confirm_session(
    session_id: str,
    req: ConfirmRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await session_service.confirm_session(db, session_id, user.id, req.data)


@router.post("/sessions/{session_id}/generate")
async def generate_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stream = await session_service.stream_generation(db, session_id, user.id)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions/{session_id}/result")
async def get_result(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await session_service.get_completed_result(db, session_id, user.id)


@router.get("/sessions/{session_id}/download")
async def download_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    archive, filename = await session_service.build_download_archive(db, session_id, user.id)
    return StreamingResponse(
        io.BytesIO(archive),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


_PROTOCOL_UPLOAD_LIMIT = 10 * 1024 * 1024


async def _read_bounded(file: UploadFile, limit: int) -> bytes:
    """Read an UploadFile in chunks; abort early once ``limit`` bytes are exceeded.

    Returning ``None`` is reserved for the no-file case; a too-large upload
    raises :class:`ProtocolSubmissionFileTooLarge` directly so the request
    is rejected without buffering the full payload.
    """
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(65536):
        total += len(chunk)
        if total > limit:
            from ..services.exceptions import ProtocolSubmissionFileTooLarge
            raise ProtocolSubmissionFileTooLarge("文件超过 10MB 限制")
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/sessions/{session_id}/protocol-submissions", status_code=201)
async def submit_protocol(
    session_id: str,
    brand: str = Form(...),
    model: str = Form(...),
    source_type: str = Form(...),
    raw_content: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file_data = await _read_bounded(file, _PROTOCOL_UPLOAD_LIMIT) if file else None
    return await session_service.submit_protocol(
        db,
        session_id,
        user.id,
        brand=brand,
        model_name=model,
        source_type=source_type,
        raw_content=raw_content,
        file_data=file_data,
        filename=file.filename if file else None,
    )


@router.get("/sessions/{session_id}/protocol-submissions")
async def list_session_submissions(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await session_service.list_session_submissions(db, session_id, user.id)
