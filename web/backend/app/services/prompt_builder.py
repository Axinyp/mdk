import json
import logging
from pathlib import Path

from . import knowledge
from ..schemas.gen import FunctionItem, ParsedData

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _read_template(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


# ── Parse 阶段 ────────────────────────────────────────

def build_parse_prompt(description: str, protocols_index: str) -> list[dict]:
    template = _read_template("parse_system.md")
    system = template.replace("{{ protocols_index }}", protocols_index)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": description},
    ]


# ── XML 生成 ──────────────────────────────────────────

def build_xml_prompt(
    confirmed_data: ParsedData,
    functions_with_joins: list[FunctionItem],
    resolution: str = "2560x1600",
    xml_version: str = "4.1.9",
) -> list[dict]:
    template = _read_template("xml_system.md")
    width, height = resolution.split("x")

    control_types = {f.control_type for f in functions_with_joins}
    logger.debug("[PROMPT] XML 控件类型: %s", control_types)
    controls_parts = []
    for ct in control_types:
        spec = knowledge.get_control_spec(ct)
        if spec:
            controls_parts.append(spec)
    controls_summary = "\n\n---\n\n".join(controls_parts) if controls_parts else knowledge.get_controls_index()

    # 按需加载用到的 XML 模板
    xml_templates = [knowledge.get_template("xml/project.xml.tpl")]
    xml_templates.append(knowledge.get_template("xml/page.xml.tpl"))

    tpl_map = {
        "DFCButton": "xml/button.xml.tpl",
        "DFCSlider": "xml/slider.xml.tpl",
        "DFCPicture": "xml/picture.xml.tpl",
        "DFCTextbox": "xml/textbox.xml.tpl",
        "DFCTime": "xml/time.xml.tpl",
    }
    for ct in control_types:
        if ct in tpl_map:
            xml_templates.append(knowledge.get_template(tpl_map[ct]))

    # 页面类型包含 dialog → 加载 dialog 模板
    if any(p.type == "dialog" for p in confirmed_data.pages):
        xml_templates.append(knowledge.get_template("xml/dialog.xml.tpl"))

    templates_block = "\n\n".join(t for t in xml_templates if t)

    xml_structure = knowledge.get_xml_structure()
    if len(xml_structure) > 2000:
        xml_structure = xml_structure[:2000] + "\n..."

    system = (
        template
        .replace("{{ xml_version }}", xml_version)
        .replace("{{ width }}", width)
        .replace("{{ height }}", height)
        .replace("{{ xml_structure_summary }}", xml_structure)
        .replace("{{ controls_spec_summary }}", controls_summary)
        .replace("{{ xml_templates }}", templates_block)
    )

    config = {
        "devices": [d.model_dump() for d in confirmed_data.devices],
        "functions": [f.model_dump() for f in functions_with_joins],
        "pages": [p.model_dump() for p in confirmed_data.pages],
        "image_path": confirmed_data.image_path,
    }

    user_content = (
        f"根据以下配置生成完整的 Project.xml：\n\n"
        f"```json\n{json.dumps(config, ensure_ascii=False, indent=2)}\n```\n\n"
        f"版本：{xml_version}\n分辨率：{resolution}\n"
        f"输出纯 XML，不要 markdown 包裹。"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


# ── CHT 生成 ──────────────────────────────────────────

def build_cht_prompt(
    confirmed_data: ParsedData,
    functions_with_joins: list[FunctionItem],
    matched_protocols: list[str],
    matched_patterns: list[str],
) -> list[dict]:
    template = _read_template("cht_system.md")

    syntax_rules = knowledge.get_syntax_rules()

    block_defs = knowledge.get_essential_blocks()
    action_types = {f.action for f in functions_with_joins if f.action}
    logger.debug("[PROMPT] CHT action 类型: %s", action_types)
    sys_functions = knowledge.get_relevant_functions(action_types)
    logger.debug("[PROMPT] CHT 知识注入 — 语法=%d, 代码块=%d, 函数=%d chars",
                 len(syntax_rules), len(block_defs), len(sys_functions))

    # 加载 CHT 模板骨架 + 设备/事件参考
    cht_skeleton = knowledge.get_cht_skeleton()
    cht_devices_ref = knowledge.get_cht_devices_ref()
    cht_events_ref = knowledge.get_cht_events_ref()

    system = (
        template
        .replace("{{ syntax_rules_summary }}", syntax_rules)
        .replace("{{ block_definitions }}", block_defs if block_defs else "（无）")
        .replace("{{ system_functions }}", sys_functions if sys_functions else "（无匹配函数）")
        .replace("{{ cht_skeleton }}", cht_skeleton)
        .replace("{{ cht_devices_ref }}", cht_devices_ref)
        .replace("{{ cht_events_ref }}", cht_events_ref)
        .replace("{{ code_patterns }}", "\n\n---\n\n".join(matched_patterns) if matched_patterns else "（无匹配模式）")
        .replace("{{ matched_protocols }}", "\n\n---\n\n".join(matched_protocols) if matched_protocols else "（无匹配协议）")
    )

    config = {
        "devices": [d.model_dump() for d in confirmed_data.devices],
        "functions": [f.model_dump() for f in functions_with_joins],
        "pages": [p.model_dump() for p in confirmed_data.pages],
    }

    user_content = (
        f"根据以下配置生成完整的 .cht 文件：\n\n"
        f"```json\n{json.dumps(config, ensure_ascii=False, indent=2)}\n```\n\n"
        f"基于 CHT 骨架模板填充各 {{{{block}}}} 占位符，输出完整代码。\n"
        f"块顺序：DEFINE_DEVICE → DEFINE_COMBINE → DEFINE_CONSTANT → DEFINE_VARIABLE → "
        f"DEFINE_FUNCTION → DEFINE_TIMER → DEFINE_START → DEFINE_EVENT → DEFINE_PROGRAME\n"
        f"输出纯代码，不要 markdown 包裹。"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


# ── 上下文收集 ────────────────────────────────────────

def collect_matched_protocols(confirmed_data: ParsedData) -> list[str]:
    results = []
    for device in confirmed_data.devices:
        if device.protocol_match:
            content = knowledge._read(knowledge.PROTOCOLS_DIR / device.protocol_match)
            if content:
                results.append(content)
    return results


def collect_matched_patterns(confirmed_data: ParsedData) -> list[str]:
    """根据确认清单中的设备/功能，按需加载匹配的代码模式"""
    keywords = set()
    for func in confirmed_data.functions:
        action = func.action.upper()
        if action in ("RELAY",):
            keywords.add("继电器")
        elif action in ("COM",):
            keywords.add("串口")
        elif action in ("IR",):
            keywords.add("红外")
        elif action in ("LEVEL",):
            keywords.add("音量")
        name = func.name
        if any(kw in name for kw in ("窗帘", "帘")):
            keywords.add("窗帘")
        if any(kw in name for kw in ("场景", "模式")):
            keywords.add("场景")
        if any(kw in name for kw in ("图片", "状态图")):
            keywords.add("图片")
        if any(kw in name for kw in ("HTTP", "http", "API")):
            keywords.add("HTTP")
        if any(kw in name for kw in ("IO", "传感")):
            keywords.add("IO")

    results = []
    for kw in keywords:
        pattern = knowledge.get_pattern(kw)
        if pattern:
            results.append(pattern)
    return results
