import asyncio
import json
import re
import time
import uuid
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.session import GenSession
from ..models.setting import Setting
from ..schemas.gen import ConfirmRequest, FunctionItem, ParsedData
from . import conversation_service, join_registry, knowledge, prompt_builder, semantic_validator, validator
from .exceptions import ConcurrentTransition
from .llm import get_default_config, llm_chat
from .session_state import InvalidTransition, SessionStatus, assert_transition

# Streaming generation: connection establishment must complete in 60s,
# but receiving the (potentially long) stream is unbounded as long as
# chunks keep arriving. ``_PROGRESS_INTERVAL`` throttles SSE progress
# pushes so we don't flood the client with one event per token.
_STREAM_OPEN_TIMEOUT = 60.0
_PROGRESS_INTERVAL = 0.8


async def create_session(db: AsyncSession, user_id: int, description: str) -> GenSession:
    session = GenSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        description=description,
        title=description[:50] if description else "未命名",
        status=SessionStatus.CREATED.value,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    await conversation_service.add_message(db, session.id, role="user", kind="description", content=description)
    await db.commit()
    logger.debug("[DB] 新建 session={}, user={}", session.id[:8], user_id)
    return session


async def _transition(db: AsyncSession, session_id: str, target: SessionStatus) -> GenSession:
    """Atomic state transition via optimistic lock.

    Issues ``UPDATE gen_sessions SET status=?, version=version+1
    WHERE id=? AND version=expected_version``. ``rowcount=0`` means another
    request already advanced the row; we surface that as ``ConcurrentTransition``
    (HTTP 409) so the caller can retry from a freshly-fetched state.

    Validates the transition table BEFORE issuing the UPDATE so callers get
    a clear ``InvalidTransition`` for definitionally-illegal moves.
    """
    logger.debug("[DB] 状态转移 session={}: → {}", session_id[:8], target.value)
    session = await db.get(GenSession, session_id)
    if not session:
        logger.error("[DB] 状态转移失败: session {} 不存在", session_id[:8])
        raise ValueError(f"Cannot transition to {target.value}: session not found")

    expected_version = session.version
    expected_status = session.status
    try:
        assert_transition(expected_status, target)
    except InvalidTransition:
        await db.refresh(session)
        expected_version = session.version
        expected_status = session.status
        assert_transition(expected_status, target)  # propagates if still invalid

    result = await db.execute(
        update(GenSession)
        .where(
            GenSession.id == session_id,
            GenSession.version == expected_version,
            GenSession.status == expected_status,
        )
        .values(status=target.value, version=GenSession.version + 1)
    )
    if result.rowcount == 0:
        # Distinguish the failure cause via a fresh SELECT (refresh would error if row deleted).
        fresh = await db.execute(
            select(GenSession.version, GenSession.status).where(GenSession.id == session_id)
        )
        row = fresh.first()
        if row is None:
            raise ValueError(f"Cannot transition to {target.value}: session no longer exists")
        actual_version, actual_status = row
        raise ConcurrentTransition(
            f"Session {session_id[:8]} was concurrently modified "
            f"(expected v={expected_version}/{expected_status}, got v={actual_version}/{actual_status})"
        )

    await db.commit()
    await db.refresh(session)
    return session


async def _mark_error(session: GenSession, db: AsyncSession, message: str):
    logger.debug("[DB] 标记错误 session={}: {}", session.id[:8], message[:100])
    session.status = SessionStatus.ERROR.value
    session.validation_report = json.dumps({"critical": 1, "warning": 0, "details": [message]}, ensure_ascii=False)
    await db.commit()


async def stream_parse(
    db: AsyncSession,
    session_id: str,
    description: str,
) -> AsyncGenerator[str, None]:
    """Streaming parse stage — yields SSE events, mirrors stage_generate shape.

    Events:
    - status:       human-readable progress text (string body)
    - progress:     {phase, chars, elapsed}
    - parsed_done:  full ParsedData JSON (consumed by router/session_service to
                    persist downstream; the same payload is forwarded to clients)
    - error:        error message (string body)

    The non-streaming ``stage_parse`` was prone to 60s HTTP timeouts on slow
    upstreams since the JSON object is only emitted at the end. Streaming the
    chunks keeps the connection healthy while the model writes, and lets the
    UI surface live progress.
    """
    t0 = time.perf_counter()
    logger.info("[FLOW] ===== 解析阶段开始 (流式) session={} =====", session_id[:8])
    session = await _transition(db, session_id, SessionStatus.PARSING)

    config = await get_default_config(db)
    if not config:
        logger.error("[FLOW] 未配置 LLM 模型，无法解析")
        await _mark_error(session, db, "No LLM configured")
        yield _sse("error", "No LLM configured")
        return

    try:
        logger.debug("[PROMPT] 构建解析 prompt, 描述长度={}", len(description))
        messages = prompt_builder.build_parse_prompt(description, knowledge.get_protocols_index())
        logger.debug("[PROMPT] 解析 prompt 就绪, 消息数={}", len(messages))

        yield _sse("status", "正在解析需求...")

        # response_format=json_object 在 stream 模式下并非所有 provider 支持
        # （Claude / Gemini 会忽略或报错）。这里依赖 prompt 强约束 + 末尾
        # _extract_json 五层兜底解析，覆盖率更广。
        stream = await llm_chat(
            messages=messages, config=config, stream=True,
            temperature=0.0, timeout=_STREAM_OPEN_TIMEOUT,
        )
        content = ""
        last_push = 0.0
        async for chunk in stream:
            delta = _chunk_text(chunk)
            if not delta:
                continue
            content += delta
            now = time.perf_counter()
            if now - last_push >= _PROGRESS_INTERVAL:
                last_push = now
                yield _sse("progress", json.dumps({
                    "phase": "parse",
                    "chars": len(content),
                    "elapsed": round(now - t0, 1),
                }, ensure_ascii=False))

        try:
            parsed_dict = _extract_json(content)
        except json.JSONDecodeError as exc:
            logger.opt(exception=exc).error("[FLOW] 解析阶段 JSON 解析失败")
            await _mark_error(session, db, f"Parse JSON failed: {exc}")
            yield _sse("error", f"LLM 返回无法解析的 JSON: {exc}")
            return

        parsed = ParsedData(**parsed_dict)
        logger.info(
            "[FLOW] 解析完成 — 设备={}, 功能={}, 页面={} ({:.1f}s)",
            len(parsed.devices), len(parsed.functions), len(parsed.pages),
            time.perf_counter() - t0,
        )

        semantic_issues = semantic_validator.validate_parsed_data(parsed)
        if semantic_issues:
            logger.warning("[FLOW] 语义校验发现 {} 个问题: {}", len(semantic_issues), semantic_issues[:3])
            if not parsed.missing_info:
                parsed.missing_info = []
            parsed.missing_info = list(parsed.missing_info) + [f"[语义告警] {s}" for s in semantic_issues]

        session.parsed_data = json.dumps(parsed.model_dump(), ensure_ascii=False)
        session.llm_model = config.model
        session.title = description[:50]
        session.status = SessionStatus.PARSED.value
        await conversation_service.save_revision(db, session.id, parsed)
        await conversation_service.add_message(
            db, session.id, role="assistant", kind="summary",
            content=_format_parse_summary(parsed),
        )
        await db.commit()
        logger.debug("[DB] 解析结果已持久化 session={}", session_id[:8])

        yield _sse("parsed_done", json.dumps(parsed.model_dump(), ensure_ascii=False))

    except asyncio.CancelledError:
        elapsed = time.perf_counter() - t0
        session.status = SessionStatus.ABORTED.value
        try:
            await db.commit()
        except Exception as commit_exc:
            await db.rollback()
            logger.warning(
                "[FLOW] Parse SSE 取消提交失败 session={}: {}",
                session_id[:8], commit_exc,
            )
        logger.warning(
            "[FLOW] Parse SSE 客户端断开 — session={} 标记为 aborted ({:.1f}s)",
            session_id[:8], elapsed,
        )
        raise
    except Exception as exc:
        logger.opt(exception=exc).error("[FLOW] 解析阶段失败: {}", exc)
        await _mark_error(session, db, f"Parse stage failed: {exc!r}")
        yield _sse("error", f"Parse stage failed: {exc!r}")


async def stage_confirm(db: AsyncSession, session_id: str, confirmed: ParsedData) -> list[FunctionItem]:
    logger.info("[FLOW] ===== 确认阶段 session={} =====", session_id[:8])
    session = await _transition(db, session_id, SessionStatus.CONFIRMED)

    try:
        functions_with_joins = join_registry.allocate(confirmed.functions)
        logger.debug("[FLOW] Join 分配完成, 功能数={}", len(functions_with_joins))
        session.confirmed_data = json.dumps(confirmed.model_dump(), ensure_ascii=False)
        session.join_registry = json.dumps([f.model_dump() for f in functions_with_joins], ensure_ascii=False)
        await db.commit()
        logger.debug("[DB] 确认数据已持久化 session={}", session_id[:8])
        return functions_with_joins
    except Exception:
        await _mark_error(session, db, "Confirm stage failed")
        raise


async def stage_generate(db: AsyncSession, session_id: str) -> AsyncGenerator[str, None]:
    t_total = time.perf_counter()
    logger.info("[FLOW] ===== 生成阶段开始 session={} =====", session_id[:8])
    session = await _transition(db, session_id, SessionStatus.GENERATING)

    config = await get_default_config(db)
    if not config:
        logger.error("[FLOW] 未配置 LLM 模型，无法生成")
        await _mark_error(session, db, "No LLM configured")
        yield _sse("error", "No LLM configured")
        return

    try:
        confirmed = ParsedData(**json.loads(session.confirmed_data))
        functions_with_joins = [FunctionItem(**f) for f in json.loads(session.join_registry)]
        logger.debug(
            "[DB] 读取确认数据 — 设备={}, 功能={}, 页面={}",
            len(confirmed.devices), len(functions_with_joins), len(confirmed.pages),
        )

        resolution_s = await db.get(Setting, "default_resolution")
        resolution = resolution_s.value if resolution_s else "2560x1600"
        version_s = await db.get(Setting, "xml_version")
        xml_version = version_s.value if version_s else "4.1.9"
        logger.debug("[DB] 读取设置 — resolution={}, xml_version={}", resolution, xml_version)

        matched_protocols = prompt_builder.collect_matched_protocols(confirmed)
        matched_patterns = prompt_builder.collect_matched_patterns(confirmed)
        logger.debug("[KNOWLEDGE] 匹配协议={}, 匹配模式={}", len(matched_protocols), len(matched_patterns))

        # ── Phase 1: XML ──
        logger.info("[FLOW] ▶ Phase 1/3: 生成 XML...")
        yield _sse("status", "正在生成 Project.xml...")

        logger.debug("[PROMPT] 构建 XML prompt...")
        xml_messages = prompt_builder.build_xml_prompt(confirmed, functions_with_joins, resolution, xml_version)
        logger.debug("[PROMPT] XML prompt 就绪, 消息数={}", len(xml_messages))

        xml_phase_start = time.perf_counter()
        xml_stream = await llm_chat(
            messages=xml_messages, config=config, stream=True, temperature=0.0,
            timeout=_STREAM_OPEN_TIMEOUT,
        )
        xml_content = ""
        last_push = 0.0
        async for chunk in xml_stream:
            delta = _chunk_text(chunk)
            if not delta:
                continue
            xml_content += delta
            now = time.perf_counter()
            if now - last_push >= _PROGRESS_INTERVAL:
                last_push = now
                yield _sse("progress", json.dumps({
                    "phase": "xml",
                    "chars": len(xml_content),
                    "elapsed": round(now - xml_phase_start, 1),
                }, ensure_ascii=False))

        xml_content = _strip_control_chars(_strip_fence(xml_content))
        session.xml_content = xml_content
        await db.commit()
        logger.debug("[DB] XML 内容已持久化, {} 字符", len(xml_content))
        logger.info(
            "[FLOW] ✓ XML 完成 — {} 字符 ({:.1f}s)",
            len(xml_content), time.perf_counter() - xml_phase_start,
        )
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
        logger.debug("[PROMPT] CHT prompt 就绪, 消息数={}", len(cht_messages))

        cht_phase_start = time.perf_counter()
        cht_stream = await llm_chat(
            messages=cht_messages, config=config, stream=True, temperature=0.0,
            timeout=_STREAM_OPEN_TIMEOUT,
        )
        cht_content = ""
        last_push = 0.0
        async for chunk in cht_stream:
            delta = _chunk_text(chunk)
            if not delta:
                continue
            cht_content += delta
            now = time.perf_counter()
            if now - last_push >= _PROGRESS_INTERVAL:
                last_push = now
                yield _sse("progress", json.dumps({
                    "phase": "cht",
                    "chars": len(cht_content),
                    "elapsed": round(now - cht_phase_start, 1),
                }, ensure_ascii=False))

        cht_content = _strip_control_chars(_strip_fence(cht_content))
        session.cht_content = cht_content
        await db.commit()
        logger.debug("[DB] CHT 内容已持久化, {} 字符", len(cht_content))
        logger.info(
            "[FLOW] ✓ CHT 完成 — {} 字符 ({:.1f}s)",
            len(cht_content), time.perf_counter() - cht_phase_start,
        )
        yield _sse("cht_done", json.dumps({"length": len(cht_content)}, ensure_ascii=False))

        # ── Phase 3: 校验 ──
        logger.info("[FLOW] ▶ Phase 3/3: 交叉校验...")
        yield _sse("status", "正在交叉校验...")

        report = await validator.run_full_validation(xml_content, cht_content)

        session.validation_report = json.dumps(report, ensure_ascii=False)
        session.status = SessionStatus.COMPLETED.value
        await db.commit()
        logger.debug("[DB] 校验报告已持久化 session={}", session_id[:8])

        elapsed_total = time.perf_counter() - t_total
        logger.info(
            "[FLOW] ✓ 全部完成 — 耗时 {:.1f}s, critical={}, warning={}",
            elapsed_total, report["summary"]["critical"], report["summary"]["warning"],
        )
        yield _sse("validation", json.dumps(report["summary"], ensure_ascii=False))
        yield _sse("done", json.dumps({"status": SessionStatus.COMPLETED.value}, ensure_ascii=False))

    except asyncio.CancelledError:
        elapsed_total = time.perf_counter() - t_total
        session.status = SessionStatus.ABORTED.value
        try:
            await db.commit()
        except Exception as commit_exc:
            await db.rollback()
            logger.warning(
                "[FLOW] SSE cancellation commit failed for session={}: {}",
                session_id[:8], commit_exc,
            )
        logger.warning(
            "[FLOW] SSE 客户端断开 — session={} 标记为 aborted (耗时 {:.1f}s)",
            session_id[:8], elapsed_total,
        )
        raise
    except Exception as exc:
        elapsed_total = time.perf_counter() - t_total
        logger.opt(exception=exc).error("[FLOW] ✗ 生成失败 — 耗时 {:.1f}s: {}", elapsed_total, exc)
        await _mark_error(session, db, f"Generate stage failed: {exc!r}")
        yield _sse("error", f"Generate stage failed: {exc!r}")


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
        end = next((i for i in range(len (lines) - 1, 0, -1) if lines[i].strip() == "```"), len(lines))
        text = "\n".join(lines[start:end])
    # Pass 1: strip control chars that are never valid JSON whitespace
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Pass 2: escape literal control chars inside string values
    try:
        return json.loads(_sanitize_json(text))
    except json.JSONDecodeError:
        pass
    # Pass 3: replace ALL control chars (incl. \t \n \r) with space
    try:
        stripped = re.sub(r'[\x00-\x1f\x7f]', ' ', text)
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    # Pass 4: byte-level — drop every char whose Unicode category is Cc (control)
    import unicodedata
    cleaned = ''.join(' ' if unicodedata.category(c) == 'Cc' else c for c in text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Pass 5: last resort — keep only printable ASCII + common Unicode, force single line
    printable = re.sub(r'[^\x20-\x7e -�]', '', text)
    return json.loads(printable)


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        return "\n".join(lines[1:end]).strip()
    return text


def _strip_control_chars(text: str) -> str:
    """Remove control characters that are invalid in XML/text output."""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


def _chunk_text(chunk) -> str:
    """Extract delta text from a litellm streaming chunk, tolerant of
    occasional ``None`` choices/delta objects from upstream proxies.
    """
    try:
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            return ""
        delta = getattr(choices[0], "delta", None)
        if delta is None:
            return ""
        return getattr(delta, "content", "") or ""
    except (AttributeError, IndexError):
        return ""


def _format_parse_summary(parsed: ParsedData) -> str:
    return (
        f"解析完成。设备 {len(parsed.devices)} 个，"
        f"功能 {len(parsed.functions)} 个，"
        f"页面 {len(parsed.pages)} 个。"
        "如无遗漏信息，可继续确认生成。"
    )
