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
    GUI.clear_focus_nodes()

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

    GUI.set_dynamic_offset(channel="sim_value", value=50.0, wrap = 100.0) # start from 50, updates once per frame

    # button array
    # x,y,w,h are all pixels
    def button(
        x: float,
        y: float,
        color: str,
        node_id: str,
        name: str,
        *,
        nav: dict | None = None,
        w: int = 64,
        h: int = 18,
    ):
        GUI.add_focus_node(
            node_id,
            (x, y, w, h),
            nav=nav,
        )
        focused = GUI.get_focus() == node_id
        selected = False
        try:
            selected = selected_button_label == name
        except:
            pass
        border_color = "blink18" if focused else color
        GUI.draw_rect(border_color, x, y, w, h, filled=False, thickness=1)
        if focused:
            GUI.draw_rect(color, x + 2, y + 2, w - 4, h - 4, filled=False, thickness=1)
        GUI.static(int(round(GUI.px(x))) + 1, int(round(GUI.py(y))) + 1, border_color, name[:8])
        if selected:
            GUI.draw_pattern_rect(color, x + 2, y + 2, w - 4, h - 4, thickness=1)


    # x,y,spacing are all grid coordinates, needs to conv to pixel before calling button
    def button_array(
        x: int,
        y: int,
        index_start: int,
        name_list: list[str],
        color: str,
        col: int,
        row: int,
        *,
        gy_spacing: int = 2,
        gx_spacing: int = 8,
    ):
        total = min(len(name_list), col * row)
        items = []
        for r in range(row):
            for c in range(col):
                idx = r * col + c
                if idx >= total:
                    continue
                node_id = f"btn_{index_start + idx}"
                nav = {}
                if c > 0:
                    nav["left"] = f"btn_{index_start + idx - 1}"
                if c < col - 1 and idx + 1 < total:
                    nav["right"] = f"btn_{index_start + idx + 1}"
                if r > 0:
                    nav["up"] = f"btn_{index_start + idx - col}"
                if r < row - 1 and idx + col < total:
                    nav["down"] = f"btn_{index_start + idx + col}"
                items.append((node_id, name_list[idx], nav, c, r))

        for node_id, name, nav, c, r in items:
                button(
                    GUI.gx(x + c * gx_spacing),
                    GUI.gy(y + r * gy_spacing),
                    color,
                    node_id,
                    name,
                    nav=nav,
                )

        if items and GUI.get_focus(None) is None:
            GUI.set_focus(items[0][0])
        label_map = {node_id: name for node_id, name, _, _, _ in items}
        return label_map
    
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


    selected_button_label = "NONE"
    select_requested = False
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
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    select_requested = True
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
            GUI.step_dynamic_offset('sim_value', speed=1.0, wrap=100.0)
            GUI.draw_box(0, 0, 60, 30, "CRT_Cyan")
            GUI.static(1, 1, "CRT_Cyan", "GAUGES 仪表示例")
            round_needle_gauge(GUI.gx(10), GUI.gy(10), GUI.get_dynamic_offset('sim_value'), 0, 100, "CRT_Cyan", False)
            n1_indicator_gauge(GUI.gx(20), GUI.gy(20), GUI.get_dynamic_offset('sim_value'), 0, 100, "CRT_Cyan")
            button_labels = button_array(
                x=34,
                y=6,
                index_start=1,
                name_list=["ENG", "FUEL", "ELEC", "HYD", "OXY", "APU"],
                color="CRT_Cyan",
                col=3,
                row=2,
            )
            selected_id = GUI.get_focus("none")
            if selected_id in button_labels and select_requested:
                selected_button_label = button_labels[selected_id]
            select_requested = False
            GUI.static(34, 4, "CRT_Cyan", f"FOCUS: {selected_id}")
            GUI.static(34, 5, "CRT_Cyan", f"SELECT: {selected_button_label}")
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
