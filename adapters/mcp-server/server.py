#!/usr/bin/env python3
"""
MDK MCP Server v2 — MKControl Development Kit
适配新的按需加载知识库结构

启动: python server.py
协议: MCP over stdio
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
except ImportError:
    print("缺少 mcp 库，请运行: pip install mcp")
    sys.exit(1)

# 路径配置
SERVER_DIR = Path(__file__).parent
MDK_ROOT = SERVER_DIR.parent.parent
CORE_DIR = MDK_ROOT / "core"
PROTOCOLS_DIR = CORE_DIR / "protocols"
REFERENCES_DIR = CORE_DIR / "references"
WIDGETS_DIR = REFERENCES_DIR / "controls" / "widgets"
PATTERNS_DIR = REFERENCES_DIR / "core" / "patterns"
DOCS_DIR = CORE_DIR / "docs"
SCRIPTS_DIR = CORE_DIR / "scripts"
TEMPLATES_DIR = CORE_DIR / "templates"


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return path.read_text(encoding='gbk')
    except FileNotFoundError:
        return f"[文件不存在: {path}]"


def find_protocol_file(name: str) -> Path | None:
    name_lower = name.lower().replace(' ', '-').replace('_', '-')
    for proto_file in PROTOCOLS_DIR.rglob("*.md"):
        if proto_file.name.startswith('_'):
            continue
        if name_lower in proto_file.stem.lower() or proto_file.stem.lower() in name_lower:
            return proto_file
        content = read_file(proto_file)
        if name_lower in content.lower()[:200]:
            return proto_file
    return None


def find_widget_file(control_type: str) -> Path | None:
    for f in WIDGETS_DIR.glob("*.md"):
        if f.name == "_index.md":
            continue
        if control_type.lower() in f.stem.lower():
            return f
    return None


def find_pattern_file(keyword: str) -> Path | None:
    index = read_file(PATTERNS_DIR / "_index.md")
    for line in index.splitlines():
        if keyword.lower() in line.lower() and '`' in line:
            m = re.search(r'`(\S+\.md)`', line)
            if m:
                p = PATTERNS_DIR / m.group(1)
                if p.exists():
                    return p
    return None


# ============================================================
# MCP Server
# ============================================================

app = Server("mdk-mcp-server")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="mkcontrol_generate",
            description="解析中控系统需求，输出确认清单（第1步）",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "自然语言描述控制需求"}
                },
                "required": ["description"]
            }
        ),
        types.Tool(
            name="mkcontrol_confirm",
            description="用户确认清单后，生成 Project.xml 和 .cht（第2步）",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmed_plan": {"type": "string", "description": "确认的配置（JSON）"},
                    "image_base_path": {"type": "string", "description": "图片目录（可选）", "default": ""}
                },
                "required": ["confirmed_plan"]
            }
        ),
        types.Tool(
            name="validate_cht",
            description="校验 .cht 文件语法（10 项检查）",
            inputSchema={
                "type": "object",
                "properties": {"cht_content": {"type": "string", "description": ".cht 文件内容"}},
                "required": ["cht_content"]
            }
        ),
        types.Tool(
            name="cross_validate",
            description="交叉校验 XML ↔ .cht JoinNumber 一致性",
            inputSchema={
                "type": "object",
                "properties": {
                    "xml_content": {"type": "string", "description": "Project.xml 内容"},
                    "cht_content": {"type": "string", "description": ".cht 内容"}
                },
                "required": ["xml_content", "cht_content"]
            }
        ),
        types.Tool(
            name="protocol_list",
            description="列出协议库所有协议，支持过滤",
            inputSchema={
                "type": "object",
                "properties": {"filter": {"type": "string", "default": ""}}
            }
        ),
        types.Tool(
            name="protocol_show",
            description="查看协议详情",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            }
        ),
        types.Tool(
            name="protocol_add",
            description="添加新设备协议",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["projector","curtain","ac","audio","display","camera","matrix","screen","lighting","custom"]},
                    "brand_model": {"type": "string"},
                    "comm_type": {"type": "string", "enum": ["RS232","RS485","TCP","UDP","IR"]},
                    "baud_rate": {"type": "integer", "default": 9600},
                    "port": {"type": "integer"},
                    "commands": {"type": "object", "additionalProperties": {"type": "string"}},
                    "notes": {"type": "string", "default": ""}
                },
                "required": ["category", "brand_model", "comm_type", "commands"]
            }
        ),
        types.Tool(
            name="protocol_update",
            description="修正已有协议",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "update_description": {"type": "string"}
                },
                "required": ["name", "update_description"]
            }
        ),
        types.Tool(
            name="protocol_delete",
            description="删除协议",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "confirmed": {"type": "boolean", "default": False}
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="protocol_import",
            description="从 .cht 反向提取协议",
            inputSchema={
                "type": "object",
                "properties": {"cht_content": {"type": "string"}},
                "required": ["cht_content"]
            }
        ),
        types.Tool(
            name="cht_devices",
            description="查询设备类型声明格式",
            inputSchema={
                "type": "object",
                "properties": {"device_type": {"type": "string", "default": ""}}
            }
        ),
        types.Tool(
            name="cht_functions",
            description="查询系统函数",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string", "default": ""}}
            }
        ),
        types.Tool(
            name="cht_patterns",
            description="查询代码模式",
            inputSchema={
                "type": "object",
                "properties": {"pattern": {"type": "string", "default": ""}}
            }
        ),
        types.Tool(
            name="xml_controls",
            description="查询控件属性规范",
            inputSchema={
                "type": "object",
                "properties": {"control_type": {"type": "string", "default": ""}}
            }
        ),
        types.Tool(
            name="xml_structure",
            description="查询 XML 结构规范",
            inputSchema={
                "type": "object",
                "properties": {"topic": {"type": "string", "default": ""}}
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        result = await dispatch_tool(name, arguments)
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] {name}: {e}")]


async def dispatch_tool(name: str, args: dict) -> str:
    handlers = {
        "mkcontrol_generate": tool_mkcontrol_generate,
        "mkcontrol_confirm": tool_mkcontrol_confirm,
        "validate_cht": tool_validate_cht,
        "cross_validate": tool_cross_validate,
        "protocol_list": tool_protocol_list,
        "protocol_show": tool_protocol_show,
        "protocol_add": tool_protocol_add,
        "protocol_update": tool_protocol_update,
        "protocol_delete": tool_protocol_delete,
        "protocol_import": tool_protocol_import,
        "cht_devices": tool_cht_devices,
        "cht_functions": tool_cht_functions,
        "cht_patterns": tool_cht_patterns,
        "xml_controls": tool_xml_controls,
        "xml_structure": tool_xml_structure,
    }
    handler = handlers.get(name)
    if not handler:
        return f"[ERROR] 未知工具: {name}"
    return await handler(args)


# ============================================================
# 工具实现
# ============================================================

async def tool_protocol_list(args: dict) -> str:
    query = args.get("filter", "").strip()
    content = read_file(PROTOCOLS_DIR / "_index.md")
    if query:
        lines = [l for l in content.splitlines() if query.lower() in l.lower()]
        return "\n".join(lines) if lines else f"未找到包含 '{query}' 的协议"
    return content


async def tool_protocol_show(args: dict) -> str:
    name = args.get("name", "").strip()
    proto_file = find_protocol_file(name)
    if proto_file:
        return read_file(proto_file)
    return f"未找到协议：{name}。可用 protocol_add 添加。"


async def tool_protocol_add(args: dict) -> str:
    category = args.get("category", "custom")
    brand_model = args.get("brand_model", "未知设备")
    comm_type = args.get("comm_type", "RS232")
    baud_rate = args.get("baud_rate", 9600)
    port = args.get("port")
    commands = args.get("commands", {})
    notes = args.get("notes", "")

    filename = re.sub(r'[^\w\-]', '-', brand_model.lower().replace(' ', '-'))
    filename = re.sub(r'-+', '-', filename).strip('-') + ".md"
    file_path = PROTOCOLS_DIR / category / filename

    cmd_table = "| 功能 | 指令 | 说明 |\n|------|------|------|\n"
    for func, cmd in commands.items():
        cmd_table += f"| {func} | `{cmd}` | |\n"

    from datetime import date
    today = date.today().strftime("%Y-%m-%d")

    content = f"""# {category.title()} - {brand_model}

## 基本信息
- 设备类型：{category}
- 通信方式：{comm_type}
- 波特率：{baud_rate}
{f'- TCP端口：{port}' if port else ''}

## 指令表
{cmd_table}

## 适用型号
- {brand_model}

## 更新记录
- {today}: MCP Server 添加{f'，{notes}' if notes else ''}
"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')

    # 更新索引
    index_path = PROTOCOLS_DIR / "_index.md"
    index_content = read_file(index_path)
    new_entry = f"- `{category}/{filename}` — {brand_model} — {comm_type}"
    index_content += f"\n{new_entry}\n"
    index_path.write_text(index_content, encoding='utf-8')

    return f"✅ 协议已添加：{file_path}"


async def tool_protocol_update(args: dict) -> str:
    name = args.get("name", "")
    update_desc = args.get("update_description", "")
    proto_file = find_protocol_file(name)
    if not proto_file:
        return f"未找到协议：{name}"
    from datetime import date
    content = read_file(proto_file)
    content += f"\n- {date.today()}: {update_desc}"
    proto_file.write_text(content, encoding='utf-8')
    return f"✅ 已更新 {proto_file.name}"


async def tool_protocol_delete(args: dict) -> str:
    name = args.get("name", "")
    confirmed = args.get("confirmed", False)
    proto_file = find_protocol_file(name)
    if not proto_file:
        return f"未找到协议：{name}"
    if not confirmed:
        return f"⚠️ 确认删除 {proto_file.name}？设置 confirmed=true 确认"
    proto_file.unlink()
    index_path = PROTOCOLS_DIR / "_index.md"
    content = read_file(index_path)
    lines = [l for l in content.splitlines() if proto_file.name not in l]
    index_path.write_text("\n".join(lines), encoding='utf-8')
    return f"✅ 已删除：{proto_file}"


async def tool_protocol_import(args: dict) -> str:
    cht_content = args.get("cht_content", "")
    send_coms = re.findall(r'SEND_COM\((\w+),\s*(\d+),\s*"([^"]+)"\)', cht_content)
    tcp_sends = re.findall(r'SEND_TCP\([^,]+,\s*(\d+),\s*"([^"]+)"\)', cht_content)
    ir_sends = re.findall(r'SEND_IRCODE\((\w+),\s*(\d+),\s*IRCODE<"([^"]+)">\)', cht_content)

    result = "## 从 .cht 提取的协议\n\n"
    if send_coms:
        result += "### 串口\n"
        by_dev = {}
        for dev, ch, cmd in send_coms:
            by_dev.setdefault(f"{dev}_ch{ch}", []).append(cmd)
        for key, cmds in by_dev.items():
            result += f"**{key}**: " + ", ".join(f"`{c}`" for c in cmds) + "\n"
    if tcp_sends:
        result += "### TCP\n"
        for port, cmd in tcp_sends:
            result += f"- port {port}: `{cmd}`\n"
    if ir_sends:
        result += "### 红外\n"
        for dev, ch, code in ir_sends:
            result += f"- {dev} ch{ch}: `{code}`\n"
    if not (send_coms or tcp_sends or ir_sends):
        result += "未提取到协议指令。\n"
    return result


async def tool_cht_devices(args: dict) -> str:
    device_type = args.get("device_type", "").upper().strip()
    content = read_file(REFERENCES_DIR / "core" / "syntax-rules.md")
    if not device_type:
        return content
    lines = content.splitlines()
    result = []
    capture = False
    for line in lines:
        if device_type in line:
            capture = True
        if capture:
            result.append(line)
            if len(result) > 20:
                break
    return "\n".join(result) if result else f"未找到：{device_type}"


async def tool_cht_functions(args: dict) -> str:
    query = args.get("query", "").strip()
    func_dirs = [DOCS_DIR / "系统函数库" / "常用", DOCS_DIR / "系统函数库" / "专用硬件"]
    if not query:
        result = "## 系统函数分类\n\n### 常用\n"
        for f in sorted(func_dirs[0].glob("*.md")):
            result += f"- {f.stem}\n"
        result += "\n### 专用硬件\n"
        for f in sorted(func_dirs[1].glob("*.md")):
            result += f"- {f.stem}\n"
        return result
    for d in func_dirs:
        for func_file in sorted(d.glob("*.md")):
            content = read_file(func_file)
            if query.lower() in func_file.stem.lower() or query.upper() in content:
                return content[:3000]
    return f"未找到：{query}"


async def tool_cht_patterns(args: dict) -> str:
    pattern = args.get("pattern", "").strip()
    if not pattern:
        return read_file(PATTERNS_DIR / "_index.md")
    pf = find_pattern_file(pattern)
    if pf:
        return read_file(pf)
    return read_file(PATTERNS_DIR / "_index.md")


async def tool_xml_controls(args: dict) -> str:
    control_type = args.get("control_type", "").strip()
    if not control_type:
        return read_file(WIDGETS_DIR / "_index.md")
    wf = find_widget_file(control_type)
    if wf:
        return read_file(wf)
    return f"未找到控件：{control_type}"


async def tool_xml_structure(args: dict) -> str:
    topic = args.get("topic", "").strip()
    content = read_file(REFERENCES_DIR / "controls" / "xml-structure.md")
    if not topic:
        return content
    sections = re.split(r'(?=^## )', content, flags=re.MULTILINE)
    for section in sections:
        if topic.lower() in section.lower():
            return section
    return content


async def tool_mkcontrol_generate(args: dict) -> str:
    desc = args.get("description", "")
    hints = []
    kw_map = {
        "继电器/灯光": ['TS-9101', 'RELAY', '继电器', '灯光'],
        "窗帘 RS485": ['窗帘', 'curtain', 'RS485'],
        "空调红外": ['空调', 'AC', '红外', 'IR'],
        "投影仪串口": ['投影', 'projector', '串口', 'COM'],
        "音量滑条": ['音量', '滑条', 'slider', 'DSP'],
        "场景模式": ['场景', '模式', 'MutualLock'],
    }
    for label, kws in kw_map.items():
        if any(kw in desc for kw in kws):
            hints.append(f"- 检测到：{label}")
    hints_str = "\n".join(hints) if hints else "（需要更多信息）"
    return f"## 需求解析\n\n{desc}\n\n### 初步识别\n{hints_str}\n\n请补充设备型号、板卡号后调用 mkcontrol_confirm。"


async def tool_mkcontrol_confirm(args: dict) -> str:
    return "完整生成需要 LLM 上下文推理，建议使用 Claude Code 的 /mk-control 命令。"


async def tool_validate_cht(args: dict) -> str:
    import subprocess, tempfile, os
    cht_content = args.get("cht_content", "")
    script = SCRIPTS_DIR / "validate.py"
    if not script.exists():
        return f"[ERROR] 脚本不存在: {script}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cht', encoding='utf-8', delete=False) as f:
        f.write(cht_content)
        tmp = f.name
    try:
        r = subprocess.run(["python", str(script), tmp], capture_output=True, text=True, timeout=30)
        return r.stdout or r.stderr or "（无输出）"
    except subprocess.TimeoutExpired:
        return "[ERROR] 校验超时"
    finally:
        os.unlink(tmp)


async def tool_cross_validate(args: dict) -> str:
    import subprocess, tempfile, os
    xml_content = args.get("xml_content", "")
    cht_content = args.get("cht_content", "")
    script = SCRIPTS_DIR / "cross_validate.py"
    if not script.exists():
        return f"[ERROR] 脚本不存在: {script}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', encoding='utf-8', delete=False) as fx:
        fx.write(xml_content)
        xml_tmp = fx.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cht', encoding='utf-8', delete=False) as fc:
        fc.write(cht_content)
        cht_tmp = fc.name
    try:
        r = subprocess.run(["python", str(script), xml_tmp, cht_tmp], capture_output=True, text=True, timeout=30)
        return r.stdout or r.stderr or "（无输出）"
    except subprocess.TimeoutExpired:
        return "[ERROR] 校验超时"
    finally:
        os.unlink(xml_tmp)
        os.unlink(cht_tmp)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
