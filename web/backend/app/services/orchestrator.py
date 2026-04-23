import json
import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.session import GenSession
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


async def stage_parse(db: AsyncSession, session: GenSession) -> ParsedData:
    session.status = "parsing"
    await db.commit()

    config = await get_default_config(db)
    if not config:
        session.status = "error"
        await db.commit()
        raise RuntimeError("No LLM configured")

    protocols_index = knowledge.get_protocols_index()
    messages = prompt_builder.build_parse_prompt(session.description, protocols_index)

    response = await llm_chat(
        messages=messages,
        config=config,
        stream=False,
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    parsed = _extract_json(content)
    parsed_data = ParsedData(**parsed)

    session.parsed_data = json.dumps(parsed, ensure_ascii=False)
    session.llm_model = config.model
    session.status = "parsed"
    await db.commit()
    return parsed_data


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = next((i for i, l in enumerate(lines) if l.strip().startswith("```")), 0) + 1
        end = next((i for i in range(len(lines) - 1, start - 1, -1) if lines[i].strip() == "```"), len(lines))
        text = "\n".join(lines[start:end])
    return json.loads(text)


async def stage_confirm(db: AsyncSession, session: GenSession, confirmed: ParsedData) -> list[FunctionItem]:
    functions_with_joins = join_registry.allocate(confirmed.functions)
    session.confirmed_data = json.dumps(confirmed.model_dump(), ensure_ascii=False)
    session.join_registry = json.dumps(
        [f.model_dump() for f in functions_with_joins], ensure_ascii=False
    )
    session.status = "confirmed"
    await db.commit()
    return functions_with_joins


async def stage_generate(db: AsyncSession, session: GenSession) -> AsyncGenerator[str, None]:
    session.status = "generating"
    await db.commit()

    config = await get_default_config(db)
    if not config:
        session.status = "error"
        await db.commit()
        yield _sse_event("error", "No LLM configured")
        return

    confirmed = ParsedData(**json.loads(session.confirmed_data))
    functions_with_joins = [FunctionItem(**f) for f in json.loads(session.join_registry)]

    from ..models.setting import Setting
    resolution_setting = await db.get(Setting, "default_resolution")
    resolution = resolution_setting.value if resolution_setting else "2560x1600"
    version_setting = await db.get(Setting, "xml_version")
    xml_version = version_setting.value if version_setting else "4.1.9"

    matched_protocols = prompt_builder.collect_matched_protocols(confirmed)
    matched_patterns = prompt_builder.collect_matched_patterns(confirmed)

    yield _sse_event("status", "正在生成 Project.xml...")

    xml_messages = prompt_builder.build_xml_prompt(confirmed, functions_with_joins, resolution, xml_version)
    xml_response = await llm_chat(messages=xml_messages, config=config, stream=False, temperature=0.0)
    xml_content = xml_response.choices[0].message.content
    xml_content = _strip_code_fence(xml_content)
    session.xml_content = xml_content
    await db.commit()

    yield _sse_event("xml_done", json.dumps({"length": len(xml_content)}, ensure_ascii=False))

    yield _sse_event("status", "正在生成 .cht 文件...")

    cht_messages = prompt_builder.build_cht_prompt(confirmed, functions_with_joins, matched_protocols, matched_patterns)
    cht_response = await llm_chat(messages=cht_messages, config=config, stream=False, temperature=0.0)
    cht_content = cht_response.choices[0].message.content
    cht_content = _strip_code_fence(cht_content)
    session.cht_content = cht_content
    await db.commit()

    yield _sse_event("cht_done", json.dumps({"length": len(cht_content)}, ensure_ascii=False))

    yield _sse_event("status", "正在交叉校验...")

    report = validator.run_full_validation(xml_content, cht_content)
    session.validation_report = json.dumps(report, ensure_ascii=False)
    session.status = "completed"
    await db.commit()

    yield _sse_event("validation", json.dumps(report["summary"], ensure_ascii=False))
    yield _sse_event("done", json.dumps({"status": "completed"}, ensure_ascii=False))


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1
        end = len(lines)
        if lines[-1].strip() == "```":
            end = len(lines) - 1
        return "\n".join(lines[start:end]).strip()
    return text


def _sse_event(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
