from datetime import datetime

from pydantic import BaseModel, Field


class DeviceItem(BaseModel):
    name: str
    type: str
    board: int
    comm: str
    protocol_match: str | None = None


class FunctionItem(BaseModel):
    name: str
    join_number: int = 0
    join_source: str = "auto"
    control_type: str = "DFCButton"
    btn_type: str | None = "NormalBtn"
    device: str = ""
    channel: int | None = None
    action: str = ""


class PageItem(BaseModel):
    name: str
    type: str = "sub"


class ParsedData(BaseModel):
    devices: list[DeviceItem] = []
    functions: list[FunctionItem] = []
    pages: list[PageItem] = []
    missing_info: list[str] = []
    image_path: str | None = None


class SessionCreate(BaseModel):
    description: str = Field(min_length=2)


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
