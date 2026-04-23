from ..schemas.gen import FunctionItem

SEGMENTS: dict[str, tuple[int, int]] = {
    "light": (100, 139),
    "curtain": (100, 139),
    "screen": (140, 149),
    "scene": (140, 149),
    "picture": (150, 169),
    "power": (165, 169),
    "text": (200, 299),
    "source": (210, 239),
    "status": (300, 499),
    "global": (500, 599),
    "slider": (1000, 1099),
    "extend": (1100, 1199),
    "dialog": (1200, 1299),
    "system": (1, 49),
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
    "curtain": ["窗帘", "幕布", "帘"],
    "screen": ["投影幕", "幕布", "升降幕"],
    "scene": ["场景", "模式"],
    "power": ["电源", "总开", "总关"],
    "source": ["信号源", "信号", "切换", "矩阵", "投影", "空调"],
    "dialog": ["弹窗", "确认", "提示"],
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


def allocate(functions: list[FunctionItem]) -> list[FunctionItem]:
    used: set[int] = set()
    result: list[FunctionItem] = []

    for func in functions:
        if func.join_source == "user_specified" and func.join_number > 0:
            used.add(func.join_number)
            result.append(func.model_copy())
        else:
            result.append(func.model_copy(update={"join_source": "auto", "join_number": 0}))

    for i, func in enumerate(result):
        if func.join_number > 0:
            continue
        category = _guess_category(func)
        start, end = SEGMENTS.get(category, (1, 49))
        for candidate in range(start, end + 1):
            if candidate not in used:
                used.add(candidate)
                result[i] = func.model_copy(update={"join_number": candidate, "join_source": "auto"})
                break

    return result
