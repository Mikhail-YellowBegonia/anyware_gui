import time
import sys
import pygame
from _bootstrap import FONTS_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from core import GUI

def main():
    pygame.init()

    # Load fonts (update paths as needed)
    font_ascii = FONTS_DIR / "DEM-MO typeface" / "Mono" / "DEM-MOMono-300.otf"
    font_cjk = FONTS_DIR / "wqy-zenhei" / "wqy-zenhei.ttc"
    GUI.set_fonts(ascii_path=str(font_ascii), cjk_path=str(font_cjk), cell_w=8, cell_h=16, size_px=16)

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
            GUI.begin_frame(clear_color="Black")

            # --- APPLICATION SCENE LOGIC ---
            GUI.draw_box(0, 0, 21, 5, "CRT_Cyan")
            GUI.static(1, 1, "CRT_Cyan", "TEMPLATE")
            # -------------------------------

            GUI.finish_frame(screen_surf)
            last_logic_time = current_time

        pygame.display.flip()
        clock.tick(GUI.target_fps)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
