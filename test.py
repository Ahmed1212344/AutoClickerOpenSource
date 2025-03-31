import tkinter as tk
from tkinter import ttk
from pynput import mouse, keyboard
import threading
import time

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Clicker Pro")
        
        # Click settings
        self.click_count = tk.IntVar(value=0)
        self.infinite_clicks = tk.BooleanVar(value=False)
        self.delay = tk.DoubleVar(value=100)
        self.time_unit = tk.StringVar(value="ms")
        self.mouse_button = tk.StringVar(value="left")
        self.hotkey = tk.StringVar(value="F6")
        self.hotkey_type = None  # 'keyboard' or 'mouse'
        self.hotkey_code = None
        self.mode = tk.StringVar(value="toggle")
        self.is_clicking = False
        self.is_pressed = False
        self.click_thread = None
        self.listener = None
        self.mouse_map = {
            "left": mouse.Button.left,
            "right": mouse.Button.right,
            "middle": mouse.Button.middle,
            "button4": mouse.Button.x1,
            "button5": mouse.Button.x2,
            "button6": mouse.Button.x1,  # Fallback to x1 if higher buttons not available
            "button7": mouse.Button.x2,
            "button8": mouse.Button.middle
        }         

        # GUI Setup
        self.create_widgets()
        self.setup_listeners()

    def create_widgets(self):
        # Click amount
        ttk.Label(self.root, text="Number of Clicks:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.click_count).grid(row=0, column=1, padx=5, pady=5)
        ttk.Checkbutton(self.root, text="Infinite", variable=self.infinite_clicks).grid(row=0, column=2, padx=5, pady=5)

        # Time settings
        ttk.Label(self.root, text="Click Interval:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.delay).grid(row=1, column=1, padx=5, pady=5)
        ttk.Combobox(self.root, textvariable=self.time_unit, values=["ms", "seconds", "minutes", "hours"]).grid(row=1, column=2, padx=5, pady=5)

        # Add mouse button options
        ttk.Label(self.root, text="Mouse Button:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Combobox(self.root, textvariable=self.mouse_button, 
                    values=["left", "right", "middle", "button4", "button5", 
                           "button6", "button7", "button8"]).grid(row=2, column=1, padx=5, pady=5)

        # Mode selection
        ttk.Label(self.root, text="Activation Mode:").grid(row=3, column=0, padx=5, pady=5)
        ttk.Radiobutton(self.root, text="Toggle", variable=self.mode, value="toggle").grid(row=3, column=1, padx=5, pady=5)
        ttk.Radiobutton(self.root, text="Hold", variable=self.mode, value="hold").grid(row=3, column=2, padx=5, pady=5)

        # Hotkey setup
        ttk.Label(self.root, text="Hotkey:").grid(row=4, column=0, padx=5, pady=5)
        ttk.Entry(self.root, textvariable=self.hotkey, state='readonly').grid(row=4, column=1, padx=5, pady=5)
        ttk.Button(self.root, text="Set Hotkey", command=self.start_hotkey_listener).grid(row=4, column=2, padx=5, pady=5)

        # Start/Stop
        ttk.Button(self.root, text="Start", command=self.toggle_clicker).grid(row=5, column=1, padx=5, pady=5)

    def setup_listeners(self):
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        ) 
        self.mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click  # Removed on_release parameter
        )
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def start_hotkey_listener(self):
        self.hotkey.set("Press any key or mouse button...")
        self.listener = keyboard.Listener(on_press=self.set_hotkey)
        self.mouse_temp_listener = mouse.Listener(on_click=self.set_mouse_hotkey)
        self.listener.start()
        self.mouse_temp_listener.start()

    def set_hotkey(self, key):
        try:
            self.hotkey_type = "keyboard"
            self.hotkey_code = key.vk
            self.hotkey.set(str(key).replace("'", ""))
            self.listener.stop()
            self.mouse_temp_listener.stop()
        except AttributeError:
            pass

    def set_mouse_hotkey(self, x, y, button, pressed):
        if pressed:
            self.hotkey_type = "mouse"
            self.hotkey_code = button
            self.hotkey.set(str(button).split(".")[-1])
            self.listener.stop()
            self.mouse_temp_listener.stop()

    def on_key_press(self, key):
        if self.mode.get() == "hold" and self.is_active_hotkey(key, "keyboard"):
            self.is_pressed = True
            self.start_clicker()

    def on_key_release(self, key):
        if self.mode.get() == "hold" and self.is_active_hotkey(key, "keyboard"):
            self.is_pressed = False
            self.stop_clicker()

    def on_mouse_click(self, x, y, button, pressed):
        # Consolidated press/release handling
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
        if self.mode.get() == "toggle":
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
        delay = self.convert_delay() / 1000  # Convert to seconds
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