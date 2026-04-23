from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MDK Web Platform"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./data/mdk.db"
    core_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "core"

    jwt_secret: str = "mdk-change-this-in-production"
    llm_encryption_key: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_prefix": "MDK_", "env_file": ".env"}

    @model_validator(mode="after")
    def validate_secrets(self):
        if not self.debug and self.jwt_secret == "mdk-change-this-in-production":
            raise ValueError("MDK_JWT_SECRET must be set when debug=False")
        if not self.llm_encryption_key:
            self.llm_encryption_key = self.jwt_secret
        return self


settings = Settings()
