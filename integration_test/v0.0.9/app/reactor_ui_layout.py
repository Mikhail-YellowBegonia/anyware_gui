LAYOUT_MODE = False

PALETTE = {
    "bg_hex": "#fdf6f0",
    "default_hex": "#586e75",
    "special_hex": "#78cd26",
}

FOCUS_SCOPE = "nav"
DEFAULT_COLOR = "Solar_Default"
SPECIAL_COLOR = "Solar_Special"

NAV_AREA = {
    "gx": 0,
    "gy": 0,
    "gw": 128,
    "gh": 4,
    "color": DEFAULT_COLOR,
    "thickness": 1,
}

BODY_AREA = {
    "gx": 0,
    "gy": 4,
    "gw": 128,
    "gh": 40,
    "color": DEFAULT_COLOR,
    "thickness": 2,
}

FOOTER_AREA = {
    "gx": 0,
    "gy": 45,
    "gw": 128,
    "gh": 3,
    "color": DEFAULT_COLOR,
    "thickness": 1,
}

NAV_RIGHT_AREA = {
    "gx": 86,
    "gy": 0,
    "gw": 40,
    "gh": 2,
}

LOGO_POLY = {
    "gx": 88,
    "gy": 0,
    "color": DEFAULT_COLOR,
    "thickness": 1,
    "vertices_px": [
        (0, 0),
        (56, 0),
        (64, 10),
        (8, 10),
    ],
}

NET_INDICATOR = {
    "gx": 97,
    "gy": 1,
    "gw": 30,
    "gh": 2,
    "color": DEFAULT_COLOR,
    "thickness": 2,
}

COMMS_INDICATOR = {
    "gx": 97,
    "gy": 2,
    "gw": 10,
    "gh": 1,
    "color": SPECIAL_COLOR,
    "text": "COMMS",
}

NET_INFO_BOX = {
    "gx": 107,
    "gy": 1,
    "gw": 20,
    "gh": 2,
    "color": DEFAULT_COLOR,
    "text_lines": [
        "PORT 8787",
        "LATENCY --ms",
    ],
}

PAGE_LABELS = {
    "status": "状态指示",
    "diagram": "形式图",
    "control": "控制面板",
    "core": "堆芯",
}

PAGE_TITLE = {
    "gx": 2,
    "gy": 3,
    "gw": 24,
    "gh": 1,
    "color": DEFAULT_COLOR,
}

NAV_BUTTONS = [
    {
        "id": "nav_status",
        "label": "状态指示",
        "target": "status",
        "gx": 1.8,
        "gy": 0.8,
        "gw": 15.4,
        "gh": 2.4,
        "nav": {"right": "nav_diagram"},
    },
    {
        "id": "nav_diagram",
        "label": "形式图",
        "target": "diagram",
        "gx": 17.8,
        "gy": 0.8,
        "gw": 15.4,
        "gh": 2.4,
        "nav": {"left": "nav_status", "right": "nav_control"},
    },
    {
        "id": "nav_control",
        "label": "控制面板",
        "target": "control",
        "gx": 33.8,
        "gy": 0.8,
        "gw": 15.4,
        "gh": 2.4,
        "nav": {"left": "nav_diagram", "right": "nav_core"},
    },
    {
        "id": "nav_core",
        "label": "堆芯",
        "target": "core",
        "gx": 49.8,
        "gy": 0.8,
        "gw": 15.4,
        "gh": 2.4,
        "nav": {"left": "nav_control"},
    },
]

PANEL_DEFAULT = {
    "gx": 0,
    "gy": 4,
    "gw": 128,
    "gh": 41,
    "color": DEFAULT_COLOR,
    "thickness": 2,
}

PANELS = {
    "status": dict(PANEL_DEFAULT),
    "diagram": dict(PANEL_DEFAULT),
    "control": dict(PANEL_DEFAULT),
    "core": dict(PANEL_DEFAULT),
}

DIAGRAM_BOXES = [
    {"id": "core", "label": "Core", "gx": 104, "gy": 16, "gw": 18, "gh": 14},
    {"id": "steam", "label": "Steam Generator", "gx": 76, "gy": 16, "gw": 18, "gh": 14},
    {"id": "turbine_high", "label": "High Turbine", "gx": 48, "gy": 16, "gw": 18, "gh": 6},
    {"id": "turbine_low", "label": "Low Turbine", "gx": 48, "gy": 24, "gw": 18, "gh": 6},
    {"id": "electrics", "label": "Electrics", "gx": 6, "gy": 16, "gw": 32, "gh": 6},
    {"id": "condenser", "label": "Condenser", "gx": 6, "gy": 24, "gw": 32, "gh": 6},
]

DIAGRAM_BOX_STYLE = {
    "color": DEFAULT_COLOR,
    "thickness": 1,
    "label_color": DEFAULT_COLOR,
    "label_align_h": "center",
    "label_align_v": "center",
}

DIAGRAM_ARROWS = [
    {"start_gx": 104, "start_gy": 19, "end_gx": 94, "end_gy": 19}, # Core to Steam Generator (coolant outflow)
    {"start_gx": 94 , "start_gy": 27, "end_gx": 104, "end_gy": 27}, # Steam Generator to Core (coolant inflow)
    {"start_gx": 76, "start_gy": 19, "end_gx": 66, "end_gy": 19}, # Steam Generator to High Turbine (steam outflow)
    {"start_gx": 57, "start_gy": 22, "end_gx": 57, "end_gy": 24}, # High Turbine to Low Turbine
    {"start_gx": 38, "start_gy": 27, "end_gx": 76, "end_gy": 27}, # Condenser to Turbine (Coldwater feedback)
    {"start_gx": 48, "start_gy": 19, "end_gx": 38, "end_gy": 19}, # High Turbine to Electrics (power output)
    {"start_gx": 48, "start_gy": 26, "end_gx": 38, "end_gy": 26}, # Steam Generator to Condenser (Hotwater outflow)
]

DIAGRAM_ARROW_STYLE = {
    "color": DEFAULT_COLOR,
    "thickness": 1.0,
    "head_len_px": 10,
    "head_w_px": 6,
}

FOOTER_BLOCKS = [
    {"gx": 2, "gy": 46, "gw": 12, "gh": 1, "color": DEFAULT_COLOR},
    {"gx": 16, "gy": 46, "gw": 12, "gh": 1, "color": SPECIAL_COLOR},
    {"gx": 120, "gy": 46, "gw": 6, "gh": 1, "color": DEFAULT_COLOR},
]

FOOTER_TEXTS = [
    {"gx": 30, "gy": 46, "gw": 20, "gh": 1, "color": SPECIAL_COLOR, "text": "五月雨计划"},
    {"gx": 103, "gy": 46, "gw": 20, "gh": 1, "color": DEFAULT_COLOR, "text": "Project Samidare"},
]
