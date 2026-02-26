import numpy as np
import sys
import time
import colorsys
import pygame
import pygame.freetype
import unicodedata
from dataclasses import dataclass

# region version and compatibility
GUI_ENGINE_NAME = "krpc-gui"
GUI_ENGINE_VERSION = "0.4.0"
GUI_ENGINE_RELEASE_DATE = "2026-02-13"
GUI_API_LEVEL = 1
GUI_DEPENDENCY_MODEL = "standalone"

@dataclass(frozen=True)
class EngineManifest:
    name: str
    version: str
    release_date: str
    api_level: int
    dependency_model: str

def get_engine_manifest():
    """Return machine-readable engine metadata for dependent layers."""
    return {
        "name": GUI_ENGINE_NAME,
        "version": GUI_ENGINE_VERSION,
        "release_date": GUI_ENGINE_RELEASE_DATE,
        "api_level": GUI_API_LEVEL,
        "dependency_model": GUI_DEPENDENCY_MODEL,
    }

def require_api_level(min_api_level: int):
    """Raise when dependent layer requires a newer GUI API level."""
    if GUI_API_LEVEL < int(min_api_level):
        raise RuntimeError(
            f"{GUI_ENGINE_NAME} API level {GUI_API_LEVEL} is lower than required {int(min_api_level)}"
        )
    return True

# 无边框窗口拖动支持
def _get_move_window_func():
    if sys.platform == "win32":
        try:
            from ctypes import windll, byref, Structure, c_long
            class RECT(Structure):
                _fields_ = [("left", c_long), ("top", c_long), ("right", c_long), ("bottom", c_long)]
            def move_win(x, y):
                info = pygame.display.get_wm_info()
                if "window" in info:
                    w, h = pygame.display.get_surface().get_size()
                    windll.user32.MoveWindow(info["window"], int(x), int(y), w, h, False)
            def get_pos():
                info = pygame.display.get_wm_info()
                if "window" not in info:
                    return (0, 0)
                rect = RECT()
                windll.user32.GetWindowRect(info["window"], byref(rect))
                return (rect.left, rect.top)
            return move_win, get_pos
        except Exception:
            return None, None
    try:
        from pygame._sdl2.video import Window
        _win = Window.from_display_module()
        def move_win(x, y):
            _win.position = (int(x), int(y))
        def get_pos():
            return tuple(_win.position)
        return move_win, get_pos
    except Exception:
        return None, None

def _set_window_always_on_top(enabled: bool = True):
    if sys.platform == "win32":
        try:
            from ctypes import windll
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST if enabled else HWND_NOTOPMOST,
                    0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE
                )
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        try:
            import subprocess
            wid = pygame.display.get_wm_info().get("window")
            if wid:
                action = "add,above" if enabled else "remove,above"
                subprocess.run(["wmctrl", "-i", "-r", str(wid), "-b", action], check=False)
        except Exception:
            pass
    else:
        try:
            from pygame._sdl2.video import Window
            import ctypes
            win = Window.from_display_module()
            wid = win.id
            for lib_name in ("libSDL2-2.0.so.0", "libSDL2.dylib", "SDL2"):
                try:
                    sdl = ctypes.CDLL(lib_name)
                    break
                except OSError:
                    continue
            else:
                raise OSError("SDL2 not found")
            sdl.SDL_GetWindowFromID.restype = ctypes.c_void_p
            sdl.SDL_GetWindowFromID.argtypes = [ctypes.c_uint32]
            sdl.SDL_SetWindowAlwaysOnTop.argtypes = [ctypes.c_void_p, ctypes.c_int]
            sdl.SDL_SetWindowAlwaysOnTop.restype = None
            sdl_win = sdl.SDL_GetWindowFromID(wid)
            if sdl_win:
                sdl.SDL_SetWindowAlwaysOnTop(sdl_win, 1 if enabled else 0)
        except Exception:
            pass

# region basics and constants
frame = 0
fps = 10
target_fps = 60 
char_resolution = [16, 8]
row_column_resolution = (80, 40)
char_block_spacing_px = 1  
line_block_spacing_px = 1  
border_padding_px = 10  
PIXEL_SCALE = 1
window_noframe = True
window_always_on_top = True
window_bg_color_rgb = (10, 10, 10)
loading_animation = ['-', '\\', '|', '/']
blk = chr(31)
hol = chr(30)
# Continuation marker for the second cell of a wide glyph.
# Use a printable-safe private marker instead of '\0' to avoid numpy U1 truncation issues.
WIDE_CONT = '\ufff9'

DISPLAY_SYSTEM_DEFAULTS = {
    "fps": fps,
    "target_fps": target_fps,
    "char_height": char_resolution[0],
    "char_width": char_resolution[1],
    "rows": row_column_resolution[1],
    "cols": row_column_resolution[0],
    "char_block_spacing_px": char_block_spacing_px,
    "line_block_spacing_px": line_block_spacing_px,
    "border_padding_px": border_padding_px,
    "pixel_scale": PIXEL_SCALE,
    "window_noframe": window_noframe,
    "window_always_on_top": window_always_on_top,
    "window_bg_color_rgb": window_bg_color_rgb,
}
DISPLAY_USER_DEFAULTS = dict(DISPLAY_SYSTEM_DEFAULTS)

DYNAMIC_OFFSET_SYSTEM_DEFAULTS = {"default": 0.0}
DYNAMIC_OFFSETS = dict(DYNAMIC_OFFSET_SYSTEM_DEFAULTS)

FOCUS_SYSTEM_DEFAULTS = {"scope": "default"}
FOCUS_NODES = {}
FOCUS_NODE_ORDER = []
FOCUS_CURRENT_ID = None
FOCUS_ACTIVE_SCOPE = FOCUS_SYSTEM_DEFAULTS["scope"]
FOCUS_BLOCKERS = {}
FOCUS_BLOCKER_ORDER = []
# endregion

# region defaults
SYSTEM_DEFAULTS = {
    "poly": {"filled": True, "thickness": 1, "base_font_height_px": None},
    "rect": {"filled": True, "thickness": 1, "base_font_height_px": None},
    "pattern": {"spacing": 4.0, "angle_deg": 45.0, "thickness": 1.0, "offset": 0.0, "base_font_height_px": None},
    "box": {"padding": 0.0, "thickness": 1},
    "ani": {"local_offset": 0, "global_offset": 0, "slowdown": 1},
}
USER_DEFAULTS = {k: dict(v) for k, v in SYSTEM_DEFAULTS.items()}

def set_draw_defaults(**categories):
    """Set custom defaults by category (e.g., set_draw_defaults(poly={"filled": False}))."""
    for cat, vals in categories.items():
        if cat not in USER_DEFAULTS or vals is None:
            continue
        USER_DEFAULTS[cat].update(vals)

def reset_draw_defaults():
    for cat, vals in SYSTEM_DEFAULTS.items():
        USER_DEFAULTS[cat] = dict(vals)

def _resolve_opts(category, overrides):
    opts = dict(SYSTEM_DEFAULTS.get(category, {}))
    opts.update(USER_DEFAULTS.get(category, {}))
    for k, v in overrides.items():
        if v is not None:
            opts[k] = v
    return opts
# endregion

# region Palette and Color Handling
def base_hsv_palette():
    p = []
    for i in range(16): p.append((0.3, 1.0, round(1-(i/15), 2), "blink" + str(i))) 
    for i in range(16,32): p.append((0.5, 1.0, round(1-((i-16)/15), 2), "blink" + str(i)))
    for i in range(32,48): p.append((0.1, 1.0, round(1-((i-32)/15), 2), "blink" + str(i)))
    for i in range(48, 200): p.append((1.0, 1.0, 1.0, "res" + str(i)))
    for i in range(200, 256): p.append((1.0, 1.0, 1.0, "stat" + str(i)))
    return p

def custom_hsv_palette(palette):
    palette[201] = (0.3, 1.0, 0.9, "CRT_Green") 
    palette[202] = (0.14, 1.0, 0.9, "Electroluminescent_Amber")
    palette[203] = (0.5, 1.0, 0.8, "CRT_Cyan")
    palette[204] = (0.0, 0.0, 1.0, "White")
    palette[205] = (0.0, 0.0, 0.0, "Black")
    palette[211] = (0.92, 1.0, 1.0, "neon_pink")
    palette[212] = (0.58, 1.0, 1.0, "neon_blue")
    palette[213] = (0.3, 1.0, 1.0, "neon_green")
    palette[214] = (0.08, 1.0, 1.0, "neon_yellow")
    palette[215] = (0.8, 1.0, 1.0, "neon_violet")
    return palette

hsv_palette = custom_hsv_palette(base_hsv_palette())
index = [i for i in range(256)]
_palette_name_to_index = {}
_palette_rgb_cache = np.zeros((256, 3), dtype=np.uint8)

_LAYOUT_MODE_ENABLED = False
_LAYOUT_MODE_BG_RGB = (200, 190, 180)
_LAYOUT_MODE_FG_RGB = (130, 159, 23)

def refresh_palette_cache():
    """Rebuild palette lookup caches after mutating hsv_palette."""
    global _palette_name_to_index, _palette_rgb_cache
    _palette_name_to_index = {}
    rgb = np.zeros((len(hsv_palette), 3), dtype=np.uint8)
    for i, (h, s, v, name) in enumerate(hsv_palette):
        if isinstance(name, str):
            _palette_name_to_index[name] = i
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        rgb[i] = (int(r * 255), int(g * 255), int(b * 255))
    _palette_rgb_cache = rgb

def pal(name):
    """Fetches color index by name from the palette."""
    if not isinstance(name, str):
        return name
    return _palette_name_to_index.get(name, 204)  # White fallback

def _resolve_color(c):
    """Helper to ensure we get an integer index."""
    if isinstance(c, str): return pal(c)
    if isinstance(c, (int, float, np.integer)): return int(c) % 256
    return c

def get_color_rgb(color_index):
    if _LAYOUT_MODE_ENABLED:
        return _LAYOUT_MODE_FG_RGB
    idx = _resolve_color(color_index)
    rgb = _palette_rgb_cache[idx]
    return (int(rgb[0]), int(rgb[1]), int(rgb[2]))

def set_layout_mode(enabled: bool, *, bg_rgb=None, fg_rgb=None):
    """Toggle "layout mode" rendering (fixed palette for layout tuning).

    - Background is forced to (200, 190, 180) by default.
    - All other colors are forced to (130, 159, 23) by default.

    This is a pure API toggle (no keybinding). Anyware apps can call this too.
    """
    global _LAYOUT_MODE_ENABLED, _LAYOUT_MODE_BG_RGB, _LAYOUT_MODE_FG_RGB
    _LAYOUT_MODE_ENABLED = bool(enabled)
    if bg_rgb is not None:
        if isinstance(bg_rgb, (list, tuple)) and len(bg_rgb) == 3:
            _LAYOUT_MODE_BG_RGB = tuple(max(0, min(255, int(v))) for v in bg_rgb)
    if fg_rgb is not None:
        if isinstance(fg_rgb, (list, tuple)) and len(fg_rgb) == 3:
            _LAYOUT_MODE_FG_RGB = tuple(max(0, min(255, int(v))) for v in fg_rgb)
    return _LAYOUT_MODE_ENABLED

def get_layout_mode():
    return bool(_LAYOUT_MODE_ENABLED)

def get_layout_mode_colors():
    return {
        "enabled": bool(_LAYOUT_MODE_ENABLED),
        "bg_rgb": tuple(_LAYOUT_MODE_BG_RGB),
        "fg_rgb": tuple(_LAYOUT_MODE_FG_RGB),
    }
# endregion

# region screen/font
screen = np.array([[' ' for _ in range(row_column_resolution[0])] for _ in range(row_column_resolution[1])])
screen_color = np.zeros((row_column_resolution[1], row_column_resolution[0]), dtype=np.uint8)
screen_raw = np.zeros((char_resolution[0]*row_column_resolution[1], char_resolution[1]*row_column_resolution[0]), dtype=int)

_font_ascii = None
_font_cjk = None
_font_ascii_path = None
_font_cjk_path = None
_glyph_cache = {}
_glyph_cache_custom = {}

def _sanitize_display_option(key, value):
    if key in ("fps", "target_fps", "char_height", "char_width", "rows", "cols"):
        return max(1, int(value))
    if key in ("char_block_spacing_px", "line_block_spacing_px", "border_padding_px"):
        return max(0, int(value))
    if key == "pixel_scale":
        return max(1, int(value))
    if key in ("window_noframe", "window_always_on_top"):
        return bool(value)
    if key == "window_bg_color_rgb":
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return tuple(max(0, min(255, int(v))) for v in value)
        return DISPLAY_USER_DEFAULTS.get("window_bg_color_rgb", (10, 10, 10))
    return value

def _allocate_framebuffers():
    global screen, screen_color, screen_raw, _glyph_cache, _glyph_cache_custom
    cols, rows = row_column_resolution
    ch_h, ch_w = char_resolution
    screen = np.full((rows, cols), ' ', dtype='<U1')
    screen_color = np.zeros((rows, cols), dtype=np.uint8)
    screen_raw = np.zeros((ch_h * rows, ch_w * cols), dtype=int)
    _glyph_cache = {}
    _glyph_cache_custom = {}

def _apply_display_defaults(rebuild_framebuffers=True):
    global fps, target_fps, char_resolution, row_column_resolution
    global char_block_spacing_px, line_block_spacing_px, border_padding_px, PIXEL_SCALE
    global window_noframe, window_always_on_top, window_bg_color_rgb

    fps = _sanitize_display_option("fps", DISPLAY_USER_DEFAULTS["fps"])
    target_fps = _sanitize_display_option("target_fps", DISPLAY_USER_DEFAULTS["target_fps"])
    char_resolution[0] = _sanitize_display_option("char_height", DISPLAY_USER_DEFAULTS["char_height"])
    char_resolution[1] = _sanitize_display_option("char_width", DISPLAY_USER_DEFAULTS["char_width"])
    row_column_resolution = (
        _sanitize_display_option("cols", DISPLAY_USER_DEFAULTS["cols"]),
        _sanitize_display_option("rows", DISPLAY_USER_DEFAULTS["rows"]),
    )
    char_block_spacing_px = _sanitize_display_option("char_block_spacing_px", DISPLAY_USER_DEFAULTS["char_block_spacing_px"])
    line_block_spacing_px = _sanitize_display_option("line_block_spacing_px", DISPLAY_USER_DEFAULTS["line_block_spacing_px"])
    border_padding_px = _sanitize_display_option("border_padding_px", DISPLAY_USER_DEFAULTS["border_padding_px"])
    PIXEL_SCALE = _sanitize_display_option("pixel_scale", DISPLAY_USER_DEFAULTS["pixel_scale"])
    window_noframe = _sanitize_display_option("window_noframe", DISPLAY_USER_DEFAULTS["window_noframe"])
    window_always_on_top = _sanitize_display_option("window_always_on_top", DISPLAY_USER_DEFAULTS["window_always_on_top"])
    window_bg_color_rgb = _sanitize_display_option("window_bg_color_rgb", DISPLAY_USER_DEFAULTS["window_bg_color_rgb"])

    if rebuild_framebuffers:
        _allocate_framebuffers()

def get_display_defaults():
    return dict(DISPLAY_USER_DEFAULTS)

def set_display_defaults(**overrides):
    for key, value in overrides.items():
        if key not in DISPLAY_USER_DEFAULTS or value is None:
            continue
        DISPLAY_USER_DEFAULTS[key] = _sanitize_display_option(key, value)
    _apply_display_defaults(rebuild_framebuffers=True)
    return get_display_defaults()

def reset_display_defaults():
    DISPLAY_USER_DEFAULTS.clear()
    DISPLAY_USER_DEFAULTS.update(DISPLAY_SYSTEM_DEFAULTS)
    _apply_display_defaults(rebuild_framebuffers=True)
    return get_display_defaults()

def get_window_size_px():
    cols, rows = row_column_resolution
    ch_h, ch_w = char_resolution
    eff_w = (ch_w + char_block_spacing_px) * PIXEL_SCALE
    eff_h = (ch_h + line_block_spacing_px) * PIXEL_SCALE
    pad = border_padding_px * PIXEL_SCALE
    return (int(pad * 2 + cols * eff_w), int(pad * 2 + rows * eff_h))

def get_window_flags(extra_flags=0):
    flags = int(extra_flags or 0)
    if window_noframe:
        flags |= pygame.NOFRAME
    return flags

def next_frame(step=1):
    """Advance global frame counter by step and return current frame."""
    global frame
    frame += max(1, int(step))
    return frame

def begin_frame(*, clear_char=' ', clear_color=0, reset_overlay=True, advance_frame=True):
    """Canonical frame start for dependent layers (Anyware-friendly)."""
    if advance_frame:
        next_frame(1)
    if reset_overlay:
        reset_overlays()
    clear_screen(char=clear_char, color=clear_color)
    return frame

def finish_frame(surface, *, flip=False):
    """Canonical frame finish for dependent layers (Anyware-friendly)."""
    render(screen, screen_color)
    draw_to_surface(surface)
    if flip:
        pygame.display.flip()
    return frame

def _normalize_dynamic_channel(channel):
    if channel is None:
        return "default"
    return str(channel)

def get_dynamic_offset(channel="default", default=0.0):
    ch = _normalize_dynamic_channel(channel)
    return float(DYNAMIC_OFFSETS.get(ch, default))

def set_dynamic_offset(channel="default", value=0.0, wrap=None):
    ch = _normalize_dynamic_channel(channel)
    v = float(value)
    if wrap is not None:
        w = float(wrap)
        if w > 0:
            v %= w
    DYNAMIC_OFFSETS[ch] = v
    return v

def step_dynamic_offset(channel="default", speed=0.0, wrap=None):
    ch = _normalize_dynamic_channel(channel)
    current = float(DYNAMIC_OFFSETS.get(ch, 0.0))
    return set_dynamic_offset(ch, current + float(speed), wrap=wrap)

def reset_dynamic_offsets(channel=None):
    if channel is None:
        DYNAMIC_OFFSETS.clear()
        DYNAMIC_OFFSETS.update(DYNAMIC_OFFSET_SYSTEM_DEFAULTS)
        return dict(DYNAMIC_OFFSETS)
    ch = _normalize_dynamic_channel(channel)
    if ch in DYNAMIC_OFFSET_SYSTEM_DEFAULTS:
        DYNAMIC_OFFSETS[ch] = float(DYNAMIC_OFFSET_SYSTEM_DEFAULTS[ch])
    else:
        DYNAMIC_OFFSETS.pop(ch, None)
    return float(DYNAMIC_OFFSETS.get(ch, 0.0))

def _normalize_focus_rect(rect):
    if rect is None:
        return (0.0, 0.0, 0.0, 0.0)
    try:
        x, y, w, h = rect
    except Exception:
        return (0.0, 0.0, 0.0, 0.0)
    x = float(x)
    y = float(y)
    w = float(w)
    h = float(h)
    if w < 0:
        x += w
        w = -w
    if h < 0:
        y += h
        h = -h
    return (x, y, w, h)

def _normalize_focus_scope(scope):
    if scope is None:
        return FOCUS_SYSTEM_DEFAULTS["scope"]
    return str(scope)

def _normalize_focus_point(point):
    if point is None:
        return (0.0, 0.0)
    try:
        x, y = point
    except Exception:
        return (0.0, 0.0)
    return (float(x), float(y))

def _normalize_focus_direction(direction):
    if direction is None:
        return None
    d = str(direction).strip().lower()
    if d in ("u", "up"):
        return "up"
    if d in ("d", "down"):
        return "down"
    if d in ("l", "left"):
        return "left"
    if d in ("r", "right"):
        return "right"
    return None

def _normalize_focus_nav_target(value):
    if value is None:
        return None
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        return (None if value[0] is None else _normalize_focus_scope(value[0]), str(value[1]))
    if isinstance(value, dict):
        nid = value.get("id", value.get("node_id"))
        if nid is None:
            return None
        return (None if value.get("scope") is None else _normalize_focus_scope(value.get("scope")), str(nid))
    return (None, str(value))

def _normalize_focus_nav(nav):
    out = {}
    if not isinstance(nav, dict):
        return out
    for k, v in nav.items():
        d = _normalize_focus_direction(k)
        if d is None or v is None:
            continue
        target = _normalize_focus_nav_target(v)
        if target is None:
            continue
        out[d] = target
    return out

def _resolve_nav_target(target, current_scope):
    if target is None:
        return (None, None)
    t_scope, t_id = target
    return (_normalize_focus_scope(current_scope if t_scope is None else t_scope), str(t_id))

def _focusable(node):
    if not isinstance(node, dict):
        return False
    if not bool(node.get("enabled", True)):
        return False
    if not bool(node.get("visible", True)):
        return False
    _, _, w, h = _normalize_focus_rect(node.get("rect", (0, 0, 0, 0)))
    return w > 0 and h > 0

def _focus_center(rect):
    x, y, w, h = _normalize_focus_rect(rect)
    return (x + w * 0.5, y + h * 0.5)

def _find_first_focus_in_scope(scope):
    sc = _normalize_focus_scope(scope)
    for nid in FOCUS_NODE_ORDER:
        node = FOCUS_NODES.get(nid)
        if node is None:
            continue
        if _normalize_focus_scope(node.get("scope")) != sc:
            continue
        if _focusable(node):
            return nid
    return None

def _focus_scope_nodes(scope):
    sc = _normalize_focus_scope(scope)
    for nid in FOCUS_NODE_ORDER:
        node = FOCUS_NODES.get(nid)
        if node is None:
            continue
        if _normalize_focus_scope(node.get("scope")) != sc:
            continue
        if _focusable(node):
            yield nid, node

def _segment_intersects(a1, a2, b1, b2, eps=1e-6):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def on_segment(p, q, r):
        return (
            min(p[0], q[0]) - eps <= r[0] <= max(p[0], q[0]) + eps
            and min(p[1], q[1]) - eps <= r[1] <= max(p[1], q[1]) + eps
        )

    o1 = orient(a1, a2, b1)
    o2 = orient(a1, a2, b2)
    o3 = orient(b1, b2, a1)
    o4 = orient(b1, b2, a2)

    if (o1 > eps and o2 < -eps or o1 < -eps and o2 > eps) and (o3 > eps and o4 < -eps or o3 < -eps and o4 > eps):
        return True

    if abs(o1) <= eps and on_segment(a1, a2, b1):
        return True
    if abs(o2) <= eps and on_segment(a1, a2, b2):
        return True
    if abs(o3) <= eps and on_segment(b1, b2, a1):
        return True
    if abs(o4) <= eps and on_segment(b1, b2, a2):
        return True
    return False

def _focus_jump_blocked(p1, p2, scope):
    sc = _normalize_focus_scope(scope)
    a1 = _normalize_focus_point(p1)
    a2 = _normalize_focus_point(p2)
    if abs(a1[0] - a2[0]) <= 1e-9 and abs(a1[1] - a2[1]) <= 1e-9:
        return False
    for bid in FOCUS_BLOCKER_ORDER:
        blocker = FOCUS_BLOCKERS.get(bid)
        if blocker is None:
            continue
        if not bool(blocker.get("enabled", True)):
            continue
        if _normalize_focus_scope(blocker.get("scope")) != sc:
            continue
        b1 = _normalize_focus_point(blocker.get("p1"))
        b2 = _normalize_focus_point(blocker.get("p2"))
        if _segment_intersects(a1, a2, b1, b2):
            return True
    return False

def set_active_focus_scope(scope, *, pick_first=True):
    global FOCUS_ACTIVE_SCOPE, FOCUS_CURRENT_ID
    sc = _normalize_focus_scope(scope)
    FOCUS_ACTIVE_SCOPE = sc
    current = FOCUS_NODES.get(FOCUS_CURRENT_ID)
    if current is not None and _focusable(current) and _normalize_focus_scope(current.get("scope")) == sc:
        return sc
    if pick_first:
        FOCUS_CURRENT_ID = _find_first_focus_in_scope(sc)
    return sc

def get_active_focus_scope(default=None):
    if FOCUS_ACTIVE_SCOPE is None:
        return default
    return FOCUS_ACTIVE_SCOPE

def clear_focus_nodes():
    global FOCUS_CURRENT_ID, FOCUS_ACTIVE_SCOPE
    FOCUS_NODES.clear()
    FOCUS_NODE_ORDER.clear()
    FOCUS_BLOCKERS.clear()
    FOCUS_BLOCKER_ORDER.clear()
    FOCUS_CURRENT_ID = None
    FOCUS_ACTIVE_SCOPE = FOCUS_SYSTEM_DEFAULTS["scope"]

def add_focus_node(node_id, rect, *, enabled=True, visible=True, nav=None, scope="default"):
    global FOCUS_CURRENT_ID
    nid = str(node_id)
    node = {
        "id": nid,
        "rect": _normalize_focus_rect(rect),
        "enabled": bool(enabled),
        "visible": bool(visible),
        "nav": _normalize_focus_nav(nav),
        "scope": _normalize_focus_scope(scope),
    }
    existed = nid in FOCUS_NODES
    FOCUS_NODES[nid] = node
    if not existed:
        FOCUS_NODE_ORDER.append(nid)
    if FOCUS_CURRENT_ID is None and _focusable(node) and _normalize_focus_scope(node.get("scope")) == _normalize_focus_scope(FOCUS_ACTIVE_SCOPE):
        FOCUS_CURRENT_ID = nid
    return dict(node)

def update_focus_node(node_id, *, rect=None, enabled=None, visible=None, nav=None, scope=None):
    nid = str(node_id)
    node = FOCUS_NODES.get(nid)
    if node is None:
        return False
    if rect is not None:
        node["rect"] = _normalize_focus_rect(rect)
    if enabled is not None:
        node["enabled"] = bool(enabled)
    if visible is not None:
        node["visible"] = bool(visible)
    if nav is not None:
        node["nav"] = _normalize_focus_nav(nav)
    if scope is not None:
        node["scope"] = _normalize_focus_scope(scope)
    return True

def remove_focus_node(node_id):
    global FOCUS_CURRENT_ID
    nid = str(node_id)
    if nid not in FOCUS_NODES:
        return False
    FOCUS_NODES.pop(nid, None)
    FOCUS_NODE_ORDER[:] = [x for x in FOCUS_NODE_ORDER if x != nid]
    if FOCUS_CURRENT_ID == nid:
        FOCUS_CURRENT_ID = _find_first_focus_in_scope(FOCUS_ACTIVE_SCOPE)
    return True

def get_focus_node(node_id):
    node = FOCUS_NODES.get(str(node_id))
    if node is None:
        return None
    return dict(node)

def list_focus_nodes():
    out = []
    for nid in FOCUS_NODE_ORDER:
        node = FOCUS_NODES.get(nid)
        if node is not None:
            out.append(dict(node))
    return out

def set_focus(node_id, *, activate_scope=True):
    global FOCUS_CURRENT_ID, FOCUS_ACTIVE_SCOPE
    nid = str(node_id)
    node = FOCUS_NODES.get(nid)
    if not _focusable(node):
        return False
    FOCUS_CURRENT_ID = nid
    if activate_scope:
        FOCUS_ACTIVE_SCOPE = _normalize_focus_scope(node.get("scope"))
    return True

def get_focus(default=None):
    if FOCUS_CURRENT_ID is None:
        return default
    return FOCUS_CURRENT_ID

def _get_focus_scope():
    current = FOCUS_NODES.get(FOCUS_CURRENT_ID)
    if isinstance(current, dict):
        return _normalize_focus_scope(current.get("scope", FOCUS_SYSTEM_DEFAULTS["scope"]))
    return FOCUS_SYSTEM_DEFAULTS["scope"]

def get_focus_scope(node_id=None, default=None):
    if node_id is None:
        node_id = FOCUS_CURRENT_ID
    node = FOCUS_NODES.get(str(node_id))
    if node is None:
        return default
    return _normalize_focus_scope(node.get("scope", FOCUS_SYSTEM_DEFAULTS["scope"]))

def list_focus_scopes():
    seen = set()
    scopes = []
    for _, node in FOCUS_NODES.items():
        sc = _normalize_focus_scope(node.get("scope"))
        if sc in seen:
            continue
        seen.add(sc)
        scopes.append(sc)
    if not scopes:
        scopes.append(FOCUS_SYSTEM_DEFAULTS["scope"])
    return scopes

def add_focus_blocker(blocker_id, p1, p2, *, scope="default", enabled=True):
    bid = str(blocker_id)
    blocker = {
        "id": bid,
        "p1": _normalize_focus_point(p1),
        "p2": _normalize_focus_point(p2),
        "scope": _normalize_focus_scope(scope),
        "enabled": bool(enabled),
    }
    existed = bid in FOCUS_BLOCKERS
    FOCUS_BLOCKERS[bid] = blocker
    if not existed:
        FOCUS_BLOCKER_ORDER.append(bid)
    return dict(blocker)

def update_focus_blocker(blocker_id, *, p1=None, p2=None, scope=None, enabled=None):
    bid = str(blocker_id)
    blocker = FOCUS_BLOCKERS.get(bid)
    if blocker is None:
        return False
    if p1 is not None:
        blocker["p1"] = _normalize_focus_point(p1)
    if p2 is not None:
        blocker["p2"] = _normalize_focus_point(p2)
    if scope is not None:
        blocker["scope"] = _normalize_focus_scope(scope)
    if enabled is not None:
        blocker["enabled"] = bool(enabled)
    return True

def remove_focus_blocker(blocker_id):
    bid = str(blocker_id)
    if bid not in FOCUS_BLOCKERS:
        return False
    FOCUS_BLOCKERS.pop(bid, None)
    FOCUS_BLOCKER_ORDER[:] = [x for x in FOCUS_BLOCKER_ORDER if x != bid]
    return True

def clear_focus_blockers(scope=None):
    if scope is None:
        FOCUS_BLOCKERS.clear()
        FOCUS_BLOCKER_ORDER.clear()
        return 0
    sc = _normalize_focus_scope(scope)
    removed = 0
    for bid in list(FOCUS_BLOCKER_ORDER):
        blocker = FOCUS_BLOCKERS.get(bid)
        if blocker is None:
            continue
        if _normalize_focus_scope(blocker.get("scope")) != sc:
            continue
        remove_focus_blocker(bid)
        removed += 1
    return removed

def list_focus_blockers(scope=None):
    out = []
    sc = None if scope is None else _normalize_focus_scope(scope)
    for bid in FOCUS_BLOCKER_ORDER:
        blocker = FOCUS_BLOCKERS.get(bid)
        if blocker is None:
            continue
        if sc is not None and _normalize_focus_scope(blocker.get("scope")) != sc:
            continue
        out.append(dict(blocker))
    return out

def draw_focus_blockers(color, scope=None, *, thickness=1.0):
    sc = _normalize_focus_scope(FOCUS_ACTIVE_SCOPE if scope is None else scope)
    c_idx = _resolve_color(color)
    count = 0
    for bid in FOCUS_BLOCKER_ORDER:
        blocker = FOCUS_BLOCKERS.get(bid)
        if blocker is None:
            continue
        if not bool(blocker.get("enabled", True)):
            continue
        if _normalize_focus_scope(blocker.get("scope")) != sc:
            continue
        p1 = _normalize_focus_point(blocker.get("p1"))
        p2 = _normalize_focus_point(blocker.get("p2"))
        line_queue.append((p1[0], p1[1], p2[0], p2[1], c_idx, thickness))
        count += 1
    return count

def _focus_order_fallback(direction, scope, current_center=None):
    if FOCUS_CURRENT_ID not in FOCUS_NODE_ORDER:
        return None
    step = -1 if direction in ("up", "left") else 1
    start = FOCUS_NODE_ORDER.index(FOCUS_CURRENT_ID)
    i = start + step
    while 0 <= i < len(FOCUS_NODE_ORDER):
        nid = FOCUS_NODE_ORDER[i]
        node = FOCUS_NODES.get(nid)
        if node is not None and _normalize_focus_scope(node.get("scope", FOCUS_SYSTEM_DEFAULTS["scope"])) == _normalize_focus_scope(scope) and _focusable(node):
            if current_center is not None and _focus_jump_blocked(current_center, _focus_center(node.get("rect", (0, 0, 0, 0))), scope):
                i += step
                continue
            return nid
        i += step
    return None

def _focus_score(direction, cur_center, cand_center):
    dx = float(cand_center[0]) - float(cur_center[0])
    dy = float(cand_center[1]) - float(cur_center[1])
    eps = 1e-6
    if direction == "up":
        if dy >= -eps:
            return None
        primary = -dy
        secondary = abs(dx)
    elif direction == "down":
        if dy <= eps:
            return None
        primary = dy
        secondary = abs(dx)
    elif direction == "left":
        if dx >= -eps:
            return None
        primary = -dx
        secondary = abs(dy)
    elif direction == "right":
        if dx <= eps:
            return None
        primary = dx
        secondary = abs(dy)
    else:
        return None
    score = primary + 2.0 * secondary
    return (score, dx * dx + dy * dy)

def move_focus(direction):
    global FOCUS_CURRENT_ID, FOCUS_ACTIVE_SCOPE
    d = _normalize_focus_direction(direction)
    if d is None:
        return FOCUS_CURRENT_ID

    scope = _normalize_focus_scope(get_active_focus_scope(FOCUS_SYSTEM_DEFAULTS["scope"]))

    current = FOCUS_NODES.get(FOCUS_CURRENT_ID)
    if (
        FOCUS_CURRENT_ID is None
        or not _focusable(current)
        or _normalize_focus_scope(current.get("scope")) != scope
    ):
        FOCUS_CURRENT_ID = _find_first_focus_in_scope(scope)
        if FOCUS_CURRENT_ID is not None:
            return FOCUS_CURRENT_ID
        return None

    nav = current.get("nav", {}) if isinstance(current, dict) else {}
    target_nav = nav.get(d)
    current_center = _focus_center(current.get("rect", (0, 0, 0, 0)))
    if target_nav is not None:
        target_scope, target_id = _resolve_nav_target(target_nav, scope)
        target = FOCUS_NODES.get(str(target_id))
        if (
            target is not None
            and _focusable(target)
            and _normalize_focus_scope(target.get("scope", FOCUS_SYSTEM_DEFAULTS["scope"])) == target_scope
            and (target_scope != scope or not _focus_jump_blocked(current_center, _focus_center(target.get("rect", (0, 0, 0, 0))), scope))
        ):
            FOCUS_CURRENT_ID = str(target_id)
            FOCUS_ACTIVE_SCOPE = target_scope
            return FOCUS_CURRENT_ID

    best_id = None
    best_score = None
    for nid, cand in _focus_scope_nodes(scope):
        if nid == FOCUS_CURRENT_ID:
            continue
        cand_center = _focus_center(cand.get("rect", (0, 0, 0, 0)))
        score = _focus_score(d, current_center, cand_center)
        if score is None:
            continue
        if _focus_jump_blocked(current_center, cand_center, scope):
            continue
        if best_score is None or score < best_score:
            best_score = score
            best_id = nid

    if best_id is None:
        best_id = _focus_order_fallback(d, scope, current_center)

    if best_id is not None:
        FOCUS_CURRENT_ID = best_id
        FOCUS_ACTIVE_SCOPE = scope
    return FOCUS_CURRENT_ID

def key_to_focus_direction(key):
    if key == pygame.K_UP:
        return "up"
    if key == pygame.K_DOWN:
        return "down"
    if key == pygame.K_LEFT:
        return "left"
    if key == pygame.K_RIGHT:
        return "right"
    return None

def move_focus_by_key(key):
    d = key_to_focus_direction(key)
    if d is None:
        return FOCUS_CURRENT_ID
    return move_focus(d)

def grid_rect_to_px(gx, gy, gw, gh, pad_px=0.0):
    p1 = grid_to_px(gx, gy, -float(pad_px), -float(pad_px))
    p2 = grid_to_px(gx + gw, gy + gh, float(pad_px), float(pad_px))
    x1, y1 = float(p1[0]), float(p1[1])
    x2, y2 = float(p2[0]), float(p2[1])
    x = min(x1, x2)
    y = min(y1, y2)
    return (x, y, abs(x2 - x1), abs(y2 - y1))

def draw_focus_frame(color, node_id=None, *, padding=0.0, thickness=1.0):
    nid = FOCUS_CURRENT_ID if node_id is None else str(node_id)
    node = FOCUS_NODES.get(nid)
    if node is None or not _focusable(node):
        return False
    x, y, w, h = _normalize_focus_rect(node.get("rect", (0, 0, 0, 0)))
    pad = float(padding)
    return draw_rect(
        color,
        x - pad,
        y - pad,
        w + 2 * pad,
        h + 2 * pad,
        filled=False,
        thickness=thickness,
    )

def _normalize_cell_char(ch):
    if ch is None:
        return ' '
    if not isinstance(ch, str):
        ch = str(ch)
    if ch == '':
        return ' '
    return ch[0]

def clear_screen(char=' ', color=0):
    c_idx = _resolve_color(color)
    cell = _normalize_cell_char(char)
    screen[:, :] = cell
    screen_color[:, :] = c_idx

def clear_row(y, char=' ', color=0):
    if not (0 <= y < row_column_resolution[1]):
        return False
    c_idx = _resolve_color(color)
    cell = _normalize_cell_char(char)
    screen[y, :] = cell
    screen_color[y, :] = c_idx
    return True

def clear_cell(x, y, char=' ', color=0):
    if not (0 <= x < row_column_resolution[0] and 0 <= y < row_column_resolution[1]):
        return False
    screen[y][x] = _normalize_cell_char(char)
    screen_color[y][x] = _resolve_color(color)
    return True

def set_fonts(ascii_path=None, cjk_path=None, cell_w=None, cell_h=None, size_px=None):
    """Load font files (TTF/OTF/TTC) and set cell size."""
    global _font_ascii, _font_cjk, _font_ascii_path, _font_cjk_path
    global char_resolution, screen_raw, _glyph_cache, _glyph_cache_custom
    if cell_h is not None:
        char_resolution[0] = int(cell_h)
        DISPLAY_USER_DEFAULTS["char_height"] = int(char_resolution[0])
    if cell_w is not None:
        char_resolution[1] = int(cell_w)
        DISPLAY_USER_DEFAULTS["char_width"] = int(char_resolution[1])
    if size_px is None:
        size_px = int(char_resolution[0])
    if ascii_path is not None:
        _font_ascii = pygame.freetype.Font(ascii_path, size_px)
        _font_ascii_path = ascii_path
    if cjk_path is not None:
        _font_cjk = pygame.freetype.Font(cjk_path, size_px)
        _font_cjk_path = cjk_path
    _glyph_cache = {}
    _glyph_cache_custom = {}
    screen_raw = np.zeros((char_resolution[0]*row_column_resolution[1], char_resolution[1]*row_column_resolution[0]), dtype=int)

def set_font(filepath, cell_w=None, cell_h=None, size_px=None):
    set_fonts(ascii_path=filepath, cjk_path=filepath, cell_w=cell_w, cell_h=cell_h, size_px=size_px)

def _is_wide_char(ch):
    return unicodedata.east_asian_width(ch) in ("W", "F")

def _get_glyph_bitmap(ch, wide):
    font = _font_cjk if wide and _font_cjk is not None else _font_ascii
    font_path = _font_cjk_path if wide and _font_cjk_path is not None else _font_ascii_path
    if font is None:
        return None
    key = (ch, wide, char_resolution[0], char_resolution[1], font_path)
    if key in _glyph_cache:
        return _glyph_cache[key]
    cell_w = char_resolution[1] * (2 if wide else 1)
    cell_h = char_resolution[0]
    surf, _ = font.render(ch, fgcolor=(255, 255, 255), bgcolor=None)
    alpha = pygame.surfarray.array_alpha(surf)
    surf_w, surf_h = surf.get_size()
    if alpha.shape == (surf_w, surf_h):
        alpha = alpha.T
    h, w = alpha.shape
    if h == 0 or w == 0:
        _glyph_cache[key] = None
        return None
    scale = min(cell_w / w, cell_h / h, 1.0)
    if scale < 1.0:
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        y_idx = (np.arange(new_h) * (h / new_h)).astype(int).clip(0, h - 1)
        x_idx = (np.arange(new_w) * (w / new_w)).astype(int).clip(0, w - 1)
        scaled = alpha[np.ix_(y_idx, x_idx)]
    else:
        scaled = alpha
    h2, w2 = scaled.shape
    out = np.zeros((cell_h, cell_w), dtype=int)
    y0 = max(0, (cell_h - h2) // 2)
    x0 = max(0, (cell_w - w2) // 2)
    out[y0:y0 + h2, x0:x0 + w2] = (scaled > 0).astype(int)
    _glyph_cache[key] = out
    return out
# endregion

# region coordinate system
def grid_to_px(gx, gy, ox=0, oy=0):
    ch_h, ch_w = char_resolution
    eff_w = (ch_w + char_block_spacing_px) * PIXEL_SCALE
    eff_h = (ch_h + line_block_spacing_px) * PIXEL_SCALE
    pad = border_padding_px * PIXEL_SCALE
    px = pad + gx * eff_w - 0.5 * char_block_spacing_px * PIXEL_SCALE + ox * PIXEL_SCALE
    py = pad + gy * eff_h - 0.5 * line_block_spacing_px * PIXEL_SCALE + oy * PIXEL_SCALE
    return px, py

def gx(grid_x: float) -> float:
    """Grid-aligned X in absolute (screen) pixels."""
    _, ch_w = char_resolution
    eff_w = (ch_w + char_block_spacing_px) * PIXEL_SCALE
    pad = border_padding_px * PIXEL_SCALE
    return pad + float(grid_x) * eff_w - 0.5 * char_block_spacing_px * PIXEL_SCALE

def gy(grid_y: float) -> float:
    """Grid-aligned Y in absolute (screen) pixels."""
    ch_h, _ = char_resolution
    eff_h = (ch_h + line_block_spacing_px) * PIXEL_SCALE
    pad = border_padding_px * PIXEL_SCALE
    return pad + float(grid_y) * eff_h - 0.5 * line_block_spacing_px * PIXEL_SCALE

def px(pixel_x: float) -> float:
    """Pixel X to grid-space X (inverse mapping of gx)."""
    _, ch_w = char_resolution
    eff_w = (ch_w + char_block_spacing_px) * PIXEL_SCALE
    pad = border_padding_px * PIXEL_SCALE
    return (float(pixel_x) - pad + 0.5 * char_block_spacing_px * PIXEL_SCALE) / eff_w

def py(pixel_y: float) -> float:
    """Pixel Y to grid-space Y (inverse mapping of gy)."""
    ch_h, _ = char_resolution
    eff_h = (ch_h + line_block_spacing_px) * PIXEL_SCALE
    pad = border_padding_px * PIXEL_SCALE
    return (float(pixel_y) - pad + 0.5 * line_block_spacing_px * PIXEL_SCALE) / eff_h

# endregion

# region rendering core
def render(screen, screen_color=None):
    cols, rows = row_column_resolution
    ch_h, ch_w = char_resolution
    screen_raw.fill(0)
    for row in range(rows):
        col = 0
        while col < cols:
            ch = screen[row][col]
            if ch == WIDE_CONT:
                col += 1
                continue
            if ch == ' ' or ch == '':
                col += 1
                continue
            wide = _is_wide_char(ch) and col + 1 < cols and screen[row][col + 1] == WIDE_CONT
            bmp = _get_glyph_bitmap(ch, wide)
            if bmp is not None:
                y_start, x_start = row * ch_h, col * ch_w
                h, w = bmp.shape
                screen_raw[y_start : y_start + h, x_start : x_start + w] = bmp
            col += 2 if wide else 1

line_queue = []
fillpoly_queue = []

def reset_overlays():
    line_queue.clear()
    fillpoly_queue.clear()
    super_text_queue.clear()

def draw_to_surface(surface):
    surface.fill(_LAYOUT_MODE_BG_RGB if _LAYOUT_MODE_ENABLED else window_bg_color_rgb)
    for item in fillpoly_queue:
        v, c = item
        pygame.draw.polygon(surface, get_color_rgb(c), v)
    cols, rows = row_column_resolution
    ch_h, ch_w = char_resolution
    eff_w = (ch_w + char_block_spacing_px) * PIXEL_SCALE
    eff_h = (ch_h + line_block_spacing_px) * PIXEL_SCALE
    pad = border_padding_px * PIXEL_SCALE
    for r in range(rows):
        y_pos = pad + r * eff_h
        for c in range(cols):
            ch = screen[r][c]
            if ch == WIDE_CONT:
                continue
            span = 2 if (_is_wide_char(ch) and c + 1 < cols and screen[r][c + 1] == WIDE_CONT) else 1
            x_pos = pad + c * eff_w
            raw_y, raw_x = r * ch_h, c * ch_w
            span_w = ch_w * span
            glyph_block = screen_raw[raw_y : raw_y + ch_h, raw_x : raw_x + span_w]
            if not glyph_block.any():
                continue
            rgb = get_color_rgb(int(screen_color[r][c]))
            for py in range(ch_h):
                lit_px = np.flatnonzero(glyph_block[py])
                if lit_px.size == 0:
                    continue
                for px in lit_px:
                    surface.fill(rgb, (x_pos + px * PIXEL_SCALE, y_pos + py * PIXEL_SCALE, PIXEL_SCALE, PIXEL_SCALE))
    for item in line_queue:
        x1, y1, x2, y2, c, t = item
        thickness = max(1, int(round(float(t) * PIXEL_SCALE)))
        pygame.draw.line(surface, get_color_rgb(c), (x1, y1), (x2, y2), thickness)
    for item in super_text_queue:
        x_px, y_px, bmp, c_idx, scale = item
        rgb = get_color_rgb(c_idx)
        h, w = bmp.shape
        px_scale = max(1, int(round(float(scale) * PIXEL_SCALE)))
        for py in range(h):
            lit_px = np.flatnonzero(bmp[py])
            if lit_px.size == 0:
                continue
            for px in lit_px:
                surface.fill(
                    rgb,
                    (
                        x_px + px * px_scale,
                        y_px + py * px_scale,
                        px_scale,
                        px_scale,
                    ),
                )
# endregion

# region Polygon Library (unified)
@dataclass(frozen=True)
class PolyShape:
    # vertices in "design pixels" at base_font_height_px. Scaling uses current font height.
    vertices_px: tuple[tuple[float, float], ...]
    base_font_height_px: float

poly_shapes: dict[str, PolyShape] = {}

def add_poly(name: str, vertices_px, base_font_height_px: float | None = None):
    """Register a polygon in the global library.

    vertices_px are in design pixels. When rendering, they are scaled by:
      current_font_height / base_font_height_px
    """
    if base_font_height_px is None:
        base_font_height_px = float(char_resolution[0] or 1)
    poly_shapes[name] = PolyShape(
        vertices_px=tuple((float(x), float(y)) for x, y in vertices_px),
        base_font_height_px=float(base_font_height_px or 1),
    )

def _resolve_poly_vertices(shape_or_vertices):
    if isinstance(shape_or_vertices, str):
        shape = poly_shapes.get(shape_or_vertices)
        if shape is None:
            return None, None
        return tuple(shape.vertices_px), float(shape.base_font_height_px or 1)
    verts = tuple((float(x), float(y)) for x, y in shape_or_vertices)
    return verts, float(char_resolution[0] or 1)

def transform_poly_vertices(shape_or_vertices, *, scale=1.0, scale_x=None, scale_y=None, angle_deg=0.0):
    """Apply scale + rotation to poly vertices around fixed origin (0, 0)."""
    vertices, _ = _resolve_poly_vertices(shape_or_vertices)
    if vertices is None:
        return None

    base_scale = float(scale)
    sx = base_scale if scale_x is None else float(scale_x)
    sy = base_scale if scale_y is None else float(scale_y)
    theta = np.deg2rad(float(angle_deg))
    cos_t = float(np.cos(theta))
    sin_t = float(np.sin(theta))

    out = []
    for x, y in vertices:
        xs = float(x) * sx
        ys = float(y) * sy
        xr = xs * cos_t - ys * sin_t
        yr = xs * sin_t + ys * cos_t
        out.append((xr, yr))
    return tuple(out)

def rescale_poly_vertices(shape_or_vertices, scale=1.0, *, scale_x=None, scale_y=None):
    """Scale vertices around fixed origin (0, 0)."""
    return transform_poly_vertices(
        shape_or_vertices,
        scale=scale,
        scale_x=scale_x,
        scale_y=scale_y,
        angle_deg=0.0,
    )

def rotate_poly_vertices(shape_or_vertices, angle_deg=0.0):
    """Rotate vertices around fixed origin (0, 0)."""
    return transform_poly_vertices(shape_or_vertices, scale=1.0, angle_deg=angle_deg)

def add_poly_transformed(
    name: str,
    source_shape_or_vertices,
    *,
    scale=1.0,
    scale_x=None,
    scale_y=None,
    angle_deg=0.0,
    base_font_height_px: float | None = None,
):
    """Register a transformed poly shape (origin fixed at (0, 0))."""
    transformed = transform_poly_vertices(
        source_shape_or_vertices,
        scale=scale,
        scale_x=scale_x,
        scale_y=scale_y,
        angle_deg=angle_deg,
    )
    if transformed is None:
        return False

    _, src_base_h = _resolve_poly_vertices(source_shape_or_vertices)
    if base_font_height_px is None:
        base_font_height_px = src_base_h
    add_poly(name, transformed, base_font_height_px=base_font_height_px)
    return True

def _poly_local_vertices_scaled(vertices_px, base_font_height_px: float):
    cur_h = float(char_resolution[0] or 1)
    base_h = float(base_font_height_px or 1)
    scale = cur_h / base_h if base_h != 0 else 1.0
    return [(x * scale * PIXEL_SCALE, y * scale * PIXEL_SCALE) for x, y in vertices_px]

def draw_poly(shape_or_vertices, color, x_px, y_px, *, filled=None, thickness=None, base_font_height_px: float | None = None):
    """Draw a polygon using the unified system.

    - shape_or_vertices: str for global shape name, or a temporary vertex list.
    - Placement uses absolute pixels (x_px, y_px). Use gx()/gy() to stay aligned.
    - Vertex units are design pixels. They scale with current font height.
    """
    opts = _resolve_opts("poly", {"filled": filled, "thickness": thickness, "base_font_height_px": base_font_height_px})
    if isinstance(shape_or_vertices, str):
        shape = poly_shapes.get(shape_or_vertices)
        if shape is None:
            return False
        vertices_px = shape.vertices_px
        base_h = shape.base_font_height_px if opts["base_font_height_px"] is None else float(opts["base_font_height_px"])
    else:
        vertices_px = tuple((float(x), float(y)) for x, y in shape_or_vertices)
        base_h = float(opts["base_font_height_px"] if opts["base_font_height_px"] is not None else (char_resolution[0] or 1))

    base_px, base_py = float(x_px), float(y_px)
    local = _poly_local_vertices_scaled(vertices_px, base_h)
    abs_v = [(base_px + x, base_py + y) for x, y in local]

    c_idx = _resolve_color(color)
    if opts["filled"]:
        fillpoly_queue.append((abs_v, c_idx))
    else:
        for i in range(len(abs_v)):
            p1, p2 = abs_v[i], abs_v[(i + 1) % len(abs_v)]
            line_queue.append((p1[0], p1[1], p2[0], p2[1], c_idx, opts["thickness"]))
    return True

def draw_rect(color, x_px, y_px, w_px, h_px, *, filled=None, thickness=None, base_font_height_px: float | None = None):
    opts = _resolve_opts("rect", {"filled": filled, "thickness": thickness, "base_font_height_px": base_font_height_px})
    if opts["filled"]:
        verts = [(0, 0), (w_px, 0), (w_px, h_px), (0, h_px)]
        return draw_poly(verts, color, x_px, y_px, filled=True, thickness=opts["thickness"], base_font_height_px=opts["base_font_height_px"])
    outline = [(0, 0), (w_px, 0), (w_px, h_px), (0, h_px)]
    return draw_poly(outline, color, x_px, y_px, filled=False, thickness=opts["thickness"], base_font_height_px=opts["base_font_height_px"])

def _design_px_to_render_px(value, base_font_height_px: float):
    cur_h = float(char_resolution[0] or 1)
    base_h = float(base_font_height_px or 1)
    scale = cur_h / base_h if base_h != 0 else 1.0
    return float(value) * scale * PIXEL_SCALE

def _design_px_to_thickness_units(value, base_font_height_px: float):
    cur_h = float(char_resolution[0] or 1)
    base_h = float(base_font_height_px or 1)
    scale = cur_h / base_h if base_h != 0 else 1.0
    return float(value) * scale

def _dot2(a, b):
    return a[0] * b[0] + a[1] * b[1]

def _dedupe_points(points, precision=6):
    seen = set()
    out = []
    for p in points:
        key = (round(float(p[0]), precision), round(float(p[1]), precision))
        if key in seen:
            continue
        seen.add(key)
        out.append((float(p[0]), float(p[1])))
    return out

def _line_polygon_intersections(vertices, normal, k, eps=1e-9):
    points = []
    n = len(vertices)
    for i in range(n):
        a = vertices[i]
        b = vertices[(i + 1) % n]
        da = _dot2(a, normal) - k
        db = _dot2(b, normal) - k

        if abs(da) <= eps and abs(db) <= eps:
            points.append(a)
            points.append(b)
            continue
        if abs(da) <= eps:
            points.append(a)
            continue
        if abs(db) <= eps:
            points.append(b)
            continue
        if da * db < 0.0:
            t = da / (da - db)
            points.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))

    return _dedupe_points(points)

def _build_hatch_segments(vertices, spacing_px, angle_deg, offset_px):
    if len(vertices) < 3:
        return []

    theta = np.deg2rad(float(angle_deg))
    direction = (float(np.cos(theta)), float(np.sin(theta)))
    normal = (-direction[1], direction[0])

    proj = [_dot2(v, normal) for v in vertices]
    k_min = min(proj)
    k_max = max(proj)

    spacing = max(1e-6, float(spacing_px))
    start = np.floor((k_min - float(offset_px)) / spacing) * spacing + float(offset_px)

    segments = []
    k = start
    eps = spacing * 1e-6 + 1e-9
    while k <= k_max + eps:
        pts = _line_polygon_intersections(vertices, normal, k)
        if len(pts) >= 2:
            pts = sorted(pts, key=lambda p: _dot2(p, direction))
            pair_count = len(pts) // 2
            for i in range(pair_count):
                p1 = pts[2 * i]
                p2 = pts[2 * i + 1]
                if abs(p1[0] - p2[0]) <= 1e-6 and abs(p1[1] - p2[1]) <= 1e-6:
                    continue
                segments.append((p1, p2))
        k += spacing
    return segments

def draw_pattern_poly(shape_or_vertices, color, x_px, y_px, *, spacing=None, angle_deg=None, thickness=None, offset=None, base_font_height_px: float | None = None):
    opts = _resolve_opts(
        "pattern",
        {
            "spacing": spacing,
            "angle_deg": angle_deg,
            "thickness": thickness,
            "offset": offset,
            "base_font_height_px": base_font_height_px,
        },
    )

    if isinstance(shape_or_vertices, str):
        shape = poly_shapes.get(shape_or_vertices)
        if shape is None:
            return False
        vertices_px = shape.vertices_px
        base_h = shape.base_font_height_px if opts["base_font_height_px"] is None else float(opts["base_font_height_px"])
    else:
        vertices_px = tuple((float(x), float(y)) for x, y in shape_or_vertices)
        base_h = float(opts["base_font_height_px"] if opts["base_font_height_px"] is not None else (char_resolution[0] or 1))

    local = _poly_local_vertices_scaled(vertices_px, base_h)
    abs_v = [(float(x_px) + x, float(y_px) + y) for x, y in local]

    spacing_px = max(1.0, _design_px_to_render_px(opts["spacing"], base_h))
    thickness_units = max(0.1, _design_px_to_thickness_units(opts["thickness"], base_h))
    offset_px = _design_px_to_render_px(opts["offset"], base_h)
    segments = _build_hatch_segments(abs_v, spacing_px, float(opts["angle_deg"]), offset_px)

    c_idx = _resolve_color(color)
    for p1, p2 in segments:
        line_queue.append((p1[0], p1[1], p2[0], p2[1], c_idx, thickness_units))
    return True

def draw_pattern_rect(color, x_px, y_px, w_px, h_px, *, spacing=None, angle_deg=None, thickness=None, offset=None, base_font_height_px: float | None = None):
    verts = [(0, 0), (w_px, 0), (w_px, h_px), (0, h_px)]
    return draw_pattern_poly(
        verts,
        color,
        x_px,
        y_px,
        spacing=spacing,
        angle_deg=angle_deg,
        thickness=thickness,
        offset=offset,
        base_font_height_px=base_font_height_px,
    )
# endregion

# region High-level drawing functions
def _clear_wide_neighbors(y, x):
    cols = row_column_resolution[0]
    if not (0 <= y < row_column_resolution[1] and 0 <= x < cols):
        return
    here = screen[y][x]
    if here == WIDE_CONT:
        left = x - 1
        if left >= 0 and _is_wide_char(screen[y][left]):
            screen[y][left] = ' '
            screen_color[y][left] = 0
        screen[y][x] = ' '
        screen_color[y][x] = 0
        return
    if _is_wide_char(here) and x + 1 < cols and screen[y][x + 1] == WIDE_CONT:
        screen[y][x + 1] = ' '
        screen_color[y][x + 1] = 0

def static(x, y, color, content):
    if not (0 <= y < row_column_resolution[1]): return False
    c_idx = _resolve_color(color)
    cols = row_column_resolution[0]
    col = int(x)
    text = content if isinstance(content, str) else str(content)
    for raw_char in text:
        if not (0 <= col < row_column_resolution[0]):
            break
        char = _normalize_cell_char(raw_char)
        if char == WIDE_CONT:
            char = ' '

        _clear_wide_neighbors(y, col)
        if _is_wide_char(char) and col + 1 < cols:
            _clear_wide_neighbors(y, col + 1)
            screen[y][col] = char
            screen_color[y][col] = c_idx
            screen[y][col + 1] = WIDE_CONT
            screen_color[y][col + 1] = c_idx
            col += 2
        else:
            screen[y][col] = char
            screen_color[y][col] = c_idx
            col += 1
    return True

def hstatic(x, y, color, content, line_step=1):
    col = int(x)
    row = int(y)
    if not (0 <= col < row_column_resolution[0]):
        return False
    step = 1 if line_step is None else max(1, int(line_step))
    c_idx = _resolve_color(color)
    cols = row_column_resolution[0]
    rows = row_column_resolution[1]
    text = content if isinstance(content, str) else str(content)

    for raw_char in text:
        if not (0 <= row < rows):
            break
        char = _normalize_cell_char(raw_char)
        if char == WIDE_CONT:
            char = ' '

        _clear_wide_neighbors(row, col)
        if _is_wide_char(char) and col + 1 < cols:
            _clear_wide_neighbors(row, col + 1)
            screen[row][col] = char
            screen_color[row][col] = c_idx
            screen[row][col + 1] = WIDE_CONT
            screen_color[row][col + 1] = c_idx
        else:
            screen[row][col] = char
            screen_color[row][col] = c_idx
        row += step
    return True

def _split_text_lines(text):
    if text is None:
        return []
    text = text if isinstance(text, str) else str(text)
    if text == "":
        return []
    return text.split("\n")

def _measure_line_cells(text):
    width = 0
    for raw_char in text:
        char = _normalize_cell_char(raw_char)
        if char == WIDE_CONT:
            char = " "
        width += 2 if _is_wide_char(char) else 1
    return width

def measure_text_cells(text, *, orientation="horizontal", line_step=1):
    orient = str(orientation).strip().lower()
    step = max(1, int(line_step))
    lines = _split_text_lines(text)
    if not lines:
        return (0, 0)
    if orient == "vertical":
        widths = []
        heights = []
        for line in lines:
            widths.append(2 if any(_is_wide_char(_normalize_cell_char(ch)) for ch in line) else 1)
            height = 1 + (len(line) - 1) * step if line else 0
            heights.append(height)
        total_w = sum(widths)
        total_h = max(heights) if heights else 0
        return (total_w, total_h)
    widths = [_measure_line_cells(line) for line in lines]
    height = 1 + (len(lines) - 1) * step
    return (max(widths) if widths else 0, height)

def _truncate_line_to_cells(text, max_cells):
    if max_cells <= 0:
        return ""
    out = []
    used = 0
    for raw_char in text:
        char = _normalize_cell_char(raw_char)
        if char == WIDE_CONT:
            char = " "
        wide = _is_wide_char(char)
        if wide:
            if used + 2 <= max_cells:
                out.append(char)
                used += 2
                continue
            if used + 1 <= max_cells:
                out.append(char)
                used += 1
            break
        if used + 1 > max_cells:
            break
        out.append(char)
        used += 1
    return "".join(out)

def _truncate_vertical(text, max_rows, line_step):
    if max_rows <= 0:
        return ""
    step = max(1, int(line_step))
    max_chars = 1 + (max_rows - 1) // step
    return text[:max_chars]

def _align_start(start, span, size, align):
    if size <= 0:
        return int(start)
    if size >= span:
        return int(start)
    align = str(align).strip().lower()
    if align in ("center", "middle"):
        return int(start + (span - size) // 2)
    if align in ("right", "bottom"):
        return int(start + (span - size))
    return int(start)

def draw_text_box(
    gx,
    gy,
    gw,
    gh,
    color,
    text,
    *,
    align_h="left",
    align_v="top",
    orientation="horizontal",
    line_step=1,
):
    """Draw text within a grid-aligned box using integer cell coordinates."""
    orient = str(orientation).strip().lower()
    lines = _split_text_lines(text)
    if not lines:
        return False
    gw = int(gw)
    gh = int(gh)
    text_w, text_h = measure_text_cells(text, orientation=orient, line_step=line_step)
    start_x = _align_start(int(gx), gw, text_w, align_h)
    start_y = _align_start(int(gy), gh, text_h, align_v)
    step = max(1, int(line_step))
    if orient == "vertical":
        x = start_x
        for line in lines:
            col_width = 2 if any(_is_wide_char(_normalize_cell_char(ch)) for ch in line) else 1
            truncated = _truncate_vertical(line, gh, step)
            hstatic(x, start_y, color, truncated, line_step=step)
            x += col_width
        return True
    for idx, line in enumerate(lines):
        y = start_y + idx * step
        if y >= int(gy) + gh:
            break
        truncated = _truncate_line_to_cells(line, gw)
        static(start_x, y, color, truncated)
    return True

def _get_glyph_bitmap_custom(ch, wide, cell_w, cell_h):
    font = _font_cjk if wide and _font_cjk is not None else _font_ascii
    font_path = _font_cjk_path if wide and _font_cjk_path is not None else _font_ascii_path
    if font is None:
        return None
    span_w = cell_w * (2 if wide else 1)
    key = (ch, wide, cell_h, span_w, font_path)
    if key in _glyph_cache_custom:
        return _glyph_cache_custom[key]
    surf, _ = font.render(ch, fgcolor=(255, 255, 255), bgcolor=None)
    alpha = pygame.surfarray.array_alpha(surf)
    surf_w, surf_h = surf.get_size()
    if alpha.shape == (surf_w, surf_h):
        alpha = alpha.T
    h, w = alpha.shape
    if h == 0 or w == 0:
        _glyph_cache_custom[key] = None
        return None
    scale = min(span_w / w, cell_h / h, 1.0)
    if scale < 1.0:
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        y_idx = (np.arange(new_h) * (h / new_h)).astype(int).clip(0, h - 1)
        x_idx = (np.arange(new_w) * (w / new_w)).astype(int).clip(0, w - 1)
        scaled = alpha[np.ix_(y_idx, x_idx)]
    else:
        scaled = alpha
    h2, w2 = scaled.shape
    out = np.zeros((cell_h, span_w), dtype=int)
    y0 = max(0, (cell_h - h2) // 2)
    x0 = max(0, (span_w - w2) // 2)
    out[y0 : y0 + h2, x0 : x0 + w2] = (scaled > 0).astype(int)
    _glyph_cache_custom[key] = out
    return out

def _measure_super_text_px(text, cell_w, cell_h, *, scale=1, line_step=1):
    lines = _split_text_lines(text)
    if not lines:
        return (0, 0)
    step = max(1, int(line_step))
    cell_w_px = int(cell_w * PIXEL_SCALE * scale)
    cell_h_px = int(cell_h * PIXEL_SCALE * scale)
    widths = []
    for line in lines:
        width_cells = _measure_line_cells(line)
        widths.append(width_cells * cell_w_px)
    height_px = cell_h_px + (len(lines) - 1) * step * cell_h_px
    return (max(widths) if widths else 0, height_px)

super_text_queue = []

def draw_super_text_px(
    x_px,
    y_px,
    color,
    text,
    *,
    scale=1,
    mode=None,
    align_h="left",
    align_v="top",
    box_w_px=None,
    box_h_px=None,
    line_step=1,
):
    """Draw super-grid text in absolute pixel coordinates (post-PIXEL_SCALE space)."""
    if text is None:
        return False
    text = text if isinstance(text, str) else str(text)
    if text == "":
        return False
    use_mode = None if mode is None else str(mode).strip().lower()
    if use_mode == "5x7":
        cell_w = 5
        cell_h = 7
        scale = 1
    else:
        cell_h, cell_w = char_resolution
        scale = max(1, int(scale))
    text_w_px, text_h_px = _measure_super_text_px(text, cell_w, cell_h, scale=scale, line_step=line_step)
    x_px = int(round(x_px))
    y_px = int(round(y_px))
    if box_w_px is not None:
        x_px = _align_start(x_px, int(box_w_px), text_w_px, align_h)
    if box_h_px is not None:
        y_px = _align_start(y_px, int(box_h_px), text_h_px, align_v)
    c_idx = _resolve_color(color)
    step = max(1, int(line_step))
    cell_w_px = int(cell_w * PIXEL_SCALE * scale)
    cell_h_px = int(cell_h * PIXEL_SCALE * scale)
    lines = _split_text_lines(text)
    if box_w_px is not None:
        max_cells = int(int(box_w_px) // max(1, cell_w_px))
        lines = [_truncate_line_to_cells(line, max_cells) for line in lines]
    if box_h_px is not None:
        max_lines = max(0, 1 + (int(box_h_px) - cell_h_px) // (step * cell_h_px))
        lines = lines[:max_lines]
    for line_idx, line in enumerate(lines):
        line_x = x_px
        line_y = y_px + line_idx * step * cell_h_px
        col_offset_px = 0
        for raw_char in line:
            char = _normalize_cell_char(raw_char)
            if char == WIDE_CONT:
                char = " "
            wide = _is_wide_char(char)
            bmp = _get_glyph_bitmap_custom(char, wide, cell_w, cell_h)
            if bmp is not None:
                super_text_queue.append(
                    (
                        int(line_x + col_offset_px),
                        int(line_y),
                        bmp,
                        int(c_idx),
                        int(scale),
                    )
                )
            col_offset_px += cell_w_px * (2 if wide else 1)
    return True

def ani_char(x, y, color, animation, local_offset=None, global_offset=None, slowdown=None):
    opts = _resolve_opts("ani", {"local_offset": local_offset, "global_offset": global_offset, "slowdown": slowdown})
    c = color[round((frame + opts["global_offset"]) / opts["slowdown"]) % len(color)] if isinstance(color, list) else color
    return static(x, y, c, animation[(round((frame + opts["local_offset"] + opts["global_offset"]) / opts["slowdown"])) % len(animation)])

def sweep(row, col1, col2, color_start, color_end):
    if not (0 <= row < row_column_resolution[1]): return False
    s_idx, e_idx = _resolve_color(color_start), _resolve_color(color_end)
    if e_idx < s_idx: s_idx, e_idx = e_idx, s_idx
    cycle = max(1, e_idx - s_idx + 1)
    c1, c2 = max(0, min(row_column_resolution[0]-1, int(col1))), max(0, min(row_column_resolution[0]-1, int(col2)))
    length = abs(c2 - c1) + 1
    step = -1 if c1 > c2 else 1
    for i in range(length):
        screen_color[row][c1 + i * step] = (frame + i) % cycle + s_idx
    return True

def draw_box(gx, gy, gw, gh, color, padding=None, thickness=None):
    opts = _resolve_opts("box", {"padding": padding, "thickness": thickness})
    c = _resolve_color(color)
    pad = opts["padding"]
    thick = opts["thickness"]
    p1, p2, p3, p4 = grid_to_px(gx,gy,-pad,-pad), grid_to_px(gx+gw,gy,pad,-pad), grid_to_px(gx,gy+gh,-pad,pad), grid_to_px(gx+gw,gy+gh,pad,pad)
    line_queue.extend([(p1[0],p1[1],p2[0],p2[1],c,thick), (p3[0],p3[1],p4[0],p4[1],c,thick), (p1[0],p1[1],p3[0],p3[1],c,thick), (p2[0],p2[1],p4[0],p4[1],c,thick)])

# endregion

# region API contract and Anyware-facing runtime
STABLE_API = (
    "get_engine_manifest",
    "require_api_level",
    "get_display_defaults",
    "set_display_defaults",
    "reset_display_defaults",
    "set_layout_mode",
    "get_layout_mode",
    "get_layout_mode_colors",
    "get_window_size_px",
    "get_window_flags",
    "set_fonts",
    "set_font",
    "next_frame",
    "begin_frame",
    "finish_frame",
    "reset_overlays",
    "clear_screen",
    "clear_row",
    "clear_cell",
    "static",
    "hstatic",
    "measure_text_cells",
    "draw_text_box",
    "draw_super_text_px",
    "ani_char",
    "sweep",
    "grid_to_px",
    "gx",
    "gy",
    "px",
    "py",
    "draw_box",
    "draw_rect",
    "draw_poly",
    "draw_pattern_rect",
    "draw_pattern_poly",
    "add_poly",
    "add_poly_transformed",
    "rescale_poly_vertices",
    "rotate_poly_vertices",
    "transform_poly_vertices",
    "set_dynamic_offset",
    "get_dynamic_offset",
    "step_dynamic_offset",
    "reset_dynamic_offsets",
    "add_focus_node",
    "update_focus_node",
    "remove_focus_node",
    "clear_focus_nodes",
    "set_focus",
    "get_focus",
    "add_focus_blocker",
    "update_focus_blocker",
    "remove_focus_blocker",
    "clear_focus_blockers",
    "set_active_focus_scope",
    "get_active_focus_scope",
    "move_focus",
    "move_focus_by_key",
    "key_to_focus_direction",
    "draw_focus_frame",
    "draw_focus_blockers",
)

EXPERIMENTAL_API = (
    "list_focus_scopes",
    "grid_rect_to_px",
)

LEGACY_INTERNAL_API = (
    "_get_move_window_func",
    "_set_window_always_on_top",
)

def get_api_contract():
    """Return tiered API contract for dependent layers."""
    return {
        "stable": list(STABLE_API),
        "experimental": list(EXPERIMENTAL_API),
        "legacy_internal": list(LEGACY_INTERNAL_API),
    }

class GuiRuntime:
    """Anyware-facing runtime facade with stable lifecycle entrypoints."""

    def __init__(self, *, min_api_level=1):
        require_api_level(min_api_level)
        self.manifest = get_engine_manifest()

    def begin_frame(self, *, clear_char=' ', clear_color=0, reset_overlay=True, advance_frame=True):
        return begin_frame(
            clear_char=clear_char,
            clear_color=clear_color,
            reset_overlay=reset_overlay,
            advance_frame=advance_frame,
        )

    def finish_frame(self, surface, *, flip=False):
        return finish_frame(surface, flip=flip)

    def assert_api_level(self, min_api_level):
        return require_api_level(min_api_level)

def create_runtime(*, min_api_level=1):
    return GuiRuntime(min_api_level=min_api_level)

__all__ = (
    "GUI_ENGINE_NAME",
    "GUI_ENGINE_VERSION",
    "GUI_ENGINE_RELEASE_DATE",
    "GUI_API_LEVEL",
    "GUI_DEPENDENCY_MODEL",
    "EngineManifest",
    "STABLE_API",
    "EXPERIMENTAL_API",
    "LEGACY_INTERNAL_API",
    "get_api_contract",
    "GuiRuntime",
    "create_runtime",
    "frame",
    "fps",
    "target_fps",
    "char_resolution",
    "row_column_resolution",
    "char_block_spacing_px",
    "line_block_spacing_px",
    "border_padding_px",
    "PIXEL_SCALE",
    "window_noframe",
    "window_always_on_top",
    "window_bg_color_rgb",
    "loading_animation",
    "blk",
    "hol",
    *STABLE_API,
    *EXPERIMENTAL_API,
)

# endregion

_apply_display_defaults(rebuild_framebuffers=True)
refresh_palette_cache()
