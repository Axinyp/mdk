import re
from pathlib import Path

from ..config import settings

CORE_DIR = settings.core_dir
PROTOCOLS_DIR = CORE_DIR / "protocols"
REFERENCES_DIR = CORE_DIR / "references"
DOCS_DIR = CORE_DIR / "docs"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk")
    except FileNotFoundError:
        return ""


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


def search_functions(query: str = "") -> str:
    func_dir = DOCS_DIR / "系统函数库"
    if not func_dir.exists():
        return "函数库目录不存在"

    if not query:
        return "\n".join(f"- **{f.stem}**" for f in sorted(func_dir.glob("*.md")))

    query_upper = query.upper()
    for func_file in func_dir.glob("*.md"):
        content = _read(func_file)
        if query.lower() in func_file.stem.lower() or query_upper in content:
            if query_upper in content:
                lines = content.splitlines()
                result_lines = []
                capture = False
                for line in lines:
                    if query_upper in line:
                        capture = True
                    if capture:
                        result_lines.append(line)
                        if len(result_lines) > 40:
                            break
                return "\n".join(result_lines) if result_lines else content[:3000]
            return content

    return f"未找到: {query}"


def get_syntax_rules() -> str:
    return _read(REFERENCES_DIR / "core" / "syntax-rules.md")


def get_patterns(keyword: str = "") -> str:
    content = _read(REFERENCES_DIR / "core" / "code-patterns.md")
    if not keyword:
        lines = content.splitlines()
        headers = [l for l in lines if l.startswith("## 模式")]
        return "## 代码模式总览\n\n" + "\n".join(headers)

    sections = re.split(r"(?=^## 模式)", content, flags=re.MULTILINE)
    for section in sections:
        if keyword.lower() in section.lower():
            return section
    return f"未找到包含 '{keyword}' 的模式"


def get_controls_spec(control_type: str = "") -> str:
    content = _read(REFERENCES_DIR / "controls" / "controls-spec.md")
    if not control_type:
        lines = content.splitlines()
        overview = [l for l in lines if "|" in l][:20]
        return "\n".join(overview)

    sections = re.split(r"(?=^## \d+\.)", content, flags=re.MULTILINE)
    for section in sections:
        if control_type.upper() in section.upper():
            return section
    return f"未找到控件: {control_type}"


def get_xml_structure(topic: str = "") -> str:
    content = _read(REFERENCES_DIR / "controls" / "xml-structure.md")
    if not topic:
        return content

    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
    for section in sections:
        if topic.lower() in section.lower():
            return section
    return content
