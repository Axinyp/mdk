import asyncio
import re
import sys
import tempfile
from pathlib import Path

from ..config import settings

SCRIPTS_DIR = settings.core_dir / "scripts"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _clean(text: str) -> str:
    return ANSI_RE.sub("", text)


async def _run_script(script_name: str, *args: str, timeout: int = 30) -> str:
    script = SCRIPTS_DIR / script_name
    if not script.exists():
        return f"[ERROR] Script not found: {script}"
    process = await asyncio.create_subprocess_exec(
        sys.executable, str(script), *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(settings.core_dir.parent),
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        return "[ERROR] Script timed out"
    out = stdout.decode("utf-8", errors="replace")
    err = stderr.decode("utf-8", errors="replace")
    return _clean(out + ("\n" + err if err else ""))


def _parse_report(output: str) -> dict:
    critical = len(re.findall(r"(?i)\bcritical\b", output))
    warning = len(re.findall(r"(?i)\bwarning\b", output))
    details = [line.strip() for line in output.splitlines() if line.strip()]
    return {"critical": critical, "warning": warning, "details": details[-50:]}


async def validate_cht_content(cht_content: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="mdk-val-") as tmp:
        path = Path(tmp) / "output.cht"
        path.write_text(cht_content, encoding="utf-8")
        output = await _run_script("validate.py", str(path))
    return _parse_report(output)


async def cross_validate_content(xml_content: str, cht_content: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="mdk-xval-") as tmp:
        xml_path = Path(tmp) / "Project.xml"
        cht_path = Path(tmp) / "output.cht"
        xml_path.write_text(xml_content, encoding="utf-8")
        cht_path.write_text(cht_content, encoding="utf-8")
        output = await _run_script("cross_validate.py", str(xml_path), str(cht_path))
    return _parse_report(output)


async def run_full_validation(xml_content: str, cht_content: str) -> dict:
    cht_report = await validate_cht_content(cht_content)
    cross_report = await cross_validate_content(xml_content, cht_content)
    return {
        "cht_syntax": cht_report,
        "cross_check": cross_report,
        "summary": {
            "critical": cht_report["critical"] + cross_report["critical"],
            "warning": cht_report["warning"] + cross_report["warning"],
        },
    }
