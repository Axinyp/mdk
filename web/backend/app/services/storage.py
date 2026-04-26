from __future__ import annotations

import asyncio
import uuid
from pathlib import Path


class LocalStorage:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("uploads")

    async def save(self, data: bytes, filename: str) -> str:
        safe_name = Path(filename).name or "upload.bin"
        storage_key = f"{uuid.uuid4().hex}_{safe_name}"
        path = self.root / storage_key
        await asyncio.to_thread(self.root.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return storage_key

    async def load(self, key: str) -> bytes:
        path = self.root / key
        return await asyncio.to_thread(path.read_bytes)


default_storage = LocalStorage()
