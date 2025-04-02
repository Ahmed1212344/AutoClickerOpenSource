import tkinter as tk
from tkinter import ttk
from pynput import mouse, keyboard
import threading
import time
import json
import os
import errno

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Clicker Pro")
        self.settings_dir = os.path.join(os.path.expanduser("~"), "AutoClicker")
        self.settings_file = os.path.join(self.settings_dir, "autoclicker_settings.json")

        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        else:
            print("Icon file not found!")
        try:
            os.makedirs(self.settings_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating settings directory: {e}")
            raise
        
        # Default settings
        self.default_settings = {
            'click_count': 0,
            'infinite_clicks': True,
            'delay': 0,
            'time_unit': "ms",
            'mouse_button': "left",
            'hotkey': "F6",
            'hotkey_type': None,
            'hotkey_code': None,
            'mode': "toggle"
        }

        # Initialize variables
        self.is_setting_hotkey = False
        self.is_clicking = False
        self.is_pressed = False
        self.click_thread = None
        self.listener = None
        self.mouse_temp_listener = None

        # Load or initialize settings
        self.load_settings()

        # Mouse button mapping
        self.mouse_map = {
            "left": mouse.Button.left,
            "right": mouse.Button.right,
            "middle": mouse.Button.middle,
            "button4": mouse.Button.x1,
            "button5": mouse.Button.x2,
            "button6": mouse.Button.x1,
            "button7": mouse.Button.x2,
            "button8": mouse.Button.middle
        }

        # GUI Setup
        self.create_widgets()
        self.setup_listeners()

        # Save settings on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Click amount
        ttk.Label(self.root, text="Number of Clicks:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.click_count).grid(row=0, column=1, padx=5, pady=5)
        ttk.Checkbutton(self.root, text="Infinite", variable=self.infinite_clicks).grid(row=0, column=2, padx=5, pady=5)

        # Time settings
        ttk.Label(self.root, text="Click Interval:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.delay).grid(row=1, column=1, padx=5, pady=5)
        ttk.Combobox(self.root, textvariable=self.time_unit, values=["ms", "seconds", "minutes", "hours"]).grid(row=1, column=2, padx=5, pady=5)

        # Mouse button options
        ttk.Label(self.root, text="Mouse Button:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Combobox(self.root, textvariable=self.mouse_button, 
                    values=["left", "right", "middle"]).grid(row=2, column=1, padx=5, pady=5)

        # Mode selection
        ttk.Label(self.root, text="Activation Mode:").grid(row=3, column=0, padx=5, pady=5)
        ttk.Radiobutton(self.root, text="Toggle", variable=self.mode, value="toggle").grid(row=3, column=1, padx=5, pady=5)
        ttk.Radiobutton(self.root, text="Hold", variable=self.mode, value="hold").grid(row=3, column=2, padx=5, pady=5)

        # Hotkey setup
        ttk.Label(self.root, text="Hotkey:").grid(row=4, column=0, padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.hotkey, state='readonly').grid(row=4, column=1, padx=5, pady=5)
        ttk.Button(self.root, text="Set Hotkey", command=self.start_hotkey_listener).grid(row=4, column=2, padx=5, pady=5)

        # Status label
        self.status_label = ttk.Label(self.root, text="", foreground="blue")
        self.status_label.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                # Initialize variables with saved values
                self.click_count = tk.IntVar(value=saved_settings.get('click_count', self.default_settings['click_count']))
                self.infinite_clicks = tk.BooleanVar(value=saved_settings.get('infinite_clicks', self.default_settings['infinite_clicks']))
                self.delay = tk.DoubleVar(value=saved_settings.get('delay', self.default_settings['delay']))
                self.time_unit = tk.StringVar(value=saved_settings.get('time_unit', self.default_settings['time_unit']))
                self.mouse_button = tk.StringVar(value=saved_settings.get('mouse_button', self.default_settings['mouse_button']))
                self.hotkey = tk.StringVar(value=saved_settings.get('hotkey', self.default_settings['hotkey']))
                self.hotkey_type = saved_settings.get('hotkey_type', self.default_settings['hotkey_type'])
                self.hotkey_code = saved_settings.get('hotkey_code', self.default_settings['hotkey_code'])
                self.mode = tk.StringVar(value=saved_settings.get('mode', self.default_settings['mode']))
            else:
                # Create initial settings file atomically
                self.save_settings(initial_save=True)
                self.initialize_default_settings()
        except Exception as e:
           print(f"Error loading settings: {e}")
           self.initialize_default_settings()
           self.initialize_default_settings()

    def initialize_default_settings(self):
        self.click_count = tk.IntVar(value=self.default_settings['click_count'])
        self.infinite_clicks = tk.BooleanVar(value=self.default_settings['infinite_clicks'])
        self.delay = tk.DoubleVar(value=self.default_settings['delay'])
        self.time_unit = tk.StringVar(value=self.default_settings['time_unit'])
        self.mouse_button = tk.StringVar(value=self.default_settings['mouse_button'])
        self.hotkey = tk.StringVar(value=self.default_settings['hotkey'])
        self.hotkey_type = self.default_settings['hotkey_type']
        self.hotkey_code = self.default_settings['hotkey_code']
        self.mode = tk.StringVar(value=self.default_settings['mode'])

    def save_settings(self, initial_save=False):
        try:
            settings = {
                'click_count': self.click_count.get(),
                'infinite_clicks': self.infinite_clicks.get(),
                'delay': self.delay.get(),
                'time_unit': self.time_unit.get(),
                'mouse_button': self.mouse_button.get(),
                'hotkey': self.hotkey.get(),
                'hotkey_type': self.hotkey_type,
                'hotkey_code': self.hotkey_code,
                'mode': self.mode.get()
            }
            
            # Use atomic write with temp file
            temp_file = self.settings_file + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(settings, f)
            
            # Replace existing file atomically
            try:
                if os.path.exists(self.settings_file):
                    os.replace(temp_file, self.settings_file)
                else:
                    os.rename(temp_file, self.settings_file)
            except OSError as e:
                if e.errno == errno.EACCES:
                    print("Permission error saving settings. Using temporary storage.")
                    os.remove(temp_file)
                else:
                    raise

        except Exception as e:
            print(f"Error saving settings: {e}")
            if initial_save:
                print("Could not create initial settings file. Some features might not work.")

    def on_close(self):
        self.save_settings()
        self.root.destroy()

    def setup_listeners(self):
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click
        )
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def start_hotkey_listener(self):
        if not self.is_setting_hotkey:
            self.is_setting_hotkey = True
            self.hotkey.set("Press any key or mouse button...")
            if self.listener:
                self.listener.stop()
            if self.mouse_temp_listener:
                self.mouse_temp_listener.stop()
                
            self.listener = keyboard.Listener(on_press=self.set_hotkey)
            self.mouse_temp_listener = mouse.Listener(on_click=self.set_mouse_hotkey)
            self.listener.start()
            self.mouse_temp_listener.start()

    def set_hotkey(self, key):
        try:
            self.hotkey_type = "keyboard"
            self.hotkey_code = key.vk
            self.hotkey.set(str(key).replace("'", ""))
        except AttributeError:
            pass
        finally:
            self.cleanup_hotkey_listeners()

    def set_mouse_hotkey(self, x, y, button, pressed):
        if pressed and self.is_setting_hotkey:
            widget = self.root.winfo_containing(x, y)
            if not widget:
                self.hotkey_type = "mouse"
                self.hotkey_code = button
                self.hotkey.set(str(button).split(".")[-1])
                self.cleanup_hotkey_listeners()

    def cleanup_hotkey_listeners(self):
        self.is_setting_hotkey = False
        if self.listener:
            self.listener.stop()
        if self.mouse_temp_listener:
            self.mouse_temp_listener.stop()
        self.status_label.config(text="")

    def on_key_press(self, key):
        if self.mode.get() == "hold" and self.is_active_hotkey(key, "keyboard"):
            self.is_pressed = True
            self.start_clicker()
        elif self.mode.get() == "toggle" and self.is_active_hotkey(key, "keyboard"):
            self.toggle_clicker()

    def on_key_release(self, key):
        if self.mode.get() == "hold" and self.is_active_hotkey(key, "keyboard"):
            self.is_pressed = False
            self.stop_clicker()

    def on_mouse_click(self, x, y, button, pressed):
        if self.is_setting_hotkey and self.root.winfo_containing(x, y):
            return
        
        if self.mode.get() == "hold" and self.is_active_hotkey(button, "mouse"):
            self.is_pressed = pressed
            if pressed:
                self.start_clicker()
            else:
                self.stop_clicker()
        elif self.mode.get() == "toggle" and pressed and self.is_active_hotkey(button, "mouse"):
            self.toggle_clicker()

    def is_active_hotkey(self, input, input_type):
        if input_type == self.hotkey_type:
            if input_type == "keyboard":
                try:
                    return input.vk == self.hotkey_code
                except AttributeError:
                    return False
            elif input_type == "mouse":
                return input == self.hotkey_code
        return False

    def start_clicker(self):
        if not self.is_clicking:
            self.is_clicking = True
            self.click_thread = threading.Thread(target=self.auto_click)
            self.click_thread.start()

    def stop_clicker(self):
        self.is_clicking = False

    def toggle_clicker(self):
        self.is_clicking = not self.is_clicking
        if self.is_clicking:
            self.click_thread = threading.Thread(target=self.auto_click)
            self.click_thread.start()

    def convert_delay(self):
        unit = self.time_unit.get()
        base_delay = self.delay.get()
        if unit == "seconds":
            return base_delay * 1000
        elif unit == "minutes":
            return base_delay * 1000 * 60
        elif unit == "hours":
            return base_delay * 1000 * 60 * 60
        return base_delay  # ms

    def auto_click(self):
        controller = mouse.Controller()
        delay = self.convert_delay() / 1000
        count = 0

        while (self.is_clicking and self.mode.get() == "toggle") or \
             (self.is_pressed and self.mode.get() == "hold"):

            controller.click(self.mouse_map[self.mouse_button.get()])
            count += 1
            
            if not self.infinite_clicks.get() and count >= self.click_count.get():
                break
            
            time.sleep(delay)
        self.is_clicking = False

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()