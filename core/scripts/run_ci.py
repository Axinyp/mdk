#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库 CI 测试套件运行器

用法: python run_ci.py [test-dir]

规则:
  - 文件名不含 "neg-" → 正向测试，validate.py 必须返回 0 错误
  - 文件名含 "neg-" → 反向测试，validate.py 必须返回 >=1 错误，
    且文件首行注释须标注期望错误关键词: # EXPECT: <关键词>
"""
import os
import re
import sys
import subprocess
from pathlib import Path

if sys.platform == "win32":
    os.system("")
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

ROOT = Path(__file__).parent
TEST_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "tests" / "ci"
VALIDATE = ROOT / "validate.py"

GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub('', text)


def get_expect_keyword(filepath: Path) -> str | None:
    """从文件首行注释提取期望错误关键词: # EXPECT: <keyword>"""
    with open(filepath, encoding='utf-8', errors='replace') as f:
        first_line = f.readline().strip()
    m = re.match(r'#\s*EXPECT\s*:\s*(.+)', first_line)
    return m.group(1).strip() if m else None


def run_test(filepath: Path) -> tuple[bool, str]:
    """运行单个测试，返回 (passed, reason)"""
    is_negative = 'neg-' in filepath.stem
    result = subprocess.run(
        [sys.executable, str(VALIDATE), str(filepath)],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    output = strip_ansi((result.stdout or '') + (result.stderr or ''))
    m = re.search(r'错误:\s*(\d+)', output)
    error_count = int(m.group(1)) if m else 0

    if is_negative:
        if error_count == 0:
            return False, f"反向测试未触发错误 (期望 >=1 个错误)"
        keyword = get_expect_keyword(filepath)
        if keyword and keyword not in output:
            return False, f"错误已触发但未匹配期望关键词: '{keyword}'"
        return True, f"正确检测到 {error_count} 个错误"
    else:
        if error_count > 0:
            lines = [l for l in output.splitlines() if '✗' in l]
            detail = '; '.join(lines[:3])
            return False, f"正向测试有 {error_count} 个错误: {detail}"
        return True, "0 错误通过"


def main():
    if not TEST_DIR.exists():
        print(f"{RED}测试目录不存在: {TEST_DIR}{NC}")
        sys.exit(1)

    test_files = sorted(TEST_DIR.glob("*.test.cht"))
    if not test_files:
        print(f"{YELLOW}未找到 *.test.cht 文件于: {TEST_DIR}{NC}")
        sys.exit(0)

    print(f"\n{BLUE}══════════════════════════════════════════════{NC}")
    print(f"{BLUE}  MKControl CHT 知识库 CI 测试套件{NC}")
    print(f"{BLUE}══════════════════════════════════════════════{NC}")
    print(f"测试目录: {TEST_DIR}")
    print(f"测试文件: {len(test_files)} 个\n")

    passed = 0
    failed = 0
    for f in test_files:
        kind = f"{YELLOW}[反向]{NC}" if 'neg-' in f.stem else f"{BLUE}[正向]{NC}"
        ok, reason = run_test(f)
        if ok:
            passed += 1
            print(f"  {GREEN}✓{NC} {kind} {f.name} — {reason}")
        else:
            failed += 1
            print(f"  {RED}✗{NC} {kind} {f.name} — {reason}")

    print(f"\n{BLUE}══════════════════════════════════════════════{NC}")
    total = passed + failed
    if failed == 0:
        print(f"{GREEN}全部通过: {passed}/{total}{NC}")
    else:
        print(f"{RED}失败: {failed}/{total}{NC}  {GREEN}通过: {passed}/{total}{NC}")
    print(f"{BLUE}══════════════════════════════════════════════{NC}\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
