import os
import re
import secrets
import string
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import select, text, update

from . import log
from .config import settings as _settings
from .database import async_session, engine
from .models import Protocol, Setting, User
from .models.llm_config import LlmConfig
from .models.session import GenSession
from .services.auth import hash_password
from .services.exceptions import DomainError
from .services.knowledge import list_protocol_files, preload as preload_knowledge
from .services.llm import decrypt_api_key
from .services.session_state import SessionStatus

_BOOTSTRAP_ALPHABET = string.ascii_letters + string.digits


def _generate_bootstrap_password(length: int = 16) -> str:
    return "".join(secrets.choice(_BOOTSTRAP_ALPHABET) for _ in range(length))


async def seed_admin(session) -> None:
    """No admin exists → provision one with a random temp password and surface it once."""
    result = await session.execute(select(User).where(User.role == "admin").limit(1))
    if result.scalars().first():
        return

    password = _generate_bootstrap_password()
    session.add(User(
        username="admin",
        password=hash_password(password),
        role="admin",
        must_change_password=True,
    ))
    await session.commit()

    banner = "═" * 72
    logger.warning(
        "{}\n[FLOW] Bootstrap admin provisioned — username=admin password={}\n"
        "[FLOW] This password is shown ONCE; record it now.\n{}",
        banner, password, banner,
    )

    password_path = Path("data") / ".bootstrap_admin_password"
    try:
        password_path.parent.mkdir(parents=True, exist_ok=True)
        password_path.write_text(f"username=admin\npassword={password}\n", encoding="utf-8")
        try:
            os.chmod(password_path, 0o600)
        except OSError:
            pass
    except OSError as exc:
        logger.warning("[FLOW] Failed to persist bootstrap password to {}: {}", password_path, exc)


async def seed_settings(session) -> None:
    defaults = [
        ("default_resolution", "2560x1600", "默认触摸屏分辨率"),
        ("xml_version", "4.1.9", "Project.xml 版本号"),
    ]
    for key, value, desc in defaults:
        existing = await session.get(Setting, key)
        if not existing:
            session.add(Setting(key=key, value=value, description=desc))
    await session.commit()


async def purge_undecryptable_api_keys(session) -> None:
    """Clear any LLM ``api_key`` ciphertext that the current encryption key
    cannot decrypt.

    Happens when the encryption key changes between runs (e.g. dev env
    without persistent ``MDK_LLM_ENCRYPTION_KEY``). Leaving stale ciphertext
    in place causes every chat call to fail with ``InvalidToken``; we'd
    rather force the admin to re-enter the key from the UI.
    """
    result = await session.execute(select(LlmConfig).where(LlmConfig.api_key.is_not(None)))
    configs = result.scalars().all()
    cleared: list[str] = []
    for cfg in configs:
        try:
            decrypt_api_key(cfg.api_key)
        except ValueError:
            cfg.api_key = None
            cleared.append(cfg.name)
    if cleared:
        await session.commit()
        logger.warning(
            "[FLOW] Cleared undecryptable LLM api_key for {} config(s): {} — please re-enter from admin UI",
            len(cleared), ", ".join(cleared),
        )


async def normalize_legacy_clarifying(session) -> None:
    """Promote any leftover ``clarifying`` sessions to ``parsed``.

    The clarifying multi-turn flow was retired; existing rows in that state
    can no longer make progress through the new UI, so we coerce them to
    ``parsed`` (which the frontend can resume normally).
    """
    result = await session.execute(
        update(GenSession)
        .where(GenSession.status == SessionStatus.CLARIFYING.value)
        .values(status=SessionStatus.PARSED.value)
    )
    if result.rowcount:
        await session.commit()
        logger.info("[FLOW] Promoted {} legacy clarifying sessions to parsed", result.rowcount)


async def sync_protocols(session) -> None:
    for proto_data in list_protocol_files():
        result = await session.execute(
            select(Protocol).where(Protocol.filename == proto_data["filename"])
        )
        if result.scalar_one_or_none():
            continue
        content = proto_data["content"]
        comm_match = re.search(r"通信方式[：:]\s*(.+)", content)
        comm_type = comm_match.group(1).strip() if comm_match else "unknown"
        session.add(Protocol(
            category=proto_data["category"],
            brand_model=proto_data["brand_model"],
            comm_type=comm_type,
            filename=proto_data["filename"],
            content=content,
        ))
    await session.commit()


class SchemaError(RuntimeError):
    """Raised when DB schema does not match Alembic head — startup should abort."""


async def check_database_revision() -> None:
    """Verify the DB schema matches Alembic head; raise SchemaError to abort startup."""
    config_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    try:
        alembic_cfg = Config(str(config_path))
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        expected_head = script_dir.get_current_head()
    except Exception as exc:
        logger.opt(exception=exc).error("[FLOW] Unable to load Alembic metadata from {}", config_path)
        raise

    from sqlalchemy.exc import OperationalError

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            current_revision = result.scalar_one_or_none()
    except OperationalError as exc:
        msg = str(exc).lower()
        if "no such table" in msg or "does not exist" in msg:
            logger.error("[FLOW] Database not initialized. Run: alembic upgrade head")
            raise SchemaError("alembic_version table missing; run `alembic upgrade head`") from exc
        logger.opt(exception=exc).error("[FLOW] Alembic version probe failed (DB connection issue)")
        raise

    if current_revision != expected_head:
        logger.error(
            "[FLOW] Schema revision mismatch: current={} expected={}. Run `alembic upgrade head`.",
            current_revision or "-", expected_head or "-",
        )
        raise SchemaError(
            f"Schema revision mismatch (current={current_revision}, expected={expected_head})"
        )

    logger.info("[FLOW] Alembic schema revision ok: {}", current_revision)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.setup(debug=_settings.debug, sql_echo=_settings.sql_echo)

    Path("data").mkdir(exist_ok=True)
    await check_database_revision()

    async with async_session() as session:
        await seed_admin(session)
        await seed_settings(session)
        await sync_protocols(session)
        await normalize_legacy_clarifying(session)
        await purge_undecryptable_api_keys(session)
    preload_knowledge()
    yield
    await engine.dispose()


app = FastAPI(title=_settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .middleware import RequestLoggingMiddleware
from .routers import admin, auth, gen, protocols, ref

app.add_middleware(RequestLoggingMiddleware)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(gen.router)
app.include_router(protocols.router)
app.include_router(ref.router)


@app.exception_handler(DomainError)
async def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Translate DomainError subclasses into stable JSON envelopes.

    Severity follows HTTP semantics: 4xx is normal client signalling and
    logs at INFO; 5xx indicates an upstream/infra failure and logs at
    WARNING so it surfaces in alerting.
    """
    log = logger.info if exc.status_code < 500 else logger.warning
    log(
        "[DOMAIN] {} ({}) on {} {}: {}",
        exc.__class__.__name__, exc.code, request.method, request.url.path, exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch anything not handled by HTTPException / DomainError; log full traceback with trace_id."""
    logger.opt(exception=exc).error(
        "✗ Unhandled {} on {} {}",
        type(exc).__name__, request.method, request.url.path,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": _settings.app_name}
