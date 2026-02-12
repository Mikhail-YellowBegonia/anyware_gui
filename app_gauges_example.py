import os
import time
import sys
import pygame
import GUI
import math

def main():
    pygame.init()

    # Load fonts (update paths as needed)
    font_ascii = os.path.join(os.path.dirname(__file__), "DEM-MO typeface", "Mono", "DEM-MOMono-400.otf")
    font_cjk = os.path.join(os.path.dirname(__file__), "wqy-zenhei", "wqy-zenhei.ttc")
    GUI.set_fonts(ascii_path=font_ascii, cjk_path=font_cjk, cell_w=8, cell_h=16, size_px=16)

    # Calculate window size
    cols, rows = GUI.row_column_resolution
    ch_h, ch_w = GUI.char_resolution
    eff_w = (ch_w + GUI.char_block_spacing_px) * GUI.PIXEL_SCALE
    eff_h = (ch_h + GUI.line_block_spacing_px) * GUI.PIXEL_SCALE
    pad = GUI.border_padding_px * GUI.PIXEL_SCALE
    window_width = int(pad * 2 + cols * eff_w)
    window_height = int(pad * 2 + rows * eff_h)

    screen_surf = pygame.display.set_mode((window_width, window_height), pygame.NOFRAME)
    pygame.display.set_caption("GUI Template")
    GUI._set_window_always_on_top(True)
    clock = pygame.time.Clock()

    move_win, get_pos = GUI._get_move_window_func()
    drag_state = {"active": False, "start_mouse": (0, 0), "start_win": (0, 0)}

    last_logic_time = time.time()
    logic_interval = 1.0 / GUI.fps

    # Pre-register static poly assets once.
    GUI.add_poly(
        "gauge_needle",
        [
            (-2, 10),
            (0, -22),
            (2, 10),
            (0, 6),
        ],
        base_font_height_px=16,
    )


    # --- GAUGES ---

    # this is a tech demo, we tend to use more fixed value than customizable properties

    # round needle gauge
    # x, y: center of the gauge in pixels
    def round_needle_gauge(x: int, y: int, value: float, min_value: float, max_value: float, color: str, endless: bool):
        """
        generate a circle poly + read needle value-> draw poly + draw needle
        """
        circle_poly = [] # 0px,0px centered, 20px radius
        for i in range(360):
            cx = math.cos(i * math.pi / 180)
            cy = math.sin(i * math.pi / 180)
            circle_poly.append((cx * 20, cy * 20))
        # draw_poly default is filled=True, so force outline mode here.
        GUI.draw_poly(circle_poly, color, x, y, filled=False, thickness=1)
        span = max_value - min_value
        if abs(span) < 1e-6:
            ratio = 0.0
        else:
            ratio = (value - min_value) / span
        if endless:
            ratio = ratio % 1.0
        else:
            ratio = max(0.0, min(1.0, ratio))
        angle = ratio * 360.0 - 90.0
        needle_vertices = GUI.rotate_poly_vertices("gauge_needle", angle_deg=angle)
        GUI.draw_poly(
            needle_vertices, color, x, y, filled=False, thickness=1, base_font_height_px=16
        )

    # N1 indication is a fan-shaped filling gauge (so no needle), with a 270 deg fan, the rest 90 deg is a value gauge
    def n1_indicator_gauge(x: int, y: int, value: float, min_value: float, max_value: float, color: str):
        def arc_points(radius: float, start_deg: float, sweep_deg: float):
            pts = []
            end_deg = start_deg + sweep_deg
            for deg in range(int(round(start_deg)), int(round(end_deg)) + 1):
                rad = deg * math.pi / 180.0
                pts.append((math.cos(rad) * radius, math.sin(rad) * radius))
            return pts

        span = max_value - min_value
        ratio = 0.0 if abs(span) < 1e-6 else (value - min_value) / span
        ratio = max(0.0, min(1.0, ratio))

        # Exact 270-degree sector.
        start_deg = 0
        total_sweep_deg = 270.0
        fill_sweep_deg = total_sweep_deg * ratio
        radius = 32.0

        total_fan = [(0.0, 0.0)] + arc_points(radius, start_deg, total_sweep_deg) + [(0.0, 0.0)]
        filled_fan = [(0.0, 0.0)] + arc_points(radius, start_deg, fill_sweep_deg) + [(0.0, 0.0)]

        # Draw fill first then outline.
        GUI.draw_poly(filled_fan, color, x, y, filled=True, thickness=1)
        GUI.draw_poly(total_fan, color, x, y, filled=False, thickness=1)

        # Value bar below fan (pixel coordinates).
        bar_w = 44.0
        bar_h = 6.0
        GUI.draw_rect(color, x - bar_w * 0.5, y + radius + 6.0, bar_w, bar_h, filled=False, thickness=1)
        GUI.draw_rect(color, x - bar_w * 0.5 + 1.0, y + radius + 7.0, (bar_w - 2.0) * ratio, bar_h - 2.0, filled=True, thickness=1)

        # static() uses grid coordinates, convert via GUI.px/py.
        text_col = int(round(GUI.px(x))) + 1
        text_row = int(round(GUI.py(y))) - 2
        GUI.static(text_col, text_row, color, "VALUE") # title
        GUI.static(text_col, text_row + 1, color, f"{value:02.0f}") # value




    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif move_win and get_pos and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                drag_state["active"] = True
                drag_state["start_mouse"] = event.pos
                drag_state["start_win"] = get_pos()
            elif move_win and event.type == pygame.MOUSEMOTION and drag_state["active"]:
                dx = event.pos[0] - drag_state["start_mouse"][0]
                dy = event.pos[1] - drag_state["start_mouse"][1]
                move_win(drag_state["start_win"][0] + dx, drag_state["start_win"][1] + dy)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                drag_state["active"] = False

        current_time = time.time()
        if current_time - last_logic_time >= logic_interval:
            GUI.frame += 1
            GUI.reset_overlays()
            GUI.clear_screen()

            # --- APPLICATION SCENE LOGIC ---
            GUI.draw_box(0, 0, 40, 40, "CRT_Cyan")
            GUI.static(1, 1, "CRT_Cyan", "GAUGES 仪表示例")
            fake_value = GUI.frame % 70
            round_needle_gauge(GUI.gx(10), GUI.gy(10), fake_value, 0, 100, "CRT_Cyan", False)
            n1_indicator_gauge(GUI.gx(20), GUI.gy(20), fake_value, 0, 100, "CRT_Cyan")
            # -------------------------------

            GUI.render(GUI.screen, GUI.screen_color)
            last_logic_time = current_time

        GUI.draw_to_surface(screen_surf)
        pygame.display.flip()
        clock.tick(GUI.target_fps)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
