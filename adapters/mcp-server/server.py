#!/usr/bin/env python3
"""
MDK MCP Server — MKControl Development Kit
提供 15 个 MCP tools，支持网页和任意 MCP client 调用。

启动: python server.py [--port 8765] [--host 0.0.0.0]
协议: MCP over HTTP/SSE (Model Context Protocol)
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

# MCP Server SDK
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
DOCS_DIR = CORE_DIR / "docs"
SCRIPTS_DIR = CORE_DIR / "scripts"


# ============================================================
# 辅助函数
# ============================================================

def read_file(path: Path) -> str:
    """读取文件内容，支持 UTF-8 和 GBK 编码"""
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return path.read_text(encoding='gbk')
    except FileNotFoundError:
        return f"[文件不存在: {path}]"


def search_protocols(query: str = "") -> list[dict]:
    """在协议索引中搜索"""
    index_path = PROTOCOLS_DIR / "_index.md"
    if not index_path.exists():
        return []

    content = read_file(index_path)
    results = []
    for line in content.splitlines():
        if line.startswith('- ') or '|' in line:
            if not query or query.lower() in line.lower():
                results.append({'line': line.strip()})
    return results


def find_protocol_file(name: str) -> Path | None:
    """模糊匹配协议文件"""
    name_lower = name.lower().replace(' ', '-').replace('_', '-')

    # 遍历所有子目录
    for proto_file in PROTOCOLS_DIR.rglob("*.md"):
        if proto_file.name.startswith('_'):
            continue
        file_stem = proto_file.stem.lower()
        if name_lower in file_stem or file_stem in name_lower:
            return proto_file

        # 读取文件内容匹配品牌名
        content = read_file(proto_file)
        first_line = content.splitlines()[0] if content else ""
        if name_lower in first_line.lower():
            return proto_file

    return None


# ============================================================
# MCP Server 工具实现
# ============================================================

app = Server("mdk-mcp-server")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # 生成工具
        types.Tool(
            name="mkcontrol_generate",
            description="解析中控系统需求，提取设备、功能、JoinNumber，输出人可读的确认清单（第1步）",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "用自然语言描述控制需求（设备、功能、连接号等）"
                    }
                },
                "required": ["description"]
            }
        ),
        types.Tool(
            name="mkcontrol_confirm",
            description="用户确认清单后，生成 Project.xml 和 .cht 文件（第2步，需先调用 mkcontrol_generate）",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmed_plan": {
                        "type": "string",
                        "description": "经用户确认的设备清单和功能配置（JSON 或文本）"
                    },
                    "image_base_path": {
                        "type": "string",
                        "description": "图片资源目录路径（可选，不填则使用纯色按钮）",
                        "default": ""
                    }
                },
                "required": ["confirmed_plan"]
            }
        ),
        types.Tool(
            name="validate_cht",
            description="校验 .cht 文件的语法规范（块顺序、变量初始化、函数调用等 14 项）",
            inputSchema={
                "type": "object",
                "properties": {
                    "cht_content": {
                        "type": "string",
                        "description": ".cht 文件内容"
                    }
                },
                "required": ["cht_content"]
            }
        ),
        types.Tool(
            name="cross_validate",
            description="交叉校验 Project.xml 和 .cht 文件的 JoinNumber 一致性",
            inputSchema={
                "type": "object",
                "properties": {
                    "xml_content": {
                        "type": "string",
                        "description": "Project.xml 文件内容"
                    },
                    "cht_content": {
                        "type": "string",
                        "description": ".cht 文件内容"
                    }
                },
                "required": ["xml_content", "cht_content"]
            }
        ),
        # 协议管理
        types.Tool(
            name="protocol_list",
            description="列出协议库中的所有协议，支持按分类或关键词过滤",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "过滤关键词（设备类型、品牌、通信方式等），留空返回全部",
                        "default": ""
                    }
                }
            }
        ),
        types.Tool(
            name="protocol_show",
            description="查看某个协议的完整详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "协议名称或关键词（如：格力空调、epson、visca）"
                    }
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="protocol_add",
            description="添加新设备协议到库",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "设备分类",
                        "enum": ["projector", "curtain", "ac", "audio", "display", "camera", "matrix", "screen", "lighting", "custom"]
                    },
                    "brand_model": {
                        "type": "string",
                        "description": "品牌和型号（如：爱普生 EB-X51）"
                    },
                    "comm_type": {
                        "type": "string",
                        "description": "通信方式",
                        "enum": ["RS232", "RS485", "TCP", "UDP", "IR"]
                    },
                    "baud_rate": {
                        "type": "integer",
                        "description": "波特率（串口时填写）",
                        "default": 9600
                    },
                    "port": {
                        "type": "integer",
                        "description": "TCP/UDP 端口（网络时填写）"
                    },
                    "commands": {
                        "type": "object",
                        "description": "指令表，格式：{\"开机\": \"指令\", \"关机\": \"指令\"}",
                        "additionalProperties": {"type": "string"}
                    },
                    "notes": {
                        "type": "string",
                        "description": "备注信息（可选）",
                        "default": ""
                    }
                },
                "required": ["category", "brand_model", "comm_type", "commands"]
            }
        ),
        types.Tool(
            name="protocol_update",
            description="修正已有协议的指令或参数",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "协议名称或关键词"},
                    "update_description": {"type": "string", "description": "描述修改内容（如：关机指令改为 0xXXXX）"}
                },
                "required": ["name", "update_description"]
            }
        ),
        types.Tool(
            name="protocol_delete",
            description="删除指定协议",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "协议名称"},
                    "confirmed": {"type": "boolean", "description": "是否已确认删除", "default": False}
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="protocol_import",
            description="从已有 .cht 文件内容反向提取设备协议",
            inputSchema={
                "type": "object",
                "properties": {
                    "cht_content": {"type": "string", "description": ".cht 文件内容"}
                },
                "required": ["cht_content"]
            }
        ),
        # 参考查询
        types.Tool(
            name="cht_devices",
            description="查询 .cht 语言的设备类型声明格式",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_type": {
                        "type": "string",
                        "description": "设备类型（如：RELAY、COM、IR、TP），留空返回总览",
                        "default": ""
                    }
                }
            }
        ),
        types.Tool(
            name="cht_functions",
            description="查询 .cht 语言的系统函数签名和用法",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "函数名或分类（如：SEND_COM、串口控制、触屏控制），留空返回分类总览",
                        "default": ""
                    }
                }
            }
        ),
        types.Tool(
            name="cht_patterns",
            description="查询 .cht 常见代码模式（场景联动、窗帘控制、音量控制等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "模式关键词（如：场景联动、窗帘、音量、红外），留空返回总览",
                        "default": ""
                    }
                }
            }
        ),
        types.Tool(
            name="xml_controls",
            description="查询 Project.xml 控件类型和属性规范",
            inputSchema={
                "type": "object",
                "properties": {
                    "control_type": {
                        "type": "string",
                        "description": "控件类型（如：DFCButton、DFCSlider），留空返回总览",
                        "default": ""
                    }
                }
            }
        ),
        types.Tool(
            name="xml_structure",
            description="查询 Project.xml 整体结构规范（版本、颜色格式、路径规范等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "查询主题（如：颜色、路径、DFCForm），留空返回整体结构",
                        "default": ""
                    }
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """工具调用分发"""
    try:
        result = await dispatch_tool(name, arguments)
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] {name}: {e}")]


async def dispatch_tool(name: str, args: dict) -> str:
    if name == "mkcontrol_generate":
        return await tool_mkcontrol_generate(args)
    elif name == "mkcontrol_confirm":
        return await tool_mkcontrol_confirm(args)
    elif name == "validate_cht":
        return await tool_validate_cht(args)
    elif name == "cross_validate":
        return await tool_cross_validate(args)
    elif name == "protocol_list":
        return await tool_protocol_list(args)
    elif name == "protocol_show":
        return await tool_protocol_show(args)
    elif name == "protocol_add":
        return await tool_protocol_add(args)
    elif name == "protocol_update":
        return await tool_protocol_update(args)
    elif name == "protocol_delete":
        return await tool_protocol_delete(args)
    elif name == "protocol_import":
        return await tool_protocol_import(args)
    elif name == "cht_devices":
        return await tool_cht_devices(args)
    elif name == "cht_functions":
        return await tool_cht_functions(args)
    elif name == "cht_patterns":
        return await tool_cht_patterns(args)
    elif name == "xml_controls":
        return await tool_xml_controls(args)
    elif name == "xml_structure":
        return await tool_xml_structure(args)
    else:
        return f"[ERROR] 未知工具: {name}"


# ============================================================
# 工具实现
# ============================================================

async def tool_protocol_list(args: dict) -> str:
    query = args.get("filter", "").strip()
    index_path = PROTOCOLS_DIR / "_index.md"
    content = read_file(index_path)

    if query:
        lines = [l for l in content.splitlines() if query.lower() in l.lower()]
        result = f"## 协议库（过滤：{query}）\n\n" + "\n".join(lines) if lines else f"未找到包含 '{query}' 的协议"
    else:
        result = content

    return result


async def tool_protocol_show(args: dict) -> str:
    name = args.get("name", "").strip()
    proto_file = find_protocol_file(name)
    if proto_file:
        return f"## {proto_file.name}\n\n" + read_file(proto_file)
    else:
        results = search_protocols(name)
        if results:
            lines = [r['line'] for r in results]
            return f"未找到精确匹配，相关协议：\n" + "\n".join(lines)
        return f"未找到协议：{name}。可用 protocol_add 工具添加。"


async def tool_protocol_add(args: dict) -> str:
    category = args.get("category", "custom")
    brand_model = args.get("brand_model", "未知设备")
    comm_type = args.get("comm_type", "RS232")
    baud_rate = args.get("baud_rate", 9600)
    port = args.get("port", None)
    commands = args.get("commands", {})
    notes = args.get("notes", "")

    # 生成文件名
    filename = re.sub(r'[^\w\-]', '-', brand_model.lower().replace(' ', '-'))
    filename = re.sub(r'-+', '-', filename).strip('-') + ".md"
    file_path = PROTOCOLS_DIR / category / filename

    # 生成指令表
    cmd_table = "| 功能 | 指令 | 说明 |\n|------|------|------|\n"
    for func, cmd in commands.items():
        cmd_table += f"| {func} | `{cmd}` | |\n"

    # 生成设备声明
    if comm_type in ("RS232", "RS485"):
        rs_type = "232" if comm_type == "RS232" else "485"
        decl = f"SET_COM(dev, ch, {baud_rate}, 8, 0, 10, 0, {rs_type});"
    elif comm_type == "TCP" and port:
        decl = f"CONNECT_TCP(dev, ch, ip_addr, {port});"
    elif comm_type == "IR":
        decl = "TR_0740S_IR = L:N:IR;  // 红外模块通道"
    else:
        decl = "// 设备声明（按实际填写）"

    # 代码示例
    first_cmd = list(commands.values())[0] if commands else "xxx"
    if comm_type in ("RS232", "RS485"):
        example = f'SEND_COM(dev, ch, "{first_cmd}");'
    elif comm_type == "TCP":
        example = f'SEND_TCP(dev, ch, "{first_cmd}");'
    elif comm_type == "IR":
        example = f'SEND_IRCODE(dev, ch, IRCODE<"{first_cmd}">);'
    else:
        example = f'// 发送指令: {first_cmd}'

    from datetime import date
    today = date.today().strftime("%Y-%m-%d")

    content = f"""# {category.title()} - {brand_model}

## 基本信息
- 设备类型：{category}
- 通信方式：{comm_type}
- 波特率：{baud_rate}（串口时）
- 数据位/停止位/校验：8/1/无
{f'- TCP端口：{port}' if port else ''}

## 设备声明
```
{decl}
```

## 指令表
{cmd_table}

## 代码示例
```
{example}
```

## 适用型号
- {brand_model}

## 更新记录
- {today}: MCP Server 添加{f'，备注：{notes}' if notes else ''}
"""

    # 写入文件
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')

    # 更新索引
    index_path = PROTOCOLS_DIR / "_index.md"
    index_content = read_file(index_path)
    section_map = {
        "projector": "## 投影仪",
        "curtain": "## 窗帘电机",
        "ac": "## 空调",
        "audio": "## 音频处理器",
        "display": "## 显示设备",
        "camera": "## 摄像机",
        "matrix": "## 矩阵切换器",
        "screen": "## 投影幕",
        "lighting": "## 调光器",
        "custom": "## 用户自定义",
    }
    new_entry = f"- `{category}/{filename}` — {brand_model} — {comm_type}{f':{port}' if port else f':{baud_rate}' if comm_type in ('RS232','RS485') else ''}"

    section_header = section_map.get(category, "## 用户自定义")
    if section_header in index_content:
        index_content = index_content.replace(section_header + "\n", section_header + "\n" + new_entry + "\n")
    else:
        index_content += f"\n{section_header}\n{new_entry}\n"

    index_path.write_text(index_content, encoding='utf-8')

    return f"✅ 协议已添加：{file_path}\n\n{content}"


async def tool_protocol_update(args: dict) -> str:
    name = args.get("name", "")
    update_desc = args.get("update_description", "")
    proto_file = find_protocol_file(name)
    if not proto_file:
        return f"未找到协议：{name}"
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    content = read_file(proto_file)
    content += f"\n- {today}: {update_desc}（通过 MCP Server 更新，请手动验证指令正确性）"
    proto_file.write_text(content, encoding='utf-8')
    return f"✅ 已追加更新记录到 {proto_file.name}。\n\n注意：请手动编辑文件中的具体指令内容。"


async def tool_protocol_delete(args: dict) -> str:
    name = args.get("name", "")
    confirmed = args.get("confirmed", False)
    proto_file = find_protocol_file(name)
    if not proto_file:
        return f"未找到协议：{name}"
    if not confirmed:
        return f"⚠️ 确认删除 {proto_file.name}？请再次调用并设置 confirmed=true"
    proto_file.unlink()
    # 更新索引
    index_path = PROTOCOLS_DIR / "_index.md"
    content = read_file(index_path)
    lines = [l for l in content.splitlines() if proto_file.name not in l]
    index_path.write_text("\n".join(lines), encoding='utf-8')
    return f"✅ 已删除协议：{proto_file}"


async def tool_protocol_import(args: dict) -> str:
    cht_content = args.get("cht_content", "")

    # 提取串口指令
    serial_cmds = {}
    for m in re.finditer(r'SET_COM\((\w+),\s*(\d+),\s*(\d+),.*?(\d+)\)', cht_content):
        dev, ch, baud, rs_type = m.group(1), m.group(2), m.group(3), m.group(4)
        key = f"{dev}_ch{ch}"
        serial_cmds[key] = serial_cmds.get(key, {'baud': baud, 'type': rs_type, 'cmds': []})

    send_coms = re.findall(r'SEND_COM\((\w+),\s*(\d+),\s*"([^"]+)"\)', cht_content)
    tcp_sends = re.findall(r'SEND_TCP\((\w+|\".+?\"),\s*(\d+),\s*"([^"]+)"\)', cht_content)
    ir_sends = re.findall(r'SEND_IRCODE\((\w+),\s*(\d+),\s*IRCODE<"([^"]+)">\)', cht_content)

    result = "## 从 .cht 提取的协议信息\n\n"

    if send_coms:
        result += "### 串口设备\n"
        by_dev = {}
        for dev, ch, cmd in send_coms:
            key = f"{dev}_ch{ch}"
            by_dev.setdefault(key, []).append(cmd)
        for key, cmds in by_dev.items():
            result += f"**{key}**\n"
            for cmd in cmds:
                result += f"  - `{cmd}`\n"
        result += "\n"

    if tcp_sends:
        result += "### TCP 设备\n"
        for dev, port, cmd in tcp_sends:
            result += f"- {dev}:{port} → `{cmd}`\n"
        result += "\n"

    if ir_sends:
        result += "### 红外设备\n"
        for dev, ch, ircode in ir_sends:
            result += f"- {dev} ch{ch} → `{ircode}`\n"
        result += "\n"

    if not (send_coms or tcp_sends or ir_sends):
        result += "未提取到明确的协议指令。\n"

    result += "\n请告知每个设备的：\n1. 设备类型（投影仪/窗帘/空调...）\n2. 品牌型号\n然后调用 protocol_add 保存到协议库。"
    return result


async def tool_cht_devices(args: dict) -> str:
    device_type = args.get("device_type", "").upper().strip()
    syntax_path = REFERENCES_DIR / "core" / "syntax-rules.md"
    content = read_file(syntax_path)
    if device_type:
        # 搜索特定设备类型
        lines = content.splitlines()
        result_lines = []
        capture = False
        for line in lines:
            if device_type in line:
                capture = True
            if capture:
                result_lines.append(line)
                if len(result_lines) > 20:
                    break
        return "\n".join(result_lines) if result_lines else f"未找到设备类型：{device_type}\n\n{content}"
    return content


async def tool_cht_functions(args: dict) -> str:
    query = args.get("query", "").strip()

    func_files = list((DOCS_DIR / "系统函数库").glob("*.md"))

    if not query:
        # 返回分类总览
        result = "## 系统函数分类总览\n\n"
        for f in sorted(func_files):
            result += f"- **{f.stem}** — `/cht-functions {f.stem}`\n"
        return result

    # 搜索特定函数或分类
    query_upper = query.upper()
    for func_file in func_files:
        content = read_file(func_file)
        if query.lower() in func_file.stem.lower() or query_upper in content:
            if query_upper in content:
                # 提取函数段落
                lines = content.splitlines()
                result_lines = []
                capture = False
                for line in lines:
                    if query_upper in line:
                        capture = True
                    if capture:
                        result_lines.append(line)
                        if len(result_lines) > 30:
                            break
                return "\n".join(result_lines) if result_lines else content[:2000]
            return content

    return f"未找到：{query}\n\n可用分类：" + "、".join(f.stem for f in sorted(func_files))


async def tool_cht_patterns(args: dict) -> str:
    pattern = args.get("pattern", "").strip()
    patterns_path = REFERENCES_DIR / "core" / "code-patterns.md"
    content = read_file(patterns_path)

    if not pattern:
        # 返回模式总览（只取每个模式的标题行）
        lines = content.splitlines()
        headers = [l for l in lines if l.startswith("## 模式")]
        return "## 代码模式总览\n\n" + "\n".join(headers) + f"\n\n使用 /cht-patterns [关键词] 查看具体模式"

    # 搜索包含关键词的模式段落
    sections = re.split(r'(?=^## 模式)', content, flags=re.MULTILINE)
    for section in sections:
        if pattern.lower() in section.lower():
            return section

    return f"未找到包含 '{pattern}' 的模式。\n\n" + content[:1000]


async def tool_xml_controls(args: dict) -> str:
    control_type = args.get("control_type", "").strip()
    spec_path = REFERENCES_DIR / "controls" / "controls-spec.md"
    content = read_file(spec_path)

    if not control_type:
        # 返回总览表
        lines = content.splitlines()
        overview_lines = []
        in_table = False
        for line in lines:
            if '| #' in line or '|---|' in line or ('| ' in line and '|' in line):
                in_table = True
            if in_table:
                overview_lines.append(line)
                if len(overview_lines) > 20:
                    break
        return "\n".join(overview_lines) + "\n\n..." + "\n\n使用 /xml-controls DFCButton 等查看控件详情"

    # 搜索特定控件
    sections = re.split(r'(?=^## \d+\.)', content, flags=re.MULTILINE)
    for section in sections:
        if control_type.upper() in section.upper():
            return section

    return f"未找到控件：{control_type}\n\n" + content[:500]


async def tool_xml_structure(args: dict) -> str:
    topic = args.get("topic", "").strip()
    struct_path = REFERENCES_DIR / "controls" / "xml-structure.md"
    content = read_file(struct_path)

    if not topic:
        return content

    # 搜索特定主题
    sections = re.split(r'(?=^## )', content, flags=re.MULTILINE)
    for section in sections:
        if topic.lower() in section.lower():
            return section

    return content


async def tool_mkcontrol_generate(args: dict) -> str:
    """解析需求 → 输出确认清单（第1步）"""
    desc = args.get("description", "")
    result = f"""## 需求解析结果

### 输入描述
{desc}

### 解析说明
MKControl 生成器需要以下信息来生成 Project.xml 和 .cht 文件：

1. **触摸屏设备**：型号 + 板卡号（如：TS-1070C，板卡10）
2. **外围设备**：型号 + 板卡号 + 通信方式
3. **功能需求**：每个功能的控制方式和逻辑连接号（JoinNumber）
4. **页面结构**：页面数量和名称
5. **图片资源**：图片目录路径（可选）

### 建议操作
1. 先调用 `protocol_list` 查看现有协议库中是否有匹配的设备
2. 补充上述缺失信息后，调用 `mkcontrol_confirm` 生成文件

### 从描述中初步提取

{_extract_hints(desc)}
"""
    return result


def _extract_hints(desc: str) -> str:
    hints = []
    if any(kw in desc for kw in ['TS-9101', 'RELAY', '继电器', '灯光']):
        hints.append("- 检测到：继电器控制（灯光/电源）")
    if any(kw in desc for kw in ['窗帘', 'curtain', 'RS485']):
        hints.append("- 检测到：窗帘电机控制（RS485）")
    if any(kw in desc for kw in ['空调', 'AC', '红外', 'IR']):
        hints.append("- 检测到：空调红外控制")
    if any(kw in desc for kw in ['投影', 'projector', '串口', 'COM']):
        hints.append("- 检测到：投影仪串口控制")
    if any(kw in desc for kw in ['音量', '滑条', 'slider', 'DSP']):
        hints.append("- 检测到：音量控制（滑条）")
    if any(kw in desc for kw in ['场景', '模式', 'MutualLock']):
        hints.append("- 检测到：场景模式切换")
    return "\n".join(hints) if hints else "（需要更多信息才能解析）"


async def tool_mkcontrol_confirm(args: dict) -> str:
    """用户确认后生成 XML + .cht（第2步）"""
    return """## mkcontrol_confirm

此工具需要：
1. 已通过 `mkcontrol_generate` 完成需求解析
2. 用户已确认设备清单和功能配置

完整的 XML + CHT 生成逻辑需要 LLM 上下文推理，建议使用 Claude Code 中的 `/mk:control` 命令进行交互式生成，
或提供完整的 confirmed_plan JSON 数据。

### confirmed_plan 格式示例
```json
{
  "tp": {"type": "TP", "board": 10},
  "devices": [
    {"name": "L9101_RELAY", "type": "RELAY", "board": 1}
  ],
  "functions": [
    {"name": "灯光1", "join": 103, "ctrl": "AutolockBtn", "relay_ch": 1}
  ],
  "pages": ["主页", "灯光控制"],
  "image_path": "./"
}
```
"""


async def tool_validate_cht(args: dict) -> str:
    """校验 .cht 语法规范（调用 core/scripts/validate.py）"""
    import subprocess, tempfile, os
    cht_content = args.get("cht_content", "")
    validate_script = SCRIPTS_DIR / "validate.py"
    if not validate_script.exists():
        return f"[ERROR] 校验脚本不存在: {validate_script}"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.cht', encoding='utf-8', delete=False) as f:
        f.write(cht_content)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["python", str(validate_script), tmp_path],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout or result.stderr or "（无输出）"
        return f"## .cht 语法校验结果\n\n```\n{output}\n```"
    except subprocess.TimeoutExpired:
        return "[ERROR] 校验超时"
    finally:
        os.unlink(tmp_path)


async def tool_cross_validate(args: dict) -> str:
    """交叉校验 XML ↔ .cht 的 JoinNumber 一致性"""
    xml_content = args.get("xml_content", "")
    cht_content = args.get("cht_content", "")

    # 剥离 // 单行注释（避免注释掉的事件被误识别）
    cht_stripped = re.sub(r'//[^\n]*', '', cht_content)

    # 提取 XML 非零 JoinNumber
    xml_joins = set()
    for m in re.finditer(r'JoinNumber="(\d+)"', xml_content):
        n = int(m.group(1))
        if n > 0:
            xml_joins.add(n)

    # 区分纯导航按钮（只有 JumpPage，没有 JoinNumber > 0）—— 豁免 Critical
    nav_only_joins = set()
    for btn in re.finditer(r'<Control[^>]*Type="DFCButton"[^>]*>(.*?)</Control>', xml_content, re.DOTALL):
        btn_body = btn.group(1)
        jn_match = re.search(r'JoinNumber="(\d+)"', btn_body)
        jn = int(jn_match.group(1)) if jn_match else 0
        has_jump = bool(re.search(r'JumpPage=".+?"', btn_body))
        if jn == 0 and has_jump:
            nav_only_joins.add(0)

    # 提取 CHT 事件
    cht_button_events = set()
    for m in re.finditer(r'BUTTON_EVENT\s*\(\s*\w+\s*,\s*(\d+)\s*\)', cht_stripped):
        cht_button_events.add(int(m.group(1)))

    cht_level_events = set()
    for m in re.finditer(r'LEVEL_EVENT\s*\(\s*\w+\s*,\s*(\d+)\s*\)', cht_stripped):
        cht_level_events.add(int(m.group(1)))

    cht_all = cht_button_events | cht_level_events
    for pattern in [r'SET_BUTTON\s*\(\w+,\s*(\d+)', r'SEND_TEXT\s*\(\w+,\s*(\d+)',
                    r'SET_LEVEL\s*\(\w+,\s*(\d+)', r'SEND_PICTURE\s*\(\w+,\s*(\d+)']:
        for m in re.finditer(pattern, cht_stripped):
            cht_all.add(int(m.group(1)))

    xml_only = xml_joins - cht_all
    cht_event_only = (cht_button_events | cht_level_events) - xml_joins

    result = "## 交叉校验结果\n\n"
    result += f"XML JoinNumber 数量: {len(xml_joins)}\n"
    result += f"CHT 事件 JoinNumber 数量: {len(cht_button_events | cht_level_events)}\n\n"

    criticals = []
    warnings = []

    if xml_only:
        criticals.append(f"XML 有但 CHT 无处理 ({len(xml_only)} 项): {sorted(xml_only)}")
    if cht_event_only:
        # 虚拟通道/外部触发属合法设计，降为 Warning
        warnings.append(f"CHT 事件但 XML 无控件 ({len(cht_event_only)} 项): {sorted(cht_event_only)}")

    if criticals:
        result += "### 🔴 Critical\n" + "\n".join(f"- {c}" for c in criticals) + "\n\n"
    if warnings:
        result += "### 🟡 Warning\n" + "\n".join(f"- {w}" for w in warnings) + "\n\n"
    if not criticals and not warnings:
        result += "✅ 无问题（Critical=0, Warning=0）\n"
    elif not criticals:
        result += f"✅ 无 Critical 问题（Warning={len(warnings)}）\n"

    return result


# ============================================================
# 启动
# ============================================================

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
