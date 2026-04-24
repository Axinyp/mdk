import base64
import hashlib
import logging
import time
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
import litellm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.llm_config import LlmConfig

logger = logging.getLogger(__name__)


def _cipher() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.llm_encryption_key.encode()).digest())
    return Fernet(key)


def encrypt_api_key(value: str | None) -> str | None:
    if not value:
        return None
    return _cipher().encrypt(value.encode()).decode()


def decrypt_api_key(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _cipher().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError) as exc:
        raise ValueError("Stored API key could not be decrypted") from exc


async def get_default_config(db: AsyncSession) -> LlmConfig | None:
    result = await db.execute(
        select(LlmConfig).where(LlmConfig.is_default.is_(True), LlmConfig.is_active.is_(True))
    )
    config = result.scalar_one_or_none()
    if config:
        return config
    result = await db.execute(
        select(LlmConfig).where(LlmConfig.is_active.is_(True)).order_by(LlmConfig.id)
    )
    return result.scalars().first()


async def get_config_by_id(db: AsyncSession, config_id: int) -> LlmConfig | None:
    result = await db.execute(select(LlmConfig).where(LlmConfig.id == config_id))
    return result.scalar_one_or_none()


def _build_litellm_params(config: LlmConfig) -> dict[str, Any]:
    model = f"{config.provider}/{config.model}"
    params: dict[str, Any] = {"model": model}
    if config.api_base:
        params["api_base"] = config.api_base
    api_key = decrypt_api_key(config.api_key)
    if api_key:
        params["api_key"] = api_key
    return params


async def llm_chat(
    messages: list[dict],
    config: LlmConfig,
    stream: bool = True,
    temperature: float = 0.0,
    response_format: dict | None = None,
) -> Any:
    params = _build_litellm_params(config)
    params.update(messages=messages, stream=stream, temperature=temperature)
    if response_format:
        params["response_format"] = response_format

    total_chars = sum(len(m.get("content", "")) for m in messages)
    logger.info("[LLM] 调用 → model=%s, stream=%s", params["model"], stream)
    logger.debug("[LLM] 详情 → messages=%d, input~%d chars, temp=%.1f, response_format=%s",
                 len(messages), total_chars, temperature, response_format)
    t0 = time.perf_counter()
    try:
        result = await litellm.acompletion(**params)
        elapsed = time.perf_counter() - t0
        if not stream and result.choices:
            resp_len = len(result.choices[0].message.content or "")
            usage = getattr(result, "usage", None)
            if usage:
                logger.info("[LLM] 完成 ← %.1fs, %d tokens (prompt=%d, completion=%d)",
                            elapsed, usage.total_tokens, usage.prompt_tokens, usage.completion_tokens)
            else:
                logger.info("[LLM] 完成 ← %.1fs, response=%d chars", elapsed, resp_len)
            logger.debug("[LLM] 响应预览: %.200s", result.choices[0].message.content or "")
        else:
            logger.info("[LLM] stream 已打开 ← %.1fs", elapsed)
        return result
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        logger.error("[LLM] 失败 ← %.1fs: %s", elapsed, exc)
        logger.debug("[LLM] 错误堆栈:", exc_info=True)
        raise


async def test_connection(config: LlmConfig) -> tuple[bool, str]:
    try:
        response = await litellm.acompletion(
            **_build_litellm_params(config),
            messages=[{"role": "user", "content": "Say hello in one word."}],
            stream=False,
            temperature=0.0,
        )
        content = response.choices[0].message.content if response.choices else ""
        if not content:
            return False, "Connected but model returned empty response"
        return True, content[:200]
    except Exception as e:
        return False, f"Connection test failed: {e}"
