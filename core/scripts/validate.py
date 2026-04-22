#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MKControl .cht 代码校验脚本 (增强版)
用法: python validate.py <yourfile.cht>

检查项目:
- 必需段落检查
- 段落顺序检查（严格行号，检测乱序和重复块）
- 括号匹配检查
- 块格式检查（DEFINE_*/函数/TIMER 不允许同行花括号）
- 变量初始化检查
- 类型关键字大小写检查
- 流程控制关键字大小写检查
- 函数定义顺序检查
- 定时器参数检查
- DATA.Data 上下文检查
- 设备命名格式检查
- 事件括号类型检查
- 常量定义检查
- 系统 API 函数大小写检查（ITOA/ATOI 等必须全大写）
- TODO 占位符检查
"""

import sys
import re
import os

# Windows: 启用 ANSI 颜色 + UTF-8 控制台输出
if sys.platform == "win32":
    os.system("")  # 激活 Windows Terminal VT100 模式
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ANSI 颜色
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# 无效类型关键字 → 正确形式映射（覆盖所有大小写变体）
INVALID_TYPE_MAP = {
    # integer → int
    'integer': 'int', 'INTEGER': 'int', 'Integer': 'int', 'INT': 'int', 'Int': 'int',
    # long 不是合法类型，应使用 int
    'long': 'int', 'LONG': 'int', 'Long': 'int',
    # float 不是合法类型，应使用 double
    'float': 'double', 'FLOAT': 'double', 'Float': 'double',
    # 其他类型的错误大小写形式
    'DOUBLE': 'double', 'Double': 'double',
    'STRING': 'string', 'String': 'string',
    'BOOLEAN': 'boolean', 'Boolean': 'boolean',
    'BYTE': 'byte',    'Byte': 'byte',
    'CHAR': 'char',    'Char': 'char',
}

REQUIRED_SECTIONS = ["DEFINE_DEVICE"]
ALL_SECTIONS = [
    "DEFINE_DEVICE", "DEFINE_COMBINE", "DEFINE_CONSTANT",
    "DEFINE_VARIABLE", "DEFINE_FUNCTION", "DEFINE_TIMER",
    "DEFINE_START", "DEFINE_EVENT", "DEFINE_PROGRAME"
]

# 正确的块顺序
CORRECT_ORDER = [
    "DEFINE_DEVICE", "DEFINE_COMBINE", "DEFINE_CONSTANT",
    "DEFINE_VARIABLE", "DEFINE_FUNCTION", "DEFINE_TIMER",
    "DEFINE_START", "DEFINE_EVENT", "DEFINE_PROGRAME"
]

KNOWN_APIS = [
    "SET_COM", "SEND_COM", "ON_RELAY", "OFF_RELAY", "QUERY_RELAY",
    "SEND_IRCODE", "SEND_IO", "SET_IO_DIR",
    "SET_BUTTON", "SET_LEVEL", "SEND_TEXT", "SEND_PAGING", "SET_PICTURE",
    "SEND_TCP", "SEND_UDP", "WAKEUP_ONLAN",
    "START_TIMER", "CANCEL_TIMER", "WAIT", "CANCEL_WAIT", "SLEEP",
    "SAVE_PARAM", "LOAD_PARAM", "DEL_ALL_PARAM",
    "BYTES_TO_STRING", "STRING_TO_BYTES", "BYTES_TO_HEX", "HEX_TO_BYTES",
    "ATOI", "ITOA", "GET_SUB_STRING", "STRING_EQ", "STRING_EQNOCASE",
    "STRING_STARTWITH", "STRING_ENDWITH",
    "TRACE", "GET_VER_INFO", "RANDOM_NUMBER",
    "SEND_LITE", "SEND_DMX", "SET_VOL_M", "GET_VOL_M",
    "SET_MATRIX_M", "GET_MATRIX_M",
    "BYTES_ADD", "GET_BYTES_LENGTH", "RESET_BYTE",
    "GET_PING_STATUS", "SEND_M2M_DATA", "SEND_M2M_JNPUSH",
]

def read_file_auto(filepath):
    """自动检测文件编码（优先 UTF-8，回退 GBK），返回 (lines, content)"""
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            return content.splitlines(keepends=True), content
        except (UnicodeDecodeError, LookupError):
            continue
    # 最终兜底：替换不可解码字符
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    return content.splitlines(keepends=True), content


def validate(filepath):
    if not os.path.exists(filepath):
        print(f"{RED}错误: 文件不存在: {filepath}{NC}")
        return False

    lines, content = read_file_auto(filepath)

    errors = []
    warnings = []

    print(f"\n{BLUE}═══════════════════════════════════════════════════{NC}")
    print(f"{BLUE}  MKControl .cht 代码校验工具 (增强版){NC}")
    print(f"{BLUE}═══════════════════════════════════════════════════{NC}")
    print(f"\n校验文件: {GREEN}{filepath}{NC}")
    print("")

    # ==================== [1] 必需段落检查 ====================
    print(f"{YELLOW}[1/12] 检查必需段落...{NC}")
    for sec in REQUIRED_SECTIONS:
        if sec not in content:
            errors.append(f"缺少必需段落: {sec}")
    if not errors or all(s in content for s in REQUIRED_SECTIONS):
        print(f"  {GREEN}✓ 必需段落完整{NC}")

    # ==================== [2] 段落顺序检查（严格行号顺序） ====================
    print(f"\n{YELLOW}[2/12] 检查段落顺序...{NC}")
    # 按实际出现的行号收集所有 DEFINE_* 块
    section_occurrences = []  # [(line_num, section_name), ...]
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        for sec in ALL_SECTIONS:
            if stripped == sec or stripped.startswith(sec + '\n') or stripped.startswith(sec + ' ') or stripped.startswith(sec + '\r'):
                section_occurrences.append((line_num, sec))
                break
            # 也匹配 "DEFINE_XXX" 后面直接跟注释的情况
            if re.match(rf'^{sec}\s*$', stripped) or re.match(rf'^{sec}\s*//', stripped):
                section_occurrences.append((line_num, sec))
                break

    # 检查重复块
    seen_sections = set()
    for line_num, sec in section_occurrences:
        if sec in seen_sections:
            errors.append(f"段落重复: {sec} 在行 {line_num} 重复出现")
        seen_sections.add(sec)

    # 检查顺序是否严格递增
    is_ordered = True
    found_sections = [sec for _, sec in section_occurrences]
    prev_idx = -1
    prev_sec = ""
    for _, sec in section_occurrences:
        curr_idx = CORRECT_ORDER.index(sec)
        if curr_idx < prev_idx:
            is_ordered = False
            errors.append(f"段落顺序错误: {sec} 出现在 {prev_sec} 之后（正确顺序: DEVICE→COMBINE→CONSTANT→VARIABLE→FUNCTION→TIMER→START→EVENT→PROGRAME）")
        prev_idx = curr_idx
        prev_sec = sec
    if is_ordered and not any("段落重复" in e for e in errors):
        print(f"  {GREEN}✓ 段落顺序正确{NC}")

    # ==================== [3] 括号匹配检查 ====================
    print(f"\n{YELLOW}[3/12] 检查括号匹配...{NC}")
    open_braces = content.count("{")
    close_braces = content.count("}")
    if open_braces != close_braces:
        errors.append(f"括号不匹配: {{ 数量={open_braces}, }} 数量={close_braces}")
    else:
        print(f"  {GREEN}✓ 括号匹配{NC}")

    # ==================== [4] 块格式检查 ====================
    print(f"\n{YELLOW}[4/12] 检查块格式...{NC}")
    block_format_errors = []
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.match(r'^\s*//', line):
            continue

        for sec in ALL_SECTIONS:
            # 检查 1: DEFINE_* 行不允许有 {}（DEFINE_* 是段落标记，不用花括号包裹）
            if re.match(rf'^{sec}\s*\{{', stripped):
                block_format_errors.append(
                    f"行 {line_num}: {sec} 不允许用 {{}} 包裹，它是段落标记，内容直接写在下方直到下一个 DEFINE_*"
                )

            # 检查 2: DEFINE_* 同行不允许跟函数/内容（必须独占一行，仅允许后跟注释）
            # 错误示例: DEFINE_FUNCTION set_input_mute_on(int ch)
            if re.match(rf'^{sec}\s+(?!//)[^\s]', stripped):
                # 排除 DEFINE_XXX 后面只有注释的情况
                after_sec = stripped[len(sec):].strip()
                if after_sec and not after_sec.startswith('//'):
                    block_format_errors.append(
                        f"行 {line_num}: {sec} 必须独占一行，不允许同行跟其他内容。"
                        f" 应换行书写:\n"
                        f"         {sec}\n"
                        f"             // 内容写在下方..."
                    )

    if block_format_errors:
        for err in block_format_errors:
            errors.append(f"块格式错误: {err}")
    else:
        print(f"  {GREEN}✓ 块格式正确{NC}")

    # ==================== [5] 变量初始化检查 ====================
    print(f"\n{YELLOW}[5/12] 检查变量初始化...{NC}")
    var_block_match = re.search(r'DEFINE_VARIABLE\s*\n(.*?)(?=\nDEFINE_|\Z)', content, re.DOTALL)
    uninitialized = []
    if var_block_match:
        var_block = var_block_match.group(1)
        # 找没有赋值的变量声明 (类型 变量名 ;)
        pattern = r'^\s*(int|string|boolean|byte|char|double)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;'
        for match in re.finditer(pattern, var_block, re.MULTILINE):
            uninitialized.append(f"{match.group(1)} {match.group(2)};")
    if uninitialized:
        for var in uninitialized:
            errors.append(f"变量未初始化: {var}")
    else:
        print(f"  {GREEN}✓ 所有变量已初始化{NC}")

    # ==================== [6] 类型关键字大小写检查 ====================
    print(f"\n{YELLOW}[6/12] 检查类型关键字大小写...{NC}")
    invalid_types = []
    _invalid_type_pattern = '|'.join(re.escape(k) for k in INVALID_TYPE_MAP.keys())
    for line_num, line in enumerate(lines, 1):
        if re.match(r'^\s*//', line):
            continue
        match = re.match(rf'^\s*({_invalid_type_pattern})\s+', line)
        if match:
            used = match.group(1)
            correct = INVALID_TYPE_MAP[used]
            invalid_types.append(f"行 {line_num}: '{used}' 应改为 '{correct}'")
    if invalid_types:
        for t in invalid_types:
            errors.append(f"类型关键字错误: {t}")
    else:
        print(f"  {GREEN}✓ 类型关键字正确{NC}")

    # ==================== [7] 流程控制关键字大小写检查 ====================
    print(f"\n{YELLOW}[7/12] 检查流程控制关键字大小写...{NC}")
    invalid_control = []
    keywords = ['IF', 'ELSE', 'SWITCH', 'CASE', 'FOR', 'WHILE', 'DO', 'BREAK', 'CONTINUE', 'RETURN']
    for line_num, line in enumerate(lines, 1):
        if re.match(r'^\s*//', line):
            continue
        for kw in keywords:
            # 排除已经正确小写的 if/else
            if re.search(rf'\b{kw}\b', line):
                invalid_control.append(f"行 {line_num}: {kw}")
    if invalid_control:
        for kw in invalid_control:
            errors.append(f"流程控制关键字应小写: {kw}")
    else:
        print(f"  {GREEN}✓ 流程控制关键字正确{NC}")

    # ==================== [8] 函数/Timer 定义顺序检查 ====================
    print(f"\n{YELLOW}[8/12] 检查函数定义顺序...{NC}")
    # 检查 START_TIMER 调用的 Timer 是否已定义
    start_timer_calls = re.findall(r'START_TIMER\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*,', content)
    timer_defs = re.findall(r'^\s*TIMER\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)', content, re.MULTILINE)
    # 检查 Timer 定义位置
    timer_in_event = False
    event_match = re.search(r'DEFINE_EVENT\s*\n(.*?)(?=\nDEFINE_|\Z)', content, re.DOTALL)
    if event_match and re.search(r'TIMER\s+\w+\s*\(\)', event_match.group(1)):
        timer_in_event = True
    
    missing_timers = []
    for timer_name in start_timer_calls:
        if timer_name not in timer_defs and not timer_in_event:
            missing_timers.append(timer_name)
    
    if missing_timers:
        for t in missing_timers:
            warnings.append(f"Timer '{t}' 可能未定义（应在调用前定义或在 DEFINE_EVENT 中）")
    print(f"  {GREEN}✓ 函数/Timer 定义顺序检查完成{NC}")

    # ==================== [9] 定时器参数检查 ====================
    print(f"\n{YELLOW}[9/12] 检查定时器参数...{NC}")
    # START_TIMER 不应该有引号
    start_timer_quoted = re.findall(r'START_TIMER\s*\(\s*"[^"]+"\s*,', content)
    if start_timer_quoted:
        errors.append("START_TIMER 参数不应加引号")
    # CANCEL_TIMER 应该有引号
    cancel_timer_unquoted = re.findall(r'CANCEL_TIMER\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)', content)
    if cancel_timer_unquoted:
        errors.append("CANCEL_TIMER 参数需要加引号，如 CANCEL_TIMER(\"timerName\")")
    # CANCEL_WAIT 应该有引号
    cancel_wait_unquoted = re.findall(r'CANCEL_WAIT\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)', content)
    if cancel_wait_unquoted:
        errors.append("CANCEL_WAIT 参数需要加引号，如 CANCEL_WAIT(\"waitName\")")
    # WAIT 语法检查：禁止 WAIT(n) 形式，应为 WAIT n { ... }
    wait_wrong_syntax = re.findall(r'\bWAIT\s*\(\s*\d+\s*\)', content)
    if wait_wrong_syntax:
        errors.append("WAIT 语法错误：应为 'WAIT 毫秒数 { ... }'，不能写成 WAIT(毫秒数)")
    # WAIT 命名唯一性检查（docs 规定：命名WAIT语句的名字在整个程序中必须唯一）
    wait_names = re.findall(r'\bWAIT\s+\d+\s+"(\w+)"', content)
    for name in set(wait_names):
        if wait_names.count(name) > 1:
            errors.append(f"WAIT 名称重复: \"{name}\" 出现 {wait_names.count(name)} 次（命名WAIT名字必须唯一）")

    if not start_timer_quoted and not cancel_timer_unquoted and not cancel_wait_unquoted \
            and not wait_wrong_syntax and not any(wait_names.count(n) > 1 for n in set(wait_names)):
        print(f"  {GREEN}✓ 定时器/WAIT 参数正确{NC}")

    # ==================== [10] DATA.Data 上下文检查 ====================
    print(f"\n{YELLOW}[10/12] 检查 DATA.Data 上下文...{NC}")
    has_data_data = 'DATA.Data' in content
    has_ondata = 'ONDATA()' in content
    if has_data_data and not has_ondata:
        errors.append("DATA.Data 只应在 ONDATA() 事件中使用")
    else:
        print(f"  {GREEN}✓ DATA.Data 使用正确{NC}")

    # ==================== [11] 设备命名格式检查 ====================
    print(f"\n{YELLOW}[11/12] 检查设备命名格式...{NC}")
    device_block_match = re.search(r'DEFINE_DEVICE\s*\n(.*?)(?=\nDEFINE_|\Z)', content, re.DOTALL)
    invalid_devices = []
    has_valid_device = False
    if device_block_match:
        device_block = device_block_match.group(1)
        # 找不在注释里的设备定义行
        # 合法载体类型：M T N L Z（S 类型当前版本禁用）
        # 合法元设备类型白名单
        VALID_ELEMENT_TYPES = {'RELAY','COM','TP','IR','IO','LITE','VOL','WM','DMX512'}
        for line in device_block.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            # 检测禁用的 S 载体类型
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[Ss]:', line):
                invalid_devices.append(f"S 类型（级联板）当前版本不支持: {line}")
                continue
            # 有效设备定义格式: 名称 = [MTNLZmtnlz]:数字:元设备类型;
            m = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[MTNLZmtnlz][0-9]*:([0-9]+):([A-Z0-9]+)', line)
            if m:
                elem_type = m.group(2).upper()
                if elem_type not in VALID_ELEMENT_TYPES:
                    invalid_devices.append(f"未知元设备类型 '{m.group(2)}': {line}")
                else:
                    has_valid_device = True
            elif '=' in line:
                invalid_devices.append(line)
            elif line and not line.startswith('DEFINE_'):
                # 非空且不是有效设备声明（如只有 11）
                if line.isdigit() or re.match(r'^[a-zA-Z_]?\d+$', line):
                    invalid_devices.append(line)
    if invalid_devices:
        for dev in invalid_devices:
            errors.append(f"DEFINE_DEVICE 中无效内容: {dev}")
    elif not has_valid_device:
        warnings.append("DEFINE_DEVICE 中未发现有效设备定义")
    else:
        print(f"  {GREEN}✓ 设备命名格式正确{NC}")

    # ==================== [12] 事件括号类型检查 ====================
    print(f"\n{YELLOW}[12/12] 检查事件括号类型...{NC}")
    invalid_brackets = []
    event_types = ['BUTTON_EVENT', 'DATA_EVENT', 'LEVEL_EVENT', 'STRING_EVENT']
    for line_num, line in enumerate(lines, 1):
        for event_type in event_types:
            if re.search(rf'{event_type}\[[^\]]+\]', line):
                invalid_brackets.append(f"行 {line_num}: {event_type}[...]")
    if invalid_brackets:
        for bracket in invalid_brackets:
            errors.append(f"事件应使用圆括号而非方括号: {bracket}")
    else:
        print(f"  {GREEN}✓ 事件括号正确{NC}")

    # ==================== [13] DEFINE_CONSTANT 类型检查 ====================
    print(f"\n{YELLOW}[13/14] 检查常量定义...{NC}")
    const_block_match = re.search(r'DEFINE_CONSTANT\s*\n(.*?)(?=\nDEFINE_|\Z)', content, re.DOTALL)
    if const_block_match:
        const_block = const_block_match.group(1)
        # 检查是否包含非整型常量
        # 错误: const_str = "hello"; 或 const_float = 3.14;
        invalid_const = re.findall(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*["\'\.\-]|\d+\.\d+', const_block, re.MULTILINE)
        # 还要检查是否有 const 关键字（不应该有）
        has_const_keyword = re.search(r'^\s*const\s+', const_block, re.MULTILINE)
        if has_const_keyword:
            errors.append("DEFINE_CONSTANT 不应使用 'const' 关键字，格式应为: 常量名=值;")
        elif invalid_const:
            warnings.append("DEFINE_CONSTANT 建议只使用整型常量")
        else:
            print(f"  {GREEN}✓ 常量定义正确{NC}")
    else:
        print(f"  {GREEN}✓ 无常量定义块{NC}")

    # ==================== [14] 系统 API 函数大小写检查 ====================
    print(f"\n{YELLOW}[14/14] 检查系统 API 函数大小写...{NC}")
    # 所有系统 API 必须全大写（从官方文档提取）
    SYSTEM_APIS_UPPER = [
        # 串口
        "SET_COM", "SEND_COM",
        # 继电器
        "ON_RELAY", "OFF_RELAY", "QUERY_RELAY",
        # 红外
        "SEND_IRCODE",
        # IO
        "SEND_IO", "SET_IO_DIR",
        # 触屏
        "SET_BUTTON", "SET_LEVEL", "SEND_TEXT", "SEND_PAGING", "SET_PICTURE", "SEND_PICTURE",
        # 网络
        "SEND_TCP", "SEND_UDP", "WAKEUP_ONLAN", "GET_PING_STATUS",
        # M2M
        "SEND_M2M_DATA", "SEND_M2M_JNPUSH",
        # 定时器
        "START_TIMER", "CANCEL_TIMER", "CANCEL_WAIT",
        # 参数
        "SAVE_PARAM", "LOAD_PARAM", "DEL_ALL_PARAM",
        # 字符串/类型转换（必须全大写）
        "BYTES_TO_STRING", "STRING_TO_BYTES", "BYTES_TO_HEX", "HEX_TO_BYTES",
        "ATOI", "ITOA", "GET_SUB_STRING", "STRING_EQ", "STRING_EQNOCASE",
        "STRING_STARTWITH", "STRING_ENDWITH",
        "BYTES_ADD", "GET_BYTES_LENGTH", "RESET_BYTE", "BYTES_TO_INT",
        "INT_TO_HEX", "INT_TO_DOUBLE",
        "DOUBLE_TO_INT", "DOUBLE_TO_STRING", "STRING_TO_DOUBLE",
        # 时间
        "GET_YEAR", "GET_MONTH", "GET_DATE", "GET_DAY",
        "GET_HOUR", "GET_MINUTE", "GET_SECOND",
        # 其他
        "TRACE", "GET_VER_INFO", "RANDOM_NUMBER",
        "SEND_LITE", "SEND_DMX", "SET_VOL_M", "GET_VOL_M",
        "SET_MATRIX_M", "GET_MATRIX_M",
    ]
    # 构建小写→正确大写的映射
    api_lower_map = {api.lower(): api for api in SYSTEM_APIS_UPPER}

    # 收集用户在 DEFINE_FUNCTION 中定义的自定义函数名（排除误报）
    user_defined_funcs = set()
    func_block_match = re.search(r'DEFINE_FUNCTION\s*\n(.*?)(?=\nDEFINE_TIMER|\nDEFINE_START|\nDEFINE_EVENT|\nDEFINE_PROGRAME|\Z)', content, re.DOTALL)
    if func_block_match:
        for m in re.finditer(r'^\s*(?:void|int|string|boolean|byte|char|double)\s+([a-zA-Z_]\w*)\s*\(', func_block_match.group(1), re.MULTILINE):
            user_defined_funcs.add(m.group(1))
    # 也收集 TIMER 定义的函数名
    for m in re.finditer(r'^\s*TIMER\s+([a-zA-Z_]\w*)\s*\(', content, re.MULTILINE):
        user_defined_funcs.add(m.group(1))

    api_case_errors = []
    for line_num, line in enumerate(lines, 1):
        # 跳过注释行
        stripped = line.lstrip()
        if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
            continue
        # 去掉行内注释
        code_part = line.split('//')[0]
        # 查找所有 word( 模式的函数调用
        for match in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code_part):
            func_name = match.group(1)
            # 跳过用户自定义函数（如 get_date 不应被匹配为系统 GET_DATE）
            if func_name in user_defined_funcs:
                continue
            func_lower = func_name.lower()
            if func_lower in api_lower_map:
                correct = api_lower_map[func_lower]
                if func_name != correct:
                    api_case_errors.append(
                        f"行 {line_num}: '{func_name}' 应改为 '{correct}'"
                    )
    if api_case_errors:
        for err in api_case_errors:
            errors.append(f"系统 API 大小写错误: {err}")
    else:
        print(f"  {GREEN}✓ 系统 API 函数大小写正确{NC}")

    # ==================== TODO 占位符检查 ====================
    print(f"\n{YELLOW}(额外) 检查 TODO 占位符...{NC}")
    todos = re.findall(r'TODO[:\s].*', content)
    if todos:
        for t in todos[:3]:  # 只显示前3个
            warnings.append(f"TODO: {t.strip()}")
        if len(todos) > 3:
            warnings.append(f"...共 {len(todos)} 处")
    else:
        print(f"  {GREEN}✓ 无 TODO 占位符{NC}")

    # ==================== 输出结果 ====================
    print(f"\n{BLUE}═══════════════════════════════════════════════════{NC}")
    print(f"校验完成")
    print(f"{RED}错误: {len(errors)}{NC}")
    print(f"{YELLOW}警告: {len(warnings)}{NC}")
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
        print(f"\n{GREEN}  ✓ 校验通过，未发现问题{NC}")
        return True
    elif not errors:
        print(f"\n{GREEN}  ✓ 无错误，{len(warnings)} 条警告{NC}")
        return True
    else:
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: python validate.py <yourfile.cht>")
        print(f"      python validate.py /path/to/file.cht")
        sys.exit(1)
    
    result = validate(sys.argv[1])
    sys.exit(0 if result else 1)