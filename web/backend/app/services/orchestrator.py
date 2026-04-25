import json
import logging
import re
import time
import traceback
import uuid
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

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
    logger.debug("[DB] 新建 session=%s, user=%d", session.id[:8], user_id)
    return session


async def _transition(db: AsyncSession, session_id: str, from_statuses: set[str], to_status: str) -> GenSession:
    logger.debug("[DB] 状态转移 session=%s: %s → %s", session_id[:8], from_statuses, to_status)
    result = await db.execute(
        update(GenSession)
        .where(GenSession.id == session_id, GenSession.status.in_(tuple(from_statuses)))
        .values(status=to_status)
    )
    if result.rowcount != 1:
        await db.rollback()
        logger.error("[DB] 状态转移失败 session=%s: 当前状态不在 %s 中", session_id[:8], from_statuses)
        raise ValueError(f"Cannot transition to {to_status}: session not in expected status")
    await db.commit()
    session = await db.get(GenSession, session_id)
    return session


async def _mark_error(session: GenSession, db: AsyncSession, message: str):
    logger.debug("[DB] 标记错误 session=%s: %s", session.id[:8], message[:100])
    session.status = "error"
    session.validation_report = json.dumps({"critical": 1, "warning": 0, "details": [message]}, ensure_ascii=False)
    await db.commit()


async def stage_parse(db: AsyncSession, session_id: str, description: str) -> ParsedData:
    logger.info("[FLOW] ===== 解析阶段开始 session=%s =====", session_id[:8])
    session = await _transition(db, session_id, {"created", "error"}, "parsing")

    config = await get_default_config(db)
    if not config:
        logger.error("[FLOW] 未配置 LLM 模型，无法解析")
        await _mark_error(session, db, "No LLM configured")
        raise RuntimeError("No LLM configured")

    try:
        logger.debug("[PROMPT] 构建解析 prompt, 描述长度=%d", len(description))
        messages = prompt_builder.build_parse_prompt(description, knowledge.get_protocols_index())
        logger.debug("[PROMPT] 解析 prompt 就绪, 消息数=%d", len(messages))

        response = await llm_chat(
            messages=messages, config=config, stream=False,
            temperature=0.0, response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        parsed = ParsedData(**_extract_json(content))
        logger.info("[FLOW] 解析完成 — 设备=%d, 功能=%d, 页面=%d",
                    len(parsed.devices), len(parsed.functions), len(parsed.pages))

        session.parsed_data = json.dumps(parsed.model_dump(), ensure_ascii=False)
        session.llm_model = config.model
        session.title = description[:50]
        session.status = "parsed"
        await db.commit()
        logger.debug("[DB] 解析结果已持久化 session=%s", session_id[:8])
        return parsed
    except Exception as exc:
        logger.error("[FLOW] 解析阶段失败: %s", exc)
        await _mark_error(session, db, f"Parse stage failed: {exc}")
        raise


async def stage_confirm(db: AsyncSession, session_id: str, confirmed: ParsedData) -> list[FunctionItem]:
    logger.info("[FLOW] ===== 确认阶段 session=%s =====", session_id[:8])
    session = await _transition(db, session_id, {"parsed", "confirmed", "error"}, "confirmed")

    try:
        functions_with_joins = join_registry.allocate(confirmed.functions)
        logger.debug("[FLOW] Join 分配完成, 功能数=%d", len(functions_with_joins))
        session.confirmed_data = json.dumps(confirmed.model_dump(), ensure_ascii=False)
        session.join_registry = json.dumps([f.model_dump() for f in functions_with_joins], ensure_ascii=False)
        await db.commit()
        logger.debug("[DB] 确认数据已持久化 session=%s", session_id[:8])
        return functions_with_joins
    except Exception:
        await _mark_error(session, db, "Confirm stage failed")
        raise


async def stage_generate(db: AsyncSession, session_id: str) -> AsyncGenerator[str, None]:
    t_total = time.perf_counter()
    logger.info("[FLOW] ===== 生成阶段开始 session=%s =====", session_id[:8])
    session = await _transition(db, session_id, {"confirmed", "error"}, "generating")

    config = await get_default_config(db)
    if not config:
        logger.error("[FLOW] 未配置 LLM 模型，无法生成")
        await _mark_error(session, db, "No LLM configured")
        yield _sse("error", "No LLM configured")
        return

    try:
        confirmed = ParsedData(**json.loads(session.confirmed_data))
        functions_with_joins = [FunctionItem(**f) for f in json.loads(session.join_registry)]
        logger.debug("[DB] 读取确认数据 — 设备=%d, 功能=%d, 页面=%d",
                     len(confirmed.devices), len(functions_with_joins), len(confirmed.pages))

        resolution_s = await db.get(Setting, "default_resolution")
        resolution = resolution_s.value if resolution_s else "2560x1600"
        version_s = await db.get(Setting, "xml_version")
        xml_version = version_s.value if version_s else "4.1.9"
        logger.debug("[DB] 读取设置 — resolution=%s, xml_version=%s", resolution, xml_version)

        matched_protocols = prompt_builder.collect_matched_protocols(confirmed)
        matched_patterns = prompt_builder.collect_matched_patterns(confirmed)
        logger.debug("[KNOWLEDGE] 匹配协议=%d, 匹配模式=%d", len(matched_protocols), len(matched_patterns))

        # ── Phase 1: XML ──
        logger.info("[FLOW] ▶ Phase 1/3: 生成 XML...")
        yield _sse("status", "正在生成 Project.xml...")

        logger.debug("[PROMPT] 构建 XML prompt...")
        xml_messages = prompt_builder.build_xml_prompt(confirmed, functions_with_joins, resolution, xml_version)
        logger.debug("[PROMPT] XML prompt 就绪, 消息数=%d", len(xml_messages))

        xml_resp = await llm_chat(messages=xml_messages, config=config, stream=False, temperature=0.0)
        xml_content = _strip_fence(xml_resp.choices[0].message.content)

        session.xml_content = xml_content
        await db.commit()
        logger.debug("[DB] XML 内容已持久化, %d 字符", len(xml_content))
        logger.info("[FLOW] ✓ XML 完成 — %d 字符", len(xml_content))
        yield _sse("xml_done", json.dumps({"length": len(xml_content)}, ensure_ascii=False))

        # ── Phase 2: CHT ──
        logger.info("[FLOW] ▶ Phase 2/3: 生成 CHT...")
        yield _sse("status", "正在生成 .cht 文件...")

        logger.debug("[PROMPT] 构建 CHT prompt...")
        cht_messages = prompt_builder.build_cht_prompt(
            confirmed, functions_with_joins, matched_protocols, matched_patterns,
            project_title=session.title or "",
            project_description=session.description or "",
        )
        logger.debug("[PROMPT] CHT prompt 就绪, 消息数=%d", len(cht_messages))

        cht_resp = await llm_chat(messages=cht_messages, config=config, stream=False, temperature=0.0)
        cht_content = _strip_fence(cht_resp.choices[0].message.content)

        session.cht_content = cht_content
        await db.commit()
        logger.debug("[DB] CHT 内容已持久化, %d 字符", len(cht_content))
        logger.info("[FLOW] ✓ CHT 完成 — %d 字符", len(cht_content))
        yield _sse("cht_done", json.dumps({"length": len(cht_content)}, ensure_ascii=False))

        # ── Phase 3: 校验 ──
        logger.info("[FLOW] ▶ Phase 3/3: 交叉校验...")
        yield _sse("status", "正在交叉校验...")

        report = await validator.run_full_validation(xml_content, cht_content)

        session.validation_report = json.dumps(report, ensure_ascii=False)
        session.status = "completed"
        await db.commit()
        logger.debug("[DB] 校验报告已持久化 session=%s", session_id[:8])

        elapsed_total = time.perf_counter() - t_total
        logger.info("[FLOW] ✓ 全部完成 — 耗时 %.1fs, critical=%d, warning=%d",
                    elapsed_total, report["summary"]["critical"], report["summary"]["warning"])
        yield _sse("validation", json.dumps(report["summary"], ensure_ascii=False))
        yield _sse("done", '{"status":"completed"}')

    except Exception as exc:
        elapsed_total = time.perf_counter() - t_total
        logger.error("[FLOW] ✗ 生成失败 — 耗时 %.1fs: %s", elapsed_total, exc)
        logger.debug("[FLOW] 完整堆栈:\n%s", traceback.format_exc())
        await _mark_error(session, db, f"Generate stage failed: {exc!r}")
        yield _sse("error", f"Generate stage failed: {exc!r}\n{traceback.format_exc()}")


def _sanitize_json(text: str) -> str:
    """Escape literal control characters inside JSON string values."""
    _ESC = {'\n': '\\n', '\r': '\\r', '\t': '\\t', '\b': '\\b', '\f': '\\f'}
    result: list[str] = []
    in_string = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == '\\' and in_string:
            result.append(c)
            i += 1
            if i < len(text):
                result.append(text[i])
            i += 1
            continue
        if c == '"':
            in_string = not in_string
        if in_string and ord(c) < 0x20:
            result.append(_ESC.get(c, f'\\u{ord(c):04x}'))
        else:
            result.append(c)
        i += 1
    return ''.join(result)


def _extract_json(text: str) -> dict:
    text = text.strip().lstrip('﻿')
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1
        end = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), len(lines))
        text = "\n".join(lines[start:end])
    # Remove control chars that are never valid in JSON (keep \t \n \r)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Escape literal \n \r \t inside string values
        return json.loads(_sanitize_json(text))


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        return "\n".join(lines[1:end]).strip()
    return text


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
