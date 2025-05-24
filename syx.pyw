import base64
import hashlib
import json
import os
import threading
import time
from tkinter import colorchooser, messagebox
import sys
import win32gui
import win32con
import ctypes
import subprocess
import customtkinter as ctk
import keyboard
import numpy as np
import pyautogui
import win32api
import requests
from hwid import generate_hwid

API_URL = "https://fastapi-app-u6xx.onrender.com"  # Ersetze xxx mit deiner tatsächlichen IP

def is_pythonw():
    return 'pythonw.exe' in sys.executable.lower()

def restart_as_hidden():
    if is_pythonw():
        return False
    try:
        pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        if os.path.exists(pythonw):
            subprocess.Popen([pythonw, sys.argv[0]], creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        return False
    except:
        return False

def redirect_output():
    try:
        app_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(app_path, 'syx_log.txt')
        sys.stdout = open(log_file, 'a', encoding='utf-8')
        sys.stderr = sys.stdout
    except:
        pass

class Security:
    @staticmethod
    def verify_license(username: str, key: str) -> bool:
        try:
            hwid = generate_hwid()
            response = requests.post(f"{API_URL}/api/verify", json={
                "username": username,
                "key": key,
                "hwid": hwid
            })
            
            if response.status_code == 200:
                return True
            elif response.status_code == 403:
                error_data = response.json()
                messagebox.showerror("Error", error_data.get("detail", {}).get("message", "License verification failed"))
                return False
            else:
                messagebox.showerror("Error", "Failed to verify license")
                return False
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")
            return False
    
    @staticmethod
    def encrypt_data(data):
        return base64.b64encode(json.dumps(data).encode())
    
    @staticmethod
    def decrypt_data(encrypted_data):
        try:
            return json.loads(base64.b64decode(encrypted_data).decode())
        except:
            return None

class Bot:
    def __init__(self):
        self.target_color = (254, 254, 64)
        self.tolerance = 40
        self.scan_interval = 0.001
        self.box_size = 4
        self.running = False
        self.click_delay = 0.05
        self.last_click = 0
        self.last_check_update = time.time()
        self.check_interval = 300
        self.block_keys = True
        self.blocked_keys = ['w', 'a', 's', 'd', 'space']
        self.stop_event = threading.Event()
        self.status_callback = None
        self.last_click_time = 0
        self.is_clicking = False

    def check_color(self, color1, color2):
        try:
            r1, g1, b1 = color1
            r2, g2, b2 = color2
            return (abs(int(r1) - int(r2)) <= self.tolerance and 
                    abs(int(g1) - int(g2)) <= self.tolerance and 
                    abs(int(b1) - int(b2)) <= self.tolerance)
        except:
            return False

    def click_target(self, x, y):
        current_time = time.time()
        if current_time - self.last_click_time < self.click_delay:
            return
        if self.is_clicking:
            return
        try:
            if win32api.GetAsyncKeyState(0x01) < 0:
                return
            self.is_clicking = True
            pyautogui.click(x, y)
            self.last_click = current_time
            self.last_click_time = current_time
            if self.status_callback:
                self.status_callback(f"!!! [{x}, {y}]")
        finally:
            self.is_clicking = False

    def scan(self):
        if not self.running or self.stop_event.is_set():
            return
        try:
            screen_width, screen_height = pyautogui.size()
            center_x, center_y = screen_width // 2, screen_height // 2
            current_time = time.time()
            
            if current_time - self.last_check_update > self.check_interval:
                self.last_check_update = current_time
            
            if self.block_keys:
                try:
                    if any(keyboard.is_pressed(key) for key in self.blocked_keys):
                        return
                    if win32api.GetAsyncKeyState(0x01) < 0:
                        return
                except:
                    pass
            
            if current_time - self.last_click_time < self.click_delay:
                return
            
            x1 = center_x - self.box_size
            y1 = center_y - self.box_size
            width = 2 * self.box_size
            height = 2 * self.box_size
            
            try:
                if x1 < 0 or y1 < 0 or x1 + width > screen_width or y1 + height > screen_height:
                    x1 = max(0, min(x1, screen_width - width))
                    y1 = max(0, min(y1, screen_height - height))
                
                screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
                pixels = np.array(screenshot)
                found = False
                found_x, found_y = 0, 0
                
                for y in range(pixels.shape[0]):
                    if found or self.stop_event.is_set():
                        break
                    for x in range(pixels.shape[1]):
                        if self.stop_event.is_set():
                            break
                        try:
                            pixel_color = pixels[y, x][:3]
                            if self.check_color(pixel_color, self.target_color):
                                found = True
                                found_x, found_y = x1 + x, y1 + y
                                break
                        except:
                            continue
                
                if found and self.running:
                    self.click_target(found_x, found_y)
                    time.sleep(max(0.01, self.click_delay / 2))
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"Error: {str(e)}")
                time.sleep(0.1)
        except:
            time.sleep(0.1)

    def start(self):
        if self.running:
            return
        self.running = True
        self.stop_event.clear()
        self.last_click_time = 0
        threading.Thread(target=self.run_loop, daemon=True).start()
        if self.status_callback:
            self.status_callback("Active")

    def stop(self):
        self.running = False
        self.stop_event.set()
        self.is_clicking = False
        if self.status_callback:
            self.status_callback("Inactive")

    def run_loop(self):
        while self.running and not self.stop_event.is_set():
            try:
                self.scan()
                time.sleep(max(0.001, self.scan_interval))
            except:
                try:
                    if self.status_callback:
                        self.status_callback("Loop Error")
                except:
                    pass
                time.sleep(0.1)

    def save_settings(self, filename="syx_settings.dat"):
        settings = {
            "target_color": self.target_color,
            "tolerance": self.tolerance,
            "scan_interval": self.scan_interval,
            "box_size": self.box_size,
            "click_delay": self.click_delay,
            "block_keys": self.block_keys
        }
        encrypted = Security.encrypt_data(settings)
        with open(filename, "wb") as f:
            f.write(encrypted)

    def load_settings(self, filename="syx_settings.dat"):
        try:
            if os.path.exists(filename):
                with open(filename, "rb") as f:
                    encrypted = f.read()
                settings = Security.decrypt_data(encrypted)
                if settings:
                    self.target_color = settings.get("target_color", self.target_color)
                    self.tolerance = settings.get("tolerance", self.tolerance)
                    self.scan_interval = settings.get("scan_interval", self.scan_interval)
                    self.box_size = settings.get("box_size", self.box_size)
                    self.click_delay = settings.get("click_delay", self.click_delay)
                    self.block_keys = settings.get("block_keys", self.block_keys)
                    return True
        except:
            pass
        return False

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SYX - Login")
        self.geometry("600x700")  # Vergrößerte Fenstergröße
        self.resizable(False, False)
        self._success = False
        self._after_ids = []
        
        self.grid_columnconfigure(0, weight=1)
        
        # Logo und Titel
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=40, pady=(60, 30), sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)
        
        logo_label = ctk.CTkLabel(title_frame, text="SYX", font=ctk.CTkFont(size=48, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(0, 10))
        
        info_label = ctk.CTkLabel(title_frame, text="Bitte geben Sie Ihre Lizenzinformationen ein", 
                                 font=ctk.CTkFont(size=16))
        info_label.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Login Form Container
        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=1, column=0, padx=40, pady=(0, 30), sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)
        
        # Username field
        username_label = ctk.CTkLabel(form_frame, text="Username:", font=ctk.CTkFont(size=14))
        username_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        self._username_entry = ctk.CTkEntry(form_frame, width=400, height=40, 
                                          placeholder_text="Geben Sie Ihren Benutzernamen ein")
        self._username_entry.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # License key field
        key_label = ctk.CTkLabel(form_frame, text="License Key:", font=ctk.CTkFont(size=14))
        key_label.grid(row=2, column=0, padx=20, pady=(20, 5), sticky="w")
        self._key_entry = ctk.CTkEntry(form_frame, width=400, height=40, show="•",
                                     placeholder_text="Geben Sie Ihren Lizenzschlüssel ein")
        self._key_entry.grid(row=3, column=0, padx=20, pady=(0, 20))
        
        # HWID display
        hwid = generate_hwid()
        hwid_label = ctk.CTkLabel(form_frame, text="Ihre HWID:", font=ctk.CTkFont(size=14))
        hwid_label.grid(row=4, column=0, padx=20, pady=(20, 5), sticky="w")
        
        hwid_frame = ctk.CTkFrame(form_frame)
        hwid_frame.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        hwid_frame.grid_columnconfigure(0, weight=1)
        
        hwid_display = ctk.CTkEntry(hwid_frame, width=340, height=40, state="readonly")
        hwid_display.grid(row=0, column=0, padx=(5, 0), pady=5)
        hwid_display.insert(0, hwid)
        
        copy_button = ctk.CTkButton(hwid_frame, text="📋 HWID Kopieren", width=100, height=40,
                                  command=lambda: self._copy_hwid(hwid))
        copy_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Login button
        login_button = ctk.CTkButton(form_frame, text="Login", width=400, height=50,
                                   font=ctk.CTkFont(size=16, weight="bold"),
                                   command=self._check_license)
        login_button.grid(row=6, column=0, padx=20, pady=(30, 20))
        
        self._key_entry.bind("<Return>", lambda event: self._check_license())
        
    def _copy_hwid(self, hwid):
        self.clipboard_clear()
        self.clipboard_append(hwid)
        messagebox.showinfo("Erfolg", "HWID wurde in die Zwischenablage kopiert!")
    
    def _check_license(self):
        username = self._username_entry.get().strip()
        key = self._key_entry.get().strip()
        
        if not username or not key:
            messagebox.showerror("Error", "Bitte geben Sie Benutzername und Lizenzschlüssel ein")
            return
        
        if Security.verify_license(username, key):
            self._success = True
            self.destroy()  # Zerstöre das Fenster
            self.quit()    # Beende die Mainloop
        else:
            self._username_entry.delete(0, 'end')
            self._key_entry.delete(0, 'end')
            self._username_entry.focus()

    def success(self):
        return self._success

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.bot = Bot()
        self.bot.status_callback = self.update_status
        self.title("SYX")
        self.geometry("800x500")
        self.resizable(True, True)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._after_ids = []
        
        self.create_sidebar()
        self.create_main_area()
        self.bot.load_settings()
        self.update_settings_display()
        
        keyboard.add_hotkey('f1', self.load_fast)
        keyboard.add_hotkey('f2', self.load_slow)
        keyboard.add_hotkey('f9', self.exit_app)
        keyboard.add_hotkey('-', self.toggle_bot)
        
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        sidebar.grid_rowconfigure(4, weight=1)
        
        logo = ctk.CTkLabel(sidebar, text="SYX", font=ctk.CTkFont(size=24, weight="bold"))
        logo.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        user_info = ctk.CTkLabel(sidebar, text="Sytrix87", font=ctk.CTkFont(size=12))
        user_info.grid(row=1, column=0, padx=20, pady=(10, 20))
        
        self.start_button = ctk.CTkButton(sidebar, text="Start/Stop", command=self.toggle_bot)
        self.start_button.grid(row=2, column=0, padx=20, pady=10)
        
        color_button = ctk.CTkButton(sidebar, text="Pick Color", command=self.choose_color)
        color_button.grid(row=3, column=0, padx=20, pady=10)
        
        presets_label = ctk.CTkLabel(sidebar, text="PRESETS", font=ctk.CTkFont(size=16))
        presets_label.grid(row=5, column=0, padx=20, pady=(30, 10))
        
        fast_button = ctk.CTkButton(sidebar, text="FAST", command=self.load_fast)
        fast_button.grid(row=6, column=0, padx=20, pady=10)
        
        slow_button = ctk.CTkButton(sidebar, text="PRECISION", command=self.load_slow)
        slow_button.grid(row=7, column=0, padx=20, pady=10)
        
        save_fast = ctk.CTkButton(sidebar, text="Save Fast", command=lambda: self.save_preset("fast"))
        save_fast.grid(row=8, column=0, padx=20, pady=10)
        
        save_slow = ctk.CTkButton(sidebar, text="Save Slow", command=lambda: self.save_preset("slow"))
        save_slow.grid(row=9, column=0, padx=20, pady=10)

    def create_main_area(self):
        main = ctk.CTkFrame(self)
        main.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        
        status_frame = ctk.CTkFrame(main)
        status_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        status_label = ctk.CTkLabel(status_frame, text="Status:", font=ctk.CTkFont(size=14))
        status_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.status_text = ctk.CTkLabel(status_frame, text="Inactive", font=ctk.CTkFont(size=14))
        self.status_text.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        settings_frame = ctk.CTkFrame(main)
        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)
        
        color_label = ctk.CTkLabel(settings_frame, text="Color:", font=ctk.CTkFont(size=14))
        color_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.color_display = ctk.CTkFrame(settings_frame, width=30, height=30)
        self.color_display.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        tolerance_label = ctk.CTkLabel(settings_frame, text="Tolerance:", font=ctk.CTkFont(size=14))
        tolerance_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.tolerance_slider = ctk.CTkSlider(settings_frame, from_=0, to=100, number_of_steps=100)
        self.tolerance_slider.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.tolerance_slider.set(self.bot.tolerance)
        
        self.tolerance_value = ctk.CTkLabel(settings_frame, text=str(self.bot.tolerance))
        self.tolerance_value.grid(row=1, column=2, padx=10, pady=10)
        
        interval_label = ctk.CTkLabel(settings_frame, text="Scan (ms):", font=ctk.CTkFont(size=14))
        interval_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        self.interval_slider = ctk.CTkSlider(settings_frame, from_=1, to=50, number_of_steps=49)
        self.interval_slider.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.interval_slider.set(self.bot.scan_interval * 1000)
        
        self.interval_value = ctk.CTkLabel(settings_frame, text=str(int(self.bot.scan_interval * 1000)))
        self.interval_value.grid(row=2, column=2, padx=10, pady=10)
        
        box_label = ctk.CTkLabel(settings_frame, text="Box Size:", font=ctk.CTkFont(size=14))
        box_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        
        self.box_slider = ctk.CTkSlider(settings_frame, from_=1, to=20, number_of_steps=19)
        self.box_slider.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        self.box_slider.set(self.bot.box_size)
        
        self.box_value = ctk.CTkLabel(settings_frame, text=f"{self.bot.box_size} ({self.bot.box_size*2+1}x{self.bot.box_size*2+1})")
        self.box_value.grid(row=3, column=2, padx=10, pady=10)
        
        delay_label = ctk.CTkLabel(settings_frame, text="Delay (ms):", font=ctk.CTkFont(size=14))
        delay_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        
        self.delay_slider = ctk.CTkSlider(settings_frame, from_=10, to=500, number_of_steps=49)
        self.delay_slider.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.delay_slider.set(self.bot.click_delay * 1000)
        
        self.delay_value = ctk.CTkLabel(settings_frame, text=str(int(self.bot.click_delay * 1000)))
        self.delay_value.grid(row=4, column=2, padx=10, pady=10)
        
        keys_label = ctk.CTkLabel(settings_frame, text="Block keys:", font=ctk.CTkFont(size=14))
        keys_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        
        self.keys_switch = ctk.CTkSwitch(settings_frame, text="", onvalue=True, offvalue=False)
        self.keys_switch.grid(row=5, column=1, padx=10, pady=10, sticky="w")
        self.keys_switch.select() if self.bot.block_keys else self.keys_switch.deselect()
        
        apply_button = ctk.CTkButton(settings_frame, text="Apply", command=self.apply_settings)
        apply_button.grid(row=6, column=0, columnspan=3, padx=10, pady=20)
        
        help_frame = ctk.CTkFrame(main)
        help_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        help_text = ctk.CTkLabel(help_frame, text="F1=FAST | F2=PRECISION | -=ACTIVATE | F9=EXIT", 
                                font=ctk.CTkFont(size=12))
        help_text.grid(row=0, column=0, padx=10, pady=10)
        
        self.tolerance_slider.configure(command=self.update_tolerance_display)
        self.interval_slider.configure(command=self.update_interval_display)
        self.box_slider.configure(command=self.update_box_display)
        self.delay_slider.configure(command=self.update_delay_display)

    def update_tolerance_display(self, value):
        self.tolerance_value.configure(text=str(int(value)))

    def update_interval_display(self, value):
        self.interval_value.configure(text=str(int(value)))

    def update_box_display(self, value):
        box_size = int(value)
        self.box_value.configure(text=f"{box_size} ({box_size*2+1}x{box_size*2+1})")

    def update_delay_display(self, value):
        self.delay_value.configure(text=str(int(value)))

    def update_settings_display(self):
        r, g, b = self.bot.target_color
        color_hex = f'#{r:02x}{g:02x}{b:02x}'
        self.color_display.configure(fg_color=color_hex)
        
        self.tolerance_slider.set(self.bot.tolerance)
        self.tolerance_value.configure(text=str(self.bot.tolerance))
        
        self.interval_slider.set(self.bot.scan_interval * 1000)
        self.interval_value.configure(text=str(int(self.bot.scan_interval * 1000)))
        
        self.box_slider.set(self.bot.box_size)
        self.box_value.configure(text=f"{self.bot.box_size} ({self.bot.box_size*2+1}x{self.bot.box_size*2+1})")
        
        self.delay_slider.set(self.bot.click_delay * 1000)
        self.delay_value.configure(text=str(int(self.bot.click_delay * 1000)))
        
        if self.bot.block_keys:
            self.keys_switch.select()
        else:
            self.keys_switch.deselect()

    def apply_settings(self):
        self.bot.tolerance = int(self.tolerance_slider.get())
        self.bot.scan_interval = float(self.interval_slider.get()) / 1000.0
        self.bot.box_size = int(self.box_slider.get())
        self.bot.click_delay = float(self.delay_slider.get()) / 1000.0
        self.bot.block_keys = bool(self.keys_switch.get())
        self.update_status("Applied")
        self.bot.save_settings()

    def choose_color(self):
        color = colorchooser.askcolor(title="Color")
        if color[0]:
            r, g, b = [int(c) for c in color[0]]
            self.bot.target_color = (r, g, b)
            self.update_settings_display()
            self.update_status(f"Color: {r},{g},{b}")

    def toggle_bot(self):
        if self.bot.running:
            self.bot.stop()
            self.start_button.configure(text="Start/Stop")
        else:
            self.bot.start()
            self.start_button.configure(text="▶ ACTIVE ▶")

    def update_status(self, status):
        self.status_text.configure(text=status)

    def load_fast(self):
        self.bot.target_color = (254, 254, 64)
        self.bot.tolerance = 40
        self.bot.scan_interval = 0.001
        self.bot.box_size = 4
        self.bot.click_delay = 0.050
        self.bot.block_keys = True
        self.update_settings_display()
        self.update_status("FAST")

    def load_slow(self):
        self.bot.target_color = (254, 254, 64)
        self.bot.tolerance = 60
        self.bot.scan_interval = 0.005
        self.bot.box_size = 4
        self.bot.click_delay = 0.100
        self.bot.block_keys = True
        self.update_settings_display()
        self.update_status("PRECISION")

    def save_preset(self, preset_type):
        settings = {
            "target_color": self.bot.target_color,
            "tolerance": self.bot.tolerance,
            "scan_interval": self.bot.scan_interval,
            "box_size": self.bot.box_size,
            "click_delay": self.bot.click_delay,
            "block_keys": self.bot.block_keys
        }
        filename = f"syx_{preset_type}.dat"
        encrypted = Security.encrypt_data(settings)
        with open(filename, "wb") as f:
            f.write(encrypted)
        self.update_status(f"{preset_type.upper()} saved")

    def exit_app(self):
        if self.bot.running:
            self.bot.stop()
        
        for after_id in self._after_ids:
            try:
                self.after_cancel(after_id)
            except:
                pass
        
        try:
            for key in ['f1', 'f2', 'f9', '-']:
                try:
                    keyboard.remove_hotkey(key)
                except:
                    pass
        except:
            pass
        
        try:
            for after_id in self.tk.call('after', 'info'):
                self.after_cancel(after_id)
        except:
            pass
        
        try:
            self.quit()
            self.destroy()
        except:
            pass

if __name__ == "__main__":
    try:
        if restart_as_hidden():
            sys.exit(0)
        
        redirect_output()
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        login = LoginWindow()
        try:
            login.mainloop()
        except Exception as e:
            print(f"Login error: {str(e)}")
        
        if login.success():
            app = MainWindow()
            try:
                for key, func in [('f1', app.load_fast), ('f2', app.load_slow), 
                                ('f9', app.exit_app), ('-', app.toggle_bot)]:
                    try:
                        keyboard.remove_hotkey(key)
                    except:
                        pass
                    try:
                        keyboard.add_hotkey(key, func)
                    except:
                        print(f"Warning: Failed to register hotkey {key}")
                
                app.mainloop()
            except KeyboardInterrupt:
                print("Exiting...")
            except Exception as e:
                print(f"Error: {str(e)}")
            finally:
                try:
                    if hasattr(app, "bot") and hasattr(app.bot, "stop"):
                        app.bot.stop()
                    for key in ['f1', 'f2', 'f9', '-']:
                        try:
                            keyboard.remove_hotkey(key)
                        except:
                            pass
                except:
                    pass
    except Exception as e:
        print(f"Startup error: {str(e)}")
    finally:
        try:
            if hasattr(sys.stdout, 'close'):
                sys.stdout.close()
        except:
            pass 
        