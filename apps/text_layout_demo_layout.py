# Hard-coded layout parameters for live reload.
# Edit this file while the demo runs to see instant layout changes.

TEXT_BOXES = [
    {
        "gx": 2,
        "gy": 2,
        "gw": 22,
        "gh": 3,
        "color": "CRT_Cyan",
        "text": "CENTER\nBOX",
        "align_h": "center",
        "align_v": "center",
        "orientation": "horizontal",
        "line_step": 1,
    },
    {
        "gx": 2,
        "gy": 6,
        "gw": 22,
        "gh": 2,
        "color": "CRT_Orange",
        "text": "LEFT TOP",
        "align_h": "left",
        "align_v": "top",
        "orientation": "horizontal",
        "line_step": 1,
    },
    {
        "gx": 2,
        "gy": 9,
        "gw": 22,
        "gh": 2,
        "color": "CRT_Green",
        "text": "RIGHT",
        "align_h": "right",
        "align_v": "bottom",
        "orientation": "horizontal",
        "line_step": 1,
    },
]

SUPER_TEXT = [
    {
        "gx": 2,
        "gy": 13,
        "color": "CRT_Yellow",
        "text": "SUPER x2",
        "scale": 2,
        "mode": None,
        "line_step": 1,
    },
    {
        "gx": 2,
        "gy": 17,
        "color": "CRT_White",
        "text": "5x7",
        "scale": 1,
        "mode": "5x7",
        "line_step": 1,
    },
]

BLINK_SUPER = {
    "gx": 2,
    "gy": 21,
    "color": "CRT_Cyan",
    "text": "BLINK",
    "scale": 3,
    "mode": None,
    "line_step": 1,
}
