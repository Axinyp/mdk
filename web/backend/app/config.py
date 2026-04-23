from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MDK Web Platform"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./data/mdk.db"
    core_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "core"

    jwt_secret: str = "mdk-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_prefix": "MDK_", "env_file": ".env"}


settings = Settings()
