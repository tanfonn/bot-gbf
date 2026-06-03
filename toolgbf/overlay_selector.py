import tkinter as tk

class ScreenSelector(tk.Toplevel):
    """Cửa sổ trong suốt để kéo thả khoanh vùng trên màn hình"""
    def __init__(self, parent, mode="roi", callback=None):
        super().__init__(parent)
        self.callback = callback
        self.mode = mode
        
        # Cấu hình cửa sổ phủ toàn màn hình, mờ 30%
        self.attributes("-alpha", 0.3)
        self.attributes("-fullscreen", True)
        self.config(bg="grey")
        self.attributes("-topmost", True)
        self.overrideredirect(True) # Xóa thanh tiêu đề và taskbar để tập trung khoanh vùng
        
        self.canvas = tk.Canvas(self, cursor="cross", bg="grey", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.lift()
        self.focus_force()
        self.grab_set() # Bắt giữ toàn bộ sự kiện chuột cho cửa sổ này

        # Ràng buộc phím Esc để thoát nhanh nếu kẹt
        self.bind("<Escape>", lambda e: self.destroy())

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=2)

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        x = min(self.start_x, end_x)
        y = min(self.start_y, end_y)
        w = abs(self.start_x - end_x)
        h = abs(self.start_y - end_y)
        
        if w > 5 and h > 5:
            if self.callback:
                self.callback((x, y, w, h))
        self.destroy()
