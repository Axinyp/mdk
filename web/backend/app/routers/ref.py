from fastapi import APIRouter, Depends, Query

from ..services import knowledge
from ..services.auth import get_current_user

router = APIRouter(prefix="/api/ref", tags=["reference"], dependencies=[Depends(get_current_user)])


@router.get("/cht/devices")
async def cht_devices(type: str = Query("", alias="type")):
    content = knowledge._read(knowledge.REFERENCES_DIR / "core" / "syntax-rules.md")
    if not type:
        return {"content": content}
    type_upper = type.upper()
    lines = content.splitlines()
    result_lines = []
    capture = False
    for line in lines:
        if type_upper in line:
            capture = True
        if capture:
            result_lines.append(line)
            if len(result_lines) > 30:
                break
    return {"content": "\n".join(result_lines) if result_lines else content}


@router.get("/cht/functions")
async def cht_functions(query: str = ""):
    return {"content": knowledge.search_functions(query)}


@router.get("/cht/patterns")
async def cht_patterns(keyword: str = ""):
    if not keyword:
        return {"content": knowledge.get_patterns_index()}
    content = knowledge.get_pattern(keyword)
    return {"content": content if content else knowledge.get_patterns_index()}


@router.get("/xml/controls")
async def xml_controls(type: str = Query("", alias="type")):
    if not type:
        return {"content": knowledge.get_controls_index()}
    content = knowledge.get_control_spec(type)
    return {"content": content if content else f"未找到控件: {type}"}


@router.get("/xml/structure")
async def xml_structure(topic: str = ""):
    return {"content": knowledge.get_xml_structure(topic)}
