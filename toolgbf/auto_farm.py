import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import pyautogui
import threading
import time
import json
import os
import shutil
import ctypes
import win32gui
import win32api
import win32con
from PIL import Image

# Import các module tự tạo
from overlay_selector import ScreenSelector
from bot_engine import BotEngine

# Đảm bảo cửa sổ nhận diện được tọa độ chính xác trên Windows High DPI
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

class AutoFarmBotPersistence:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Farm RPA Pro v2.1 (Optimized)")
        self.root.geometry("500x620")
        
        self.engine = BotEngine()
        self.roi = None
        self.tasks = []
        self.profiles = ["Default"]
        self.current_profile = "Default"
        self.captcha_image_path = None
        self.captcha_input_pos = None 
        self.captcha_ocr_roi = None  # Luu vung chua chu de OCR
        self.captcha_send_pos = None # Luu vi tri nut Send
        self.start_time = 0 
        
        self.config_file = "config_farm.json"
        self.template_dir = "templates"
        
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # --- Khu vực Quản lý Profile ---
        lf_profile = tk.LabelFrame(main_frame, text="0. Quản lý Profile (Trang lưu trữ)", font=("Arial", 10, "bold"), padx=5, pady=5)
        lf_profile.pack(fill="x", pady=5)

        self.cb_profile = ttk.Combobox(lf_profile, values=self.profiles, state="readonly")
        self.cb_profile.set(self.current_profile)
        self.cb_profile.pack(side="left", padx=5, pady=5, expand=True, fill="x")
        self.cb_profile.bind("<<ComboboxSelected>>", self.on_profile_change)

        tk.Button(lf_profile, text="+", command=self.add_profile, bg="#9b59b6", fg="white", width=3).pack(side="left", padx=2)
        tk.Button(lf_profile, text="X", command=self.delete_profile, bg="#e67e22", fg="white", width=3).pack(side="left", padx=2)

        # --- Khu vực cấu hình vùng quét ---
        lf_roi = tk.LabelFrame(main_frame, text="1. Vùng hoạt động (ROI)", font=("Arial", 10, "bold"), padx=5, pady=5)
        lf_roi.pack(fill="x", pady=5)
        
        tk.Button(lf_roi, text="Khoanh Vùng Màn Hình", command=self.select_roi, bg="#3498db", fg="white").pack(side="left", padx=5)
        self.lbl_roi_status = tk.Label(lf_roi, text="Chưa xác định", fg="red")
        self.lbl_roi_status.pack(side="left", padx=10)

        # --- Khu vực Cảnh báo CAPTCHA ---
        lf_captcha = tk.LabelFrame(main_frame, text="2. Tự động CAPTCHA (Folder 'capcha/')", font=("Arial", 10, "bold"), padx=5, pady=5)
        lf_captcha.pack(fill="x", pady=5)
        
        self.lbl_captcha_status = tk.Label(lf_captcha, text="Chế độ: 100% Tự động (Vision AI)", fg="#2c3e50", font=("Arial", 9, "italic"))
        self.lbl_captcha_status.pack(side="left", padx=5)
        
        tk.Button(lf_captcha, text="Mở Folder", command=lambda: os.startfile("capcha"), bg="#bdc3c7", font=("Arial", 8)).pack(side="right", padx=5)

        # --- Khu vực thêm nút bấm ---
        lf_capture = tk.LabelFrame(main_frame, text="3. Thêm Nút Farm", font=("Arial", 10, "bold"), padx=5, pady=5)
        lf_capture.pack(fill="x", pady=5)
        
        tk.Button(lf_capture, text="+ Thêm Nút", command=self.select_template, bg="#2ecc71", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(lf_capture, text="Xóa Đã Chọn", command=self.delete_selected_task, bg="#e67e22", fg="white", width=12).pack(side="right", padx=5)
        tk.Button(lf_capture, text="Xóa Hết", command=self.clear_all_tasks, bg="#e74c3c", fg="white", width=10).pack(side="right", padx=5)

        # --- Danh sách tác vụ ---
        lf_list = tk.LabelFrame(main_frame, text="Danh sách tổ hợp nút", font=("Arial", 10, "bold"), padx=5, pady=5)
        lf_list.pack(fill="both", expand=True, pady=5)
        
        self.tree = ttk.Treeview(lf_list, columns=("ID", "Loại", "Thông số"), show="headings", height=6, selectmode="extended")
        self.tree.heading("ID", text="Tên Nút")
        self.tree.heading("Loại", text="Chế độ")
        self.tree.heading("Thông số", text="Chi tiết")
        self.tree.column("ID", width=120)
        self.tree.column("Loại", width=100)
        self.tree.column("Thông số", width=200)
        self.tree.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(lf_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(fill="y", side="right")

        # --- Điều khiển ---
        lf_control = tk.LabelFrame(main_frame, text="4. Điều khiển", font=("Arial", 10, "bold"), padx=5, pady=5)
        lf_control.pack(fill="x", pady=5)
        
        self.btn_start = tk.Button(lf_control, text="START BOT", command=self.start_bot, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), height=2)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_stop = tk.Button(lf_control, text="STOP BOT", command=self.stop_bot, bg="#c0392b", fg="white", font=("Arial", 11, "bold"), height=2)
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=5)

        # --- Khu vực Theo dõi ---
        lf_monitor = tk.LabelFrame(main_frame, text="5. Theo dõi hoạt động", font=("Arial", 10, "bold"), padx=5, pady=5)
        lf_monitor.pack(fill="x", pady=5)

        self.lbl_runtime = tk.Label(lf_monitor, text="Thời gian chạy: 00:00:00", font=("Arial", 10))
        self.lbl_runtime.pack(side="left", padx=10)

        self.lbl_current_action = tk.Label(lf_monitor, text="Chờ lệnh...", font=("Arial", 10), fg="brown")
        self.lbl_current_action.pack(side="right", padx=10)
        
        self.lbl_bot_status = tk.Label(main_frame, text="Trạng thái: Đang dừng", font=("Arial", 10, "bold"), fg="blue")
        self.lbl_bot_status.pack(pady=2)

    def on_profile_change(self, event=None):
        self.current_profile = self.cb_profile.get()
        self.engine.template_cache.clear() # Xóa cache khi đổi profile
        self.load_config()

    def add_profile(self):
        new_name = simpledialog.askstring("Profile", "Tên Page mới:")
        if new_name and new_name not in self.profiles:
            self.profiles.append(new_name)
            self.cb_profile["values"] = self.profiles
            self.cb_profile.set(new_name)
            # Lưu trước khi load để tránh bị mất danh sách mới
            self.save_config()
            self.on_profile_change()

    def delete_profile(self):
        if self.current_profile == "Default": return
        if messagebox.askyesno("Xác nhận", f"Xóa Page '{self.current_profile}'?"):
            profile_dir = os.path.join(self.template_dir, self.current_profile)
            if os.path.exists(profile_dir):
                shutil.rmtree(profile_dir, ignore_errors=True)
            self.profiles.remove(self.current_profile)
            self.current_profile = "Default"
            self.cb_profile.set("Default")
            self.on_profile_change()
            self.save_config()

    def select_roi(self):
        ScreenSelector(self.root, mode="roi", callback=self.save_roi_callback)

    def save_roi_callback(self, coords):
        self.roi = coords
        self.lbl_roi_status.config(text=f"Đã chọn: {coords[2]}x{coords[3]}", fg="green")
        self.save_config()

    def select_captcha_template(self):
        if not self.roi: return
        messagebox.showinfo("Hướng dẫn", "Khoanh vùng dòng chữ 'Enter the verification below' để làm dấu hiệu nhận biết.")
        ScreenSelector(self.root, mode="template", callback=self.save_captcha_callback)

    def select_captcha_ocr_roi(self):
        if not self.roi: return
        messagebox.showinfo("Hướng dẫn", "Khoanh vùng CHÍNH XÁC ô chứa các ký tự loằng ngoằng để Bot đọc chữ.")
        ScreenSelector(self.root, mode="template", callback=self.save_captcha_ocr_callback)

    def save_captcha_ocr_callback(self, coords):
        self.captcha_ocr_roi = coords
        messagebox.showinfo("Thành công", "Đã lưu vùng quét chữ!")
        self.save_config()

    def select_captcha_input(self):
        if not self.roi: return
        messagebox.showinfo("Hướng dẫn", "Click vào giữa ô nhập 'Enter verification here'.")
        ScreenSelector(self.root, mode="template", callback=self.save_captcha_input_callback)

    def select_captcha_send(self):
        if not self.roi: return
        messagebox.showinfo("Hướng dẫn", "Click vào nút 'Send' xanh xanh.")
        ScreenSelector(self.root, mode="template", callback=self.save_captcha_send_callback)

    def save_captcha_send_callback(self, coords):
        hwnd = self.engine.get_chrome_hwnd()
        if not hwnd: return
        cx = coords[0] + (coords[2] // 2)
        cy = coords[1] + (coords[3] // 2)
        try:
            self.captcha_send_pos = win32gui.ScreenToClient(hwnd, (cx, cy))
            messagebox.showinfo("Thành công", "Đã lưu vị trí nút Gửi!")
            self.save_config()
        except: pass

    def save_captcha_input_callback(self, coords):
        hwnd = self.engine.get_chrome_hwnd()
        if not hwnd: return
        
        # Lấy tâm của vùng đã chọn để click
        center_x = coords[0] + (coords[2] // 2)
        center_y = coords[1] + (coords[3] // 2)
        
        # Chuyển đổi sang tọa độ Client của Chrome
        try:
            client_pt = win32gui.ScreenToClient(hwnd, (center_x, center_y))
            self.captcha_input_pos = client_pt
            messagebox.showinfo("Thành công", "Đã lưu vị trí ô nhập!")
            self.save_config()
        except:
            pass

    def save_captcha_callback(self, coords):
        self.root.withdraw()
        time.sleep(0.3)
        screenshot = pyautogui.screenshot(region=coords)
        self.root.deiconify()
        
        profile_dir = os.path.join(self.template_dir, self.current_profile)
        os.makedirs(profile_dir, exist_ok=True)
        path = os.path.join(profile_dir, "captcha.png")
        screenshot.save(path)
        self.captcha_image_path = path
        self.lbl_captcha_status.config(text="ON", fg="green")
        self.save_config()

    def select_template(self):
        if not self.roi:
            messagebox.showwarning("ROI", "Khoanh vùng ROI trước!")
            return
        ScreenSelector(self.root, mode="template", callback=self.save_template_callback)

    def save_template_callback(self, coords):
        self.root.withdraw()
        time.sleep(0.3)
        screenshot = pyautogui.screenshot(region=coords)
        self.root.deiconify()
        
        name = simpledialog.askstring("Nút", "Tên nút:")
        if not name: return
        
        is_seq = messagebox.askyesno("Chế độ", "Chạy tuần tự (Sequence)?\n(No = Lặp định kỳ)")
        task_type = "sequence" if is_seq else "schedule"
        
        interval = 0
        if task_type == "schedule":
            interval = simpledialog.askinteger("Hẹn giờ", "Lặp lại sau (giây):", initialvalue=10)
        
        delay = simpledialog.askfloat("Chờ", "Nghỉ sau khi bấm (giây):", initialvalue=1.0) or 1.0

        profile_dir = os.path.join(self.template_dir, self.current_profile)
        os.makedirs(profile_dir, exist_ok=True)
        path = os.path.join(profile_dir, f"{name}.png")
        screenshot.save(path)
        
        self.tasks.append({
            "id": name, "type": task_type, "image": path,
            "interval": interval, "delay": delay, "next_run": 0
        })
        self.update_treeview()
        self.save_config()

    def update_treeview(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for t in self.tasks:
            detail = f"{'Tuần tự' if t['type']=='sequence' else f'Lặp {t['interval']}s'} | Chờ {t['delay']}s"
            self.tree.insert("", "end", values=(t["id"], t["type"].upper(), detail))

    def edit_selected_task(self):
        sel = self.tree.selection()
        if not sel: return
        task_id = str(self.tree.item(sel[0])["values"][0])
        task = next((t for t in self.tasks if str(t["id"]) == task_id), None)
        if not task: return

        if task["type"] == "schedule":
            v = simpledialog.askinteger("Sửa", "Giây lặp lại:", initialvalue=task["interval"])
            if v: task["interval"] = v
        
        d = simpledialog.askfloat("Sửa", "Giây chờ sau click:", initialvalue=task["delay"])
        if d: task["delay"] = d
        
        self.update_treeview()
        self.save_config()

    def delete_selected_task(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Xóa", f"Xóa {len(sel)} nút đã chọn?"):
            for item in sel:
                tid = str(self.tree.item(item)["values"][0])
                # Tìm đúng task để xóa file ảnh
                actual_task = next((t for t in self.tasks if str(t["id"]) == tid), None)
                if actual_task and os.path.exists(actual_task["image"]):
                    try: os.remove(actual_task["image"])
                    except: pass
                # Cập nhật lại danh sách tasks
                self.tasks = [t for t in self.tasks if str(t["id"]) != tid]
            self.update_treeview()
            self.save_config()

    def clear_all_tasks(self):
        if messagebox.askyesno("Xóa sạch", "Xóa toàn bộ các nút trong Page?"):
            for t in self.tasks:
                if os.path.exists(t["image"]):
                    try: os.remove(t["image"])
                    except: pass
            self.tasks = []
            self.update_treeview()
            self.save_config()

    def save_config(self):
        full_config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    full_config = json.load(f)
            except: pass
        
        full_config["profiles"] = self.profiles
        full_config["last_profile"] = self.current_profile # Lưu lại profile cuối cùng sử dụng
        full_config[self.current_profile] = {
            "roi": self.roi,
            "captcha_path": self.captcha_image_path,
            "captcha_input_pos": self.captcha_input_pos,
            "captcha_ocr_roi": self.captcha_ocr_roi,
            "captcha_send_pos": self.captcha_send_pos,
            "tasks": self.tasks
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(full_config, f, ensure_ascii=False, indent=4)

    def load_config(self):
        if not os.path.exists(self.config_file): return
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                full = json.load(f)
                self.profiles = full.get("profiles", ["Default"])
                last_p = full.get("last_profile", "Default")
                
                # Nếu đang ở Default lúc khởi động, ưu tiên chọn profile cũ
                if self.current_profile == "Default" and last_p in self.profiles:
                    self.current_profile = last_p
                
                self.cb_profile["values"] = self.profiles
                self.cb_profile.set(self.current_profile)
                
                data = full.get(self.current_profile, {})
                self.roi = data.get("roi")
                self.captcha_image_path = data.get("captcha_path")
                self.captcha_input_pos = data.get("captcha_input_pos")
                self.captcha_ocr_roi = data.get("captcha_ocr_roi")
                self.captcha_send_pos = data.get("captcha_send_pos")
                self.tasks = data.get("tasks", [])
                for t in self.tasks: t["next_run"] = 0
                
                self.lbl_roi_status.config(text=f"Vùng: {self.roi[2]}x{self.roi[3]}" if self.roi else "Chưa xác định", 
                                          fg="green" if self.roi else "red")
                self.update_treeview()
        except: pass

    def start_bot(self):
        if not self.roi or not self.tasks: return
        if not self.engine.is_running:
            self.engine.is_running = True
            self.start_time = time.time()
            self.lbl_bot_status.config(text="BOT ĐANG CHẠY...", fg="green")
            self.lbl_current_action.config(text="Đang khởi động...", fg="green")
            self.update_timer()
            threading.Thread(target=self.bot_run_loop, daemon=True).start()

    def stop_bot(self):
        self.engine.is_running = False
        self.lbl_bot_status.config(text="Đã dừng", fg="blue")
        self.lbl_current_action.config(text="Đã dừng", fg="blue")

    def update_timer(self):
        if self.engine.is_running:
            elapsed = int(time.time() - self.start_time)
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            self.lbl_runtime.config(text=f"Thời gian chạy: {h:02d}:{m:02d}:{s:02d}")
            self.root.after(1000, self.update_timer)

    def bot_run_loop(self):
        seq_idx = 0
        last_captcha = 0
        hwnd = self.engine.get_chrome_hwnd()
        
        if not hwnd:
            print("LỖI: Không tìm thấy cửa sổ Chrome. Hãy mở trình duyệt trước!")
        
        while self.engine.is_running:
            if not hwnd:
                hwnd = self.engine.get_chrome_hwnd()
                if hwnd: print("Đã kết nối được với Chrome.")
                time.sleep(1)
                continue

            now = time.time()
            # 1. Check Captcha 5s/lần
            if now - last_captcha >= 5:
                # --- PHẦN TỰ ĐỘNG THÔNG MINH (AI INFERENCE) ---
                # Danh sách các tệp tin đặc thù mà người dùng đã cung cấp
                marker_img = "capcha/pop_up_capcha.png"
                ocr_marker_img = "capcha/ô_chứa_chứ.png"
                input_send_img = "capcha/ô_nhập_và_nút_gửi.png"
                
                detected = False
                current_ocr_roi = self.captcha_ocr_roi
                current_input_pos = self.captcha_input_pos
                current_send_pos = self.captcha_send_pos
                
                # BƯỚC 1: NHẬN DIỆN POPUP
                # Nếu có ảnh pop_up_capcha.png, dùng nó làm dấu hiệu nhận biết
                if os.path.exists(marker_img):
                    found_marker = self.engine.find_template_coords(hwnd, self.roi, marker_img)
                    if found_marker:
                        detected = True
                        mx, my, mw, mh = found_marker
                        print(f"[AUTO] Robot đã suy luận thấy CAPTCHA Popup tại: {mx, my}")
                        
                        # BƯỚC 2: TÌM VÙNG CHỨA CHỮ (OCR AREA)
                        if os.path.exists(ocr_marker_img):
                            found_ocr = self.engine.find_template_coords(hwnd, self.roi, ocr_marker_img)
                            if found_ocr:
                                current_ocr_roi = found_ocr
                                print("[AUTO] Đã tìm thấy vùng xử lý OCR.")
                        
                        # BƯỚC 3: TÌM Ô NHẬP HOẶC NÚT GỬI
                        # Nếu người dùng chụp chung ô nhập và nút gửi
                        if os.path.exists(input_send_img):
                            found_is = self.engine.find_template_coords(hwnd, self.roi, input_send_img)
                            if found_is:
                                is_x, is_y, is_w, is_h = found_is
                                # Tọa độ Client của tâm vùng này
                                c_pt = win32gui.ScreenToClient(hwnd, (is_x + is_w//2, is_y + is_h//2))
                                
                                # Thường ô nhập nằm trên hoặc ở trên, nút gửi ở dưới hoặc nằm chung
                                # Nếu chưa có config thì tạm lấy tâm làm ô nhập và offset nhẹ làm nút gửi 
                                if not current_input_pos:
                                    current_input_pos = c_pt # Giả định click vào tâm là vào ô nhập
                                if not current_send_pos:
                                    # Nút gửi thường nằm bên phải hoặc phía dưới ô nhập trong GBF
                                    # Ở đây bot sẽ thử click tâm + offset để tìm nút Send nếu không có config
                                    current_send_pos = (c_pt[0], c_pt[1] + 40) 

                # Nếu không có file tự động thì dùng cài đặt cũ
                elif self.captcha_image_path and self.engine.is_image_present(hwnd, self.roi, self.captcha_image_path):
                    detected = True

                last_captcha = now
                if detected:
                    self.root.after(0, lambda: self.lbl_current_action.config(text="Đang tự giải Captcha...", fg="red"))
                    print("[AUTO] Thực hiện quy trình giải mã 100% tự động...")
                    
                    # Thử giải mã CAPTCHA (tối đa 3 lần)
                    for attempt in range(3):
                        # Quet tai vung OCR chuyen biet
                        target_roi = current_ocr_roi if current_ocr_roi else self.roi
                        # Sử dụng ảnh mẫu để tăng độ chính xác nếu có
                        captcha_text = self.engine.solve_captcha(hwnd, target_roi)
                        
                        if captcha_text and current_input_pos:
                            # 1. Nhập chữ vào ô
                            print(f"[AUTO] Nhập mã: {captcha_text}")
                            self.engine.send_keys(hwnd, captcha_text, current_input_pos)
                            time.sleep(1.5)
                            
                            # 2. Nhấn nút Send
                            if current_send_pos:
                                print("[AUTO] Nhấn nút Gửi.")
                                lx, ly = current_send_pos
                                lp = win32api.MAKELONG(lx, ly)
                                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
                                time.sleep(0.05)
                                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lp)
                            
                            time.sleep(6) # Đợi trang Load
                            
                            # Kiểm tra xem Popup còn không
                            still_there = False
                            if os.path.exists(marker_img):
                                still_there = self.engine.find_template_coords(hwnd, self.roi, marker_img) is not None
                            else:
                                still_there = self.engine.is_image_present(hwnd, self.roi, self.captcha_image_path)
                                
                            if not still_there:
                                print("[AUTO] Giải mã thành công!")
                                now = time.time()
                                break
                        
                        print(f"[AUTO] Lỗi hoặc không đọc được chữ, thử lại lần {attempt + 2}...")
                        time.sleep(4)

                    # Nếu sau 3 lần vẫn còn captcha, bot sẽ tạm nghỉ 30s rồi quét lại 
                    # thay vì dừng hẳn và hiện thông báo làm phiền người dùng.
                    if self.engine.is_image_present(hwnd, self.roi, self.captcha_image_path):
                        print("[AUTO] Chưa vượt được CAPTCHA. Sẽ thử lại sau 30 giây...")
                        self.root.after(0, lambda: self.lbl_current_action.config(text="Captcha lỗi - Thử lại sau 30s", fg="orange"))
                        time.sleep(30)
                    continue

            # 2. Schedule tasks
            schedules = [t for t in self.tasks if t["type"] == "schedule"]
            for t in schedules:
                if now >= t["next_run"]:
                    self.root.after(0, lambda name=t['id']: self.lbl_current_action.config(text=f"Check: {name}", fg="orange"))
                    if self.engine.find_and_click(hwnd, self.roi, t["image"]):
                        self.root.after(0, lambda name=t['id']: self.lbl_current_action.config(text=f"Click: {name}", fg="#27ae60"))
                        t["next_run"] = time.time() + t["interval"]
                        time.sleep(t["delay"])
                        now = time.time()

            # 3. Sequence tasks (Mượt hơn bằng cách giảm sleep nếu không thấy nút)
            sequences = [t for t in self.tasks if t["type"] == "sequence"]
            if sequences:
                if seq_idx >= len(sequences): seq_idx = 0
                target = sequences[seq_idx]
                self.root.after(0, lambda name=target['id']: self.lbl_current_action.config(text=f"Tìm: {name}", fg="#2980b9"))
                if self.engine.find_and_click(hwnd, self.roi, target["image"]):
                    self.root.after(0, lambda name=target['id']: self.lbl_current_action.config(text=f"Click: {name}", fg="#2ecc71"))
                    seq_idx = (seq_idx + 1) % len(sequences)
                    time.sleep(target["delay"])
                else:
                    time.sleep(0.1) # Quét nhanh hơn khi không thấy nút
            else:
                time.sleep(0.2)

        self.root.after(0, self.stop_bot)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoFarmBotPersistence(root)
    root.mainloop()
