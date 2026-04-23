from ..schemas.gen import FunctionItem

SEGMENTS: dict[str, tuple[int, int]] = {
    "system": (1, 49),
    "light": (100, 139),
    "screen": (140, 149),
    "picture": (150, 164),
    "power": (165, 169),
    "text": (200, 209),
    "source": (210, 239),
    "text_ext": (240, 299),
    "status": (300, 499),
    "global": (500, 599),
    "slider": (1000, 1099),
    "extend": (1100, 1199),
    "dialog": (1200, 1299),
}

ALLOCATABLE_RANGES: dict[str, tuple[tuple[int, int], ...]] = {
    "system": ((1, 49),),
    "light": ((100, 139),),
    "screen": ((140, 149),),
    "picture": ((150, 164),),
    "power": ((165, 169),),
    "text": ((200, 209), (240, 299)),
    "source": ((210, 239),),
    "status": ((300, 499),),
    "global": ((500, 599),),
    "slider": ((1000, 1099),),
    "extend": ((1100, 1199),),
    "dialog": ((1200, 1299),),
}

ACTION_TO_CATEGORY: dict[str, str] = {
    "RELAY": "light",
    "COM": "light",
    "IR": "source",
    "TCP": "source",
    "UDP": "source",
    "LEVEL": "slider",
}

CONTROL_TYPE_CATEGORY: dict[str, str] = {
    "DFCSlider": "slider",
    "DFCTextbox": "text",
    "DFCPicture": "picture",
}

NAME_KEYWORDS: dict[str, list[str]] = {
    "light": ["灯", "灯光", "照明"],
    "screen": ["窗帘", "幕布", "帘", "投影幕"],
    "power": ["电源", "总开", "总关"],
    "source": ["信号源", "信号", "切换", "矩阵", "投影", "空调"],
    "dialog": ["弹窗", "确认", "提示"],
    "global": ["场景", "模式"],
}


def _guess_category(func: FunctionItem) -> str:
    if func.control_type in CONTROL_TYPE_CATEGORY:
        return CONTROL_TYPE_CATEGORY[func.control_type]
    if func.action in ACTION_TO_CATEGORY:
        cat = ACTION_TO_CATEGORY[func.action]
        name_lower = func.name.lower()
        for kw_cat, keywords in NAME_KEYWORDS.items():
            if any(kw in name_lower for kw in keywords):
                return kw_cat
        return cat
    name_lower = func.name.lower()
    for cat, keywords in NAME_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return cat
    return "system"


def _next_available(segment: str, used: set[int]) -> int:
    ranges = ALLOCATABLE_RANGES.get(segment, ((1, 49),))
    for start, end in ranges:
        for n in range(start, end + 1):
            if n not in used:
                return n
    raise ValueError(f"JoinNumber segment exhausted: {segment}")


def allocate(functions: list[FunctionItem]) -> list[FunctionItem]:
    used: set[int] = set()
    result: list[FunctionItem] = []

    for func in functions:
        if func.join_source == "user_specified" and func.join_number > 0:
            if func.join_number in used:
                raise ValueError(f"Duplicate JoinNumber: {func.join_number}")
            used.add(func.join_number)
            result.append(func.model_copy())
        else:
            result.append(func.model_copy(update={"join_source": "auto", "join_number": 0}))

    for i, func in enumerate(result):
        if func.join_number > 0:
            continue
        category = _guess_category(func)
        join_number = _next_available(category, used)
        used.add(join_number)
        result[i] = func.model_copy(update={"join_number": join_number, "join_source": "auto"})

    return result
