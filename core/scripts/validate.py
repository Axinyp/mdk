#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MKControl .cht 代码校验脚本 v2（模板生成适配版）

用法: python validate.py <yourfile.cht>

设计原则：
  - 骨架由模板保证（块顺序、块存在、块格式）→ 不重复检查
  - 聚焦 LLM 填充内容的正确性
  - 新增模板生成特有的检查项
"""

import sys
import re
import os

# Windows: 启用 ANSI 颜色 + UTF-8
if sys.platform == "win32":
    os.system("")
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# 类型关键字错误映射
INVALID_TYPE_MAP = {
    'integer': 'int', 'INTEGER': 'int', 'Integer': 'int', 'INT': 'int', 'Int': 'int',
    'long': 'int', 'LONG': 'int', 'Long': 'int',
    'FLOAT': 'double', 'Float': 'double',
    'DOUBLE': 'double', 'Double': 'double',
    'STRING': 'string', 'String': 'string',
    'BOOLEAN': 'boolean', 'Boolean': 'boolean',
    'BYTE': 'byte', 'Byte': 'byte',
    'CHAR': 'char', 'Char': 'char',
}

# 系统 API（必须全大写）
SYSTEM_APIS = [
    "SET_COM", "SEND_COM", "ON_RELAY", "OFF_RELAY", "QUERY_RELAY",
    "SEND_IRCODE", "SEND_IO", "SET_IO_DIR",
    "SET_BUTTON", "SET_LEVEL", "SEND_TEXT", "SEND_PAGING", "SET_PICTURE", "SEND_PICTURE",
    "SEND_TCP", "SEND_UDP", "WAKEUP_ONLAN", "GET_PING_STATUS",
    "SEND_M2M_DATA", "SEND_M2M_JNPUSH",
    "START_TIMER", "CANCEL_TIMER", "CANCEL_WAIT",
    "SAVE_PARAM", "LOAD_PARAM", "DEL_ALL_PARAM",
    "BYTES_TO_STRING", "STRING_TO_BYTES", "BYTES_TO_HEX", "HEX_TO_BYTES",
    "ATOI", "ITOA", "GET_SUB_STRING", "STRING_EQ", "STRING_EQNOCASE",
    "STRING_STARTWITH", "STRING_ENDWITH",
    "BYTES_ADD", "GET_BYTES_LENGTH", "RESET_BYTE", "BYTES_TO_INT",
    "INT_TO_HEX", "INT_TO_DOUBLE", "DOUBLE_TO_INT", "DOUBLE_TO_STRING", "STRING_TO_DOUBLE",
    "GET_YEAR", "GET_MONTH", "GET_DATE", "GET_DAY",
    "GET_HOUR", "GET_MINUTE", "GET_SECOND",
    "TRACE", "GET_VER_INFO", "RANDOM_NUMBER",
    "SEND_LITE", "SEND_DMX", "SET_VOL_M", "GET_VOL_M",
    "SET_MATRIX_M", "GET_MATRIX_M",
]

VALID_ELEMENT_TYPES = {'RELAY', 'COM', 'TP', 'IR', 'IO', 'LITE', 'VOL', 'WM', 'DMX512'}


def read_file(filepath):
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            return content.splitlines(keepends=True), content
        except (UnicodeDecodeError, LookupError):
            continue
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    return content.splitlines(keepends=True), content


def strip_comments(content):
    """去除单行注释，避免匹配注释中的代码"""
    return re.sub(r'//[^\n]*', '', content)


def extract_block(content, block_name):
    """提取指定 DEFINE_* 块的内容"""
    pattern = rf'{block_name}\s*\n(.*?)(?=\nDEFINE_|\Z)'
    m = re.search(pattern, content, re.DOTALL)
    return m.group(1) if m else ""


def validate(filepath):
    if not os.path.exists(filepath):
        print(f"{RED}错误: 文件不存在: {filepath}{NC}")
        return False

    lines, content = read_file(filepath)
    code = strip_comments(content)

    errors = []
    warnings = []

    print(f"\n{BLUE}═══════════════════════════════════════════════════{NC}")
    print(f"{BLUE}  MKControl .cht 校验工具 v2（模板适配版）{NC}")
    print(f"{BLUE}═══════════════════════════════════════════════════{NC}")
    print(f"\n校验文件: {GREEN}{filepath}{NC}\n")

    # ==================== [1] 模板占位符残留 ====================
    print(f"{YELLOW}[1/10] 检查模板占位符残留...{NC}")
    placeholders = re.findall(r'\{\{(\w+)\}\}', content)
    if placeholders:
        for p in placeholders:
            errors.append(f"模板占位符未替换: {{{{{p}}}}}")
    else:
        print(f"  {GREEN}✓ 无残留占位符{NC}")

    # ==================== [2] 括号匹配 ====================
    print(f"\n{YELLOW}[2/10] 检查括号匹配...{NC}")
    opens = content.count("{")
    closes = content.count("}")
    if opens != closes:
        errors.append(f"括号不匹配: {{ 数量={opens}, }} 数量={closes}")
    else:
        print(f"  {GREEN}✓ 括号匹配{NC}")

    # ==================== [3] 变量初始化 ====================
    print(f"\n{YELLOW}[3/10] 检查变量初始化...{NC}")
    var_block = extract_block(content, 'DEFINE_VARIABLE')
    uninitialized = re.findall(
        r'^\s*(int|string|boolean|byte|char|double)\s+([a-zA-Z_]\w*)\s*;',
        var_block, re.MULTILINE
    )
    if uninitialized:
        for typ, name in uninitialized:
            errors.append(f"变量未初始化: {typ} {name};")
    else:
        print(f"  {GREEN}✓ 所有变量已初始化{NC}")

    # ==================== [4] 类型关键字大小写 ====================
    print(f"\n{YELLOW}[4/10] 检查类型关键字大小写...{NC}")
    pattern = '|'.join(re.escape(k) for k in INVALID_TYPE_MAP)
    type_errors = []
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith('//'):
            continue
        m = re.match(rf'^\s*({pattern})\s+', line)
        if m:
            type_errors.append(f"行 {i}: '{m.group(1)}' → '{INVALID_TYPE_MAP[m.group(1)]}'")
    if type_errors:
        for e in type_errors:
            errors.append(f"类型关键字错误: {e}")
    else:
        print(f"  {GREEN}✓ 类型关键字正确{NC}")

    # ==================== [5] 系统 API 大小写 ====================
    print(f"\n{YELLOW}[5/10] 检查系统 API 大小写...{NC}")
    api_lower_map = {api.lower(): api for api in SYSTEM_APIS}
    # 收集用户自定义函数名（排除误报）
    user_funcs = set()
    func_block = extract_block(content, 'DEFINE_FUNCTION')
    for m in re.finditer(r'^\s*(?:void|int|string|boolean|byte|char|double)\s+(\w+)\s*\(', func_block, re.MULTILINE):
        user_funcs.add(m.group(1))
    for m in re.finditer(r'^\s*TIMER\s+(\w+)\s*\(', content, re.MULTILINE):
        user_funcs.add(m.group(1))

    api_errors = []
    for i, line in enumerate(lines, 1):
        code_part = line.split('//')[0]
        if not code_part.strip():
            continue
        for m in re.finditer(r'\b([a-zA-Z_]\w*)\s*\(', code_part):
            fn = m.group(1)
            if fn in user_funcs:
                continue
            if fn.lower() in api_lower_map and fn != api_lower_map[fn.lower()]:
                api_errors.append(f"行 {i}: '{fn}' → '{api_lower_map[fn.lower()]}'")
    if api_errors:
        for e in api_errors:
            errors.append(f"API 大小写错误: {e}")
    else:
        print(f"  {GREEN}✓ 系统 API 大小写正确{NC}")

    # ==================== [6] 设备声明 + 引用一致性 ====================
    print(f"\n{YELLOW}[6/10] 检查设备声明与引用...{NC}")
    device_block = extract_block(content, 'DEFINE_DEVICE')
    declared_devices = {}
    for m in re.finditer(r'(\w+)\s*=\s*([LMTNZ]):(\d+):(\w+)', device_block):
        name, carrier, board, elem = m.groups()
        if elem.upper() not in VALID_ELEMENT_TYPES:
            errors.append(f"未知元设备类型 '{elem}': {name} = {carrier}:{board}:{elem}")
        declared_devices[name] = elem.upper()

    # 检查事件/函数中引用的设备是否已声明
    event_block = extract_block(code, 'DEFINE_EVENT')
    start_block = extract_block(code, 'DEFINE_START')
    check_code = event_block + "\n" + start_block + "\n" + func_block
    device_refs = set()
    for pattern_str in [
        r'BUTTON_EVENT\s*\(\s*(\w+)\s*,',
        r'LEVEL_EVENT\s*\(\s*(\w+)\s*,',
        r'DATA_EVENT\s*\(\s*(\w+)',
        r'SET_COM\s*\(\s*(\w+)\s*,',
        r'SEND_COM\s*\(\s*(\w+)\s*,',
        r'ON_RELAY\s*\(\s*(\w+)\s*,',
        r'OFF_RELAY\s*\(\s*(\w+)\s*,',
        r'SEND_IRCODE\s*\(\s*(\w+)\s*,',
        r'SET_BUTTON\s*\(\s*(\w+)\s*,',
        r'SET_LEVEL\s*\(\s*(\w+)\s*,',
        r'SEND_TEXT\s*\(\s*(\w+)\s*,',
        r'SEND_PICTURE\s*\(\s*(\w+)\s*,',
        r'SEND_PAGING\s*\(\s*(\w+)\s*,',
    ]:
        for m in re.finditer(pattern_str, check_code):
            device_refs.add(m.group(1))

    undeclared = device_refs - set(declared_devices.keys())
    # 排除可能是变量名的情况（如 loopbackIp）
    undeclared = {d for d in undeclared if not d[0].islower() or d in ('tp',)}
    if undeclared:
        for d in sorted(undeclared):
            errors.append(f"设备 '{d}' 在代码中使用但未在 DEFINE_DEVICE 中声明")
    else:
        print(f"  {GREEN}✓ 设备声明与引用一致{NC}")

    # ==================== [7] SET_COM 覆盖串口设备 ====================
    print(f"\n{YELLOW}[7/10] 检查串口初始化...{NC}")
    com_devices = {name for name, typ in declared_devices.items() if typ == 'COM'}
    set_com_devices = set(re.findall(r'SET_COM\s*\(\s*(\w+)\s*,', code))
    missing_init = com_devices - set_com_devices
    if missing_init:
        for d in sorted(missing_init):
            warnings.append(f"串口设备 '{d}' 未调用 SET_COM 初始化")
    else:
        if com_devices:
            print(f"  {GREEN}✓ 所有串口已初始化{NC}")
        else:
            print(f"  {GREEN}✓ 无串口设备{NC}")

    # ==================== [8] Timer/WAIT 语法 ====================
    print(f"\n{YELLOW}[8/10] 检查 Timer/WAIT 语法...{NC}")
    timer_ok = True
    if re.findall(r'START_TIMER\s*\(\s*"[^"]+"\s*,', content):
        errors.append("START_TIMER 参数不应加引号: START_TIMER(timerName, ms)")
        timer_ok = False
    if re.findall(r'CANCEL_TIMER\s*\(\s*[a-zA-Z_]\w*\s*\)', content):
        errors.append('CANCEL_TIMER 参数需要加引号: CANCEL_TIMER("timerName")')
        timer_ok = False
    if re.findall(r'\bWAIT\s*\(\s*\d+\s*\)', content):
        errors.append("WAIT 语法错误: 应为 WAIT 毫秒数 { ... }，不能写成 WAIT(毫秒数)")
        timer_ok = False
    wait_names = re.findall(r'\bWAIT\s+\d+\s+"(\w+)"', content)
    for name in set(wait_names):
        if wait_names.count(name) > 1:
            errors.append(f'WAIT 名称重复: "{name}" 出现 {wait_names.count(name)} 次')
            timer_ok = False
    if timer_ok:
        print(f"  {GREEN}✓ Timer/WAIT 语法正确{NC}")

    # ==================== [9] 重复事件检查 ====================
    print(f"\n{YELLOW}[9/10] 检查重复事件...{NC}")
    btn_events = re.findall(r'BUTTON_EVENT\s*\(\s*\w+\s*,\s*(\d+)\s*\)', code)
    lvl_events = re.findall(r'LEVEL_EVENT\s*\(\s*\w+\s*,\s*(\d+)\s*\)', code)
    dup_ok = True
    for jn in set(btn_events):
        count = btn_events.count(jn)
        if count > 1:
            errors.append(f"BUTTON_EVENT JN={jn} 重复定义 {count} 次")
            dup_ok = False
    for jn in set(lvl_events):
        count = lvl_events.count(jn)
        if count > 1:
            errors.append(f"LEVEL_EVENT JN={jn} 重复定义 {count} 次")
            dup_ok = False
    if dup_ok:
        print(f"  {GREEN}✓ 无重复事件{NC}")

    # ==================== [10] 常量 + TODO ====================
    print(f"\n{YELLOW}[10/13] 检查常量 + TODO...{NC}")
    const_block = extract_block(content, 'DEFINE_CONSTANT')
    if re.search(r'^\s*const\s+', const_block, re.MULTILINE):
        errors.append("DEFINE_CONSTANT 不应使用 'const' 关键字，格式: 常量名 = 值;")
    if re.search(r'^\s*\w+\s*=\s*"', const_block, re.MULTILINE):
        errors.append("DEFINE_CONSTANT 只允许整型常量，不允许字符串")

    todos = re.findall(r'TODO[:\s].*', content)
    if todos:
        for t in todos[:5]:
            warnings.append(f"TODO: {t.strip()}")
        if len(todos) > 5:
            warnings.append(f"...共 {len(todos)} 处 TODO")
    else:
        print(f"  {GREEN}✓ 常量正确，无 TODO{NC}")

    # ==================== [11] GET_LEVEL 错误用法 ====================
    print(f"\n{YELLOW}[11/13] 检查 GET_LEVEL 错误用法...{NC}")
    get_level_uses = re.findall(r'\bGET_LEVEL\s*\(', content)
    if get_level_uses:
        for _ in get_level_uses:
            errors.append("GET_LEVEL() 函数不存在: 在 LEVEL_EVENT 回调中用 LEVEL.Value 属性获取当前值")
    else:
        print(f"  {GREEN}✓ 无 GET_LEVEL 错误用法{NC}")

    # ==================== [12] IRCODE<> 内字符串拼接 ====================
    print(f"\n{YELLOW}[12/13] 检查 IRCODE<> 拼接...{NC}")
    ircode_concat_matches = re.findall(r'IRCODE\s*<[^>]*\+[^>]*>', content)
    if ircode_concat_matches:
        for m in ircode_concat_matches:
            errors.append(f"IRCODE<> 内禁止使用 + 拼接 (编译期宏只接受字面常量): {m[:70]}")
    else:
        print(f"  {GREEN}✓ IRCODE<> 内无非法拼接{NC}")

    # ==================== [13] DEFINE_COMBINE 单 TP 误填 ====================
    print(f"\n{YELLOW}[13/13] 检查 DEFINE_COMBINE 合法性...{NC}")
    combine_block = extract_block(content, 'DEFINE_COMBINE')
    combine_entries = re.findall(r'\b\w+\s*;', strip_comments(combine_block))
    tp_devices = [name for name, typ in declared_devices.items() if typ == 'TP']
    if combine_entries and len(tp_devices) <= 1:
        errors.append(
            f"DEFINE_COMBINE 填写了 {len(combine_entries)} 个设备但仅有 {len(tp_devices)} 个 TP: "
            "单触屏工程此块必须留空，否则编译报 'overlap' 错误"
        )
    else:
        print(f"  {GREEN}✓ DEFINE_COMBINE 合法{NC}")

    # ==================== 输出结果 ====================
    print(f"\n{BLUE}═══════════════════════════════════════════════════{NC}")
    print(f"{RED}错误: {len(errors)}{NC}  {YELLOW}警告: {len(warnings)}{NC}")
    print(f"{BLUE}═══════════════════════════════════════════════════{NC}")

    if errors:
        print(f"\n{RED}[错误]{NC}")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print(f"\n{YELLOW}[警告]{NC}")
        for w in warnings:
            print(f"  ⚠ {w}")
    if not errors and not warnings:
        print(f"\n{GREEN}  ✓ 校验通过{NC}")

    return len(errors) == 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: python validate.py <yourfile.cht>")
        sys.exit(1)
    ok = validate(sys.argv[1])
    sys.exit(0 if ok else 1)
