import pygame

from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core import GUI
from core.anyware import AnywareApp, Button, Label, Page, SegmentDisplay

_COLOR = "White"

# --- Manual layout constants (grid units) ---
GRID_COLS = 60
GRID_ROWS = 50

PANEL_W = 55
PANEL_H = 39

LEFT_X = 4
LEFT_Y = 1
LEFT_W = 23
LEFT_H = 23

RIGHT_X = 28
RIGHT_Y = 1
RIGHT_W = 23
RIGHT_H = 23

KEY_X = 2
KEY_Y = 24
KEY_W = 51
KEY_H = 14

STATUS_COL_W = 8
STATUS_COL_GAP = 2
STATUS_ROW_H = 2
STATUS_ROW_GAP = 1

DISPLAY_TOP_H = 9
DISPLAY_LOWER_GAP = 2
DISPLAY_ROW_H = 4

KEY_COL_W = 6
KEY_COL_GAP = 1
KEY_ROW_H = 3
KEY_ROW_GAP = 1
KEY_OFFSET = 2

# Segment display sizing (px)
SEG2_DIGIT_W = 22
SEG2_DIGIT_H = 36
SEG2_SPACING = 6
SEG5_DIGIT_W = 22
SEG5_DIGIT_H = 36
SEG5_SPACING = 6


def gw_px(cols: float) -> float:
    return GUI.gx(cols) - GUI.gx(0)


def gh_px(rows: float) -> float:
    return GUI.gy(rows) - GUI.gy(0)


class DskyPage(Page):
    def __init__(self):
        super().__init__("dsky")
        self._first_key_id: str | None = None
        self._build_status_panel()
        self._build_display_panel()
        self._build_keypad()

    def _center_x(self, gx: int, w_cols: int, text: str) -> int:
        return gx + max(0, (w_cols - len(text)) // 2)

    def _place_lines(self, gx: int, gy: int, w_cols: int, h_rows: int, lines: list[str], color: str):
        if not lines:
            return
        start = gy + max(0, (h_rows - len(lines)) // 2)
        for idx, line in enumerate(lines):
            self.add(
                Label(
                    gx=self._center_x(gx, w_cols, line),
                    gy=start + idx,
                    text=line,
                    color=color,
                )
            )

    def _add_status_light(self, light_id: str, gx: int, gy: int, w_cols: int, h_rows: int, label: str):
        btn = Button(
            light_id,
            "",
            gx=gx,
            gy=gy,
            width_px=gw_px(w_cols),
            height_px=gh_px(h_rows),
            color=_COLOR,
            pressable=False,
            focusable=False,
        )
        self.add(btn)

        if not label:
            return
        self._place_lines(gx, gy, w_cols, h_rows, label.split("\n"), _COLOR)

    def _build_status_panel(self):
        left_x = LEFT_X + 2
        left_y = LEFT_Y + 1
        col_w = STATUS_COL_W
        col_gap = STATUS_COL_GAP
        row_h = STATUS_ROW_H
        row_gap = STATUS_ROW_GAP

        rows = [
            ("UPLINK\nACTY", "TEMP"),
            ("NO ATT", "GIMBAL\nLOCK"),
            ("STBY", "PROG"),
            ("KEY REL", "RESTART"),
            ("OPR ERR", "TRACKER"),
            ("", "ALT"),
            ("", "VEL"),
        ]

        for r, (left_label, right_label) in enumerate(rows):
            y = left_y + r * (row_h + row_gap)
            self._add_status_light(
                f"status_l_{r}",
                left_x,
                y,
                col_w,
                row_h,
                left_label,
            )
            self._add_status_light(
                f"status_r_{r}",
                left_x + col_w + col_gap,
                y,
                col_w,
                row_h,
                right_label,
            )

    def _build_display_panel(self):
        rp_x = RIGHT_X
        rp_y = RIGHT_Y
        rp_w = RIGHT_W
        top_h = DISPLAY_TOP_H
        quad_w = rp_w // 2
        quad_h = top_h // 2

        # COMP ACTY indicator
        self._add_status_light(
            "comp_acty",
            rp_x + 2,
            rp_y + 1,
            quad_w - 3,
            4,
            "COMP\nACTY",
        )

        # PROG / VERB / NOUN labels and 2-digit displays
        self.add(Label(gx=rp_x + quad_w + 2, gy=rp_y + 1, text="PROG", color=_COLOR))
        self.add(
            SegmentDisplay(
                gx=rp_x + quad_w + 2,
                gy=rp_y + 3,
                text="00",
                digits=2,
                digit_w_px=SEG2_DIGIT_W,
                digit_h_px=SEG2_DIGIT_H,
                spacing_px=SEG2_SPACING,
                on_color=_COLOR,
                off_color=None,
            )
        )

        self.add(Label(gx=rp_x + 2, gy=rp_y + quad_h + 2, text="VERB", color=_COLOR))
        self.add(
            SegmentDisplay(
                gx=rp_x + 2,
                gy=rp_y + quad_h + 4,
                text="00",
                digits=2,
                digit_w_px=SEG2_DIGIT_W,
                digit_h_px=SEG2_DIGIT_H,
                spacing_px=SEG2_SPACING,
                on_color=_COLOR,
                off_color=None,
            )
        )

        self.add(Label(gx=rp_x + quad_w + 2, gy=rp_y + quad_h + 2, text="NOUN", color=_COLOR))
        self.add(
            SegmentDisplay(
                gx=rp_x + quad_w + 2,
                gy=rp_y + quad_h + 4,
                text="00",
                digits=2,
                digit_w_px=SEG2_DIGIT_W,
                digit_h_px=SEG2_DIGIT_H,
                spacing_px=SEG2_SPACING,
                on_color=_COLOR,
                off_color=None,
            )
        )

        # Lower 3-line numeric displays (5 digits + sign)
        lower_y = rp_y + top_h + DISPLAY_LOWER_GAP
        disp_row_h = DISPLAY_ROW_H
        for i in range(3):
            y = lower_y + i * disp_row_h
            self.add(Label(gx=rp_x + 2, gy=y + 1, text="+", color=_COLOR))
            self.add(
                SegmentDisplay(
                    gx=rp_x + 4,
                    gy=y,
                    text="00000",
                    digits=5,
                    digit_w_px=SEG5_DIGIT_W,
                    digit_h_px=SEG5_DIGIT_H,
                    spacing_px=SEG5_SPACING,
                    on_color=_COLOR,
                    off_color=None,
                )
            )

    def _add_key(self, key_id: str, gx: int, gy: int, w_cols: int, h_rows: int, label: str):
        btn = Button(
            key_id,
            label if "\n" not in label else "",
            gx=gx,
            gy=gy,
            width_px=gw_px(w_cols),
            height_px=gh_px(h_rows),
            scope="keys",
            color=_COLOR,
        )
        self.add(btn)

        lines = label.split("\n")
        if len(lines) > 1:
            self._place_lines(gx, gy, w_cols, h_rows, lines, _COLOR)

        if self._first_key_id is None:
            self._first_key_id = key_id

    def _build_keypad(self):
        key_x = KEY_X
        key_y = KEY_Y
        col_w = KEY_COL_W
        col_gap = KEY_COL_GAP
        row_h = KEY_ROW_H
        row_gap = KEY_ROW_GAP

        start_x = key_x + 1
        start_y = key_y + 1

        row0 = start_y
        row1 = row0 + row_h + row_gap
        row2 = row1 + row_h + row_gap
        offset = KEY_OFFSET

        # Side buttons (offset rows)
        self._add_key("key_verb", start_x + 0 * (col_w + col_gap), row0 + offset, col_w, row_h, "VERB")
        self._add_key("key_noun", start_x + 0 * (col_w + col_gap), row1 + offset, col_w, row_h, "NOUN")
        self._add_key("key_entr", start_x + 6 * (col_w + col_gap), row0 + offset, col_w, row_h, "ENTR")
        self._add_key("key_rset", start_x + 6 * (col_w + col_gap), row1 + offset, col_w, row_h, "RSET")

        # Middle 5 columns x 3 rows
        row0_labels = ["+", "7", "8", "9", "CLR"]
        row1_labels = ["-", "4", "5", "6", "PRO"]
        row2_labels = ["0", "1", "2", "3", "KEY\nREL"]
        for c, label in enumerate(row0_labels, start=1):
            self._add_key(f"key_r0_{c}", start_x + c * (col_w + col_gap), row0, col_w, row_h, label)
        for c, label in enumerate(row1_labels, start=1):
            self._add_key(f"key_r1_{c}", start_x + c * (col_w + col_gap), row1, col_w, row_h, label)
        for c, label in enumerate(row2_labels, start=1):
            self._add_key(f"key_r2_{c}", start_x + c * (col_w + col_gap), row2, col_w, row_h, label)

    def on_enter(self, ctx) -> None:
        if self._first_key_id:
            ctx.set_active_focus_scope("keys")
            ctx.set_focus(self._first_key_id)

    def handle_event(self, event, ctx) -> bool:
        if event.type == pygame.KEYDOWN and ctx.key_to_focus_direction(event.key) is not None:
            ctx.move_focus_by_key(event.key)
            return True
        return super().handle_event(event, ctx)

    def render(self, ctx) -> None:
        panel_w = PANEL_W
        panel_h = PANEL_H

        left_x = LEFT_X
        left_y = LEFT_Y
        left_w = LEFT_W
        left_h = LEFT_H

        right_x = RIGHT_X
        right_y = RIGHT_Y
        right_w = RIGHT_W
        right_h = RIGHT_H

        key_x = KEY_X
        key_y = KEY_Y
        key_w = KEY_W
        key_h = KEY_H

        ctx.draw_box(0, 0, panel_w - 1, panel_h - 1, _COLOR, thickness=2)
        ctx.draw_box(left_x, left_y, left_w - 1, left_h - 1, _COLOR, thickness=1)
        ctx.draw_box(right_x, right_y, right_w - 1, right_h - 1, _COLOR, thickness=1)
        ctx.draw_box(key_x, key_y, key_w - 1, key_h - 1, _COLOR, thickness=1)

        # Separator in right panel
        sep_y = right_y + DISPLAY_TOP_H - 1
        x_px = ctx.gx(right_x)
        y_px = ctx.gy(sep_y) + 40
        w_px = ctx.gx(right_x + right_w) - ctx.gx(right_x) - 10
        ctx.draw_rect(_COLOR, x_px, y_px, w_px, 1, filled=True, thickness=1)

        super().render(ctx)
        ctx.draw_focus_frame("blink18", padding=2.0, thickness=1.2)


def main():
    app = AnywareApp(
        title="DSKY Integration Test",
        clear_color="Black",
        display_defaults={
            "rows": GRID_ROWS,
            "cols": GRID_COLS,
            "fps": 10,
            "target_fps": 60,
            "window_noframe": False,
            "window_always_on_top": False,
            "window_bg_color_rgb": (8, 12, 14),
        },
        allow_raw_gui=False,
        min_gui_api_level=1,
    )

    font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-400.otf"
    font_cjk = FONTS_DIR / "wqy-zenhei" / "wqy-zenhei.ttc"
    app.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

    app.set_root_page(DskyPage())
    app.run()


if __name__ == "__main__":
    main()
