import json
import os
import secrets
import sys
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings

LEGACY_JWT_SECRET = "mdk-change-this-in-production"

_DEV_SECRETS_PATH = Path(__file__).resolve().parent.parent / "data" / ".dev_secrets"


def _load_or_create_dev_secrets() -> dict[str, str]:
    """In debug mode, persist random dev secrets to ``data/.dev_secrets``
    so that backend restarts do not invalidate previously-encrypted data.

    Production deployments must set MDK_JWT_SECRET / MDK_LLM_ENCRYPTION_KEY
    explicitly; this fallback only applies when ``debug=True``.
    """
    if _DEV_SECRETS_PATH.exists():
        try:
            data = json.loads(_DEV_SECRETS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("jwt_secret") and data.get("llm_encryption_key"):
                return data
        except (json.JSONDecodeError, OSError):
            pass

    fresh = {
        "jwt_secret": secrets.token_urlsafe(32),
        "llm_encryption_key": secrets.token_urlsafe(32),
    }
    try:
        _DEV_SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DEV_SECRETS_PATH.write_text(json.dumps(fresh), encoding="utf-8")
        try:
            os.chmod(_DEV_SECRETS_PATH, 0o600)
        except OSError:
            pass
    except OSError as exc:
        sys.stderr.write(
            f"[config] Failed to persist dev secrets to {_DEV_SECRETS_PATH}: {exc}\n"
        )
    return fresh


class Settings(BaseSettings):
    app_name: str = "MDK Web Platform"
    debug: bool = False
    sql_echo: bool = False

    database_url: str = "sqlite+aiosqlite:///./data/mdk.db"
    core_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "core"

    jwt_secret: str | None = None
    llm_encryption_key: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_prefix": "MDK_", "env_file": ".env"}

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        if self.debug:
            dev = _load_or_create_dev_secrets()
            if not self.jwt_secret or self.jwt_secret == LEGACY_JWT_SECRET:
                self.jwt_secret = dev["jwt_secret"]
                sys.stderr.write(
                    "[config] MDK_JWT_SECRET unset in debug mode; using persistent dev secret from data/.dev_secrets.\n"
                )
            if not self.llm_encryption_key:
                self.llm_encryption_key = dev["llm_encryption_key"]
                sys.stderr.write(
                    "[config] MDK_LLM_ENCRYPTION_KEY unset in debug mode; using persistent dev key from data/.dev_secrets.\n"
                )
            return self

        if not self.jwt_secret or self.jwt_secret == LEGACY_JWT_SECRET:
            raise ValueError("MDK_JWT_SECRET must be set to a non-legacy value when debug=False")
        if not self.llm_encryption_key:
            raise ValueError("MDK_LLM_ENCRYPTION_KEY must be set when debug=False")
        return self


settings = Settings()
