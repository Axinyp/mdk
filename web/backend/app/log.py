"""
集中式日志配置模块。

职责：
- 统一日志格式与级别控制
- 控制台彩色输出（按操作类型 + 日志级别着色）
- 第三方库降噪

操作类型标签：
  [FLOW]      流程控制 / 阶段里程碑
  [DB]        数据库读写
  [LLM]       大模型调用
  [PROMPT]    Prompt 构建
  [KNOWLEDGE] 知识库加载
  [SCRIPT]    外部脚本执行
"""

import logging
import os
import re
import sys

# ── ANSI 颜色码 ─────────────────────────────────────

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "\033[36m",      # cyan
    logging.INFO: "\033[32m",       # green
    logging.WARNING: "\033[33m",    # yellow
    logging.ERROR: "\033[31m",      # red
    logging.CRITICAL: "\033[35;1m", # magenta bold
}

_TAG_COLORS: dict[str, str] = {
    "[FLOW]":      "\033[34;1m",  # blue bold
    "[DB]":        "\033[35m",    # magenta
    "[LLM]":       "\033[33;1m",  # yellow bold
    "[PROMPT]":    "\033[36m",    # cyan
    "[KNOWLEDGE]": "\033[32m",    # green
    "[SCRIPT]":    "\033[37;1m",  # white bold
}

_TAG_RE = re.compile(r"(\[(?:FLOW|DB|LLM|PROMPT|KNOWLEDGE|SCRIPT)\])")


def _enable_win_ansi():
    """Windows 10+ 启用虚拟终端 ANSI 转义支持。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandleFunction(-11) if hasattr(kernel32, "GetStdHandleFunction") else kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


# ── 自定义 Formatter ────────────────────────────────

class ColorFormatter(logging.Formatter):
    """
    为控制台输出添加颜色：
    - 时间戳灰色
    - 日志级别按 DEBUG/INFO/WARNING/ERROR 着色
    - 操作类型标签 [FLOW]/[DB]/[LLM] 等独立着色
    - 模块名暗色
    """

    def __init__(self, use_color: bool = True):
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        ts = self.formatTime(record, "%H:%M:%S")
        level = record.levelname.ljust(7)
        name = record.name
        msg = record.getMessage()

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)

        if not self.use_color:
            line = f"{ts} {level} [{name}] {msg}"
            if record.exc_text:
                line += "\n" + record.exc_text
            return line

        lc = _LEVEL_COLORS.get(record.levelno, "")
        colored_msg = _TAG_RE.sub(lambda m: _TAG_COLORS.get(m.group(1), "") + m.group(1) + _RESET, msg)

        line = (
            f"{_DIM}{ts}{_RESET} "
            f"{lc}{_BOLD}{level}{_RESET} "
            f"{_DIM}[{name}]{_RESET} "
            f"{colored_msg}"
        )
        if record.exc_text:
            line += "\n" + f"{_LEVEL_COLORS[logging.ERROR]}{record.exc_text}{_RESET}"
        return line


# ── 第三方库降噪列表 ────────────────────────────────

_NOISY_LOGGERS = (
    "httpx", "httpcore", "urllib3", "asyncio",
    "watchfiles", "LiteLLM", "litellm",
    "sqlalchemy.engine", "aiosqlite",
)


# ── 初始化入口 ──────────────────────────────────────

def setup(debug: bool = False):
    """
    初始化全局日志。应在应用启动最早阶段调用一次。

    参数：
        debug: True 则输出 DEBUG 级别，False 输出 INFO 级别
    """
    _enable_win_ansi()

    use_color = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()
    if os.environ.get("NO_COLOR"):
        use_color = False

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(ColorFormatter(use_color=use_color))
        root.addHandler(handler)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
