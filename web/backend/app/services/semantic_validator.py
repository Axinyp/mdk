"""
LLM 输出语义验证层

在 Pydantic 结构校验之后执行，捕获 schema 无法检测的语义错误。
返回 list[str]，非空表示有问题需要修正或记录告警。
[warn] 前缀 = 非阻断警告；无前缀 = critical 阻断（forbidden key 违规）。
"""
import re

from loguru import logger

from ..schemas.gen import DeviceItem, FunctionItem, ParsedData

# ── action × params 契约表（Tier 1 核心 28）─────────────────────────────────
# required: 必须存在且非空；forbidden: 不允许出现（structural error）
ACTION_PARAMS_CONTRACT: dict[str, dict] = {
    "ON_RELAY":          {"required": ["dev", "channel"]},
    "OFF_RELAY":         {"required": ["dev", "channel"]},
    "SEND_COM":          {"required": ["dev", "channel", "str"]},
    "SEND_IRCODE":       {"required": ["dev", "channel", "str"]},
    "SEND_LITE":         {"required": ["dev", "channel", "val"]},
    "SEND_IO":           {"required": ["dev", "channel", "vol"]},
    "SEND_TCP":          {"required": ["ip", "port", "str"], "forbidden": ["dev", "channel"]},
    "SEND_UDP":          {"required": ["ip", "port", "str"], "forbidden": ["dev", "channel"]},
    "WAKEUP_ONLAN":      {"required": ["MAC"]},
    "SEND_M2M_DATA":     {"required": ["ip", "data"]},
    "SEND_M2M_JNPUSH":   {"required": ["ip", "jNumber"]},
    "SEND_M2M_JNRELEASE":{"required": ["ip", "jNumber"]},
    "SEND_M2M_LEVEL":    {"required": ["ip", "jNumber", "val"]},
    "SET_BUTTON":        {"required": ["dev", "channel", "state"]},
    "SET_LEVEL":         {"required": ["dev", "channel", "val"]},
    "SEND_TEXT":         {"required": ["dev", "channel", "text"]},
    "SEND_PAGING":       {"required": ["dev", "channel", "text"]},
    "SEND_PICTURE":      {"required": ["dev", "channel", "picIndex"]},
    "SET_VOL_M":         {"required": ["channel", "mute", "vol"], "forbidden": ["dev"]},
    "SET_MATRIX_M":      {"required": ["out", "in"], "forbidden": ["dev"]},
    "SLEEP":             {"required": ["time"]},
    "START_TIMER":       {"required": ["name", "time"]},
    "CANCEL_TIMER":      {"required": ["name"]},
    "CANCEL_WAIT":       {"required": ["name"]},
    "SET_COM":           {"required": ["dev", "channel", "sband", "databit", "jo", "stopbit", "dataStream", "comType"]},
    "SET_IO_DIR":        {"required": ["dev", "channel", "dir", "pullordown"]},
    "TRACE":             {"required": ["msg"]},
}

# CHT 合法设备类型（与 validate.py 保持一致）
VALID_DEVICE_TYPES = {"RELAY", "COM", "TP", "IR", "IO", "LITE", "VOL", "WM", "DMX512"}

# 不应出现在 ParsedData.devices 中的非法类型（LLM 幻觉常见来源）
INVALID_DEVICE_TYPES = {"DSP", "MATRIX", "CAM", "CAMERA", "AUDIO", "VIDEO"}


def validate_action_params(func: FunctionItem, devices: list[DeviceItem]) -> list[str]:
    """对单个 FunctionItem 跑契约校验。返回问题列表（空表示通过）。

    [warn] 前缀 = 非阻断（required 缺失，用户可在 ParamsForm 补填）。
    无前缀   = critical 阻断（forbidden key 出现，说明 LLM 根本性误解了函数签名）。
    """
    issues: list[str] = []
    action = (func.action or "").upper()
    if not action or action in ("TBD", "TEMPLATE"):
        return issues
    contract = ACTION_PARAMS_CONTRACT.get(action)
    if not contract:
        issues.append(f"[warn] 功能 '{func.name}': action '{action}' 不在 Tier 1 契约表，无法校验参数")
        return issues
    params = func.params or {}
    for key in contract.get("required", []):
        if key not in params or params[key] in (None, ""):
            issues.append(f"[warn] 功能 '{func.name}' ({action}): 缺少必填参数 '{key}'")
    for key in contract.get("forbidden", []):
        if key in params:
            issues.append(
                f"功能 '{func.name}' ({action}): 不应包含参数 '{key}'"
                f"（{action} 只接受 {contract.get('required')}）"
            )
    if "dev" in contract.get("required", []):
        dev_name = params.get("dev")
        device_names = {d.name for d in devices}
        if dev_name and dev_name not in device_names:
            issues.append(f"[warn] 功能 '{func.name}' ({action}): dev='{dev_name}' 未在 DEFINE_DEVICE 中声明")
    return issues


def validate_parsed_data(data: ParsedData) -> list[str]:
    """对 LLM 解析结果进行语义检查 + 契约校验。

    返回告警/错误列表，调用方决定是记录日志还是返回给用户。
    """
    issues: list[str] = []
    device_names = {d.name for d in data.devices}

    # --- 设备声明检查 ---
    for dev in data.devices:
        _check_device(dev, issues)

    # --- 设备命名规则检查 ---
    _check_device_naming(data.devices, issues)

    # --- 功能项 dev 引用一致性检查（通过 params.dev，兼容新 schema）---
    for fn in data.functions:
        dev_field = (fn.params or {}).get("dev", "")
        if dev_field and dev_field not in device_names:
            issues.append(
                f"功能 '{fn.name}' 引用了未在设备清单中声明的设备 '{dev_field}'"
            )

    # --- 重复设备名检查 ---
    names = [d.name for d in data.devices]
    seen: set[str] = set()
    for name in names:
        if name in seen:
            issues.append(f"设备名重复: '{name}'")
        seen.add(name)

    # --- 契约校验（Tier 1 action × params）---
    for fn in data.functions:
        issues.extend(validate_action_params(fn, data.devices))

    if issues:
        logger.warning("[SEMANTIC] ParsedData 语义问题 ({} 条): {}", len(issues), issues[:5])

    return issues


def _check_device(dev: DeviceItem, issues: list[str]) -> None:
    dev_type = dev.type.upper() if dev.type else ""

    if dev_type in INVALID_DEVICE_TYPES:
        issues.append(
            f"设备 '{dev.name}' 使用了非法 CHT 类型 '{dev.type}' "
            f"(DSP/MATRIX/CAM 在 CHT 中没有对应元素类型，请检查协议类型)"
        )
    elif dev_type and dev_type not in VALID_DEVICE_TYPES:
        issues.append(
            f"设备 '{dev.name}' 使用了未知类型 '{dev.type}'，"
            f"合法类型: {', '.join(sorted(VALID_DEVICE_TYPES))}"
        )


def _check_device_naming(devices: list[DeviceItem], issues: list[str]) -> None:
    """
    检查设备命名是否使用了板卡号作为后缀（常见 LLM 错误）。
    规则：名称末尾数字应为顺序序号（1、2、3…），而非实际 board 号。

    启发式判断：若多个同类型设备的名称后缀数字 == 对应 board 号，则告警。
    """
    type_groups: dict[str, list[DeviceItem]] = {}
    for dev in devices:
        key = dev.type.upper()
        type_groups.setdefault(key, []).append(dev)

    for typ, group in type_groups.items():
        if len(group) <= 1:
            continue
        mismatches = []
        for i, dev in enumerate(group, start=1):
            m = re.search(r'(\d+)$', dev.name)
            if m:
                name_suffix = int(m.group(1))
                if name_suffix == dev.board and name_suffix != i:
                    mismatches.append(dev.name)
        if mismatches:
            issues.append(
                f"设备命名疑似使用板卡号作为后缀 {mismatches}: "
                "后缀应为顺序序号 (IR1, IR2…)，实际板卡号写在 L:X 部分"
            )
