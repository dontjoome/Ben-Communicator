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

        # Initialize current mode
        self.current_mode = "Keyboard"  # Default mode is "Keyboard"

        # Initialize rows and row_titles
        self.row_titles = [
            "Controls", "A-B-C-D-E-F", "G-H-I-J-K-L", "M-N-O-P-Q-R", "S-T-U-V-W-X", "Y-Z 1 2 3", "4 5 6 7 8 9"
        ]
        self.rows = [
            ["Space", "Del Letter", "Del Word", "Clear", "Layout", "Main"],
            ["A", "B", "C", "D", "E", "F"],
            ["G", "H", "I", "J", "K", "L"],
            ["M", "N", "O", "P", "Q", "R"],
            ["S", "T", "U", "V", "W", "X"],
            ["Y", "Z", "0", "1", "2", "3"],
            ["4", "5", "6", "7", "8", "9"]
        ]

        # Create the layout
        self.create_layout()
        self.bind_keys()
        self.highlight_row(0)  # Start with the first row highlighted

    def create_layout(self):
        """Create the layout for the current mode."""
        for widget in self.winfo_children():
            widget.destroy()  # Clear existing widgets

        # Create the text display bar (row 0)
        self.text_bar_button = tk.Button(
            self,
            textvariable=self.current_text,
            font=("Arial Black", 72),
            bg="light blue",
            command=self.read_text_tts,
        )
        self.text_bar_button.grid(row=0, column=0, columnspan=6, sticky="nsew")

        # Create buttons for each row
        self.buttons = []
        for row_index, row_keys in enumerate(self.rows):
            button_row = []
            for col_index, key in enumerate(row_keys):
                font_size = 48 if self.current_mode == "Keyboard" else (12 if len(key) > 10 else 24)
                btn = tk.Button(
                    self,
                    text=key,
                    font=("Arial Bold", font_size),
                    bg="light blue",
                    command=lambda k=key: self.handle_button_press(k),
                )
                btn.grid(row=row_index + 1, column=col_index, sticky="nsew")  # Offset by 1 for the text bar
                button_row.append(btn)
            self.buttons.append(button_row)

        # Configure the grid
        for i in range(len(self.rows) + 1):  # Include the text box
            self.grid_rowconfigure(i, weight=1)
        for j in range(6):  # Always 6 columns
            self.grid_columnconfigure(j, weight=1)

        # Configure the grid
        for i in range(len(self.rows) + 1):  # Include the text box
            self.grid_rowconfigure(i, weight=1)
        for j in range(6):  # Always 6 columns
            self.grid_columnconfigure(j, weight=1)

    def create_button(self, text, command):
        """Create a button with dynamic font size based on text length."""
        font_size = 48  # Default font size
        if self.current_mode == "Words" and len(text) > 10:  # Adjust font size for long text
            font_size = 12

        return tk.Button(
            self,
            text=text,
            font=("Arial Bold", font_size),
            bg="light blue",
            command=command,
        )

    def toggle_mode(self):
        """Toggle between Keyboard Mode and Words Mode."""
        if self.current_mode == "Keyboard":
            self.current_mode = "Words"
            self.show_main_menu()  # Display the main Words Mode menu
            self.current_row_index = 0  # Reset to Controls row
            self.in_row_selection_mode = True
            self.highlight_row(0)
        else:
            self.current_mode = "Keyboard"
            # Reset to Keyboard Mode layout
            self.row_titles = [
                "Controls", "A-B-C-D-E-F", "G-H-I-J-K-L", "M-N-O-P-Q-R", "S-T-U-V-W-X", "Y-Z-0-1-2-3", "4-5-6-7-8-9"
            ]
            self.rows = [
                ["Space", "Del Letter", "Del Word", "Clear", "Layout", "Main"],  # Controls
                ["A", "B", "C", "D", "E", "F"],
                ["G", "H", "I", "J", "K", "L"],
                ["M", "N", "O", "P", "Q", "R"],
                ["S", "T", "U", "V", "W", "X"],
                ["Y", "Z", "0", "1", "2", "3"],
                ["4", "5", "6", "7", "8", "9"]
            ]
            self.create_layout()
            self.current_row_index = 0  # Highlight Controls row
            self.in_row_selection_mode = True
            self.highlight_row(0)

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
        """Scan forward through rows or buttons."""
        if not self.winfo_exists():
            return

        if self.in_row_selection_mode:
            # Move to the next row, looping back if necessary
            prev_row_index = self.current_row_index
            self.current_row_index = (self.current_row_index + 1) % (len(self.rows) + 1)  # Include the text bar
            print(f"Scanning forward to row {self.current_row_index}")

            self.highlight_row(self.current_row_index, prev_row_index)
            if self.current_row_index == 0:
                print("Text bar highlighted.")
            else:
                self.speak_row_title(self.current_row_index)
        else:
            # Scan buttons within the current row
            prev_button_index = self.current_button_index
            self.current_button_index = (self.current_button_index + 1) % len(self.rows[self.current_row_index - 1])

            if self.current_button_index == 0:  # Button looped back
                self.in_row_selection_mode = True
                self.highlight_row(self.current_row_index)
                self.speak_row_title(self.current_row_index)
            else:
                self.highlight_button(self.current_button_index, prev_button_index)
                self.speak_button_label(self.current_button_index)

    def scan_backward(self):
        """Scan backward through rows or buttons."""
        if not self.winfo_exists():
            return

        if self.in_row_selection_mode:
            # Move to the previous row, looping back if necessary
            prev_row_index = self.current_row_index
            self.current_row_index = (self.current_row_index - 1) % (len(self.rows) + 1)  # Include the text bar
            print(f"Scanning backward to row {self.current_row_index}")

            self.highlight_row(self.current_row_index, prev_row_index)
            if self.current_row_index == 0:
                print("Text bar highlighted.")
            else:
                self.speak_row_title(self.current_row_index)
        else:
            # Scan buttons within the current row
            prev_button_index = self.current_button_index
            self.current_button_index = (self.current_button_index - 1) % len(self.rows[self.current_row_index - 1])

            if self.current_button_index == len(self.rows[self.current_row_index - 1]) - 1:  # Button looped back
                self.in_row_selection_mode = True
                self.highlight_row(self.current_row_index)
                self.speak_row_title(self.current_row_index)
            else:
                self.highlight_button(self.current_button_index, prev_button_index)
                self.speak_button_label(self.current_button_index)

    def select_button(self, event=None):
        """Handle selection triggered by the Return key."""
        if self.in_row_selection_mode:
            if self.current_row_index == 0:  # Text bar selected
                self.read_text_tts()  # Play the text
            else:
                # Transition to Button Selection Mode
                self.in_row_selection_mode = False
                self.current_button_index = 0  # Start with the first button in the row

                # Un-highlight the row and highlight the first button
                if self.current_row_index > 0:
                    for button in self.buttons[self.current_row_index - 1]:
                        button.config(bg="light blue")
                    self.highlight_button(self.current_button_index)

                # Speak the first button label
                self.speak_button_label(self.current_button_index)
        else:
            # Perform the action for the selected button
            key = self.rows[self.current_row_index - 1][self.current_button_index]
            self.handle_button_press(key)

            if self.current_mode == "Keyboard":
                # In Alphabet mode, reset to the same row
                self.in_row_selection_mode = True
                self.highlight_row(self.current_row_index)
            elif self.current_mode == "Words":
                if key in self.get_submenus():
                    # If a submenu is selected, reset to the Controls row
                    self.in_row_selection_mode = True
                    self.current_row_index = 0  # Controls row
                    self.highlight_row(0)
                else:
                    # In submenus, reset to the current row
                    self.in_row_selection_mode = True
                    self.highlight_row(self.current_row_index)

    def highlight_row(self, row_index, prev_row_index=None):
        """Highlight the buttons in the current row."""
        if prev_row_index is not None:
            if prev_row_index == 0:  # Un-highlight the text bar
                self.text_bar_button.config(bg="light blue")
            else:
                # Un-highlight the previous row
                for button in self.buttons[prev_row_index - 1]:
                    button.config(bg="light blue")

        if row_index == 0:  # Highlight the text bar
            self.text_bar_button.config(bg="yellow")
        else:
            # Highlight the current row
            for button in self.buttons[row_index - 1]:
                button.config(bg="yellow")
        self.update_idletasks()

    def highlight_button(self, button_index, prev_button_index=None):
        """Highlight the current button and reset the previous button."""
        if prev_button_index is not None:
            self.buttons[self.current_row_index - 1][prev_button_index].config(bg="light blue", fg="black")

        self.buttons[self.current_row_index - 1][button_index].config(bg="yellow", fg="black")
        self.update_idletasks()

    def speak_row_title(self, row_index):
        """Speak the title of the current row."""
        if row_index == 0:  # Text box row
            title = "Text Box"
        elif row_index == 1:  # Controls row
            title = "Controls"
        else:
            # Adjust the actual row index based on the current mode
            if self.current_mode == "Keyboard":
                # Offset for alphabet keyboard mode (text box + controls rows)
                actual_row_index = row_index - 1
            elif self.current_mode == "Words":
                # Offset for word keyboard mode (text box + controls rows)
                actual_row_index = row_index - 2

            # Check if the actual row index is within bounds
            if 0 <= actual_row_index < len(self.row_titles):
                title = self.row_titles[actual_row_index]
            else:
                title = ""  # No title for rows beyond defined row_titles

        if title:
            print(f"TTS: {title}")  # Debugging line
            self.tts_engine.say(title)
            self.tts_engine.runAndWait()

    def speak_button_label(self, button_index):
        """Speak the label of the current button."""
        label = self.rows[self.current_row_index - 1][button_index]
        self.tts_engine.say(label)
        self.tts_engine.runAndWait()

    def handle_button_press(self, char):
        """Handle button actions based on the mode."""
        if char == "Layout":
            self.toggle_mode()
        elif char == "Main":
            self.open_and_exit("comm-v8.py")  # Close and open the main script
        elif char == "Back":
            self.show_main_menu()  # Return to the main Words Mode menu
        elif char in ["Space", "Del Word", "Clear"]:
            # Shared actions between Keyboard and Words modes
            if char == "Space":
                self.current_text.set(self.current_text.get() + " ")
            elif char == "Clear":
                self.current_text.set("")
            elif char == "Del Word":
                words = self.current_text.get().split()
                self.current_text.set(" ".join(words[:-1]))
        elif self.current_mode == "Keyboard":
            # Handle alphabet keyboard-specific actions
            if char == "Del Letter":
                self.current_text.set(self.current_text.get()[:-1])
            else:
                self.current_text.set(self.current_text.get() + char)
        elif self.current_mode == "Words":
            # Handle words mode-specific actions
            submenus = self.get_submenus()
            if char in submenus:  # Navigate to a submenu
                self.show_submenu(char)  # Navigate to the selected submenu
            elif char in [word for row in self.rows for word in row]:  # If a word is clicked in a submenu
                self.current_text.set(self.current_text.get() + char + " ")  # Append the word to the text box`

    def show_submenu(self, submenu_title):
        """Display the submenu for the selected title."""
        submenus = self.get_submenus()
        if submenu_title in submenus:
            submenu = submenus[submenu_title]

            # Update row titles for TTS feedback
            self.row_titles = submenu["row_titles"]

            # Collect words for the 6x6 grid
            words = [word for row in submenu["rows"] for word in row]  # Flatten the rows

            # Ensure 36 buttons
            words = words[:36] + [""] * (36 - len(words))

            # Create a 6x6 grid, first row for controls
            self.rows = [
                ["Back", "Space", "Del Word", "Clear", "Layout", "Main"],  # Controls row
                words[:6],  # Row 1
                words[6:12],  # Row 2
                words[12:18],  # Row 3
                words[18:24],  # Row 4
                words[24:30],  # Row 5
                words[30:36],  # Row 6
            ]
            self.create_layout()

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

    def show_main_menu(self):
        """Display the main Words Mode menu with a 6x6 grid of submenu titles."""
        submenus = self.get_submenus()

        # Row titles for TTS
        self.row_titles = [
            "General References", "Daily Life", "Education and Nature",
            "Emotions and Actions", "Practical and Everyday Living", "Shows and TV"
        ]

        # Submenu titles for rows
        submenu_titles = [
            "Common Phrases/Needs", "Pronouns", "Request Basics", "Time/Days Reference",
            "Location Reference", "Family & Proper Names", "Forming Questions", "Health & Body",
            "Clothing & Accessories", "Weather & Seasons", "Food & Drink", "Entertainment",
            "Numbers & Math", "Transportation", "Work & Tools", "School & Learning",
            "Animals", "Nature", "Emotions & Feelings", "Travel & Vacations",
            "Holidays & Celebrations", "Shopping & Money", "Technology & Media", "Verbs & Actions",
            "Household", "Sports & Activities", "Hobbies & Interests", "Jobs & Professions",
            "Colors", "People & Titles", "Simpsons/Futurama", "Family Guy/American Dad",
            "South Park", "Dragon Ball Universe", "Drake & Josh/iCarly/Victorious", "Rugrats/Spongebob"
        ]

        # Create rows with controls and submenu buttons
        self.rows = [
            ["Space", "Del Word", "Clear", "Back", "Layout", "Main"],  # Controls row
            submenu_titles[:6],  # General References
            submenu_titles[6:12],  # Daily Life
            submenu_titles[12:18],  # Education and Nature
            submenu_titles[18:24],  # Emotions and Actions
            submenu_titles[24:30],  # Practical and Everyday Living
            submenu_titles[30:36]   # Shows and TV
        ]
        self.create_layout()

    def show_main_menu(self):
        """Display the main Words Mode menu with a 6x6 grid of submenu titles."""
        submenus = self.get_submenus()
        
        # Categorized row titles for TTS feedback
        self.row_titles = [
            "General References",   # Row 1
            "Daily Life",           # Row 2
            "Education and Nature", # Row 3
            "Emotions and Actions", # Row 4
            "Practical and Everyday Living", # Row 5
            "Shows and TV"          # Row 6
        ]

        # Collect submenu titles for the 6x6 grid
        submenu_titles = [
            # General References (6 titles)
            "Common Phrases/Needs", "Pronouns", "Request Basics", "Time/Days Reference",
            "Location Reference", "Family & Proper Names",

            # Daily Life (6 titles)
            "Forming Questions", "Health & Body", "Clothing & Accessories", "Weather & Seasons",
            "Food & Drink", "Entertainment",

            # Education and Nature (6 titles)
            "Numbers & Math", "Transportation", "Work & Tools", "School & Learning",
            "Animals", "Nature",

            # Emotions and Actions (6 titles)
            "Emotions & Feelings", "Travel & Vacations", "Holidays & Celebrations",
            "Shopping & Money", "Technology & Media", "Verbs & Actions",

            # Practical and Everyday Living (6 titles)
            "Household", "Sports & Activities", "Hobbies & Interests", "Jobs & Professions",
            "Colors", "People & Titles",

            # Shows and TV (6 titles)
            "Simpsons/Futurama", "Family Guy/American Dad", "South Park",
            "Dragon Ball Universe", "Drake & Josh/iCarly/Victorious", "Rugrats/Spongebob"
        ]


        # Ensure 36 buttons
        submenu_titles = submenu_titles[:36] + [""] * (36 - len(submenu_titles))

        # Create a 6x6 grid
        self.rows = [
            ["Back", "Space", "Del Word", "Clear", "Layout", "Main"],  # Controls
            submenu_titles[:6],  # Row 1
            submenu_titles[6:12],  # Row 2
            submenu_titles[12:18],  # Row 3
            submenu_titles[18:24],  # Row 4
            submenu_titles[24:30],  # Row 5
            submenu_titles[30:36],  # Row 6
        ]
        # Reset scanning to start at the Controls row
        self.current_row = 1  # Set highlight to start on Controls row
        self.create_layout()

    def get_submenus(self):
        return {
            "row_titles": [
                "General References",
                "Daily Life",
                "Education and Nature",
                "Emotions and Actions",
                "Practical and Technology",
                "Shows and TV",
            ],
            "Common Phrases/Needs": {  # Add the rest of your hierarchical data here
                "row_titles": ["Basic Actions", "Movement", "Communication", "Work", "Play", "Feelings"],
                "rows": [
                    ["Do", "Make", "Get", "Take", "Give", "Put"],
                    ["Run", "Walk", "Jump", "Sit", "Stand", "Climb"],
                    ["Talk", "Ask", "Tell", "Listen", "Speak", "Say"],
                    ["Build", "Fix", "Clean", "Write", "Plan", "Work"],
                    ["Play", "Laugh", "Dance", "Sing", "Draw", "Cook"],
                    ["Love", "Hate", "Need", "Feel", "Want", "Smile"],
                ],
            },
            "Pronouns": {
                "row_titles": ["Subject", "Subject 2", "Possessive", "Reflexive", "Demonstrative", "Interrogative"],
                "rows": [
                    ["I", "You", "He", "She", "It", "We"],  # Subject
                    ["Me", "You", "Him", "Her", "It", "Us"],  # Object
                    ["My", "Your", "His", "Her", "Its", "Our"],  # Possessive
                    ["Myself", "Yourself", "Himself", "Herself", "Itself", "Ourselves"],  # Reflexive
                    ["This", "That", "These", "Those", "Here", "There"],  # Demonstrative
                    ["Who", "What", "Which", "Whose", "Whom", "Why"],  # Interrogative
                ]
            },
            "Request Basics": {
                "row_titles": ["Food & Drink", "Help", "Comfort", "Information", "Toys/Games", "Other"],
                "rows": [
                    ["Water", "Juice", "Milk", "Tea", "Coffee", "Snack"],
                    ["Help", "Fix", "Move", "Reach", "Carry", "Hold"],
                    ["Cold", "Hot", "Blanket", "Pillow", "Fan", "Jacket"],
                    ["Who", "What", "Where", "When", "Why", "How"],
                    ["Ball", "Doll", "Car", "Puzzle", "Game", "Book"],
                    ["Yes", "No", "Stop", "Go", "Wait", "Come"]
                ],
            },
            "Time/Days Reference": {
                "row_titles": ["Times of Day", "Days of Week", "Months", "Seasons", "Time Units", "Relative Time"],
                "rows": [
                    ["Morning", "Afternoon", "Evening", "Night", "Midnight", "Noon"],
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                    ["January", "February", "March", "April", "May", "June"],
                    ["Summer", "Winter", "Spring", "Autumn", "Rainy", "Dry"],
                    ["Hour", "Minute", "Second", "Day", "Week", "Month"],
                    ["Now", "Soon", "Later", "Tomorrow", "Yesterday", "Today"]
                ],
            },
            "Location Reference": {
                "row_titles": ["Home", "School", "Outdoors", "Public", "Travel", "Other"],
                "rows": [
                    ["Kitchen", "Bathroom", "Bedroom", "Living Room", "Garage", "Yard"],
                    ["Classroom", "Office", "Library", "Gym", "House", "Cafeteria"],
                    ["Park", "Beach", "Mountain", "Forest", "Trail", "Field"],
                    ["Store", "Market", "Hospital", "Police", "Mall", "Airport"],
                    ["Car", "Bus", "Train", "Plane", "Boat", "Bike"],
                    ["City", "Village", "Island", "Hotel", "Camp", "Farm"]
                ],
            },
            "People & Titles": {
                "row_titles": ["Family", "Friends", "Helpers", "Titles", "Generic Names", "Other"],
                "rows": [
                    ["Mom", "Dad", "Sister", "Brother", "Grandma", "Grandpa"],
                    ["Friend", "Buddy", "Neighbor", "Classmate", "Bestie", "Pal"],
                    ["Doctor", "Nurse", "Teacher", "Coach", "Therapist", "Helper"],
                    ["Mr.", "Mrs.", "Miss", "Dr.", "Sir", "Ma’am"],
                    ["Guy", "Girl", "Boy", "Kid", "Person", "Someone"],
                    ["Boss", "Coworker", "Client", "Officer", "Driver", "Visitor"]
                ],
            },
            "Forming Questions": {
                "row_titles": ["Basic", "Clarification", "Personal", "Descriptive", "Decision-Making", "Other"],
                "rows": [
                    ["Who", "What", "Where", "When", "Why", "How"],
                    ["Which", "Whose", "How Many", "How Much", "How Long", "Why Not"],
                    ["Are You", "Can You", "Do You", "Will You", "Would You", "Could You"],
                    ["Describe", "Explain", "Define", "Show Me", "Tell Me", "Repeat"],
                    ["This?", "That?", "Here?", "There?", "Right?", "Wrong?"],
                    ["Is It?", "Was It?", "Should It?", "Could It?", "Would It?", "Will It?"]
                ],
            },
            "Health & Body": {
                "row_titles": ["Body Parts", "Senses", "Physical States", "Illnesses", "Treatments", "Medical Tools"],
                "rows": [
                    ["Head", "Face", "Neck", "Arm", "Leg", "Hand"],
                    ["Eyes", "Ears", "Nose", "Mouth", "Skin", "Hair"],
                    ["Tired", "Hungry", "Thirsty", "Cold", "Hot", "Sick"],
                    ["Fever", "Cough", "Pain", "Injury", "Allergy", "Flu"],
                    ["Medicine", "Therapy", "Bandage", "Rest", "Ice Pack", "Injection"],
                    ["Stethoscope", "Thermometer", "Syringe", "Wheelchair", "Crutch", "IV"]
                ],
            },
            "Clothing & Accessories": {
                "row_titles": ["Tops", "Bottoms", "Outerwear", "Footwear", "Accessories", "Seasonal"],
                "rows": [
                    ["Shirt", "T-Shirt", "Blouse", "Tank Top", "Sweater", "Hoodie"],
                    ["Pants", "Jeans", "Shorts", "Skirt", "Leggings", "Trousers"],
                    ["Coat", "Jacket", "Blazer", "Raincoat", "Poncho", "Vest"],
                    ["Shoes", "Boots", "Sandals", "Sneakers", "Heels", "Slippers"],
                    ["Hat", "Gloves", "Scarf", "Belt", "Watch", "Sunglasses"],
                    ["Swimsuit", "Snow Boots", "Winter Coat", "Thermals", "Flip Flops", "Rain Boots"]
                ],
            },
            "Weather & Seasons": {
                "row_titles": ["General Weather", "Seasons", "Precipitation", "Sky Conditions", "Wind", "Temperature"],
                "rows": [
                    ["Sunny", "Cloudy", "Rainy", "Snowy", "Foggy", "Stormy"],
                    ["Spring", "Summer", "Autumn", "Winter", "Season", "Holiday"],
                    ["Rain", "Snow", "Hail", "Drizzle", "Sleet", "Downpour"],
                    ["Clear", "Overcast", "Cloudy", "Bright", "Dark", "Rainbow"],
                    ["Windy", "Breezy", "Gusty", "Calm", "Hurricane", "Tornado"],
                    ["Hot", "Cold", "Warm", "Cool", "Freezing", "Boiling"]
                ],
            },
            "Food & Drink": {
                "row_titles": ["Fruits", "Vegetables", "Proteins", "Carbs", "Snacks", "Drinks"],
                "rows": [
                    ["Apple", "Banana", "Orange", "Peach", "Grape", "Mango"],
                    ["Carrot", "Broccoli", "Potato", "Lettuce", "Onion", "Pepper"],
                    ["Chicken", "Beef", "Fish", "Egg", "Tofu", "Pork"],
                    ["Bread", "Rice", "Pasta", "Cereal", "Bagel", "Tortilla"],
                    ["Chips", "Cookie", "Candy", "Cake", "Popcorn", "Pretzel"],
                    ["Water", "Juice", "Milk", "Tea", "Coffee", "Soda"]
                ],
            },
            "Colors": {
                "row_titles": ["Primary Colors", "Secondary Colors", "Neutrals", "Pastels", "Brights", "Dark Shades"],
                "rows": [
                    ["Red", "Blue", "Yellow", "Green", "Purple", "Orange"],
                    ["Pink", "Brown", "Gray", "Black", "White", "Beige"],
                    ["Gold", "Silver", "Bronze", "Charcoal", "Ivory", "Cream"],
                    ["Lavender", "Peach", "Mint", "Coral", "Teal", "Maroon"],
                    ["Scarlet", "Crimson", "Turquoise", "Amber", "Magenta", "Cyan"],
                    ["Navy", "Indigo", "Olive", "Tan", "Violet", "Lilac"]
                ],
            },
            "Numbers & Math": {
                "row_titles": ["Single Digits", "Teens", "Tens", "Large Numbers", "Fractions", "Math Symbols"],
                "rows": [
                    ["One", "Two", "Three", "Four", "Five", "Six"],
                    ["Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"],
                    ["Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen"],
                    ["Hundred", "Thousand", "Million", "Billion", "Trillion", "Zero"],
                    ["Half", "Quarter", "Third", "Eighth", "Tenth", "Whole"],
                    ["Plus", "Minus", "Times", "Divide", "Equals", "Percent"]
                ],
            },
            "Transportation": {
                "row_titles": ["Land", "Water", "Air", "Public", "Emergency", "Miscellaneous"],
                "rows": [
                    ["Car", "Truck", "Bike", "Motorcycle", "Bus", "Train"],
                    ["Boat", "Ship", "Canoe", "Ferry", "Submarine", "Kayak"],
                    ["Plane", "Helicopter", "Jet", "Glider", "Drone", "Balloon"],
                    ["Taxi", "Subway", "Tram", "Metro", "Ride Share", "Trolley"],
                    ["Ambulance", "Fire Truck", "Police Car", "Rescue Boat", "Patrol", "Helicopter"],
                    ["Scooter", "Skateboard", "Hoverboard", "Segway", "RV", "ATV"]
                ],
            },
            "Work & Tools": {
                "row_titles": ["Household", "Construction", "Garden", "Office", "Mechanical", "Power Tools"],
                "rows": [
                    ["Broom", "Mop", "Vacuum", "Bucket", "Soap", "Duster"],
                    ["Hammer", "Screwdriver", "Wrench", "Saw", "Drill", "Tape"],
                    ["Shovel", "Rake", "Hoe", "Pruners", "Trowel", "Hose"],
                    ["Pen", "Pencil", "Paper", "Eraser", "Stapler", "Tape"],
                    ["Wrench", "Ratchet", "Clamp", "Socket", "Jack", "Hex Key"],
                    ["Cordless Drill", "Chainsaw", "Sander", "Grinder", "Router", "Impact Driver"]
                ],
            },
            "School & Learning": {
                "row_titles": ["Subjects", "Supplies", "People", "Places", "Activities", "Miscellaneous"],
                "rows": [
                    ["Math", "Science", "History", "English", "Art", "Music"],
                    ["Pencil", "Eraser", "Notebook", "Marker", "Ruler", "Glue"],
                    ["Teacher", "Student", "Principal", "Counselor", "Coach", "Librarian"],
                    ["Classroom", "Library", "Office", "Gym", "Cafeteria", "Playground"],
                    ["Test", "Quiz", "Homework", "Project", "Presentation", "Assignment"],
                    ["Chalk", "Board", "Textbook", "Computer", "Tablet", "Printer"]
                ],
            },
            "Entertainment": {
                "row_titles": ["Movies", "TV Shows", "Games", "Books", "Music", "Events"],
                "rows": [
                    ["Comedy", "Drama", "Horror", "Action", "Romance", "Sci-Fi"],
                    ["Cartoon", "Series", "Sitcom", "Reality", "News", "Documentary"],
                    ["Video Game", "Board Game", "Cards", "Chess", "Trivia", "Puzzle"],
                    ["Novel", "Mystery", "Biography", "Fantasy", "Poetry", "Comics"],
                    ["Song", "Album", "Artist", "Band", "Playlist", "Concert"],
                    ["Theater", "Festival", "Circus", "Parade", "Show", "Party"]
                ],
            },
            "Animals": {
                "row_titles": ["Pets", "Farm Animals", "Wild Animals", "Birds", "Reptiles", "Aquatic"],
                "rows": [
                    ["Dog", "Cat", "Bird", "Fish", "Hamster", "Rabbit"],
                    ["Cow", "Horse", "Pig", "Chicken", "Sheep", "Goat"],
                    ["Lion", "Tiger", "Elephant", "Bear", "Wolf", "Deer"],
                    ["Parrot", "Eagle", "Owl", "Crow", "Seagull", "Sparrow"],
                    ["Snake", "Lizard", "Turtle", "Crocodile", "Iguana", "Gecko"],
                    ["Shark", "Dolphin", "Whale", "Octopus", "Seal", "Crab"]
                ],
            },
            "Nature": {
                "row_titles": ["Landforms", "Water", "Sky", "Plants", "Weather", "Miscellaneous"],
                "rows": [
                    ["Mountain", "Valley", "Hill", "Canyon", "Desert", "Plateau"],
                    ["River", "Lake", "Ocean", "Stream", "Pond", "Waterfall"],
                    ["Sun", "Moon", "Stars", "Clouds", "Rainbow", "Sky"],
                    ["Tree", "Flower", "Grass", "Cactus", "Bush", "Shrub"],
                    ["Rain", "Snow", "Fog", "Hail", "Wind", "Storm"],
                    ["Sand", "Rock", "Dirt", "Soil", "Ice", "Lava"]
                ],
            },
            "Family & Proper Names": {
                "row_titles": ["Immediate Family", "Friends", "Extended Family", "Pet Names", "Common Names", "Other"],
                "rows": [
                    ["Mom", "Dad", "Brother", "Sister", "Grandma", "Grandpa"],
                    ["Friend", "Buddy", "Pal", "Neighbor", "Bestie", "Classmate"],
                    ["Uncle", "Aunt", "Cousin", "Niece", "Nephew", "Guardian"],
                    ["Rush", "Trixie", "Jazz", "Daisy", "Pepper", "Livingston"],
                    ["Allen", "Lauren", "Bryan", "Ari", "Jake", "Nancy"],
                    ["Jared", "Alexa", "Matthew", "Marissa", "Blake", "Leo"]
                ],
            },
            "Emotions & Feelings": {
                "row_titles": ["Positive", "Negative", "Neutral", "Intense", "Mild", "Physical States"],
                "rows": [
                    ["Joyful", "Excited", "Grateful", "Proud", "Hopeful", "Optimistic"],
                    ["Angry", "Frustrated", "Lonely", "Worried", "Ashamed", "Sad"],
                    ["Okay", "Fine", "Calm", "Content", "Neutral", "Meh"],
                    ["Shocked", "Overwhelmed", "Anxious", "Terrified", "Eager", "Elated"],
                    ["Annoyed", "Bored", "Confused", "Shy", "Jealous", "Scared"],
                    ["Tired", "Hungry", "Thirsty", "Hot", "Cold", "Sick"]
                ],
            },
            "Travel & Vacations": {
                "row_titles": ["Transportation", "Lodging", "Activities", "Essentials", "Documents", "Destinations"],
                "rows": [
                    ["Car", "Bus", "Train", "Plane", "Bike", "Boat"],
                    ["Hotel", "Hostel", "Motel", "Resort", "Cabin", "Airbnb"],
                    ["Hiking", "Camping", "Fishing", "Skiing", "Sightseeing", "Swimming"],
                    ["Backpack", "Snacks", "Water", "Camera", "Map", "Suitcase"],
                    ["Passport", "Visa", "ID", "Ticket", "Guidebook", "Reservation"],
                    ["Beach", "Mountain", "City", "Forest", "Island", "Village"]
                ],
            },
            "Holidays & Celebrations": {
                "row_titles": ["Winter Holidays", "Spring Holidays", "Summer Holidays", "Fall Holidays", "Festivals", "Miscellaneous"],
                "rows": [
                    ["Christmas", "New Year", "Hanukkah", "Kwanzaa", "Diwali", "Eid"],
                    ["Easter", "Passover", "Purim", "Ramadan", "Earth Day", "Lent"],
                    ["Independence Day", "Father's Day", "Mother's Day", "Labor Day", "Bastille", "Memorial Day"],
                    ["Halloween", "Thanksgiving", "Harvest", "Veterans", "Oktoberfest", "Columbus"],
                    ["Birthday", "Anniversary", "Graduation", "Parade", "Concert", "Party"],
                    ["Fair", "Circus", "Show", "Fireworks", "Festival", "Wedding"]
                ],
            },
            "Shopping & Money": {
                "row_titles": ["General Shopping", "Groceries", "Clothing", "Electronics", "Furniture", "Other"],
                "rows": [
                    ["Mall", "Store", "Shop", "Cart", "Bag", "Checkout"],
                    ["Bread", "Eggs", "Milk", "Cheese", "Fruit", "Vegetables"],
                    ["Shoes", "Shirt", "Pants", "Jacket", "Hat", "Scarf"],
                    ["Phone", "Tablet", "TV", "Camera", "Laptop", "Speaker"],
                    ["Desk", "Chair", "Table", "Bed", "Cabinet", "Couch"],
                    ["Cash", "Card", "Coupon", "Receipt", "Sale", "Barcode"]
                ],
            },
            "Technology & Media": {
                "row_titles": ["Devices", "Components", "Networks", "Software", "Accessories", "Other"],
                "rows": [
                    ["Phone", "Tablet", "Monitor", "Camera", "Laptop", "Desktop"],
                    ["CPU", "GPU", "RAM", "SSD", "Battery", "Charger"],
                    ["WiFi", "Router", "Server", "Cloud", "Ethernet", "Bluetooth"],
                    ["App", "Browser", "Game", "Tool", "Website", "Editor"],
                    ["Keyboard", "Mouse", "Speaker", "Dock", "Microphone", "Cable"],
                    ["Music", "Video", "Photo", "Podcast", "Stream", "Playlist"]
                ],
            },

            "Verbs & Actions": {
                "row_titles": ["General Actions", "Movement", "Speech", "Work", "Play", "Emotion"],
                "rows": [
                    ["Begin", "Create", "Discover", "Solve", "Try", "Achieve"],
                    ["Leap", "Crawl", "Slide", "Spin", "Kick", "Glide"],
                    ["Debate", "Narrate", "Declare", "Repeat", "Mutter", "Exclaim"],
                    ["Analyze", "Assemble", "Calculate", "Design", "Program", "Draft"],
                    ["Sketch", "Build", "Explore", "Invent", "Roleplay", "Compete"],
                    ["Admire", "Forgive", "Comfort", "Encourage", "Ponder", "Wonder"]
                ],
            },
            "Household": {
                "row_titles": ["Rooms", "Appliances", "Furniture", "Cleaning Supplies", "Decorations", "Miscellaneous"],
                "rows": [
                    ["Pantry", "Attic", "Basement", "Closet", "Hallway", "Balcony"],
                    ["Stove", "Blender", "Freezer", "Kettle", "Toaster", "Air Fryer"],
                    ["Armchair", "Stool", "Bookshelf", "Hammock", "Crib", "Bench"],
                    ["Dustpan", "Cleaning Cloth", "Brush", "Squeegee", "Cleaner", "Disinfectant"],
                    ["Candle", "Photo Frame", "Plant Pot", "Wall Art", "Clock", "Shelf"],
                    ["Ladder", "Toolbox", "Remote", "Thermostat", "Power Strip", "Doorbell"]
                ],
            },
            "Sports & Activities": {
                "row_titles": ["Team Sports", "Individual Sports", "Outdoor Activities", "Indoor Activities", "Water Sports", "Other Activities"],
                "rows": [
                    ["Cricket", "Rugby", "Softball", "Lacrosse", "Field Hockey", "Ultimate Frisbee"],
                    ["Badminton", "Fencing", "Judo", "Taekwondo", "Track", "Figure Skating"],
                    ["Rock Climbing", "Orienteering", "Geocaching", "Trail Running", "Stargazing", "Birdwatching"],
                    ["Pool", "Table Tennis", "Foosball", "Martial Arts", "Pottery", "Baking"],
                    ["Snorkeling", "Kayaking", "Canoeing", "Scuba Diving", "Water Skiing", "Wakeboarding"],
                    ["Snowshoeing", "Ice Skating", "Surfing", "Parkour", "Curling", "Zumba"]
                ],
            },
            "Hobbies & Interests": {
                "row_titles": ["Arts & Crafts", "Music", "Gardening", "Collecting", "Technology", "Games"],
                "rows": [
                    ["Origami", "Calligraphy", "Weaving", "Woodworking", "Embroidery", "Quilting"],
                    ["Harmonica", "Bass", "Keyboard", "Flute", "Saxophone", "Viola"],
                    ["Herbs", "Vegetables", "Flowers", "Fruit Trees", "Succulents", "Vines"],
                    ["Vintage Items", "Toys", "Rocks", "Artifacts", "Memorabilia", "Postcards"],
                    ["Drones", "VR", "AI Projects", "Home Automation", "Coding Challenges", "Data Visualization"],
                    ["RPGs", "Simulations", "Mystery Games", "Party Games", "Escape Rooms", "Word Games"]
                ],
            },
            "Jobs & Professions": {
                "row_titles": ["Medical", "Education", "Technology", "Trades", "Creative", "Service"],
                "rows": [
                    ["Optometrist", "Radiologist", "Pharmacist", "Veterinarian", "Orthodontist", "Midwife"],
                    ["Dean", "Substitute", "Assistant", "Researcher", "Specialist", "Trainer"],
                    ["Architect", "Developer", "SysAdmin", "Data Scientist", "Cryptographer", "AI Engineer"],
                    ["Plasterer", "Bricklayer", "Blacksmith", "Landscaper", "Plumber", "Roofer"],
                    ["Cartoonist", "Animator", "Set Designer", "Screenwriter", "Composer", "Lyricist"],
                    ["Barber", "Butcher", "Tailor", "Receptionist", "Courier", "Waitstaff"]
                ],
            },

            "Simpsons/Futurama": {
                "row_titles": ["Main Characters", "Supporting Characters", "Antagonists", "Secondary Characters", "Iconic Items/Places", "Miscellaneous"],
                "rows": [
                    ["Homer", "Marge", "Bart", "Lisa", "Maggie", "Milhouse"],  # Main Characters
                    ["Bender", "Fry", "Leela", "Zoidberg", "Professor", "Amy"],  # Supporting Characters
                    ["Mr. Burns", "Smithers", "Moe", "Barney", "Lenny", "Carl"],  # Antagonists
                    ["Krusty", "Apu", "Comic Book Guy", "Ralph", "Nelson", "Skinner"],  # Secondary Characters
                    ["Robot Devil", "Hermes", "Scruffy", "Kif", "Zapp", "Mom"],  # Iconic Items/Places
                    ["Itchy", "Scratchy", "Futurama Ship", "Nibbler", "Hypnotoad", "Slurm"],  # Miscellaneous
                ]
            },

            "Family Guy/American Dad": {
                "row_titles": ["Main Characters", "Supporting Characters", "Antagonists", "Secondary Characters", "Iconic Items/Places", "Miscellaneous"],
                "rows": [
                    ["Peter", "Lois", "Stewie", "Brian", "Chris", "Meg"],  # Main Characters
                    ["Quagmire", "Cleveland", "Joe", "Mort", "Dr. Hartman", "Herbert"],  # Supporting Characters
                    ["Stan", "Francine", "Steve", "Roger", "Hayley", "Klaus"],  # Antagonists
                    ["Chris", "Principal Shepherd", "Neil", "Consuela", "Seamus", "Tricia"],  # Secondary Characters
                    ["The Chicken", "Death", "Angela", "Bruce", "Jillian", "Tom Tucker"],  # Iconic Items/Places
                    ["Ricky Spanish", "Bullock", "Greg", "Terry", "Barry", "Snot"],  # Miscellaneous
                ]
            },
            "South Park": {
                "row_titles": ["Main Characters", "Supporting Characters", "Antagonists", "Secondary Characters", "Iconic Items/Places", "Miscellaneous"],
                "rows": [
                    ["Cartman", "Stan", "Kyle", "Kenny", "Butters", "Wendy"],  # Main Characters
                    ["Randy", "Sharon", "Shelly", "Mr. Garrison", "Mr. Mackey", "Chef"],  # Supporting Characters
                    ["Token", "Jimmy", "Timmy", "Craig", "Tweek", "Clyde"],  # Antagonists
                    ["Terrance", "Phillip", "PC Principal", "Satan", "Mr. Hankey", "Big Gay Al"],  # Secondary Characters
                    ["Mayor", "Dr. Mephesto", "Principal Victoria", "Lemmiwinks", "Ike", "Pip"],  # Iconic Items/Places
                    ["ManBearPig", "Cartman's Mom", "Starvin' Marvin", "Ms. Choksondik", "Nathan", "Scott Tenorman"],  # Miscellaneous
                ]
            },
            "Dragon Ball Universe": {
                "row_titles": ["Main Characters", "Supporting Characters", "Antagonists", "Secondary Characters", "Iconic Items/Places", "Miscellaneous"],
                "rows": [
                    ["Goku", "Vegeta", "Piccolo", "Krillin", "Bulma", "Trunks"],  # Main Characters
                    ["Frieza", "Cell", "Majin Buu", "Gohan", "Chi-Chi", "Yamcha"],  # Supporting Characters
                    ["Tien", "Chiaotzu", "Android 18", "Android 17", "Master Roshi", "Videl"],  # Antagonists
                    ["Beerus", "Whis", "Jiren", "Zeno", "Raditz", "Nappa"],  # Secondary Characters
                    ["Goten", "Bardock", "Kame House", "Korin", "Kami", "Dende"],  # Iconic Items/Places
                    ["Dragon Balls", "Nimbus", "Fusion", "Spirit Bomb", "Ultra Instinct", "Saiyan"],  # Miscellaneous
                ]
            },
            "Drake & Josh/iCarly/Victorious": {
                "row_titles": ["Main Characters", "Supporting Characters", "Antagonists", "Secondary Characters", "Iconic Items/Places", "Miscellaneous"],
                "rows": [
                    ["Drake", "Josh", "Megan", "Walter", "Audrey", "Crazy Steve"],  # Main Characters
                    ["Carly", "Sam", "Freddie", "Spencer", "Gibby", "Nevel"],  # Supporting Characters
                    ["Tori", "Andre", "Jade", "Beck", "Cat", "Robbie"],  # Antagonists
                    ["Helen", "Mrs. Benson", "Trina", "Sinjin", "Lane", "Socko"],  # Secondary Characters
                    ["Peck", "Shampoo Hat", "Movie Theater", "iCarly Show", "Pear Phone", "Smoothie"],  # Iconic Items/Places
                    ["Hollywood Arts", "Spaghetti Tacos", "Puppets", "Spencer's Sculptures", "Mood App", "Groovy Smoothie"],  # Miscellaneous
                ]
            },
            "Rugrats/Spongebob": {
                "row_titles": ["Main Characters", "Supporting Characters", "Antagonists", "Secondary Characters", "Iconic Items/Places", "Miscellaneous"],
                "rows": [
                    ["Tommy", "Chuckie", "Phil", "Lil", "Angelica", "Dil"],  # Main Characters
                    ["Stu", "Didi", "Grandpa", "Spike", "Susie", "Kimi"],  # Supporting Characters
                    ["Spongebob", "Patrick", "Squidward", "Mr. Krabs", "Sandy", "Plankton"],  # Antagonists
                    ["Gary", "Karen", "Bubble Buddy", "Mermaid Man", "Barnacle Boy", "Flying Dutchman"],  # Secondary Characters
                    ["Jellyfish", "Krusty Krab", "Chum Bucket", "Goofy Goober", "Pineapple", "Lagoon"],  # Iconic Items/Places
                    ["Reptar", "Pickles", "Angelica's Doll", "Rugrats Adventures", "Tide Pool", "Bikini Bottom"],  # Miscellaneous
                ]
            }
        }

if __name__ == "__main__":
    app = KeyboardFrameApp()
    app.mainloop()
