import json
import time
import uuid
from typing import Any

from loguru import logger as _root_logger
from starlette.types import ASGIApp, Receive, Scope, Send

from .log import bound_trace_id

logger = _root_logger.bind(logger_name="app.http")

_SILENT_PATHS = {"/api/health"}
_REDACT_KEYS = frozenset({"password", "api_key", "token", "secret", "key", "access_token"})
# Content-types whose response bodies we skip (streams / binary).
_SKIP_RESP_BODY = ("text/event-stream", "application/zip", "application/octet-stream")


def _redact(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: "[REDACTED]" if k.lower() in _REDACT_KEYS else _redact(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_redact(i) for i in data]
    return data


def _fmt_body(raw: bytes, content_type: str) -> str:
    """Render a request/response body for logging.

    JSON payloads go through ``_redact`` to strip secrets. Non-JSON falls
    back to lenient UTF-8 decoding so we never emit ``�`` for chunked
    multi-byte boundaries (callers always feed us a complete buffer).
    """
    if not raw:
        return ""
    if "json" in content_type:
        try:
            return json.dumps(_redact(json.loads(raw)), ensure_ascii=False, separators=(",", ":"))
        except (json.JSONDecodeError, ValueError):
            pass
    return raw.decode("utf-8", errors="replace")


def _get_header(headers: list[tuple[bytes, bytes]], name: bytes) -> str:
    for k, v in headers:
        if k.lower() == name:
            return v.decode("utf-8", errors="replace")
    return ""


async def _buffer_body(receive: Receive) -> tuple[bytes, Receive]:
    """Consume all request body chunks, then return a replay-able receive."""
    chunks: list[bytes] = []
    while True:
        msg = await receive()
        chunks.append(msg.get("body", b""))
        if not msg.get("more_body", False):
            break
    full = b"".join(chunks)
    replayed = False

    async def _replay() -> dict:
        nonlocal replayed
        if not replayed:
            replayed = True
            return {"type": "http.request", "body": full, "more_body": False}
        return await receive()  # downstream disconnect events

    return full, _replay


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method      = scope["method"]
        path        = scope["path"]
        qs          = scope.get("query_string", b"")
        client      = scope.get("client")
        client_host = client[0] if client else "-"
        silent      = path in _SILENT_PATHS
        t0          = time.perf_counter()
        trace_id    = uuid.uuid4().hex[:8]

        with bound_trace_id(trace_id):
            req_headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
            req_ct  = _get_header(req_headers, b"content-type")
            req_raw, patched_receive = await _buffer_body(receive)
            req_body_str = _fmt_body(req_raw, req_ct) if req_raw else ""

            if not silent:
                qs_str = ("?" + qs.decode("utf-8", errors="replace")) if qs else ""
                if req_body_str:
                    logger.info("→ {} {}{}  client={}  body={}", method, path, qs_str, client_host, req_body_str)
                else:
                    logger.info("→ {} {}{}  client={}", method, path, qs_str, client_host)

            status_holder: list[int] = []
            skip_resp_body = False
            resp_ct = ""
            resp_chunks: list[bytes] = []

            async def send_wrapper(message: dict) -> None:
                nonlocal skip_resp_body, resp_ct

                if message["type"] == "http.response.start":
                    status_holder.append(message["status"])
                    resp_headers = message.get("headers", [])
                    resp_ct = _get_header(resp_headers, b"content-type")
                    skip_resp_body = any(t in resp_ct for t in _SKIP_RESP_BODY)
                    # inject / de-dup x-trace-id
                    headers = [(k, v) for k, v in resp_headers if k.lower() != b"x-trace-id"]
                    headers.append((b"x-trace-id", trace_id.encode()))
                    message = {**message, "headers": headers}

                elif message["type"] == "http.response.body" and not skip_resp_body:
                    chunk = message.get("body", b"")
                    if chunk:
                        resp_chunks.append(chunk)

                await send(message)

            try:
                await self.app(scope, patched_receive, send_wrapper)
            except Exception as exc:
                elapsed = (time.perf_counter() - t0) * 1000
                logger.opt(exception=exc).error(
                    "✗ {} {}  {:.0f}ms  UNHANDLED {}: {}",
                    method, path, elapsed, type(exc).__name__, exc,
                )
                raise

            if not silent and status_holder:
                elapsed = (time.perf_counter() - t0) * 1000
                status  = status_holder[0]
                log_fn  = logger.warning if status >= 400 else logger.info
                if resp_chunks:
                    resp_body_str = _fmt_body(b"".join(resp_chunks), resp_ct)
                    log_fn("← {} {}  {}  {:.0f}ms  resp={}", method, path, status, elapsed, resp_body_str)
                else:
                    log_fn("← {} {}  {}  {:.0f}ms", method, path, status, elapsed)
