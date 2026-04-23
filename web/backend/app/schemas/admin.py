from datetime import datetime

from pydantic import BaseModel, Field


class LlmConfigCreate(BaseModel):
    name: str
    provider: str
    model: str
    api_base: str | None = None
    api_key: str | None = None
    is_default: bool = False
    is_active: bool = True


class LlmConfigUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    model: str | None = None
    api_base: str | None = None
    api_key: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class LlmConfigResponse(BaseModel):
    id: int
    name: str
    provider: str
    model: str
    api_base: str | None
    api_key_set: bool
    is_default: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LlmTestRequest(BaseModel):
    config_id: int | None = None
    provider: str | None = None
    model: str | None = None
    api_base: str | None = None
    api_key: str | None = None


class LlmTestResponse(BaseModel):
    success: bool
    message: str
    model: str | None = None


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6)
    role: str = Field(default="member", pattern="^(admin|member)$")


class UserUpdate(BaseModel):
    role: str | None = None
    status: str | None = None


class SettingResponse(BaseModel):
    key: str
    value: str
    description: str | None

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value: str
