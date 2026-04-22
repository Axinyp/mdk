"""
MDK (MKControl Development Kit) — Hermes Agent 插件
"""

import os
import re
from pathlib import Path

# 路径配置
PLUGIN_DIR = Path(__file__).parent
MDK_CORE = PLUGIN_DIR.parent.parent / "core"
PROTOCOLS_DIR = MDK_CORE / "protocols"
REFERENCES_DIR = MDK_CORE / "references"
DOCS_DIR = MDK_CORE / "docs"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk")
    except FileNotFoundError:
        return f"[文件不存在: {path}]"


def _find_protocol(name: str) -> Path | None:
    name_lower = name.lower().replace(" ", "-").replace("_", "-")
    for proto_file in PROTOCOLS_DIR.rglob("*.md"):
        if proto_file.name.startswith("_"):
            continue
        if name_lower in proto_file.stem.lower():
            return proto_file
        content = _read(proto_file)
        if name_lower in content.lower()[:200]:
            return proto_file
    return None


def register(ctx):
    """Hermes 插件注册入口"""

    # 注册 SKILL.md 文件
    for skill_name in ["mkcontrol", "protocol", "cht-ref", "xml-ref"]:
        skill_path = MDK_CORE / "skills" / skill_name / "SKILL.md"
        if skill_path.exists():
            ctx.register_skill(str(skill_path))

    @ctx.register_tool(
        name="protocol_list",
        description="列出协议库所有协议，支持关键词过滤",
        schema={
            "type": "object",
            "properties": {
                "filter": {"type": "string", "default": "", "description": "过滤关键词"}
            }
        }
    )
    def protocol_list(filter: str = "") -> dict:
        index_path = PROTOCOLS_DIR / "_index.md"
        content = _read(index_path)
        if filter:
            lines = [l for l in content.splitlines() if filter.lower() in l.lower()]
            content = "\n".join(lines) if lines else f"未找到包含 '{filter}' 的协议"
        return {"content": content}

    @ctx.register_tool(
        name="protocol_show",
        description="查看某个协议的完整详情",
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "协议名称或关键词"}
            },
            "required": ["name"]
        }
    )
    def protocol_show(name: str) -> dict:
        proto_file = _find_protocol(name)
        if proto_file:
            return {"content": _read(proto_file)}
        return {"content": f"未找到协议：{name}。请用 /protocol-add 添加。"}

    @ctx.register_tool(
        name="cht_patterns",
        description="查询 .cht 常见代码模式",
        schema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "default": "", "description": "模式关键词"}
            }
        }
    )
    def cht_patterns(pattern: str = "") -> dict:
        content = _read(REFERENCES_DIR / "core" / "code-patterns.md")
        if not pattern:
            headers = [l for l in content.splitlines() if l.startswith("## 模式")]
            return {"content": "## 代码模式总览\n\n" + "\n".join(headers)}
        sections = re.split(r"(?=^## 模式)", content, flags=re.MULTILINE)
        for section in sections:
            if pattern.lower() in section.lower():
                return {"content": section}
        return {"content": f"未找到模式：{pattern}\n\n" + content[:500]}

    @ctx.register_tool(
        name="cht_functions",
        description="查询系统函数签名和用法",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "default": "", "description": "函数名或分类"}
            }
        }
    )
    def cht_functions(query: str = "") -> dict:
        func_dir = DOCS_DIR / "系统函数库"
        if not query:
            files = sorted(func_dir.glob("*.md"))
            result = "## 系统函数分类\n\n" + "\n".join(f"- {f.stem}" for f in files)
            return {"content": result}
        for func_file in sorted(func_dir.glob("*.md")):
            content = _read(func_file)
            if query.lower() in func_file.stem.lower() or query.upper() in content:
                return {"content": content[:3000]}
        return {"content": f"未找到：{query}"}

    @ctx.register_tool(
        name="xml_controls",
        description="查询控件类型和属性规范",
        schema={
            "type": "object",
            "properties": {
                "control_type": {"type": "string", "default": "", "description": "控件类型如 DFCButton"}
            }
        }
    )
    def xml_controls(control_type: str = "") -> dict:
        content = _read(REFERENCES_DIR / "controls" / "controls-spec.md")
        if not control_type:
            return {"content": content[:2000] + "\n...（使用 xml_controls DFCButton 等查看详情）"}
        sections = re.split(r"(?=^## \d+\.)", content, flags=re.MULTILINE)
        for section in sections:
            if control_type.upper() in section.upper():
                return {"content": section}
        return {"content": f"未找到控件：{control_type}"}

    @ctx.register_tool(
        name="xml_structure",
        description="查询 Project.xml 整体结构规范",
        schema={
            "type": "object",
            "properties": {
                "topic": {"type": "string", "default": "", "description": "查询主题"}
            }
        }
    )
    def xml_structure(topic: str = "") -> dict:
        content = _read(REFERENCES_DIR / "controls" / "xml-structure.md")
        if not topic:
            return {"content": content}
        sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
        for section in sections:
            if topic.lower() in section.lower():
                return {"content": section}
        return {"content": content[:2000]}
