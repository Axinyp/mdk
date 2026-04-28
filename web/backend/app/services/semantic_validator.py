"""
LLM 输出语义验证层

在 Pydantic 结构校验之后执行，捕获 schema 无法检测的语义错误。
返回 list[ValidationIssue]。
severity="error" → 阻断（forbidden key 违规，说明 LLM 根本性误解函数签名）。
severity="warn"  → 非阻断（参数缺失或命名疑问，用户可在 UI 中补填）。
"""
import re
from dataclasses import dataclass
from typing import Literal

from loguru import logger

from ..schemas.gen import DeviceItem, FunctionItem, ParsedData


@dataclass
class ValidationIssue:
    severity: Literal["error", "warn"]
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.message}"

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


def validate_action_params(func: FunctionItem, devices: list[DeviceItem]) -> list[ValidationIssue]:
    """对单个 FunctionItem 跑契约校验。

    forbidden key 出现 → error（LLM 根本性误解函数签名，阻断）。
    required key 缺失 → warn（用户可在 ParamsForm 补填，非阻断）。
    dev 引用未声明   → warn（非阻断）。
    """
    issues: list[ValidationIssue] = []
    action = (func.action or "").upper()
    if not action or action in ("TBD", "TEMPLATE"):
        return issues
    contract = ACTION_PARAMS_CONTRACT.get(action)
    if not contract:
        issues.append(ValidationIssue("warn", f"功能 '{func.name}': action '{action}' 不在 Tier 1 契约表，无法校验参数"))
        return issues
    params = func.params or {}
    for key in contract.get("required", []):
        if key not in params or params[key] in (None, ""):
            issues.append(ValidationIssue("warn", f"功能 '{func.name}' ({action}): 缺少必填参数 '{key}'"))
    for key in contract.get("forbidden", []):
        if key in params:
            issues.append(ValidationIssue(
                "error",
                f"功能 '{func.name}' ({action}): 不应包含参数 '{key}'"
                f"（{action} 只接受 {contract.get('required')}）",
            ))
    if "dev" in contract.get("required", []):
        dev_name = params.get("dev")
        device_names = {d.name for d in devices}
        if dev_name and dev_name not in device_names:
            issues.append(ValidationIssue("warn", f"功能 '{func.name}' ({action}): dev='{dev_name}' 未在 DEFINE_DEVICE 中声明"))
    return issues


def validate_parsed_data(data: ParsedData) -> list[ValidationIssue]:
    """对 LLM 解析结果进行语义检查 + 契约校验。

    返回 list[ValidationIssue]，调用方按 severity 决定阻断还是放行。
    """
    issues: list[ValidationIssue] = []

    # --- 设备声明检查 ---
    for dev in data.devices:
        _check_device(dev, issues)

    # --- 设备命名规则检查 ---
    _check_device_naming(data.devices, issues)

    # --- 重复设备名检查 ---
    names = [d.name for d in data.devices]
    seen: set[str] = set()
    for name in names:
        if name in seen:
            issues.append(ValidationIssue("warn", f"设备名重复: '{name}'"))
        seen.add(name)

    # --- 契约校验（Tier 1 action × params）---
    for fn in data.functions:
        issues.extend(validate_action_params(fn, data.devices))

    if issues:
        logger.warning("[SEMANTIC] ParsedData 语义问题 ({} 条): {}", len(issues), [str(i) for i in issues[:5]])

    return issues


def _check_device(dev: DeviceItem, issues: list[ValidationIssue]) -> None:
    dev_type = dev.type.upper() if dev.type else ""

    if dev_type in INVALID_DEVICE_TYPES:
        issues.append(ValidationIssue(
            "warn",
            f"设备 '{dev.name}' 使用了非法 CHT 类型 '{dev.type}' "
            f"(DSP/MATRIX/CAM 在 CHT 中没有对应元素类型，请检查协议类型)",
        ))
    elif dev_type and dev_type not in VALID_DEVICE_TYPES:
        issues.append(ValidationIssue(
            "warn",
            f"设备 '{dev.name}' 使用了未知类型 '{dev.type}'，"
            f"合法类型: {', '.join(sorted(VALID_DEVICE_TYPES))}",
        ))


def _check_device_naming(devices: list[DeviceItem], issues: list[ValidationIssue]) -> None:
    """启发式检查：名称后缀是否误用了板卡号（应为顺序序号）。"""
    type_groups: dict[str, list[DeviceItem]] = {}
    for dev in devices:
        key = dev.type.upper()
        type_groups.setdefault(key, []).append(dev)

    for _typ, group in type_groups.items():
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
            issues.append(ValidationIssue(
                "warn",
                f"设备命名疑似使用板卡号作为后缀 {mismatches}: "
                "后缀应为顺序序号 (IR1, IR2…)，实际板卡号写在 L:X 部分",
            ))
