import tkinter as tk
import threading
import time
import pyttsx3  # For Text-to-Speech functionality
import subprocess
import sys
import os
import ctypes
import win32gui

class KeyboardFrameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Keyboard Application")
        self.geometry("960x540")
        self.attributes("-fullscreen", True)
        self.configure(bg="black")

        self.create_window_controls()
        self.keyboard_frame = KeyboardFrame(self)
        self.keyboard_frame.pack(expand=True, fill="both")

        self.monitor_focus_thread = threading.Thread(target=self.monitor_focus, daemon=True)
        self.monitor_focus_thread.start()

        self.monitor_start_menu_thread = threading.Thread(target=self.monitor_start_menu, daemon=True)
        self.monitor_start_menu_thread.start()

    def create_window_controls(self):
        """Adds Close and Minimize buttons to the top of the app window."""
        control_frame = tk.Frame(self, bg="gray")  # Change background color to make it visible
        control_frame.pack(side="top", fill="x")

        minimize_button = tk.Button(
            control_frame, text="Minimize", bg="light blue", fg="black",
            command=self.iconify, font=("Arial", 12)
        )
        minimize_button.pack(side="right", padx=5, pady=5)

        close_button = tk.Button(
            control_frame, text="Close", bg="red", fg="white",
            command=self.destroy, font=("Arial", 12)
        )
        close_button.pack(side="right", padx=5, pady=5)

    def monitor_focus(self):
        """Ensure this application stays in focus."""
        while True:
            time.sleep(0.5)  # Check every 500ms
            try:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                if hwnd != self.winfo_id():
                    self.force_focus()
            except Exception as e:
                print(f"Focus monitoring error: {e}")

    def force_focus(self):
        """Force this application to the foreground."""
        try:
            self.iconify()
            self.deiconify()
            ctypes.windll.user32.SetForegroundWindow(self.winfo_id())
        except Exception as e:
            print(f"Error forcing focus: {e}")

    def send_esc_key(self):
        """Send the ESC key to close the Start Menu."""
        ctypes.windll.user32.keybd_event(0x1B, 0, 0, 0)  # ESC key down
        ctypes.windll.user32.keybd_event(0x1B, 0, 2, 0)  # ESC key up
        print("ESC key sent to close Start Menu.")

    def is_start_menu_open(self):
        """Check if the Start Menu is currently open and focused."""
        hwnd = win32gui.GetForegroundWindow()  # Get the handle of the active (focused) window
        class_name = win32gui.GetClassName(hwnd)  # Get the class name of the active window
        return class_name in ["Shell_TrayWnd", "Windows.UI.Core.CoreWindow"]

    def monitor_start_menu(self):
        """Continuously check and close the Start Menu if it is open."""
        while True:
            try:
                if self.is_start_menu_open():
                    print("Start Menu detected. Closing it now.")
                    self.send_esc_key()
            except Exception as e:
                print(f"Error in monitor_start_menu: {e}")
            time.sleep(0.5)  # Adjust frequency as needed

class KeyboardFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.current_text = tk.StringVar()
        self.current_row_index = 0
        self.current_button_index = 0
        self.in_row_selection_mode = True
        self.spacebar_pressed = False
        self.backward_scanning_active = False
        self.scanning_thread = None
        self.press_time = None  # To record the time when spacebar is pressed
        self.debounce_time = 0.1

        self.tts_engine = pyttsx3.init()  # Initialize TTS engine

        self.row_titles = [
            "Controls", "A-B-C-D-E-F", "G-H-I-J-K-L", "M-N-O-P-Q-R", "S-T-U-V-W-X", "Y-Z 1 2 3", "4 5 6 7 8 9"
        ]
        self.rows = [
            ["Play", "Space", "Del Letter", "Del Word", "Clear", "Back"],
            ["A", "B", "C", "D", "E", "F"],
            ["G", "H", "I", "J", "K", "L"],
            ["M", "N", "O", "P", "Q", "R"],
            ["S", "T", "U", "V", "W", "X"],
            ["Y", "Z", "0", "1", "2", "3"],
            ["4", "5", "6", "7", "8", "9"]
        ]

        self.create_layout()
        self.bind_keys()
        self.highlight_row(0)  # Start with the first row highlighted

    def create_layout(self):
        # Create the text display bar
        self.text_bar_button = tk.Button(
            self,
            textvariable=self.current_text,
            font=("Arial Black", 72),
            bg="light blue",
            command=self.read_text_tts,
        )
        self.text_bar_button.grid(row=0, column=0, columnspan=6, sticky="nsew")

        # Create buttons and store references
        self.buttons = []  # Store button references for each row
        for row_index, row_keys in enumerate(self.rows):
            button_row = []
            for col_index, key in enumerate(row_keys):
                btn = tk.Button(
                    self,
                    text=key,
                    font=("Arial Bold", 48),
                    bg="light blue",
                    command=lambda k=key: self.handle_button_press(k)
                )
                btn.grid(row=row_index + 1, column=col_index, sticky="nsew")
                button_row.append(btn)
            self.buttons.append(button_row)

        # Configure rows and columns to fill the screen
        for i in range(len(self.rows) + 1):  # +1 for the text bar
            self.grid_rowconfigure(i, weight=1)
        for j in range(6):  # Assuming 6 columns
            self.grid_columnconfigure(j, weight=1)

    def create_window_controls(self):
        """Adds Close and Minimize buttons to the top of the app window."""
        control_frame = tk.Frame(self, bg="gray")  # Change background color to make it visible
        control_frame.pack(side="top", fill="x")

        minimize_button = tk.Button(
            control_frame, text="Minimize", bg="light blue", fg="black",
            command=self.iconify, font=("Arial", 12)
        )
        minimize_button.pack(side="right", padx=5, pady=5)

        close_button = tk.Button(
            control_frame, text="Close", bg="red", fg="white",
            command=self.destroy, font=("Arial", 12)
        )
        close_button.pack(side="right", padx=5, pady=5)

    def bind_keys(self):
        """Bind keys for scanning and selecting."""
        self.bind_all("<KeyPress-space>", self.start_scanning)
        self.bind_all("<KeyRelease-space>", self.stop_scanning)
        self.bind_all("<KeyPress-Return>", self.start_selecting)
        self.bind_all("<KeyRelease-Return>", self.stop_selecting)

    def start_selecting(self, event):
        """Start tracking when the Return key is pressed."""
        if not hasattr(self, "return_press_time") or self.return_press_time is None:
            self.return_press_time = time.time()  # Record the press time
            print("Return key pressed.")

    def stop_selecting(self, event):
        """Handle selection logic when the Return key is released."""
        if hasattr(self, "return_press_time") and self.return_press_time is not None:
            press_duration = time.time() - self.return_press_time
            print(f"Return key released after {press_duration:.2f} seconds.")

            # Activate selection only if the key was held for at least 0.1 seconds
            if press_duration >= 0.1:
                print("Select action triggered.")
                self.select_button()

            # Reset the press time
            self.return_press_time = None

    def start_scanning(self, event):
        """Start tracking when the spacebar is pressed."""
        if not self.spacebar_pressed:
            self.spacebar_pressed = True
            self.spacebar_press_time = time.time()  # Record the press time
            print("Spacebar pressed.")

            # Start a thread to monitor backward scanning
            threading.Thread(target=self.monitor_backward_scanning, daemon=True).start()

    def stop_scanning(self, event):
        """Handle the logic when the spacebar is released."""
        if self.spacebar_pressed:
            self.spacebar_pressed = False
            press_duration = time.time() - self.spacebar_press_time
            print(f"Spacebar released after {press_duration:.2f} seconds.")
            
            # Forward scanning if held between 0.25 and 3 seconds
            if 0.25 <= press_duration <= 3:
                print("Scanning forward by one selection.")
                self.scan_forward()

            # Reset tracking variables
            self.spacebar_press_time = None

    def monitor_backward_scanning(self):
        """Continuously scan backward if the spacebar is held for more than 3 seconds."""
        while self.spacebar_pressed:
            press_duration = time.time() - self.spacebar_press_time

            if press_duration > 3:
                print("Spacebar held for more than 3 seconds. Scanning backward.")
                self.scan_backward()
                time.sleep(2)  # Scan backward every 2 seconds while held

            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)

    def monitor_forward_scanning(self):
        """Monitor the duration of the spacebar press and handle forward scanning."""
        time.sleep(1)  # Wait for 1 second before starting scanning
        if self.spacebar_pressed:
            print("Spacebar held for 1 second. Starting forward scanning.")
            while self.spacebar_pressed:
                self.scan_forward()  # Trigger forward scan
                time.sleep(2)  # Wait for 2 seconds between scans

    def scan_forward(self):
        """Scan forward through rows or buttons based on the mode."""
        if not self.winfo_exists():  # Ensure the frame still exists
            return

        if self.in_row_selection_mode:
            # Forward scan through rows
            prev_row_index = self.current_row_index
            self.current_row_index = (self.current_row_index + 1) % len(self.rows)
            self.highlight_row(self.current_row_index, prev_row_index)
            self.speak_row_title(self.current_row_index)
        else:
            # Forward scan through buttons in the current row
            prev_button_index = self.current_button_index
            self.current_button_index = (self.current_button_index + 1) % len(self.rows[self.current_row_index])

            if self.current_button_index == 0:
                # Loop detected, return to row selection mode
                print("Loop detected in button selection mode. Returning to row selection mode.")
                self.in_row_selection_mode = True
                self.highlight_row(self.current_row_index)
                self.speak_row_title(self.current_row_index)
            else:
                # Highlight and TTS for each button
                self.highlight_button(self.current_button_index, prev_button_index)
                self.speak_button_label(self.current_button_index)

    def scan_backward(self):
        """Scan backward through rows or buttons based on the mode."""
        if self.in_row_selection_mode:
            # Backward scan through rows
            prev_row_index = self.current_row_index
            self.current_row_index = (self.current_row_index - 1) % len(self.rows)
            self.highlight_row(self.current_row_index, prev_row_index)
            self.speak_row_title(self.current_row_index)
        else:
            # Backward scan through buttons in the current row
            prev_button_index = self.current_button_index
            self.current_button_index = (self.current_button_index - 1) % len(self.rows[self.current_row_index])

            if self.current_button_index == len(self.rows[self.current_row_index]) - 1:
                # Loop detected, return to row selection mode
                print("Loop detected in button selection mode. Returning to row selection mode.")
                self.in_row_selection_mode = True
                self.highlight_row(self.current_row_index)
                self.speak_row_title(self.current_row_index)
            else:
                # Highlight and TTS for each button
                self.highlight_button(self.current_button_index, prev_button_index)
                self.speak_button_label(self.current_button_index)


    def select_button(self, event=None):
        """Handle selection triggered by the Return key."""
        if self.in_row_selection_mode:
            # Transition to Button Select Mode
            self.in_row_selection_mode = False
            self.current_button_index = 0  # Reset to the first button in the selected row

            # Clear the row highlight
            for button in self.buttons[self.current_row_index]:
                button.config(bg="light blue", fg="black")

            # Highlight the first button in the row
            self.highlight_button(self.current_button_index)

            # Speak the first button in the row
            self.speak_button_label(self.current_button_index)
        else:
            # Handle the selected button action
            key = self.rows[self.current_row_index][self.current_button_index]
            self.handle_button_press(key)

            # Return to Row Select Mode after action
            self.in_row_selection_mode = True
            self.highlight_row(self.current_row_index)  # Highlight the row again


    def highlight_row(self, row_index, prev_row_index=None):
        """Highlight the buttons in the current row during row selection mode."""
        if prev_row_index is not None:
            # Un-highlight the previous row
            for button in self.buttons[prev_row_index]:
                button.config(bg="light blue")

        # Highlight the current row
        for button in self.buttons[row_index]:
            button.config(bg="yellow")
        self.update_idletasks()

    def highlight_button(self, button_index, prev_button_index=None):
        """Highlight the current button and reset the previous button."""
        if prev_button_index is not None:
            self.buttons[self.current_row_index][prev_button_index].config(bg="light blue", fg="black")

        self.buttons[self.current_row_index][button_index].config(bg="yellow", fg="black")
        self.update_idletasks()

    def speak_row_title(self, row_index):
        """Speak the title of the current row."""
        title = self.row_titles[row_index]
        self.tts_engine.say(title)
        self.tts_engine.runAndWait()

    def speak_button_label(self, button_index):
        """Speak the label of the currently highlighted button."""
        label = self.rows[self.current_row_index][button_index]
        self.tts_engine.say(label)
        self.tts_engine.runAndWait()

    def handle_button_press(self, char):
        """Handle the action for a button press."""
        if char == "Play":
            self.read_text_tts()
        elif char == "Back":
            self.open_and_exit("comm-v8.py")  # Replace with the target script
        elif char == "Space":
            self.current_text.set(self.current_text.get() + " ")
        elif char == "Clear":
            self.current_text.set("")
        elif char == "Del Letter":
            self.current_text.set(self.current_text.get()[:-1])
        elif char == "Del Word":
            words = self.current_text.get().split()
            self.current_text.set(" ".join(words[:-1]))
        else:
            self.current_text.set(self.current_text.get() + char)

    def open_and_exit(self, script_name):
        """Open a new Python script in the same directory and close the current application."""
        try:
            script_path = os.path.join(os.path.dirname(__file__), script_name)
            subprocess.Popen([sys.executable, script_path])
            self.parent.destroy()
        except Exception as e:
            print(f"Failed to open script {script_name}: {e}")

    def read_text_tts(self):
        """Read the current text with TTS."""
        text = self.current_text.get()
        if text:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()

if __name__ == "__main__":
    app = KeyboardFrameApp()
    app.mainloop()
