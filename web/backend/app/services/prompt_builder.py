import json
from pathlib import Path

from . import knowledge
from ..schemas.gen import FunctionItem, ParsedData

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _read_template(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def build_parse_prompt(description: str, protocols_index: str) -> list[dict]:
    template = _read_template("parse_system.md")
    system = template.replace("{{ protocols_index }}", protocols_index)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": description},
    ]


def build_xml_prompt(
    confirmed_data: ParsedData,
    functions_with_joins: list[FunctionItem],
    resolution: str = "2560x1600",
    xml_version: str = "4.1.9",
) -> list[dict]:
    template = _read_template("xml_system.md")
    width, height = resolution.split("x")

    xml_structure = knowledge.get_xml_structure()
    if len(xml_structure) > 2000:
        xml_structure = xml_structure[:2000] + "\n..."

    control_types = {f.control_type for f in functions_with_joins}
    controls_parts = []
    for ct in control_types:
        spec = knowledge.get_controls_spec(ct)
        if spec and len(spec) > 800:
            spec = spec[:800] + "\n..."
        controls_parts.append(spec)
    controls_summary = "\n\n".join(controls_parts)

    system = (
        template
        .replace("{{ xml_version }}", xml_version)
        .replace("{{ width }}", width)
        .replace("{{ height }}", height)
        .replace("{{ xml_structure_summary }}", xml_structure)
        .replace("{{ controls_spec_summary }}", controls_summary)
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


def build_cht_prompt(
    confirmed_data: ParsedData,
    functions_with_joins: list[FunctionItem],
    matched_protocols: list[str],
    matched_patterns: list[str],
) -> list[dict]:
    template = _read_template("cht_system.md")

    syntax_rules = knowledge._read(knowledge.REFERENCES_DIR / "core" / "syntax-rules.md")
    if len(syntax_rules) > 1500:
        syntax_rules = syntax_rules[:1500] + "\n..."

    system = (
        template
        .replace("{{ syntax_rules_summary }}", syntax_rules)
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
        f"块顺序：DEFINE_DEVICE → DEFINE_VARIABLE → DEFINE_FUNCTION → DEFINE_START → DEFINE_EVENT\n"
        f"输出纯代码，不要 markdown 包裹。"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


def collect_matched_protocols(confirmed_data: ParsedData) -> list[str]:
    results = []
    for device in confirmed_data.devices:
        if device.protocol_match:
            content = knowledge._read(knowledge.PROTOCOLS_DIR / device.protocol_match)
            if content:
                results.append(content)
    return results


def collect_matched_patterns(confirmed_data: ParsedData) -> list[str]:
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

    results = []
    for kw in keywords:
        pattern = knowledge.get_patterns(kw)
        if pattern and "未找到" not in pattern:
            results.append(pattern)
    return results
