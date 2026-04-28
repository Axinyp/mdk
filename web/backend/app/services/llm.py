import asyncio
import base64
import hashlib
import random
import time
from typing import Any, Awaitable, Callable

import httpx
import litellm
from cryptography.fernet import Fernet, InvalidToken
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.llm_config import LlmConfig

_DEFAULT_TIMEOUT = 60.0
_MAX_RETRIES = 2
_RETRY_BASE_DELAY = 1.0

_TRANSIENT_ERROR_NAMES = {
    "RateLimitError", "APIConnectionError", "Timeout",
    "APITimeoutError", "InternalServerError", "ServiceUnavailableError",
}
_PERMANENT_ERROR_NAMES = {
    "AuthenticationError", "BadRequestError", "InvalidRequestError",
    "PermissionDeniedError", "NotFoundError",
}


def _is_transient(exc: Exception) -> bool:
    """Whether ``exc`` is worth retrying. Unknown classes default to non-transient."""
    if isinstance(exc, asyncio.TimeoutError):
        return True
    name = type(exc).__name__
    if name in _TRANSIENT_ERROR_NAMES:
        return True
    if name in _PERMANENT_ERROR_NAMES:
        return False
    return False


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
    timeout: float = _DEFAULT_TIMEOUT,
    max_attempts: int | None = None,
) -> Any:
    """Call litellm.acompletion with a per-attempt timeout and retry logic.

    Retries up to ``_MAX_RETRIES`` extra attempts on asyncio.TimeoutError
    and on classified transient upstream errors (rate limit, connection,
    service-unavailable). Streaming calls are NOT retried — once a stream
    is opened, side effects may have started, and replaying is unsafe.

    ``max_attempts`` overrides the default for slow/large-output calls
    (XML / CHT generation) where retrying a slow upstream is wasteful.
    """
    params = _build_litellm_params(config)
    params.update(messages=messages, stream=stream, temperature=temperature)
    if response_format:
        params["response_format"] = response_format

    total_chars = sum(len(m.get("content", "")) for m in messages)
    logger.info("[LLM] 调用 → model={}, stream={}, timeout={}s", params["model"], stream, timeout)
    logger.debug(
        "[LLM] 详情 → messages={}, input~{} chars, temp={:.1f}, response_format={}",
        len(messages), total_chars, temperature, response_format,
    )

    if max_attempts is None:
        max_attempts = 1 if stream else _MAX_RETRIES + 1
    else:
        max_attempts = max(1, max_attempts)
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        t0 = time.perf_counter()
        try:
            result = await asyncio.wait_for(litellm.acompletion(**params), timeout=timeout)
            elapsed = time.perf_counter() - t0
            if not stream and result.choices:
                resp_len = len(result.choices[0].message.content or "")
                usage = getattr(result, "usage", None)
                if usage:
                    logger.info(
                        "[LLM] 完成 ← {:.1f}s (attempt {}/{}), {} tokens (prompt={}, completion={})",
                        elapsed, attempt + 1, max_attempts,
                        usage.total_tokens, usage.prompt_tokens, usage.completion_tokens,
                    )
                else:
                    logger.info(
                        "[LLM] 完成 ← {:.1f}s (attempt {}/{}), response={} chars",
                        elapsed, attempt + 1, max_attempts, resp_len,
                    )
                logger.debug("[LLM] 响应预览: {}", (result.choices[0].message.content or "")[:200])
            else:
                logger.info("[LLM] stream 已打开 ← {:.1f}s (attempt {}/{})", elapsed, attempt + 1, max_attempts)
            return result

        except asyncio.TimeoutError as exc:
            elapsed = time.perf_counter() - t0
            last_exc = exc
            level = "暂态超时" if attempt < max_attempts - 1 else "超时（无重试）"
            logger.warning("[LLM] {} ← {:.1f}s (attempt {}/{})", level, elapsed, attempt + 1, max_attempts)

        except Exception as exc:
            elapsed = time.perf_counter() - t0
            last_exc = exc
            if stream or not _is_transient(exc):
                logger.opt(exception=exc).error(
                    "[LLM] 不可重试错误 ← {:.1f}s ({}): {}",
                    elapsed, type(exc).__name__, exc,
                )
                raise
            label = "暂态错误" if attempt < max_attempts - 1 else "暂态错误（无重试）"
            logger.warning(
                "[LLM] {} ← {:.1f}s (attempt {}/{}): {}",
                label, elapsed, attempt + 1, max_attempts, type(exc).__name__,
            )

        if attempt < max_attempts - 1:
            delay = _RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 0.5)
            await asyncio.sleep(delay)

    logger.error("[LLM] 所有重试均失败 ({} 次): {}", max_attempts, last_exc)
    assert last_exc is not None  # loop exits only after at least one exception
    raise last_exc


async def test_connection(config: LlmConfig) -> tuple[bool, str]:
    """Probe the configured model with a short message.

    Per-attempt timeout is 10s; a hard outer timeout of 20s caps the total
    duration regardless of retry count so the UI is not blocked for long.
    """
    try:
        response = await asyncio.wait_for(
            llm_chat(
                messages=[{"role": "user", "content": "Say hello in one word."}],
                config=config,
                stream=False,
                temperature=0.0,
                timeout=10.0,
            ),
            timeout=20.0,
        )
        content = response.choices[0].message.content if response.choices else ""
        if not content:
            return False, "Connected but model returned empty response"
        return True, content[:200]
    except asyncio.TimeoutError:
        return False, "Connection test timed out (20s)"
    except Exception as e:
        return False, f"Connection test failed: {e}"


# ── Model listing (per-provider registry) ──────────────────────────────────────
#
# Each provider exposes its catalogue at a different path / shape. The OpenAI
# spec (`GET /v1/models` → `{data: [{id}]}`) is the de-facto standard so it's
# the default fallback for unknown providers. To support a new provider, write
# an async fn `(api_base, api_key) -> list[str]` and decorate it with
# ``@register_model_fetcher("provider_name")`` — the rest of the stack picks
# it up automatically.

_MODEL_LIST_TIMEOUT = 10.0
ModelFetcher = Callable[[str | None, str | None], Awaitable[list[str]]]
_MODEL_FETCHERS: dict[str, ModelFetcher] = {}


def register_model_fetcher(provider: str):
    def decorator(fn: ModelFetcher) -> ModelFetcher:
        _MODEL_FETCHERS[provider] = fn
        return fn
    return decorator


def _normalise_openai_base(api_base: str | None) -> str:
    """Most OpenAI-compatible APIs accept either ``https://x`` or ``https://x/v1``
    as ``api_base``. Normalise to the absolute models endpoint."""
    base = (api_base or "https://api.openai.com").rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/models"
    return f"{base}/v1/models"


@register_model_fetcher("openai")
async def _fetch_openai_compatible(api_base: str | None, api_key: str | None) -> list[str]:
    """Standard OpenAI-style catalogue; covers DeepSeek, Qwen DashScope-compat,
    Moonshot, OpenRouter, vLLM, LM Studio, etc.
    """
    url = _normalise_openai_base(api_base)
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    async with httpx.AsyncClient(timeout=_MODEL_LIST_TIMEOUT) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        payload = resp.json()
    items = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        # Some clones return {"models":[...]} or a bare list
        items = payload.get("models") if isinstance(payload, dict) else payload
    ids: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            mid = item.get("id") or item.get("name") or item.get("model")
            if isinstance(mid, str):
                ids.append(mid)
        elif isinstance(item, str):
            ids.append(item)
    return sorted(set(ids))


@register_model_fetcher("ollama")
async def _fetch_ollama(api_base: str | None, _api_key: str | None) -> list[str]:
    """Ollama's local catalogue: ``GET {base}/api/tags`` → ``{models:[{name}]}``."""
    base = (api_base or "http://localhost:11434").rstrip("/")
    url = f"{base}/api/tags"
    async with httpx.AsyncClient(timeout=_MODEL_LIST_TIMEOUT) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        payload = resp.json()
    return sorted({m["name"] for m in payload.get("models", []) if isinstance(m, dict) and "name" in m})


_ANTHROPIC_FALLBACK = [
    # Curated current-gen lineup. Anthropic only published a public list-models
    # endpoint in late 2024 and not all keys are entitled to it; this fallback
    # keeps the UI useful when the call 401s.
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-3-7-sonnet-latest",
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-latest",
]


@register_model_fetcher("anthropic")
async def _fetch_anthropic(api_base: str | None, api_key: str | None) -> list[str]:
    base = (api_base or "https://api.anthropic.com").rstrip("/")
    url = f"{base}/v1/models"
    headers = {
        "anthropic-version": "2023-06-01",
        "x-api-key": api_key or "",
    }
    try:
        async with httpx.AsyncClient(timeout=_MODEL_LIST_TIMEOUT) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
        items = payload.get("data") or []
        ids = [item["id"] for item in items if isinstance(item, dict) and "id" in item]
        if ids:
            return sorted(ids)
    except Exception as exc:
        logger.debug("[LLM] anthropic list-models endpoint unreachable, using fallback: {}", exc)
    return list(_ANTHROPIC_FALLBACK)


async def list_available_models(config: LlmConfig) -> list[str]:
    """Fetch available model IDs from the provider's listing endpoint.

    Routes by ``config.provider``; unknown providers fall back to the
    OpenAI-compatible fetcher (most third-party clones speak the OpenAI spec).
    The stored API key is decrypted only inside this function.

    Raises whatever the underlying fetcher raises (httpx.HTTPStatusError /
    httpx.ConnectError / etc.) so the caller can surface a useful message.
    """
    fetcher = _MODEL_FETCHERS.get(config.provider) or _MODEL_FETCHERS["openai"]
    api_key = decrypt_api_key(config.api_key)
    return await fetcher(config.api_base, api_key)


def supported_model_list_providers() -> list[str]:
    """Provider names that have a dedicated fetcher registered."""
    return sorted(_MODEL_FETCHERS.keys())
