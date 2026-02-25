import sys
import time
import math
import pygame
from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core import GUI


GUI.add_poly(
    "example_arrow",
    [
        (0, 8),
        (10, 0),
        (10, 5),
        (24, 5),
        (24, 11),
        (10, 11),
        (10, 16),
    ],
    base_font_height_px=16,
)

GUI.add_poly(
    "example_diamond",
    [
        (12, 0),
        (24, 12),
        (12, 24),
        (0, 12),
    ],
    base_font_height_px=16,
)

GUI.add_poly(
    "example_needle",
    [
        (-2, 10),
        (0, -22),
        (2, 10),
        (0, 6),
    ],
    base_font_height_px=16,
)

AUTO_OFFSET_CHANNEL = "app_example.pattern.auto"


def main():
    pygame.init()

    # Recommended display setup for examples
    GUI.set_display_defaults(
        fps=16,
        target_fps=60,
        window_noframe=False,
        window_always_on_top=False,
        window_bg_color_rgb=(8, 12, 14),
    )

    # Optional global style defaults
    GUI.set_draw_defaults(
        box={"padding": 0.0, "thickness": 1},
        ani={"slowdown": 1},
        pattern={"spacing": 4.0, "angle_deg": 45.0, "thickness": 1.0, "offset": 0.0},
    )

    font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-300.otf"
    font_cjk = FONTS_DIR / "wqy-zenhei" / "wqy-zenhei.ttc"
    GUI.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

    screen_surf = pygame.display.set_mode(GUI.get_present_size_px(), GUI.get_window_flags())
    GUI.apply_display_dpi_from_surface(screen_surf)
    pygame.display.set_caption("GUI Example Showcase")
    if GUI.window_always_on_top:
        GUI._set_window_always_on_top(True)

    clock = pygame.time.Clock()

    auto_offset = True
    manual_offset = 0.0
    GUI.set_dynamic_offset(AUTO_OFFSET_CHANNEL, 0.0, wrap=1000.0)

    # Focus/navigation demo nodes (no scope switching in this phase)
    GUI.clear_focus_nodes()
    px1, py1 = GUI.grid_to_px(16, 7, 1, 1)
    px2, py2 = GUI.grid_to_px(36, 7, 1, 1)
    pxa, pya = GUI.grid_to_px(20, 19, 0, 0)
    pxd, pyd = GUI.grid_to_px(36, 19, 0, 0)
    GUI.add_focus_node("title", GUI.grid_rect_to_px(1, 1, 14, 3), nav={"down": "rect_left"})
    GUI.add_focus_node(
        "rect_left",
        (px1, py1, 150, 90),
        nav={"up": "title", "right": "rect_right", "down": "poly_arrow"},
    )
    GUI.add_focus_node(
        "rect_right",
        (px2, py2, 150, 90),
        nav={"up": "title", "left": "rect_left", "down": "poly_diamond"},
    )
    GUI.add_focus_node("poly_arrow", (pxa, pya, 24, 16), nav={"up": "rect_left", "right": "poly_diamond"})
    GUI.add_focus_node("poly_diamond", (pxd, pyd, 24, 24), nav={"up": "rect_right", "left": "poly_arrow"})
    GUI.set_focus("title")

    last_logic_time = time.time()
    logic_interval = 1.0 / GUI.fps

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif GUI.key_to_focus_direction(event.key) is not None:
                    GUI.move_focus_by_key(event.key)
                elif event.key == pygame.K_SPACE:
                    auto_offset = not auto_offset
                    if auto_offset:
                        GUI.set_dynamic_offset(AUTO_OFFSET_CHANNEL, manual_offset, wrap=1000.0)
                    else:
                        manual_offset = GUI.get_dynamic_offset(AUTO_OFFSET_CHANNEL, manual_offset)
                elif event.key == pygame.K_LEFTBRACKET:
                    manual_offset -= 0.5
                elif event.key == pygame.K_RIGHTBRACKET:
                    manual_offset += 0.5
                elif event.key == pygame.K_r:
                    auto_offset = True
                    manual_offset = 0.0
                    GUI.set_dynamic_offset(AUTO_OFFSET_CHANNEL, 0.0, wrap=1000.0)

        current_time = time.time()
        if current_time - last_logic_time >= logic_interval:
            GUI.frame += 1
            GUI.reset_overlays()
            GUI.clear_screen(color="Black")

            offset = (
                GUI.step_dynamic_offset(AUTO_OFFSET_CHANNEL, speed=0.2, wrap=1000.0)
                if auto_offset
                else manual_offset
            )

            cols, rows = GUI.row_column_resolution
            GUI.draw_box(0, 0, cols - 1, rows - 1, "CRT_Cyan", thickness=2)
            GUI.static(2, 1, "CRT_Cyan", "GUI EXAMPLE")
            GUI.static(2, 2, "CRT_Cyan", "ARROWS:navigate  SPACE:auto offset  [ / ]:manual offset")
            GUI.static(2, 3, "CRT_Cyan", f"offset={offset:.1f}  auto={auto_offset}")
            GUI.static(2, 4, "CRT_Cyan", f"focus={GUI.get_focus('none')}  R:reset  ESC:quit")
            GUI.sweep(1, 34, 56, "blink16", "blink31")

            # clear_row / clear_cell examples
            GUI.clear_row(6, char=" ", color="Black")
            GUI.static(2, 6, "CRT_Cyan", "clear_row() + clear_cell() demo")
            GUI.static(34, 6, "CRT_Cyan", "[ERASED]")
            for c in range(34, 42):
                GUI.clear_cell(c, 6, char=" ", color="Black")

            # static / hstatic / ani_char
            GUI.static(2, 8, "CRT_Cyan", "static(): Hello 你好")
            GUI.hstatic(2, 10, "CRT_Cyan", "竖排示例", line_step=2)
            GUI.hstatic(6, 10, "CRT_Cyan", "HSTATIC", line_step=2)
            GUI.ani_char(10, 8, ["blink10", "blink18", "blink26"], GUI.loading_animation)

            # draw_rect / draw_pattern_rect (default + override)
            px1, py1 = GUI.grid_to_px(16, 7, 1, 1)
            GUI.draw_rect("CRT_Cyan", px1, py1, 150, 90, filled=False, thickness=1)
            GUI.draw_pattern_rect("CRT_Cyan", px1 + 2, py1 + 2, 146, 86, offset=offset)  # mostly defaults

            px2, py2 = GUI.grid_to_px(36, 7, 1, 1)
            GUI.draw_rect("CRT_Cyan", px2, py2, 150, 90, filled=False, thickness=1)
            GUI.draw_pattern_rect(
                "CRT_Cyan",
                px2 + 2,
                py2 + 2,
                146,
                86,
                spacing=3.0,
                angle_deg=25.0,
                thickness=1.2,
                offset=offset,
            )

            # draw_poly / draw_pattern_poly
            pxa, pya = GUI.grid_to_px(20, 19, 0, 0)
            GUI.draw_poly("example_arrow", "CRT_Cyan", pxa, pya, filled=False, thickness=1)
            GUI.draw_pattern_poly("example_arrow", "CRT_Cyan", pxa, pya, spacing=3.5, angle_deg=65.0, offset=offset)

            pxd, pyd = GUI.grid_to_px(36, 19, 0, 0)
            GUI.draw_poly("example_diamond", "CRT_Cyan", pxd, pyd, filled=False, thickness=1)
            GUI.draw_pattern_poly("example_diamond", "CRT_Cyan", pxd, pyd, spacing=4.0, angle_deg=135.0, offset=offset)

            # poly transform: rescale + rotate around (0, 0)
            gcx, gcy = GUI.grid_to_px(52, 20, 0, 0)
            pulse = 1.0 + 0.18 * math.sin(GUI.frame * 0.08)
            angle = (GUI.frame * 4.0) % 360.0
            needle = GUI.transform_poly_vertices("example_needle", scale_x=1.4, scale_y=pulse, angle_deg=angle)
            GUI.draw_rect("CRT_Cyan", gcx - 20, gcy - 20, 40, 40, filled=False, thickness=1)
            GUI.draw_poly(needle, "blink18", gcx, gcy, filled=False, thickness=1.2)
            GUI.static(49, 23, "CRT_Cyan", "TRANSFORM")
            GUI.static(49, 24, "CRT_Cyan", f"a={angle:05.1f} s={pulse:.2f}")

            GUI.draw_focus_frame("blink18", padding=2.0, thickness=1.2)

            GUI.render(GUI.screen, GUI.screen_color)
            last_logic_time = current_time

        GUI.draw_to_surface(screen_surf)
        pygame.display.flip()
        clock.tick(GUI.target_fps)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
