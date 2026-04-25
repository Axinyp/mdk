import asyncio
import logging
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)

SCRIPTS_DIR = settings.core_dir / "scripts"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _clean(text: str) -> str:
    return ANSI_RE.sub("", text)


def _run_script_sync(script_name: str, *args: str, timeout: int = 30) -> str:
    script = SCRIPTS_DIR / script_name
    if not script.exists():
        logger.error("[SCRIPT] 脚本不存在: %s", script)
        return f"[ERROR] Script not found: {script}"
    logger.info("[SCRIPT] 执行 %s %s", script_name, " ".join(args)[:80])
    t0 = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(settings.core_dir.parent),
        )
        elapsed = time.perf_counter() - t0
        out = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        cleaned = _clean(out)
        logger.info("[SCRIPT] %s 完成 ← %.1fs, exit=%d, output=%d chars",
                    script_name, elapsed, result.returncode, len(cleaned))
        if result.returncode != 0:
            logger.warning("[SCRIPT] %s 非零退出码=%d", script_name, result.returncode)
            logger.debug("[SCRIPT] stderr: %s", (result.stderr or "")[:500])
        return cleaned
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - t0
        logger.error("[SCRIPT] %s 超时 ← %.1fs (limit=%ds)", script_name, elapsed, timeout)
        return "[ERROR] Script timed out"


async def _run_script(script_name: str, *args: str, timeout: int = 30) -> str:
    return await asyncio.to_thread(_run_script_sync, script_name, *args, timeout=timeout)


def _parse_report(output: str) -> dict:
    # Try to parse the summary count lines first (e.g. "Critical (3 项)" or "Critical: 0 项")
    # Only count lines that indicate actual issues, not the "0 项" summary lines
    critical = 0
    warning = 0
    for line in output.splitlines():
        # Match "🔴 Critical (N 项)" — actual issues found
        m = re.search(r"Critical\s*\((\d+)\s*项\)", line)
        if m:
            critical += int(m.group(1))
            continue
        # Match "🟡 Warning (N 项)"
        m = re.search(r"Warning\s*\((\d+)\s*项\)", line)
        if m:
            warning += int(m.group(1))
            continue
        # Fallback: lines starting with "错误:" from validate.py
        m = re.search(r"错误:\s*(\d+)", line)
        if m:
            critical += int(m.group(1))
        m = re.search(r"警告:\s*(\d+)", line)
        if m:
            warning += int(m.group(1))
    details = [line.strip() for line in output.splitlines() if line.strip()]
    return {"critical": critical, "warning": warning, "details": details[-50:]}


async def validate_cht_content(cht_content: str) -> dict:
    logger.debug("[SCRIPT] CHT 语法校验, 内容长度=%d", len(cht_content))
    with tempfile.TemporaryDirectory(prefix="mdk-val-") as tmp:
        path = Path(tmp) / "output.cht"
        path.write_text(cht_content, encoding="utf-8")
        output = await _run_script("validate.py", str(path))
    report = _parse_report(output)
    logger.debug("[SCRIPT] CHT 校验结果 — critical=%d, warning=%d", report["critical"], report["warning"])
    return report


async def cross_validate_content(xml_content: str, cht_content: str) -> dict:
    logger.debug("[SCRIPT] 交叉校验, XML=%d chars, CHT=%d chars", len(xml_content), len(cht_content))
    with tempfile.TemporaryDirectory(prefix="mdk-xval-") as tmp:
        xml_path = Path(tmp) / "Project.xml"
        cht_path = Path(tmp) / "output.cht"
        xml_path.write_text(xml_content, encoding="utf-8")
        cht_path.write_text(cht_content, encoding="utf-8")
        output = await _run_script("cross_validate.py", str(xml_path), str(cht_path))
    report = _parse_report(output)
    logger.debug("[SCRIPT] 交叉校验结果 — critical=%d, warning=%d", report["critical"], report["warning"])
    return report


async def run_full_validation(xml_content: str, cht_content: str) -> dict:
    logger.info("[SCRIPT] 开始完整校验流程...")
    cht_report = await validate_cht_content(cht_content)
    cross_report = await cross_validate_content(xml_content, cht_content)
    summary = {
        "critical": cht_report["critical"] + cross_report["critical"],
        "warning": cht_report["warning"] + cross_report["warning"],
    }
    logger.info("[SCRIPT] 校验完成 — 总计 critical=%d, warning=%d", summary["critical"], summary["warning"])
    return {
        "cht_syntax": cht_report,
        "cross_check": cross_report,
        "summary": summary,
    }
