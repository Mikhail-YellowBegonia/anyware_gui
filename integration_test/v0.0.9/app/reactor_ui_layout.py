LAYOUT_MODE = False

PALETTE = {
    "bg_hex": "#fdf6f0",
    "default_hex": "#586e75",
    "special_hex": "#78cd26",
}

FOCUS_SCOPE = "nav"
DEFAULT_COLOR = "Solar_Default"
SPECIAL_COLOR = "Solar_Special"

NAV_BUTTONS = [
    {
        "id": "nav_status",
        "label": "状态指示",
        "target": "status",
        "gx": 2,
        "gy": 1,
        "gw": 18,
        "gh": 2,
        "nav": {"right": "nav_diagram"},
    },
    {
        "id": "nav_diagram",
        "label": "形式图",
        "target": "diagram",
        "gx": 22,
        "gy": 1,
        "gw": 18,
        "gh": 2,
        "nav": {"left": "nav_status", "right": "nav_control"},
    },
    {
        "id": "nav_control",
        "label": "控制面板",
        "target": "control",
        "gx": 42,
        "gy": 1,
        "gw": 18,
        "gh": 2,
        "nav": {"left": "nav_diagram", "right": "nav_core"},
    },
    {
        "id": "nav_core",
        "label": "堆芯",
        "target": "core",
        "gx": 62,
        "gy": 1,
        "gw": 18,
        "gh": 2,
        "nav": {"left": "nav_control"},
    },
]

PANEL_DEFAULT = {
    "gx": 2,
    "gy": 4,
    "gw": 156,
    "gh": 54,
    "color": DEFAULT_COLOR,
    "thickness": 2,
}

PANELS = {
    "status": dict(PANEL_DEFAULT),
    "diagram": dict(PANEL_DEFAULT),
    "control": dict(PANEL_DEFAULT),
    "core": dict(PANEL_DEFAULT),
}
