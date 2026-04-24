import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path

from .config import settings as _settings

logging.basicConfig(
    level=logging.DEBUG if _settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
# 第三方库降噪
for _name in ("httpx", "httpcore", "urllib3", "asyncio", "watchfiles", "LiteLLM"):
    logging.getLogger(_name).setLevel(logging.WARNING)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .database import Base, async_session, engine
from .models import GenSession, LlmConfig, Protocol, Setting, User
from .services.auth import hash_password
from .services.knowledge import list_protocol_files


async def seed_admin(session):
    result = await session.execute(select(User).where(User.username == "admin"))
    if not result.scalar_one_or_none():
        session.add(User(
            username="admin",
            password=hash_password("admin123"),
            role="admin",
            must_change_password=True,
        ))
        await session.commit()


async def seed_settings(session):
    defaults = [
        ("default_resolution", "2560x1600", "默认触摸屏分辨率"),
        ("xml_version", "4.1.9", "Project.xml 版本号"),
    ]
    for key, value, desc in defaults:
        existing = await session.get(Setting, key)
        if not existing:
            session.add(Setting(key=key, value=value, description=desc))
    await session.commit()


async def sync_protocols(session):
    for proto_data in list_protocol_files():
        result = await session.execute(
            select(Protocol).where(Protocol.filename == proto_data["filename"])
        )
        if not result.scalar_one_or_none():
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("data").mkdir(exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        await seed_admin(session)
        await seed_settings(session)
        await sync_protocols(session)
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

from .routers import admin, auth, gen, protocols, ref

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(gen.router)
app.include_router(protocols.router)
app.include_router(ref.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": _settings.app_name}
