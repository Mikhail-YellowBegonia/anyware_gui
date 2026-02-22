import json
import numpy as np

def load_char_set_into(filepath: str):
    """Legacy JSON bitmap loader. Returns (char_set, (w, h))."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    res = data.get("resolution", [5, 5])
    chars_data = data.get("chars") or data.get("characters") or {}
    w, h = res[0], res[1]
    char_set = np.zeros((256, h, w), dtype=int)
    for ch, grid in chars_data.items():
        if len(ch) != 1:
            continue
        idx = ord(ch)
        if idx >= 256:
            continue
        arr = np.array(grid, dtype=int)
        gh, gw = arr.shape[0], arr.shape[1]
        out = np.zeros((h, w), dtype=int)
        out[: min(h, gh), : min(w, gw)] = arr[: min(h, gh), : min(w, gw)]
        char_set[idx] = out
    return char_set, (w, h)
