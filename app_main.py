import os
import sys
import time
import pygame
import GUI


GUI.add_poly(
    "pattern_debug_poly",
    [
        (0, 0),
        (32, 4),
        (44, 20),
        (24, 34),
        (2, 28),
    ],
    base_font_height_px=16,
)

PATTERN_OFFSET_CHANNEL = "app_main.pattern_debug"

def main():
    pygame.init()

    # Window/display overrides (new in GUI core)
    GUI.set_display_defaults(
        fps=20,
        target_fps=60,
        window_noframe=False,
        window_always_on_top=False,
        window_bg_color_rgb=(8, 12, 12),
    )

    font_ascii = os.path.join(os.path.dirname(__file__), "DEM-MO typeface", "Mono", "DEM-MOMono-400.otf")
    font_cjk = os.path.join(os.path.dirname(__file__), "wqy-zenhei", "wqy-zenhei.ttc")
    GUI.set_fonts(ascii_path=font_ascii, cjk_path=font_cjk, cell_w=8, cell_h=16, size_px=16)

    screen_surf = pygame.display.set_mode(GUI.get_window_size_px(), GUI.get_window_flags())
    pygame.display.set_caption("GUI Pattern Debug Demo")
    if GUI.window_always_on_top:
        GUI._set_window_always_on_top(True)

    clock = pygame.time.Clock()
    move_win, get_pos = GUI._get_move_window_func()
    drag_state = {"active": False, "start_mouse": (0, 0), "start_win": (0, 0)}

    pattern = {
        "mode": "rect",
        "spacing": 4.0,
        "angle_deg": 45.0,
        "thickness": 1.0,
        "offset": 0.0,
        "auto_offset": True,
    }

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
                elif event.key == pygame.K_LEFT:
                    pattern["spacing"] = max(1.0, pattern["spacing"] - 0.5)
                elif event.key == pygame.K_RIGHT:
                    pattern["spacing"] = pattern["spacing"] + 0.5
                elif event.key == pygame.K_UP:
                    pattern["angle_deg"] = (pattern["angle_deg"] + 5.0) % 180.0
                elif event.key == pygame.K_DOWN:
                    pattern["angle_deg"] = (pattern["angle_deg"] - 5.0) % 180.0
                elif event.key == pygame.K_LEFTBRACKET:
                    pattern["offset"] -= 0.5
                elif event.key == pygame.K_RIGHTBRACKET:
                    pattern["offset"] += 0.5
                elif event.key == pygame.K_MINUS:
                    pattern["thickness"] = max(0.2, pattern["thickness"] - 0.2)
                elif event.key == pygame.K_EQUALS:
                    pattern["thickness"] = pattern["thickness"] + 0.2
                elif event.key == pygame.K_m:
                    pattern["mode"] = "poly" if pattern["mode"] == "rect" else "rect"
                elif event.key == pygame.K_p:
                    pattern["auto_offset"] = not pattern["auto_offset"]
                    if pattern["auto_offset"]:
                        GUI.set_dynamic_offset(PATTERN_OFFSET_CHANNEL, pattern["offset"], wrap=1000.0)
                    else:
                        pattern["offset"] = GUI.get_dynamic_offset(PATTERN_OFFSET_CHANNEL, pattern["offset"])
                elif event.key == pygame.K_r:
                    pattern = {
                        "mode": "rect",
                        "spacing": 4.0,
                        "angle_deg": 45.0,
                        "thickness": 1.0,
                        "offset": 0.0,
                        "auto_offset": True,
                    }
                    GUI.set_dynamic_offset(PATTERN_OFFSET_CHANNEL, 0.0, wrap=1000.0)
            elif (
                GUI.window_noframe
                and move_win
                and get_pos
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                drag_state["active"] = True
                drag_state["start_mouse"] = event.pos
                drag_state["start_win"] = get_pos()
            elif GUI.window_noframe and move_win and event.type == pygame.MOUSEMOTION and drag_state["active"]:
                dx = event.pos[0] - drag_state["start_mouse"][0]
                dy = event.pos[1] - drag_state["start_mouse"][1]
                move_win(drag_state["start_win"][0] + dx, drag_state["start_win"][1] + dy)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                drag_state["active"] = False

        current_time = time.time()
        if current_time - last_logic_time >= logic_interval:
            GUI.frame += 1
            GUI.reset_overlays()
            GUI.clear_screen(color="Black")

            if pattern["auto_offset"]:
                pattern["offset"] = GUI.step_dynamic_offset(PATTERN_OFFSET_CHANNEL, speed=0.2, wrap=1000.0)

            cols, rows = GUI.row_column_resolution
            GUI.draw_box(0, 0, cols - 1, rows - 1, "CRT_Cyan", thickness=2)
            GUI.static(2, 1, "CRT_Cyan", "PATTERN DEBUG DEMO")
            GUI.static(2, 2, "CRT_Cyan", "Arrows:spacing/angle  [-]/[+]:offset  -/=:thickness")
            GUI.static(2, 3, "CRT_Cyan", "M:mode  P:auto-offset  R:reset  ESC:quit")
            GUI.static(2, 4, "CRT_Cyan", f"mode={pattern['mode']}  spacing={pattern['spacing']:.1f}")
            GUI.static(2, 5, "CRT_Cyan", f"angle={pattern['angle_deg']:.1f}  thickness={pattern['thickness']:.1f}")
            GUI.static(2, 6, "CRT_Cyan", f"offset={pattern['offset']:.1f}  auto={pattern['auto_offset']}")

            GUI.hstatic(2, 10, "CRT_Cyan", "竖排测试", line_step=2)
            GUI.hstatic(5, 10, "CRT_Cyan", "HSTATIC", line_step=2)

            x1, y1 = GUI.grid_to_px(16, 8, 1, 1)
            x2, y2 = GUI.grid_to_px(cols - 2, rows - 2, -1, -1)
            view_w = max(10.0, x2 - x1)
            view_h = max(10.0, y2 - y1)

            GUI.draw_rect("CRT_Cyan", x1, y1, view_w, view_h, filled=False, thickness=1)

            if pattern["mode"] == "rect":
                GUI.draw_pattern_rect(
                    "CRT_Cyan",
                    x1 + 2,
                    y1 + 2,
                    view_w - 4,
                    view_h - 4,
                    spacing=pattern["spacing"],
                    angle_deg=pattern["angle_deg"],
                    thickness=pattern["thickness"],
                    offset=pattern["offset"],
                )
            else:
                px = x1 + view_w * 0.25
                py = y1 + view_h * 0.2
                GUI.draw_pattern_poly(
                    "pattern_debug_poly",
                    "CRT_Cyan",
                    px,
                    py,
                    spacing=pattern["spacing"],
                    angle_deg=pattern["angle_deg"],
                    thickness=pattern["thickness"],
                    offset=pattern["offset"],
                )
                GUI.draw_poly("pattern_debug_poly", "CRT_Cyan", px, py, filled=False, thickness=1)

            GUI.render(GUI.screen, GUI.screen_color)
            last_logic_time = current_time

        GUI.draw_to_surface(screen_surf)
        pygame.display.flip()
        clock.tick(GUI.target_fps)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
