from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.session import ParseRevision, SessionMessage
from ..schemas.gen import ParsedData


async def add_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    kind: str,
    content: str,
) -> SessionMessage:
    msg = SessionMessage(session_id=session_id, role=role, kind=kind, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(
    db: AsyncSession,
    session_id: str,
    limit: int = 20,
) -> list[SessionMessage]:
    result = await db.execute(
        select(SessionMessage)
        .where(SessionMessage.session_id == session_id)
        .order_by(SessionMessage.created_at.asc(), SessionMessage.id.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_latest_revision(
    db: AsyncSession,
    session_id: str,
) -> ParseRevision | None:
    result = await db.execute(
        select(ParseRevision)
        .where(ParseRevision.session_id == session_id)
        .order_by(ParseRevision.revision.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def save_revision(
    db: AsyncSession,
    session_id: str,
    parsed: ParsedData,
) -> ParseRevision:
    latest = await get_latest_revision(db, session_id)
    next_rev = 1 if latest is None else latest.revision + 1
    rev = ParseRevision(
        session_id=session_id,
        revision=next_rev,
        parsed_data=json.dumps(parsed.model_dump(), ensure_ascii=False),
        missing_info=json.dumps(parsed.missing_info, ensure_ascii=False),
    )
    db.add(rev)
    await db.commit()
    await db.refresh(rev)
    return rev


def format_clarification_question(missing_info: list[str]) -> str:
    if not missing_info:
        return ""
    lines = ["还缺少以下信息，请逐项补充："]
    lines.extend(f"{i}. {item}" for i, item in enumerate(missing_info, start=1))
    return "\n".join(lines)


def build_parse_context(messages: list[SessionMessage]) -> str:
    parts: list[str] = []
    for msg in messages:
        if msg.role == "user" and msg.kind == "description":
            parts.append(f"初始需求：\n{msg.content}")
        elif msg.role == "assistant" and msg.kind == "clarification":
            parts.append(f"系统追问：\n{msg.content}")
        elif msg.role == "user" and msg.kind == "answer":
            parts.append(f"用户补充：\n{msg.content}")
    return "\n\n".join(parts)
