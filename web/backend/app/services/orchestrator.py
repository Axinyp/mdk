import json
import uuid
from typing import AsyncGenerator

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.session import GenSession
from ..models.setting import Setting
from ..schemas.gen import ConfirmRequest, FunctionItem, ParsedData
from . import join_registry, knowledge, prompt_builder, validator
from .llm import get_default_config, llm_chat


async def create_session(db: AsyncSession, user_id: int, description: str) -> GenSession:
    session = GenSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        description=description,
        title=description[:50] if description else "未命名",
        status="created",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def _transition(db: AsyncSession, session_id: str, from_statuses: set[str], to_status: str) -> GenSession:
    result = await db.execute(
        update(GenSession)
        .where(GenSession.id == session_id, GenSession.status.in_(tuple(from_statuses)))
        .values(status=to_status)
    )
    if result.rowcount != 1:
        await db.rollback()
        raise ValueError(f"Cannot transition to {to_status}: session not in expected status")
    await db.commit()
    session = await db.get(GenSession, session_id)
    return session


async def _mark_error(session: GenSession, db: AsyncSession, message: str):
    session.status = "error"
    session.validation_report = json.dumps({"critical": 1, "warning": 0, "details": [message]}, ensure_ascii=False)
    await db.commit()


async def stage_parse(db: AsyncSession, session_id: str, description: str) -> ParsedData:
    session = await _transition(db, session_id, {"created", "error"}, "parsing")

    config = await get_default_config(db)
    if not config:
        await _mark_error(session, db, "No LLM configured")
        raise RuntimeError("No LLM configured")

    try:
        messages = prompt_builder.build_parse_prompt(description, knowledge.get_protocols_index())
        response = await llm_chat(
            messages=messages, config=config, stream=False,
            temperature=0.0, response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        parsed = ParsedData(**_extract_json(content))

        session.parsed_data = json.dumps(parsed.model_dump(), ensure_ascii=False)
        session.llm_model = config.model
        session.title = description[:50]
        session.status = "parsed"
        await db.commit()
        return parsed
    except Exception:
        await _mark_error(session, db, "Parse stage failed")
        raise


async def stage_confirm(db: AsyncSession, session_id: str, confirmed: ParsedData) -> list[FunctionItem]:
    session = await _transition(db, session_id, {"parsed", "confirmed"}, "confirmed")

    try:
        functions_with_joins = join_registry.allocate(confirmed.functions)
        session.confirmed_data = json.dumps(confirmed.model_dump(), ensure_ascii=False)
        session.join_registry = json.dumps([f.model_dump() for f in functions_with_joins], ensure_ascii=False)
        await db.commit()
        return functions_with_joins
    except Exception:
        await _mark_error(session, db, "Confirm stage failed")
        raise


async def stage_generate(db: AsyncSession, session_id: str) -> AsyncGenerator[str, None]:
    session = await _transition(db, session_id, {"confirmed"}, "generating")

    config = await get_default_config(db)
    if not config:
        await _mark_error(session, db, "No LLM configured")
        yield _sse("error", "No LLM configured")
        return

    try:
        confirmed = ParsedData(**json.loads(session.confirmed_data))
        functions_with_joins = [FunctionItem(**f) for f in json.loads(session.join_registry)]

        resolution_s = await db.get(Setting, "default_resolution")
        resolution = resolution_s.value if resolution_s else "2560x1600"
        version_s = await db.get(Setting, "xml_version")
        xml_version = version_s.value if version_s else "4.1.9"

        matched_protocols = prompt_builder.collect_matched_protocols(confirmed)
        matched_patterns = prompt_builder.collect_matched_patterns(confirmed)

        yield _sse("status", "正在生成 Project.xml...")
        xml_messages = prompt_builder.build_xml_prompt(confirmed, functions_with_joins, resolution, xml_version)
        xml_resp = await llm_chat(messages=xml_messages, config=config, stream=False, temperature=0.0)
        xml_content = _strip_fence(xml_resp.choices[0].message.content)
        session.xml_content = xml_content
        await db.commit()
        yield _sse("xml_done", json.dumps({"length": len(xml_content)}, ensure_ascii=False))

        yield _sse("status", "正在生成 .cht 文件...")
        cht_messages = prompt_builder.build_cht_prompt(confirmed, functions_with_joins, matched_protocols, matched_patterns)
        cht_resp = await llm_chat(messages=cht_messages, config=config, stream=False, temperature=0.0)
        cht_content = _strip_fence(cht_resp.choices[0].message.content)
        session.cht_content = cht_content
        await db.commit()
        yield _sse("cht_done", json.dumps({"length": len(cht_content)}, ensure_ascii=False))

        yield _sse("status", "正在交叉校验...")
        report = await validator.run_full_validation(xml_content, cht_content)
        session.validation_report = json.dumps(report, ensure_ascii=False)
        session.status = "completed"
        await db.commit()
        yield _sse("validation", json.dumps(report["summary"], ensure_ascii=False))
        yield _sse("done", '{"status":"completed"}')

    except Exception:
        await _mark_error(session, db, "Generate stage failed")
        yield _sse("error", "Generate stage failed")


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1
        end = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), len(lines))
        text = "\n".join(lines[start:end])
    return json.loads(text)


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        return "\n".join(lines[1:end]).strip()
    return text


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
