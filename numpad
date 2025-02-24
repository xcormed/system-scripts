# numpad.py
import customtkinter as ctk
import tkinter as tk

class Numpad:
    def __init__(self, root, entry_widget, x_offset=20, y_offset=20):
        self.root = root
        self.entry = entry_widget
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.numpad_window = None
        self.is_closing = False

        # Bind the entry widget to trigger the numpad on focus
        self.entry.bind("<FocusIn>", self.open_numpad)

    def open_numpad(self, event=None):
        # Check if the numpad is already open or if it's in the process of closing
        if self.numpad_window is not None and self.numpad_window.winfo_exists():
            return
        if self.is_closing:
            return

        # Create the numpad window
        self.numpad_window = ctk.CTkToplevel(self.root)
        self.numpad_window.title("Number Pad")
        self.numpad_window.geometry("212x300")
        self.numpad_window.attributes('-topmost', True)

        # Position the numpad near the entry
        x = self.entry.winfo_rootx() + self.x_offset
        y = self.entry.winfo_rooty() + self.y_offset    
        self.numpad_window.geometry(f"+{x}+{y}")

        # Define functions for numpad buttons
        def insert_number(number):
            self.entry.insert(tk.END, str(number))
        
        def backspace():
            self.entry.delete(len(self.entry.get()) - 1)
        
        def clear_entry():
            self.entry.delete(0, tk.END)
        
        # Create number pad buttons
        buttons = [
            ('1', 1, 0), ('2', 1, 1), ('3', 1, 2),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2),
            ('7', 3, 0), ('8', 3, 1), ('9', 3, 2),
            ('0', 4, 1)
        ]
        
        for (text, row, col) in buttons:
            button = ctk.CTkButton(self.numpad_window, text=text, width=60, height=60, 
                                   font=("Arial", 18), 
                                   command=lambda t=text: insert_number(t))
            button.grid(row=row, column=col, padx=5, pady=5)
        
        # Special buttons for backspace and clear
        back_button = ctk.CTkButton(self.numpad_window, text="⌫", width=60, height=60,
                                    font=("Arial", 18), command=backspace)
        back_button.grid(row=4, column=0, padx=5, pady=5)
        
        clear_button = ctk.CTkButton(self.numpad_window, text="Clear", width=60, height=60,
                                     font=("Arial", 18), command=clear_entry)
        clear_button.grid(row=4, column=2, padx=5, pady=5)

        # Close the numpad window
        def close_numpad(event=None):
            if self.numpad_window is not None and self.numpad_window.winfo_exists():
                self.numpad_window.destroy()
            self.numpad_window = None  # Reset numpad_window reference
            self.is_closing = True     # Set closing flag

            # Reset the closing flag after a short delay to prevent immediate reopen
            self.root.after(100, lambda: setattr(self, "is_closing", False))

        # Set the close function for the numpad window and handle outside clicks
        self.numpad_window.protocol("WM_DELETE_WINDOW", close_numpad)
        