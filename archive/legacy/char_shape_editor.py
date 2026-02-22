#!/usr/bin/env python3
"""
字符形状编辑器 (V2)：
- 仅支持 JSON 格式，统一使用 "chars" 键。
- 动态分辨率支持。
- 实时预览全部 128 个 ASCII 字符。
- 点击预览图快速切换字符。
"""
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# 默认设置
ASCII_MAX = 127

def load_char_set_json(path: str) -> dict:
    """从 JSON 文件加载字符集。支持 'chars' 或 'characters' 键。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 归一化键名
    if "characters" in data and "chars" not in data:
        data["chars"] = data.pop("characters")
    return data

def save_char_set_json(path: str, resolution: list, chars: dict) -> None:
    """保存为 JSON。"""
    data = {"resolution": resolution, "chars": chars}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class CharShapeEditor:
    def __init__(self, width: int = 7, height: int = 6):
        self.width = width
        self.height = height
        self.current_char = "A"
        # 初始化 128 个字符的空白格
        self.chars = {chr(i): [[0 for _ in range(width)] for _ in range(height)] for i in range(128)}
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        
        self.root = tk.Tk()
        self.root.title("ASCII 字符编辑器 (Flexible Resolution)")
        self.root.geometry("1000x600")
        
        # 左侧编辑区
        self.left_panel = ttk.Frame(self.root, padding=10)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        
        # 顶部配置
        f_config = ttk.Frame(self.left_panel)
        f_config.pack(fill=tk.X, pady=5)
        
        ttk.Label(f_config, text="W:").pack(side=tk.LEFT)
        self.var_w = tk.StringVar(value=str(self.width))
        ttk.Entry(f_config, textvariable=self.var_w, width=3).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(f_config, text="H:").pack(side=tk.LEFT)
        self.var_h = tk.StringVar(value=str(self.height))
        ttk.Entry(f_config, textvariable=self.var_h, width=3).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(f_config, text="调整尺寸", command=self._resize_grid).pack(side=tk.LEFT, padx=5)
        
        # 当前字符
        f_char = ttk.Frame(self.left_panel)
        f_char.pack(fill=tk.X, pady=5)
        ttk.Label(f_char, text="当前字符:").pack(side=tk.LEFT)
        self.var_char = tk.StringVar(value="A")
        self.entry_char = ttk.Entry(f_char, textvariable=self.var_char, width=5)
        self.entry_char.pack(side=tk.LEFT, padx=2)
        ttk.Button(f_char, text="应用", command=self._on_char_commit).pack(side=tk.LEFT, padx=2)
        
        # 编辑画布
        self.cell_size = 40
        self.canvas_w = 400
        self.canvas_h = 400
        self.canvas = tk.Canvas(self.left_panel, width=self.canvas_w, height=self.canvas_h, bg="#1e1e1e")
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self._on_click)
        self.rect_ids = []
        
        # 底部按钮
        f_btns = ttk.Frame(self.left_panel)
        f_btns.pack(fill=tk.X, pady=5)
        ttk.Button(f_btns, text="加载 JSON", command=self._open_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(f_btns, text="保存 JSON", command=self._save_json).pack(side=tk.LEFT, padx=2)

        # 右侧预览区
        self.right_panel = ttk.Frame(self.root, padding=10)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        ttk.Label(self.right_panel, text="实时预览 (32-127)").pack()
        
        self.preview_canvas = tk.Canvas(self.right_panel, bg="#111")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.bind("<Button-1>", self._on_preview_click)
        
        self._sync_grid_to_current()
        self._build_canvas()
        self._draw_all_previews()
        
        # 状态栏
        self.status = tk.StringVar(value="准备就绪")
        ttk.Label(self.root, textvariable=self.status, relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X)

    def _sync_grid_to_current(self):
        self.grid = [row[:] for row in self.chars.get(self.current_char, [[0]*self.width for _ in range(self.height)])]

    def _save_current_to_chars(self):
        self.chars[self.current_char] = [row[:] for row in self.grid]

    def _build_canvas(self):
        self.canvas.delete("all")
        self.rect_ids = []
        # 计算居中起始位置
        start_x = (self.canvas_w - self.width * self.cell_size) // 2
        start_y = (self.canvas_h - self.height * self.cell_size) // 2
        
        for r in range(self.height):
            row_ids = []
            for c in range(self.width):
                x1, y1 = start_x + c * self.cell_size, start_y + r * self.cell_size
                x2, y2 = x1 + self.cell_size - 1, y1 + self.cell_size - 1
                color = "#4fc3f7" if self.grid[r][c] else "#333"
                rid = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#555")
                row_ids.append(rid)
            self.rect_ids.append(row_ids)

    def _refresh_canvas(self):
        for r in range(self.height):
            for c in range(self.width):
                color = "#4fc3f7" if self.grid[r][c] else "#333"
                if r < len(self.rect_ids) and c < len(self.rect_ids[r]):
                    self.canvas.itemconfig(self.rect_ids[r][c], fill=color)

    def _on_click(self, event):
        start_x = (self.canvas_w - self.width * self.cell_size) // 2
        start_y = (self.canvas_h - self.height * self.cell_size) // 2
        c = (event.x - start_x) // self.cell_size
        r = (event.y - start_y) // self.cell_size
        if 0 <= r < self.height and 0 <= c < self.width:
            self.grid[r][c] = 1 - self.grid[r][c]
            self._refresh_canvas()
            self._save_current_to_chars()
            self._draw_single_preview(ord(self.current_char))

    def _on_char_commit(self):
        s = self.var_char.get()
        if len(s) == 1:
            self._save_current_to_chars()
            self.current_char = s
            self._sync_grid_to_current()
            self._build_canvas()
            self.status.set(f"当前编辑: {repr(s)}")
        else:
            self.status.set("错误: 必须输入单个字符")

    def _resize_grid(self):
        try:
            new_w = int(self.var_w.get())
            new_h = int(self.var_h.get())
            if new_w < 1 or new_h < 1 or new_w > 20 or new_h > 20:
                raise ValueError
            
            # 转换所有字符的数据
            for ch in self.chars:
                old_data = self.chars[ch]
                new_data = [[0 for _ in range(new_w)] for _ in range(new_h)]
                for r in range(min(new_h, len(old_data))):
                    for c in range(min(new_w, len(old_data[0]))):
                        new_data[r][c] = old_data[r][c]
                self.chars[ch] = new_data
            
            self.width, self.height = new_w, new_h
            self._sync_grid_to_current()
            self._build_canvas()
            self._draw_all_previews()
            self.status.set(f"尺寸调整为 {new_w}x{new_h}")
        except ValueError:
            messagebox.showerror("错误", "请输入 1-20 之间的整数")

    # 预览逻辑
    def _draw_all_previews(self):
        self.preview_canvas.delete("all")
        self.preview_rects = {} # char_code -> rect_list
        
        # 16列 x 8行 (从 0 到 127)
        cols = 16
        cell_w = 30
        cell_h = 40
        padding = 5
        
        for i in range(128):
            row = i // cols
            col = i % cols
            x_base = col * (cell_w + padding) + 10
            y_base = row * (cell_h + padding) + 10
            
            # 绘制字符标签
            char_label = repr(chr(i)) if i > 32 else str(i)
            self.preview_canvas.create_text(x_base + cell_w//2, y_base - 5, text=char_label, fill="#888", font=("Arial", 6))
            
            # 绘制小网格
            p_w = cell_w / self.width
            p_h = (cell_h - 10) / self.height
            data = self.chars.get(chr(i), [[0]*self.width for _ in range(self.height)])
            
            for r in range(self.height):
                for c in range(self.width):
                    x1 = x_base + c * p_w
                    y1 = y_base + r * p_h
                    x2 = x1 + p_w
                    y2 = y1 + p_h
                    color = "#4fc3f7" if data[r][c] else "#222"
                    self.preview_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags=f"p{i}")
            
            # 背景透明层捕获点击
            self.preview_canvas.create_rectangle(x_base, y_base, x_base+cell_w, y_base+cell_h-10, fill="", outline="#444", tags=f"p{i}")

    def _draw_single_preview(self, char_code):
        self.preview_canvas.delete(f"p{char_code}")
        cols = 16
        cell_w = 30
        cell_h = 40
        padding = 5
        
        i = char_code
        row = i // cols
        col = i % cols
        x_base = col * (cell_w + padding) + 10
        y_base = row * (cell_h + padding) + 10
        
        p_w = cell_w / self.width
        p_h = (cell_h - 10) / self.height
        data = self.chars[chr(i)]
        
        for r in range(self.height):
            for c in range(self.width):
                x1 = x_base + c * p_w
                y1 = y_base + r * p_h
                x2 = x1 + p_w
                y2 = y1 + p_h
                color = "#4fc3f7" if data[r][c] else "#222"
                self.preview_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags=f"p{i}")
        self.preview_canvas.create_rectangle(x_base, y_base, x_base+cell_w, y_base+cell_h-10, fill="", outline="#444", tags=f"p{i}")

    def _on_preview_click(self, event):
        item = self.preview_canvas.find_closest(event.x, event.y)
        tags = self.preview_canvas.gettags(item)
        for t in tags:
            if t.startswith("p"):
                try:
                    code = int(t[1:])
                    self.var_char.set(chr(code))
                    self._on_char_commit()
                except ValueError:
                    pass

    def _open_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path: return
        try:
            data = load_char_set_json(path)
            res = data.get("resolution", [7, 6])
            self.width, self.height = res[0], res[1]
            self.var_w.set(str(self.width))
            self.var_h.set(str(self.height))
            
            # 加载数据，确保 128 个字符都有占位
            loaded_chars = data.get("chars", {})
            self.chars = {chr(i): [[0 for _ in range(self.width)] for _ in range(self.height)] for i in range(128)}
            for k, v in loaded_chars.items():
                if len(k) == 1:
                    self.chars[k] = v
            
            self._sync_grid_to_current()
            self._build_canvas()
            self._draw_all_previews()
            self.status.set(f"已加载: {path}")
        except Exception as e:
            messagebox.showerror("失败", str(e))

    def _save_json(self):
        self._save_current_to_chars()
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path: return
        try:
            save_char_set_json(path, [self.width, self.height], self.chars)
            messagebox.showinfo("成功", "保存成功")
        except Exception as e:
            messagebox.showerror("失败", str(e))

    def run(self):
        self.root.mainloop()

# 供外部调用的简易加载接口
def load_char_set_file(path: str) -> tuple:
    data = load_char_set_json(path)
    res = data.get("resolution", [7, 6])
    return (res[0], res[1]), data.get("chars", {})

if __name__ == "__main__":
    # 尝试自动加载当前目录的 char_set.json
    editor = CharShapeEditor()
    if os.path.exists("char_set.json"):
        try:
            data = load_char_set_json("char_set.json")
            res = data.get("resolution", [7, 6])
            editor.width, editor.height = res[0], res[1]
            editor.var_w.set(str(editor.width))
            editor.var_h.set(str(editor.height))
            chars = data.get("chars", {})
            for k, v in chars.items():
                if len(k) == 1:
                    editor.chars[k] = v
            editor._sync_grid_to_current()
            editor._build_canvas()
            editor._draw_all_previews()
        except:
            pass
    editor.run()