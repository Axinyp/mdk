"""集中式日志配置（基于 loguru）。

职责：
- 全链路 trace_id 传播（loguru contextualize，async 调用链自动继承）
- 控制台彩色输出 + 文件按日轮转（utf-8）
- 文件 sink 每条日志 open/write/close，避免在 Windows 上持续独占文件句柄
- 拦截 stdlib logging（uvicorn / sqlalchemy / litellm 等转发到 loguru）
- 第三方库降噪
"""

from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from loguru import logger

# 直接用 ANSI 转义码而非 loguru 颜色标签：loguru 只解析 format 模板里的
# `<color>` 标签，不解析从 record 字段值（{extra[message_display]}）注入进来的
# 标签。早期版本写成 `<yellow>...</yellow>` 时，控制台会出现字面文本输出。
# `_USE_COLOR=False` 时（重定向/管道）`_colorize_tags` 不会被调用，因此管道
# 场景仍然干净；文件 sink 也强制 `colorize_tags=False`，与日志文件的 plain 格式一致。
_TAG_COLORS: dict[str, str] = {
    "[FLOW]":      "\x1b[34;1m[FLOW]\x1b[22;39m",      # blue + bold
    "[DB]":        "\x1b[35m[DB]\x1b[39m",             # magenta
    "[LLM]":       "\x1b[33;1m[LLM]\x1b[22;39m",       # yellow + bold
    "[PROMPT]":    "\x1b[36m[PROMPT]\x1b[39m",         # cyan
    "[KNOWLEDGE]": "\x1b[32m[KNOWLEDGE]\x1b[39m",      # green
    "[SCRIPT]":    "\x1b[37;1m[SCRIPT]\x1b[22;39m",    # white + bold
    "[ROUTE]":     "\x1b[32;1m[ROUTE]\x1b[22;39m",     # green + bold
    "[HTTP]":      "\x1b[34m[HTTP]\x1b[39m",           # blue
    "[SEMANTIC]":  "\x1b[35;1m[SEMANTIC]\x1b[22;39m",  # magenta + bold
    "[PROTOCOL]":  "\x1b[36;1m[PROTOCOL]\x1b[22;39m",  # cyan + bold
}

_NOISY_LOGGERS = (
    "httpx", "httpcore", "urllib3", "asyncio",
    "watchfiles", "LiteLLM", "litellm",
    "sqlalchemy.engine", "aiosqlite",
)


def _pad(value: object, width: int) -> str:
    return str(value or "-")[:width].ljust(width)


def _colorize_tags(message: str) -> str:
    for tag, markup in _TAG_COLORS.items():
        message = message.replace(tag, markup)
    return message


def _prepare_record(record: dict, *, colorize_tags: bool) -> None:
    extra = record["extra"]
    extra["trace_display"]   = _pad(extra.get("trace_id", "-"), 8)
    extra["logger_display"]  = _pad(extra.get("logger_name") or record["name"], 22)
    extra["level_display"]   = record["level"].name.ljust(7)
    extra["message_display"] = _colorize_tags(record["message"]) if colorize_tags else record["message"]


_USE_COLOR = False


def _console_format(record: dict) -> str:
    _prepare_record(record, colorize_tags=_USE_COLOR)
    if _USE_COLOR:
        return (
            "<dim>{time:HH:mm:ss}</dim> "
            "<level>{extra[level_display]}</level> "
            "<dim>[{extra[trace_display]}]</dim> "
            "<dim>[{extra[logger_display]}]</dim> "
            "{extra[message_display]}\n"
            "{exception}"
        )
    return (
        "{time:HH:mm:ss} "
        "{extra[level_display]} "
        "[{extra[trace_display]}] "
        "[{extra[logger_display]}] "
        "{extra[message_display]}\n"
        "{exception}"
    )


def _file_format(record: dict) -> str:
    _prepare_record(record, colorize_tags=False)
    return (
        "{time:HH:mm:ss} "
        "{extra[level_display]} "
        "[{extra[trace_display]}] "
        "[{extra[logger_display]}] "
        "{extra[message_display]}\n"
        "{exception}"
    )


class _NonLockingDailyFileSink:
    """File sink that re-opens the log file for every record.

    Loguru's default file handler keeps an OS handle open for the lifetime
    of the process; on Windows that prevents other tools from
    renaming/deleting the file while the server runs. We trade a small per-
    write cost for the ability to manage the file at any time.

    Rotation/retention is implemented inline: on each write, if the calendar
    date has rolled over, the current ``mdk.log`` is renamed to
    ``mdk-YYYY-MM-DD.log``; archive files older than ``retention_days``
    are deleted at startup and after each rotation.
    """

    def __init__(self, path: Path, retention_days: int = 7) -> None:
        self.path = path
        self.retention_days = retention_days
        self._current_date = self._today()
        self._purge_stale_archives()

    @staticmethod
    def _today() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _archive_pattern(self) -> str:
        return f"{self.path.stem}-*{self.path.suffix}"

    def _purge_stale_archives(self) -> None:
        if self.retention_days <= 0:
            return
        cutoff = time.time() - self.retention_days * 86400
        try:
            for p in self.path.parent.glob(self._archive_pattern()):
                try:
                    if p.stat().st_mtime < cutoff:
                        p.unlink()
                except OSError:
                    pass
        except OSError:
            pass

    def _maybe_rotate(self) -> None:
        today = self._today()
        if today == self._current_date:
            return
        if self.path.exists():
            archived = self.path.parent / f"{self.path.stem}-{self._current_date}{self.path.suffix}"
            try:
                self.path.replace(archived)
            except OSError:
                pass  # rotation best-effort; never block logging
        self._current_date = today
        self._purge_stale_archives()

    def __call__(self, message: object) -> None:
        try:
            self._maybe_rotate()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(str(message))
        except OSError:
            pass  # never let logging crash the app


class _InterceptHandler(logging.Handler):
    """将 stdlib logging 记录转发到 loguru。"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.bind(logger_name=record.name).opt(
            depth=depth,
            exception=record.exc_info,
        ).log(level, record.getMessage())


def _configure_stdlib_intercept(debug: bool, sql_echo: bool) -> None:
    root_level = logging.DEBUG if debug else logging.INFO

    logging.root.handlers = [_InterceptHandler()]
    logging.root.setLevel(root_level)
    logging.captureWarnings(True)

    manager = logging.root.manager
    for existing in list(manager.loggerDict.values()):
        if isinstance(existing, logging.Logger):
            existing.handlers.clear()
            existing.propagate = True

    for name in _NOISY_LOGGERS:
        std_logger = manager.getLogger(name)
        if name == "sqlalchemy.engine" and sql_echo:
            std_logger.setLevel(logging.INFO)
        else:
            std_logger.setLevel(logging.WARNING)


@contextmanager
def bound_trace_id(tid: str) -> Iterator[None]:
    """在协程作用域内绑定 trace_id 到 loguru extra 上下文。"""
    with logger.contextualize(trace_id=tid):
        yield


def setup(debug: bool, sql_echo: bool, log_dir: str = "logs") -> None:
    """初始化全局日志。在应用启动最早阶段调用一次。"""
    global _USE_COLOR

    _configure_stdlib_intercept(debug=debug, sql_echo=sql_echo)

    target_dir = Path(__file__).resolve().parent.parent / log_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    log_path = (target_dir / "mdk.log").resolve()

    logger.remove()
    logger.configure(extra={"trace_id": "-", "logger_name": None})

    level = "DEBUG" if debug else "INFO"
    use_color = (
        hasattr(sys.stderr, "isatty")
        and sys.stderr.isatty()
        and not os.environ.get("NO_COLOR")
    )
    _USE_COLOR = use_color

    logger.add(
        sys.stderr,
        level=level,
        colorize=use_color,
        backtrace=debug,
        diagnose=debug,
        format=_console_format,
    )
    logger.add(
        _NonLockingDailyFileSink(log_path, retention_days=7),
        level=level,
        colorize=False,
        enqueue=True,
        backtrace=debug,
        diagnose=debug,
        format=_file_format,
    )

    logger.bind(logger_name="app.log").info("[FLOW] 文件日志初始化完成: {}", log_path)
