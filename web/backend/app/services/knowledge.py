import logging
import re
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)

CORE_DIR = settings.core_dir
PROTOCOLS_DIR = CORE_DIR / "protocols"
REFERENCES_DIR = CORE_DIR / "references"
DOCS_DIR = CORE_DIR / "docs"
TEMPLATES_DIR = CORE_DIR / "templates"
WIDGETS_DIR = REFERENCES_DIR / "controls" / "widgets"
PATTERNS_DIR = REFERENCES_DIR / "core" / "patterns"
BLOCKS_DIR = DOCS_DIR / "代码组织"
FUNC_COMMON_DIR = DOCS_DIR / "系统函数库" / "常用"
FUNC_HARDWARE_DIR = DOCS_DIR / "系统函数库" / "专用硬件"

ACTION_TO_FUNC: dict[str, str] = {
    "RELAY": "继电器控制函数",
    "COM": "串口控制函数",
    "IR": "红外控制函数",
    "LEVEL": "DSP音量控制函数",
    "TCP": "网络控制相关函数",
    "UDP": "网络控制相关函数",
    "IO": "IO控制函数",
    "DMX": "DMX512控制函数",
}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk")
    except FileNotFoundError:
        return ""


# ── 协议 ──────────────────────────────────────────────

def get_protocols_index() -> str:
    return _read(PROTOCOLS_DIR / "_index.md")


def list_protocol_files() -> list[dict]:
    results = []
    for f in PROTOCOLS_DIR.rglob("*.md"):
        if f.name.startswith("_"):
            continue
        category = f.parent.name
        content = _read(f)
        first_line = content.splitlines()[0] if content else ""
        brand = first_line.lstrip("# ").strip() if first_line.startswith("#") else f.stem
        results.append({
            "category": category,
            "filename": f"{category}/{f.name}",
            "brand_model": brand,
            "content": content,
        })
    return results


# ── 系统函数 ──────────────────────────────────────────

def search_functions(query: str = "") -> str:
    func_dirs = [
        DOCS_DIR / "系统函数库" / "常用",
        DOCS_DIR / "系统函数库" / "专用硬件",
    ]
    if not any(d.exists() for d in func_dirs):
        return "函数库目录不存在"

    if not query:
        result = "## 系统函数分类\n\n### 常用\n"
        if func_dirs[0].exists():
            for f in sorted(func_dirs[0].glob("*.md")):
                result += f"- {f.stem}\n"
        result += "\n### 专用硬件\n"
        if func_dirs[1].exists():
            for f in sorted(func_dirs[1].glob("*.md")):
                result += f"- {f.stem}\n"
        return result

    query_upper = query.upper()
    for d in func_dirs:
        if not d.exists():
            continue
        for func_file in sorted(d.glob("*.md")):
            content = _read(func_file)
            if query.lower() in func_file.stem.lower() or query_upper in content:
                return content[:3000]
    return f"未找到: {query}"


# ── 语法规则 ──────────────────────────────────────────

def get_syntax_rules() -> str:
    return _read(REFERENCES_DIR / "core" / "syntax-rules.md")


# ── 代码模式（按需加载拆分文件）────────────────────────

def get_patterns_index() -> str:
    return _read(PATTERNS_DIR / "_index.md")


def get_pattern(keyword: str) -> str:
    """按关键词在 patterns/_index.md 中匹配，返回对应拆分文件内容"""
    index = _read(PATTERNS_DIR / "_index.md")
    for line in index.splitlines():
        if keyword.lower() in line.lower() and "`" in line:
            m = re.search(r"`(\S+\.md)`", line)
            if m:
                p = PATTERNS_DIR / m.group(1)
                content = _read(p)
                if content:
                    return content
    return ""


# ── 控件规范（按需加载拆分文件）────────────────────────

def get_controls_index() -> str:
    return _read(WIDGETS_DIR / "_index.md")


def get_control_spec(control_type: str) -> str:
    """按控件类型查找 widgets/<type>.md"""
    for f in WIDGETS_DIR.iterdir():
        if f.name == "_index.md" or not f.suffix == ".md":
            continue
        if control_type.lower() in f.stem.lower():
            return _read(f)
    return ""


# ── XML 结构 ──────────────────────────────────────────

def get_xml_structure(topic: str = "") -> str:
    content = _read(REFERENCES_DIR / "controls" / "xml-structure.md")
    if not topic:
        return content
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
    for section in sections:
        if topic.lower() in section.lower():
            return section
    return content


# ── 模板系统 ──────────────────────────────────────────

def get_templates_index() -> str:
    return _read(TEMPLATES_DIR / "_index.md")


def get_template(name: str) -> str:
    """读取模板文件，如 'xml/project.xml.tpl' 或 'cht/simple-program.cht.tpl'"""
    return _read(TEMPLATES_DIR / name)


def get_cht_skeleton() -> str:
    return _read(TEMPLATES_DIR / "cht" / "simple-program.cht.tpl")


def get_cht_devices_ref() -> str:
    return _read(TEMPLATES_DIR / "cht" / "devices.md")


def get_cht_events_ref() -> str:
    return _read(TEMPLATES_DIR / "cht" / "events.md")


# ── 代码块定义（docs/代码组织）────────────────────────

def get_block_definition(block_name: str, max_chars: int = 1500) -> str:
    path = BLOCKS_DIR / f"{block_name}.md"
    content = _read(path)
    if content and len(content) > max_chars:
        content = content[:max_chars] + "\n..."
    return content


def get_essential_blocks() -> str:
    parts = []
    for name in ["DEFINE_DEVICE", "DEFINE_EVENT", "DEFINE_START"]:
        content = get_block_definition(name)
        if content:
            parts.append(content)
            logger.debug("[KNOWLEDGE] 加载代码块: %s (%d chars)", name, len(content))
        else:
            logger.warning("[KNOWLEDGE] 代码块缺失: %s.md", name)
    return "\n\n---\n\n".join(parts)


# ── 系统函数（docs/系统函数库）────────────────────────

def get_relevant_functions(action_types: set[str]) -> str:
    func_names = {"触屏控制函数"}
    for action in action_types:
        mapped = ACTION_TO_FUNC.get(action.upper())
        if mapped:
            func_names.add(mapped)
        else:
            logger.warning("[KNOWLEDGE] 未知 action '%s', 无法映射到系统函数", action)

    logger.debug("[KNOWLEDGE] 需加载系统函数: %s", func_names)
    parts = []
    for name in sorted(func_names):
        path = FUNC_COMMON_DIR / f"{name}.md"
        content = _read(path)
        if not content:
            path = FUNC_HARDWARE_DIR / f"{name}.md"
            content = _read(path)
        if content:
            if len(content) > 2000:
                logger.debug("[KNOWLEDGE] 函数 '%s' 截断: %d → 2000 chars", name, len(content))
                content = content[:2000] + "\n..."
            parts.append(content)
            logger.debug("[KNOWLEDGE] 加载函数: %s (%d chars)", name, len(content))
        else:
            logger.warning("[KNOWLEDGE] 函数文件缺失: %s.md", name)
    return "\n\n---\n\n".join(parts)
