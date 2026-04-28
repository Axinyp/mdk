"""Tests for knowledge.py startup cache behaviour."""

from pathlib import Path
from unittest.mock import patch

from app.services import knowledge

_EXPECTED_PRELOAD_PATHS = {
    knowledge.PROTOCOLS_DIR / "_index.md",
    knowledge.REFERENCES_DIR / "core" / "syntax-rules.md",
    knowledge.PATTERNS_DIR / "_index.md",
    knowledge.WIDGETS_DIR / "_index.md",
    knowledge.BLOCKS_DIR / "DEFINE_DEVICE.md",
    knowledge.BLOCKS_DIR / "DEFINE_EVENT.md",
    knowledge.BLOCKS_DIR / "DEFINE_START.md",
    knowledge.TEMPLATES_DIR / "cht" / "simple-program.cht.tpl",
}


def setup_function():
    knowledge._read.cache_clear()


def test_preload_reads_all_expected_paths() -> None:
    with patch.object(Path, "read_text", autospec=True, return_value="content") as mock_read:
        knowledge.preload()

    actual = {call.args[0] for call in mock_read.call_args_list}
    assert actual == _EXPECTED_PRELOAD_PATHS


def test_preload_second_call_uses_cache() -> None:
    with patch.object(Path, "read_text", autospec=True, return_value="content") as mock_read:
        knowledge.preload()
        after_first = mock_read.call_count
        knowledge.preload()

    assert after_first == len(_EXPECTED_PRELOAD_PATHS)
    assert mock_read.call_count == after_first  # no extra reads on second call


def test_preload_warns_on_empty_critical_assets() -> None:
    from loguru import logger

    captured: list[str] = []
    handler_id = logger.add(lambda m: captured.append(m.record["message"]), level="WARNING")
    try:
        with patch.object(Path, "read_text", autospec=True, return_value=""):
            knowledge.preload()
    finally:
        logger.remove(handler_id)

    warned = [m for m in captured if "关键资产为空" in m]
    assert len(warned) == len(knowledge._CRITICAL_ASSETS)
