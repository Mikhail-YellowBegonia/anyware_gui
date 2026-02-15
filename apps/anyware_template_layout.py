LAYOUT_MODE = True
FOCUS_SCOPE = "main"

TEXT_BOXES = [
    {
        "id": "title",
        "gx": 2,
        "gy": 1,
        "gw": 56,
        "gh": 1,
        "align_h": "left",
        "align_v": "top",
    },
    {
        "id": "hint",
        "gx": 2,
        "gy": 2,
        "gw": 56,
        "gh": 1,
        "align_h": "left",
        "align_v": "top",
    },
    {
        "id": "frame",
        "gx": 2,
        "gy": 4,
        "gw": 56,
        "gh": 1,
        "align_h": "left",
        "align_v": "top",
    },
    {
        "id": "selected",
        "gx": 2,
        "gy": 5,
        "gw": 56,
        "gh": 1,
        "align_h": "left",
        "align_v": "top",
    },
]

RECTS = []

BUTTONS = [
    {
        "id": "demo_btn_1",
        "label": "BTN 1",
        "gx": 4,
        "gy": 8,
        "gw": 12,
        "gh": 2,
        "nav": {"right": "demo_btn_2"},
    },
    {
        "id": "demo_btn_2",
        "label": "BTN 2",
        "gx": 19,
        "gy": 8,
        "gw": 12,
        "gh": 2,
        "nav": {"left": "demo_btn_1"},
    },
]
