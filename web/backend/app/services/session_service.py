"""High-level session orchestration. Routers in ``routers/gen.py`` should
delegate all business logic here; they only translate request/response shapes.
"""

from __future__ import annotations

import io
import json
import zipfile
from json import JSONDecodeError
from typing import AsyncGenerator

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.session import GenSession, ParseRevision, ProtocolSubmission, SessionMessage
from ..schemas.gen import ParsedData, SessionMessageResponse, SessionResponse
from . import conversation_service, orchestrator, protocol_ingestion
from .exceptions import (
    DomainError,
    GenerationNotComplete,
    InvalidStageTransition,
    LLMResponseInvalid,
    LLMUnavailable,
    ProtocolSubmissionFileTooLarge,
    ProtocolSubmissionInvalid,
    SessionInputInvalid,
    SessionNotFound,
)
from .session_state import InvalidTransition, SessionStatus


# ── Lookups ─────────────────────────────────────────────────────────

async def get_user_session(db: AsyncSession, session_id: str, user_id: int) -> GenSession:
    """Fetch a session owned by ``user_id``. Hides the wrong-owner case
    behind ``SessionNotFound`` to avoid leaking session existence."""
    result = await db.execute(
        select(GenSession).where(GenSession.id == session_id, GenSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise SessionNotFound("Session not found")
    return session


async def enrich_session(db: AsyncSession, session: GenSession) -> dict:
    latest = await conversation_service.get_latest_revision(db, session.id)
    payload = SessionResponse.model_validate(session).model_dump()
    payload["current_revision"] = latest.revision if latest else None
    return payload


async def list_user_sessions(db: AsyncSession, user_id: int) -> list[GenSession]:
    result = await db.execute(
        select(GenSession)
        .where(GenSession.user_id == user_id)
        .order_by(GenSession.updated_at.desc())
    )
    return list(result.scalars().all())


async def list_messages(db: AsyncSession, session_id: str, user_id: int) -> list[SessionMessage]:
    session = await get_user_session(db, session_id, user_id)
    return await conversation_service.get_messages(db, session.id)


# ── Helpers ─────────────────────────────────────────────────────────

def _message_payload(messages: list[SessionMessage]) -> list[dict]:
    # mode="json" so datetime/UUID etc. serialize to strings — required by
    # the SSE path (`json.dumps` doesn't know how to handle datetime); the
    # plain HTTP path is unaffected since FastAPI uses jsonable_encoder
    # which already returns strings for those types.
    return [SessionMessageResponse.model_validate(m).model_dump(mode="json") for m in messages]


def _wrap_parse_exception(exc: Exception) -> Exception:
    """Translate orchestrator exceptions to domain errors.

    Known parse-time failures map to specific domain types; any other
    upstream / transport / provider error from ``llm_chat`` is treated
    as ``LLMUnavailable`` so it surfaces as a stable 502 instead of a
    generic 500.
    """
    if isinstance(exc, DomainError):
        return exc
    if isinstance(exc, JSONDecodeError):
        return LLMResponseInvalid(f"LLM 返回了无法解析的 JSON: {exc}")
    if isinstance(exc, InvalidTransition):
        return InvalidStageTransition(str(exc))
    if isinstance(exc, ValueError) and "session not found" in str(exc).lower():
        return SessionNotFound("Session not found")
    if isinstance(exc, RuntimeError) and str(exc) == "No LLM configured":
        return LLMUnavailable(str(exc))
    return LLMUnavailable(f"LLM upstream error: {exc}")


# ── Lifecycle stages ────────────────────────────────────────────────

async def create_session(db: AsyncSession, user_id: int, description: str) -> dict:
    session = await orchestrator.create_session(db, user_id, description)
    return await enrich_session(db, session)


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


async def _drain_parse_stream(
    db: AsyncSession,
    session: GenSession,
) -> AsyncGenerator[str, None]:
    """Forward orchestrator parse SSE events; on success append a `done`
    event carrying refreshed status + messages so the client can refresh
    its conversation pane in a single round-trip.
    """
    parse_failed = False
    async for ev in orchestrator.stream_parse(db, session.id, session.description):
        if ev.startswith("event: error"):
            parse_failed = True
        yield ev

    if not parse_failed:
        await db.refresh(session)
        messages = await conversation_service.get_messages(db, session.id)
        yield _sse("done", json.dumps({
            "status": session.status,
            "messages": _message_payload(messages),
        }, ensure_ascii=False))


async def stream_process_message(
    db: AsyncSession,
    session_id: str,
    user_id: int,
    content: str,
) -> AsyncGenerator[str, None]:
    """Append a user answer, rebuild parse context, then stream-parse.

    The user message + description update commit alongside the state
    transition to PARSING inside the orchestrator (atomic optimistic-lock
    UPDATE). On streaming parse failure the session is marked ERROR by the
    orchestrator and an SSE error event is yielded — the conversation
    history retains the user's input either way.
    """
    session = await get_user_session(db, session_id, user_id)
    try:
        await conversation_service.add_message(
            db, session.id, role="user", kind="answer", content=content,
        )
        messages = await conversation_service.get_messages(db, session.id)
        combined = conversation_service.build_parse_context(messages)
        session.description = combined
        await db.commit()
    except Exception as exc:
        wrapped = _wrap_parse_exception(exc)
        if wrapped is not exc:
            raise wrapped from exc
        raise

    async for ev in _drain_parse_stream(db, session):
        yield ev


async def stream_parse_session(
    db: AsyncSession,
    session_id: str,
    user_id: int,
    *,
    answer: str | None = None,
    description: str | None = None,
) -> AsyncGenerator[str, None]:
    """Stream-parse / re-parse a session.

    - ``description`` (override): replaces the session description and ignores
      prior conversation, used by the description fold-bar's "重新解析".
    - ``answer``: appended as a user message, then combined into parse context.
    - neither: re-parses with current session.description.
    """
    session = await get_user_session(db, session_id, user_id)
    try:
        if description is not None:
            text = description.strip()
            if not text:
                raise SessionInputInvalid("描述不能为空")
            session.description = text
        else:
            if answer:
                await conversation_service.add_message(
                    db, session.id, role="user", kind="answer", content=answer.strip(),
                )
            messages = await conversation_service.get_messages(db, session.id)
            combined = conversation_service.build_parse_context(messages)
            session.description = combined or session.description
        await db.commit()
    except Exception as exc:
        wrapped = _wrap_parse_exception(exc)
        if wrapped is not exc:
            raise wrapped from exc
        raise

    async for ev in _drain_parse_stream(db, session):
        yield ev


async def delete_session(
    db: AsyncSession,
    session_id: str,
    user_id: int,
) -> None:
    """Delete a session owned by ``user_id``.

    Foreign keys do not have ``ondelete=CASCADE`` (see models.session), so we
    purge dependent rows manually:

    - SessionMessage / ParseRevision: hard-deleted (per-session conversation
      history is meaningless without the session)
    - ProtocolSubmission: ``session_id`` set to NULL so review assets survive
      (they may already be approved or in the queue)

    Hides the wrong-owner case behind ``SessionNotFound`` to avoid leaking
    session existence.
    """
    session = await get_user_session(db, session_id, user_id)
    await db.execute(delete(SessionMessage).where(SessionMessage.session_id == session.id))
    await db.execute(delete(ParseRevision).where(ParseRevision.session_id == session.id))
    await db.execute(
        update(ProtocolSubmission)
        .where(ProtocolSubmission.session_id == session.id)
        .values(session_id=None)
    )
    await db.delete(session)
    await db.commit()


async def confirm_session(
    db: AsyncSession,
    session_id: str,
    user_id: int,
    data: ParsedData,
) -> dict:
    await get_user_session(db, session_id, user_id)
    try:
        functions = await orchestrator.stage_confirm(db, session_id, data)
    except InvalidTransition as exc:
        raise InvalidStageTransition(str(exc)) from exc

    return {
        "status": SessionStatus.CONFIRMED.value,
        "functions": [f.model_dump() for f in functions],
    }


async def stream_generation(
    db: AsyncSession,
    session_id: str,
    user_id: int,
) -> AsyncGenerator[str, None]:
    """Verify ownership before opening the SSE stream, then defer to orchestrator."""
    session = await get_user_session(db, session_id, user_id)
    return orchestrator.stage_generate(db, session.id)


async def get_completed_result(db: AsyncSession, session_id: str, user_id: int) -> dict:
    session = await get_user_session(db, session_id, user_id)
    if session.status != SessionStatus.COMPLETED.value:
        raise GenerationNotComplete(f"Not completed: {session.status}")
    return {
        "xml_content": session.xml_content,
        "cht_content": session.cht_content,
        "validation_report": json.loads(session.validation_report) if session.validation_report else None,
    }


async def build_download_archive(
    db: AsyncSession,
    session_id: str,
    user_id: int,
) -> tuple[bytes, str]:
    session = await get_user_session(db, session_id, user_id)
    if not session.xml_content or not session.cht_content:
        raise GenerationNotComplete("No generated content")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Project.xml", session.xml_content)
        zf.writestr("output.cht", session.cht_content)
        if session.validation_report:
            zf.writestr("validation_report.json", session.validation_report)
    return buf.getvalue(), f"mdk_{session_id[:8]}.zip"


# ── Protocol submissions ────────────────────────────────────────────

async def submit_protocol(
    db: AsyncSession,
    session_id: str | None,
    user_id: int,
    *,
    brand: str,
    model_name: str,
    source_type: str,
    raw_content: str | None,
    file_data: bytes | None,
    filename: str | None,
) -> dict:
    """Submit a protocol for review.

    ``session_id`` may be ``None`` for standalone submissions made from the
    protocol management page; when provided, the session is verified to be
    owned by ``user_id`` so the submission can be traced back.
    """
    bound_session_id: str | None = None
    if session_id is not None:
        session = await get_user_session(db, session_id, user_id)
        bound_session_id = session.id

    if source_type == "paste":
        if not raw_content or len(raw_content.strip()) < 10:
            raise ProtocolSubmissionInvalid("内容过短，至少需要 10 个字符")
        content = raw_content.strip()
        submit_filename: str | None = None
    elif source_type == "file":
        if file_data is None:
            raise ProtocolSubmissionInvalid("未上传文件")
        if len(file_data) > 10 * 1024 * 1024:
            raise ProtocolSubmissionFileTooLarge("文件超过 10MB 限制")
        content = file_data.decode("utf-8", errors="replace")
        submit_filename = filename
    else:
        raise ProtocolSubmissionInvalid("source_type 必须为 paste 或 file")

    submission = await protocol_ingestion.ingest(
        raw_content=content,
        source_type=source_type,
        brand=brand,
        model_name=model_name,
        filename=submit_filename,
        session_id=bound_session_id,
        submitter_id=user_id,
        db=db,
    )
    return {
        "id": submission.id,
        "review_status": submission.review_status,
        "brand": submission.brand,
        "model_name": submission.model_name,
    }


async def list_session_submissions(
    db: AsyncSession,
    session_id: str,
    user_id: int,
) -> list[dict]:
    session = await get_user_session(db, session_id, user_id)
    result = await db.execute(
        select(ProtocolSubmission)
        .where(ProtocolSubmission.session_id == session.id)
        .order_by(ProtocolSubmission.created_at.desc())
    )
    return [
        {
            "id": s.id,
            "source_type": s.source_type,
            "brand": s.brand,
            "model_name": s.model_name,
            "review_status": s.review_status,
            "created_at": s.created_at.isoformat(),
        }
        for s in result.scalars().all()
    ]
