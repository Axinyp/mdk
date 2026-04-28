from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DeviceItem(BaseModel):
    name: str
    type: str
    board: int
    comm: str
    protocol_match: str | None = None


class FunctionItem(BaseModel):
    name: str
    join_number: int = 0
    join_source: str | None = "auto"
    control_type: str | None = "DFCButton"
    btn_type: str | None = "NormalBtn"
    action: str = ""                    # 官方函数名直引（SEND_UDP / ON_RELAY ...）
    params: dict[str, Any] = {}         # 签名镜像，无参函数填 {}
    image: str | None = None
    template_id: str | None = None      # PR-3 占位符

    @field_validator('action', 'join_source', 'control_type', mode='before')
    @classmethod
    def coerce_none_str(cls, v: object) -> object:
        return "" if v is None else v


class PageItem(BaseModel):
    name: str
    type: str = "sub"
    bg_image: str | None = None


class ParsedData(BaseModel):
    devices: list[DeviceItem] = []
    functions: list[FunctionItem] = []
    pages: list[PageItem] = []
    missing_info: list[str] = []
    image_path: str | None = None


class SessionCreate(BaseModel):
    description: str = Field(min_length=2)


class MessageRequest(BaseModel):
    content: str = Field(min_length=1)


class SessionMessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    kind: str
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: str
    user_id: int
    title: str | None
    status: str
    description: str | None
    parsed_data: str | None
    confirmed_data: str | None
    join_registry: str | None
    xml_content: str | None
    cht_content: str | None
    validation_report: str | None
    llm_model: str | None
    current_revision: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListItem(BaseModel):
    id: str
    title: str | None
    status: str
    description: str | None
    llm_model: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConfirmRequest(BaseModel):
    data: ParsedData


class GenerationResult(BaseModel):
    xml_content: str
    cht_content: str
    validation_report: dict
