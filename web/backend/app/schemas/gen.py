from datetime import datetime
from typing import Literal

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
    device: str | None = None
    channel: int | None = None
    action: str | None = ""
    image: str | None = None

    @field_validator('device', 'action', 'join_source', 'control_type', mode='before')
    @classmethod
    def coerce_none_str(cls, v: object) -> object:
        return "" if v is None else v


class PageItem(BaseModel):
    name: str
    type: str = "sub"
    bg_image: str | None = None


class SceneActionItem(BaseModel):
    device: str = ""
    action: str = "RELAY.On"
    value: str | None = None


class SceneModeItem(BaseModel):
    name: str
    scene_type: Literal["meeting", "rest", "leave", "custom"] = "custom"
    trigger_join: int = 0
    actions: list[SceneActionItem] = []


class ParsedData(BaseModel):
    devices: list[DeviceItem] = []
    functions: list[FunctionItem] = []
    pages: list[PageItem] = []
    missing_info: list[str] = []
    image_path: str | None = None
    scenes: list[SceneModeItem] = []


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
