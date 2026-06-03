import cv2
import numpy as np
import win32gui
import win32ui
import win32con
import win32api
import ctypes
import time
import os
import pytesseract
from PIL import Image

class BotEngine:
    def __init__(self):
        self.is_running = False
        self.template_cache = {} # Lưu trữ ảnh mẫu trong RAM để chạy mượt hơn
        # Tùy chỉnh đường dẫn tesseract nếu cần (Mặc định thường là C:\Program Files\Tesseract-OCR\tesseract.exe)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def get_chrome_hwnd(self):
        # Ưu tiên tìm cửa sổ Chrome đang hoạt động
        hwnds = []
        def enum_cb(h, _):
            if win32gui.IsWindowVisible(h):
                title = win32gui.GetWindowText(h)
                class_name = win32gui.GetClassName(h)
                if "Chrome_WidgetWin_1" in class_name and ("Google Chrome" in title or "Chrome" in title):
                    hwnds.append(h)
        win32gui.EnumWindows(enum_cb, None)
        return hwnds[0] if hwnds else None

    def capture_background(self, hwnd, roi):
        rx, ry, rw, rh = roi
        
        # Kiểm tra nếu cửa sổ bị thu nhỏ (minimized)
        if win32gui.IsIconic(hwnd):
            # Tạm thời khôi phục nhưng không tập trung (ShowNoActivate) 
            # để PrintWindow có thể hoạt động chính xác hơn trên một số bản Chrome
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
            time.sleep(0.1)

        try:
            client_pt1 = win32gui.ScreenToClient(hwnd, (rx, ry))
            client_pt2 = win32gui.ScreenToClient(hwnd, (rx + rw, ry + rh))
            cx, cy = client_pt1
            cw, ch = client_pt2[0] - cx, client_pt2[1] - cy
        except:
            cx, cy, cw, ch = 0, 0, rw, rh

        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        w_total, h_total = right - left, bot - top
        
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w_total, h_total)
        saveDC.SelectObject(saveBitMap)
        
        # Flag 3 (PW_RENDERFULLCONTENT) giúp chụp Chrome ngay cả khi bị che/ẩn
        ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
        
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        
        img = Image.frombuffer(
            'RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        
        # Clean up
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        # Tính toán vị trí client so với cửa sổ
        c2w_pt = win32gui.ClientToScreen(hwnd, (cx, cy))
        wx = max(0, c2w_pt[0] - left)
        wy = max(0, c2w_pt[1] - top)
        
        crop_img = img.crop((wx, wy, wx + cw, wy + ch))
        return cv2.cvtColor(np.array(crop_img), cv2.COLOR_RGB2BGR), cx, cy

    def find_and_click(self, hwnd, roi, image_path, threshold=0.8):
        # Cache ảnh mẫu để không phải đọc từ ổ cứng nhiều lần
        if image_path not in self.template_cache:
            tmpl = cv2.imread(image_path)
            if tmpl is not None:
                self.template_cache[image_path] = tmpl
            else:
                return False
        
        template = self.template_cache[image_path]
        
        try:
            img_bgr, cx, cy = self.capture_background(hwnd, roi)
            res = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)

            if len(loc[0]) > 0:
                pt_y, pt_x = loc[0][0], loc[1][0]
                th, tw = template.shape[:2]
                
                click_x = cx + pt_x + (tw // 2)
                click_y = cy + pt_y + (th // 2)
                
                lparam = win32api.MAKELONG(click_x, click_y)
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                time.sleep(0.05)
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                return True
        except Exception as e:
            print(f"Error in find_and_click: {e}")
            
        return False

    def find_template_coords(self, hwnd, roi, image_path, threshold=0.8):
        """Tìm tọa độ của một template mà không click"""
        if not image_path or not os.path.exists(image_path):
            return None
            
        if image_path not in self.template_cache:
            tmpl = cv2.imread(image_path)
            if tmpl is not None:
                self.template_cache[image_path] = tmpl
            else:
                return None
        
        template = self.template_cache[image_path]
        try:
            img_bgr, cx, cy = self.capture_background(hwnd, roi)
            res = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            
            if len(loc[0]) > 0:
                pt_y, pt_x = loc[0][0], loc[1][0]
                th, tw = template.shape[:2]
                # Trả về tọa độ Screen (tương đối với ROI đã bù cx, cy)
                return (cx + pt_x, cy + pt_y, tw, th)
        except:
            pass
        return None

    def is_image_present(self, hwnd, roi, image_path):
        if not image_path or not os.path.exists(image_path):
            return False
        
        if image_path not in self.template_cache:
            tmpl = cv2.imread(image_path)
            if tmpl is not None:
                self.template_cache[image_path] = tmpl
            else:
                return False

        try:
            img_bgr, _, _ = self.capture_background(hwnd, roi)
            res = cv2.matchTemplate(img_bgr, self.template_cache[image_path], cv2.TM_CCOEFF_NORMED)
            return np.where(res >= 0.8)[0].size > 0
        except:
            return False

    def solve_captcha(self, hwnd, roi, captcha_path=None):
        """Xử lý ảnh nâng cao để vượt qua nhiễu (đường kẻ, vòng tròn) và giải CAPTCHA"""
        # Nếu dùng auto-detect thì roi chính là vùng chứa chữ, không cần captcha_path nữa
        # Nhưng vẫn giữ captcha_path để tương thích ngược
            
        try:
            # Chụp vùng CAPTCHA thực tế trên màn hình
            img_bgr, _, _ = self.capture_background(hwnd, roi)
            
            # Nếu ảnh quá nhỏ hoặc lỗi, trả về None
            if img_bgr is None or img_bgr.shape[0] < 5 or img_bgr.shape[1] < 5:
                return None
            
            # --- BƯỚC XỬ LÝ ẢNH NÂNG CAO ---
            # 1. Chuyển sang ảnh xám
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            
            # 2. Phóng to ảnh để OCR đọc tốt hơn (Interpolation)
            gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
            
            # 3. Khử nhiễu mạnh (Dùng Bilateral Filter để giữ nét chữ nhưng xóa vệt nhiễu nhẹ)
            denoised = cv2.bilateralFilter(gray, 11, 85, 85)
            
            # 4. Nhị phân hóa (Thresholding) - Dùng Adaptive để xử lý độ sáng không đều
            thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 13, 4)
            
            # 5. Làm dày nét chữ một chút (Dilation) nếu chữ bị mảnh do lọc nhiễu
            kernel = np.ones((2,2), np.uint8)
            dilated = cv2.dilate(thresh, kernel, iterations=1)
            
            # 6. Morphological operations (Đóng/Mở ảnh) để xóa các đường kẻ mảnh và vòng tròn bị đứt đoạn
            processed = cv2.morphologyEx(dilated, cv2.MORPH_OPEN, kernel)
            
            # Đảo ngược lại màu (Chữ đen nền trắng cho OCR)
            processed = cv2.bitwise_not(processed)
            
            # Lưu ảnh debug để xem Bot đang thấy gì (Tùy chọn)
            # cv2.imwrite("debug_captcha.png", processed)
            
            # Chuyển về PIL để pytesseract đọc
            pil_img = Image.fromarray(processed)
            
            # Cấu hình OCR cực kỳ linh hoạt: Chữ thường (a-z), Chữ hoa (A-Z) và Số (0-9)
            # psm 7: Xử lý như một dòng chữ đơn nhất
            custom_config = r'--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            text = pytesseract.image_to_string(pil_img, config=custom_config)
            
            clean_text = "".join(text.split()).strip()
            if clean_text:
                print(f"[OCR] Kết quả: {clean_text}")
            return clean_text
        except Exception as e:
            print(f"Lỗi OCR nâng cao: {e}")
            return None

    def send_keys(self, hwnd, text, click_pos):
        """Click vào vị trí ô nhập và gõ phím ngầm"""
        if not click_pos: return
        
        cx, cy = click_pos
        lparam = win32api.MAKELONG(cx, cy)
        
        # Click để focus ô nhập
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
        time.sleep(0.05)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
        time.sleep(0.3)
        
        for char in text:
            # Gửi từng ký tự qua message WM_CHAR
            win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
            time.sleep(0.05)
            
        # Gửi phím Enter sau khi gõ xong
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        time.sleep(0.05)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
