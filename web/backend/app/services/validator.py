import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from ..config import settings

SCRIPTS_DIR = settings.core_dir / "scripts"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _clean_output(text: str) -> str:
    return ANSI_RE.sub("", text)


def _run_script(script_name: str, *file_paths: str, timeout: int = 30) -> str:
    script = SCRIPTS_DIR / script_name
    if not script.exists():
        return f"[ERROR] Script not found: {script}"
    try:
        result = subprocess.run(
            [sys.executable, str(script), *file_paths],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout,
            cwd=str(settings.core_dir.parent),
        )
        return _clean_output((result.stdout or "") + ("\n" + result.stderr if result.stderr else ""))
    except subprocess.TimeoutExpired:
        return "[ERROR] Script timed out"
    except Exception as e:
        return f"[ERROR] {e}"


def validate_cht_content(cht_content: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="mdk-validate-") as tmp:
        path = Path(tmp) / "output.cht"
        path.write_text(cht_content, encoding="utf-8")
        output = _run_script("validate.py", str(path))
    return _parse_report(output)


def cross_validate_content(xml_content: str, cht_content: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="mdk-cross-") as tmp:
        xml_path = Path(tmp) / "Project.xml"
        cht_path = Path(tmp) / "output.cht"
        xml_path.write_text(xml_content, encoding="utf-8")
        cht_path.write_text(cht_content, encoding="utf-8")
        output = _run_script("cross_validate.py", str(xml_path), str(cht_path))
    return _parse_report(output)


def _parse_report(output: str) -> dict:
    critical = len(re.findall(r"(?i)\bcritical\b", output))
    warning = len(re.findall(r"(?i)\bwarning\b", output))
    details = [line.strip() for line in output.splitlines() if line.strip()]
    return {
        "critical": critical,
        "warning": warning,
        "details": details[-50:],
    }


def run_full_validation(xml_content: str, cht_content: str) -> dict:
    cht_report = validate_cht_content(cht_content)
    cross_report = cross_validate_content(xml_content, cht_content)
    return {
        "cht_syntax": cht_report,
        "cross_check": cross_report,
        "summary": {
            "critical": cht_report["critical"] + cross_report["critical"],
            "warning": cht_report["warning"] + cross_report["warning"],
        },
    }
