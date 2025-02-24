import tkinter as tk
import subprocess
import platform
import psutil

class Keyboard:
    def __init__(self, root, entry_widget):
        self.root = root

        self.entry = entry_widget
        self.entry.bind("<FocusIn>", self.open_osk)
        self.entry.bind("<FocusOut>", self.close_osk)

        self.is_osk_open = False

    def open_osk(self, event=None):
        if not self.is_osk_open:
            # Open the On-Screen Keyboard
            if platform.system() == "Windows":
                subprocess.Popen("cmd /c start osk", shell=True)
                self.is_osk_open = True

    def close_osk(self, event=None):
        if self.is_osk_open:
            # Close the On-Screen Keyboard
            try:
                for proc in psutil.process_iter():
                    if proc.name() == "osk.exe":
                        proc.terminate()
                        proc.wait()  # Wait for the process to terminate
                #self.is_osk_open = False
                self.root.after(100, lambda: setattr(self, "is_osk_open", False))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass  # Handle cases where the process may not exist or can't be terminated
