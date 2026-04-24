"""
MDK (MKControl Development Kit) — Hermes Agent 插件 v2
适配新的按需加载知识库结构
"""

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

    # 注册唯一 SKILL.md
    skill_path = MDK_CORE / "skills" / "mkcontrol" / "SKILL.md"
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
        content = _read(PROTOCOLS_DIR / "_index.md")
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
        patterns_dir = REFERENCES_DIR / "core" / "patterns"
        if not pattern:
            return {"content": _read(patterns_dir / "_index.md")}
        # 在索引中找匹配的文件
        index = _read(patterns_dir / "_index.md")
        for line in index.splitlines():
            if pattern.lower() in line.lower() and "`" in line:
                filename = re.search(r'`(\S+\.md)`', line)
                if filename:
                    content = _read(patterns_dir / filename.group(1))
                    if content:
                        return {"content": content}
        return {"content": f"未找到模式：{pattern}\n\n" + index}

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
        func_dir = DOCS_DIR / "系统函数库" / "常用"
        func_dir_hw = DOCS_DIR / "系统函数库" / "专用硬件"
        all_dirs = [func_dir, func_dir_hw]
        if not query:
            result = "## 系统函数分类\n\n### 常用\n"
            for f in sorted(func_dir.glob("*.md")):
                result += f"- {f.stem}\n"
            result += "\n### 专用硬件\n"
            for f in sorted(func_dir_hw.glob("*.md")):
                result += f"- {f.stem}\n"
            return {"content": result}
        for d in all_dirs:
            for func_file in sorted(d.glob("*.md")):
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
        widgets_dir = REFERENCES_DIR / "controls" / "widgets"
        if not control_type:
            return {"content": _read(widgets_dir / "_index.md")}
        # 查找匹配的控件文件
        for f in widgets_dir.glob("*.md"):
            if f.name == "_index.md":
                continue
            if control_type.lower() in f.stem.lower():
                return {"content": _read(f)}
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
