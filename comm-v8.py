import tkinter as tk
from pyttsx3 import init
import threading
import time
import subprocess
import platform
import pyautogui
import ctypes  # For Windows-specific focus handling
from pynput import keyboard
import win32gui
import win32process
import win32con
import queue
import json
import os
import logging
import requests

# Function to bring the application to the foreground and monitor focus
def bring_to_foreground_with_monitoring():
    """Minimize when Chrome is running and restore focus when Chrome closes."""
    hwnd = win32gui.FindWindow(None, "Accessible Menu")  # Replace with the exact title
    if not hwnd:
        print("Application window not found.")
        return

    app_minimized = False  # Track the app's state

    while True:
        try:
            if is_chrome_running():
                if not app_minimized:  # Only minimize if not already minimized
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    print("Chrome detected. Application minimized.")
                    app_minimized = True
            else:
                if app_minimized:  # Restore the app if previously minimized
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    time.sleep(0.1)  # Small delay to allow window state update
                    win32gui.SetForegroundWindow(hwnd)
                    print("Chrome closed. Application restored to focus.")
                    app_minimized = False

        except Exception as e:
            print(f"Error in bring_to_foreground_with_monitoring: {e}")
        
        time.sleep(1)  # Adjust monitoring frequency

def monitor_app_focus(app_title="Accessible Menu"):
    """Continuously monitor Chrome's state and ensure the application is maximized and focused."""
    while True:
        try:
            # Check if Chrome is running
            if not is_chrome_running():
                print("Chrome is not running. Ensuring application is maximized and in focus.")
                
                hwnd = win32gui.FindWindow(None, app_title)
                if hwnd:
                    # Restore and maximize the application window
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # Ensure it's not minimized
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)  # Maximize the window
                    win32gui.SetForegroundWindow(hwnd)  # Bring it to the foreground
                    print("Application is maximized and in focus.")
                else:
                    print(f"Application window with title '{app_title}' not found.")
            else:
                print("Chrome is running. Application can remain minimized or in the background.")
        except Exception as e:
            print(f"Error in monitor_app_focus: {e}")
        
        time.sleep(2)  # Adjust the monitoring frequency as needed

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to minimize the terminal window
def minimize_terminal():
    if platform.system() == "Windows":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                print("Terminal minimized.")
        except Exception as e:
            print(f"Error minimizing terminal: {e}")

# Function to minimize the app when Chrome is open
def monitor_and_minimize(app):
    """Continuously monitor for Chrome activity and minimize the Tkinter app if restored."""
    while True:
        try:
            active_window, _ = get_active_window_name()

            # Check if Chrome is the active window
            if "Chrome" in active_window or "Google Chrome" in active_window:
                print("Chrome detected. Minimizing the app.")
                app.iconify()  # Minimize the Tkinter window

            # Check if the app is restored and Chrome is still open
            if app.state() == "normal" and ("Chrome" in active_window or "Google Chrome" in active_window):
                print("App restored while Chrome is open. Minimizing again.")
                app.iconify()

        except Exception as e:
            print(f"Error in monitor_and_minimize: {e}")
        time.sleep(1)  # Adjust frequency of checks if needed

import psutil

def is_chrome_running():
    """Check if any Chrome process is running."""
    for process in psutil.process_iter(['name']):
        if process.info['name'] and 'chrome' in process.info['name'].lower():
            return True
    return False

def monitor_and_minimize(app):
    """Continuously monitor for Chrome activity and minimize the Tkinter app."""
    while True:
        try:
            if is_chrome_running():
                print("Chrome detected. Minimizing the app.")
                minimize_with_win32("Accessible Menu")
            else:
                print("Chrome not running.")
        except Exception as e:
            print(f"Error in monitor_and_minimize: {e}")
        time.sleep(1)  # Adjust the frequency of checks
        
# Function to minimize the on-screen keyboard
def minimize_on_screen_keyboard():
    """Minimizes the on-screen keyboard if it's active."""
    try:
        retries = 5
        for attempt in range(retries):
            hwnd = win32gui.FindWindow("IPTip_Main_Window", None)  # Verify this class name
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                print(f"On-screen keyboard minimized on attempt {attempt + 1}.")
                return
            time.sleep(1)  # Wait before retrying
        print("On-screen keyboard not found after retries.")
    except Exception as e:
        print(f"Error minimizing on-screen keyboard: {e}")

# Function to Monitor and Close Start Menu
def send_esc_key():
    """Send the ESC key to close the Start Menu."""
    ctypes.windll.user32.keybd_event(0x1B, 0, 0, 0)  # ESC key down
    ctypes.windll.user32.keybd_event(0x1B, 0, 2, 0)  # ESC key up
    print("ESC key sent to close Start Menu.")

def is_start_menu_open():
    """Check if the Start Menu is currently open and focused."""
    hwnd = win32gui.GetForegroundWindow()  # Get the handle of the active (focused) window
    class_name = win32gui.GetClassName(hwnd)  # Get the class name of the active window
    return class_name in ["Shell_TrayWnd", "Windows.UI.Core.CoreWindow"]

def monitor_start_menu():
    """Continuously check and close the Start Menu if it is open."""
    while True:
        try:
            # Check if the Start Menu is active
            if is_start_menu_open():
                print("Start Menu detected. Closing it now.")
                send_esc_key()
            else:
                hwnd = win32gui.GetForegroundWindow()
                active_window_title = win32gui.GetWindowText(hwnd)
                print(f"Active window: {active_window_title} (Start Menu not active).")
        except Exception as e:
            print(f"Error in monitor_start_menu: {e}")
        
        time.sleep(0.5)  # Adjust frequency as needed

# List all available window titles for debugging
def log_window_titles():
    def callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            results.append(win32gui.GetWindowText(hwnd))
    windows = []
    win32gui.EnumWindows(callback, windows)
    print("Available window titles:")
    for title in windows:
        print(f"Window title: {title}")
        
def log_active_window_title():
    while True:
        try:
            active_window, _ = get_active_window_name()
            print(f"Active window: {active_window}")
        except Exception as e:
            print(f"Error logging window title: {e}")
        time.sleep(1)        

# Initialize Text-to-Speech
engine = init()
speak_queue = queue.Queue()

def speak(text):
    if speak_queue.qsize() >= 1:
        with speak_queue.mutex:
            speak_queue.queue.clear()
    speak_queue.put(text)

def play_speak_queue():
    while True:
        text = speak_queue.get()
        if text is None:
            speak_queue.task_done()
            break
        engine.say(text)
        engine.runAndWait()
        speak_queue.task_done()

speak_thread = threading.Thread(target=play_speak_queue, daemon=True)
speak_thread.start()

# Function to get the active window title
def get_active_window_name():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    name = win32gui.GetWindowText(hwnd)
    return name, pid

# Utility Functions
def minimize_with_win32(app_title="Accessible Menu"):
    hwnd = win32gui.FindWindow(None, app_title)
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        print("Forced minimization with win32.")
    else:
        print("App window not found for minimization.")

# Function to close Chrome using Alt+F4
def close_chrome_cleanly():
    """Close Chrome browser cleanly using Alt+F4."""
    try:
        name, _ = get_active_window_name()
        if "Chrome" in name:
            print("Chrome is active. Closing it.")
            pyautogui.hotkey("alt", "f4")  # Close Chrome window
        else:
            print("Chrome is not the active window.")
    except Exception as e:
        print(f"Error closing Chrome: {e}")

# Function to bring the application back into focus
def bring_application_to_focus():
    try:
        app_hwnd = win32gui.FindWindow(None, "Accessible Menu")  # Replace with your window title
        if app_hwnd:
            win32gui.ShowWindow(app_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(app_hwnd)
            print("Application brought to focus.")
        else:
            print("No GUI window found.")
    except Exception as e:
        print(f"Error focusing application: {e}")

LAST_WATCHED_FILE = "last_watched.json"

def load_last_watched():
    if os.path.exists(LAST_WATCHED_FILE):
        with open(LAST_WATCHED_FILE, "r") as file:
            return json.load(file)
    return {}

def save_last_watched(data):
    with open(LAST_WATCHED_FILE, "w") as file:
        json.dump(data, file)
        
class KeySequenceListener:
    def __init__(self, app):
        self.app = app
        self.sequence = ["enter", "enter", "enter"]  # Define the key sequence
        self.current_index = 0
        self.last_key_time = None
        self.timeout = 8 # Timeout for completing the sequence (seconds)
        self.held_keys = set()  # Track keys that are currently held
        self.recently_pressed = set()  # To debounce key presses
        self.start_listener()

    def start_listener(self):
        def on_press(key):
            try:
                key_name = (
                    key.char.lower() if hasattr(key, 'char') and key.char else str(key).split('.')[-1].lower()
                )
                if key_name in self.recently_pressed:  # Ignore key if already recently pressed
                    return

                self.recently_pressed.add(key_name)
                self.check_key(key_name)
            except AttributeError:
                pass

        def on_release(key):
            try:
                key_name = (
                    key.char.lower() if hasattr(key, 'char') and key.char else str(key).split('.')[-1].lower()
                )
                self.recently_pressed.discard(key_name)  # Allow key to be pressed again
            except AttributeError:
                pass

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()

    def check_key(self, key_name):
        # Handle timeout for the sequence
        if self.last_key_time and time.time() - self.last_key_time > self.timeout:
            print("Sequence timeout. Resetting index.")
            self.current_index = 0  # Reset sequence on timeout

        self.last_key_time = time.time()

        # Check the current key against the sequence
        if key_name == self.sequence[self.current_index]:
            print(f"Matched {key_name} at index {self.current_index}")
            self.current_index += 1  # Move to the next key in the sequence
            if self.current_index == len(self.sequence):  # Full sequence detected
                self.handle_sequence()
                self.current_index = 0  # Reset sequence index
        else:
            print(f"Key mismatch or invalid input. Resetting sequence.")
            self.current_index = 0  # Reset on invalid input

    def handle_sequence(self):
        print("Key sequence detected. Closing Chrome and focusing application.")
        threading.Thread(target=self.perform_actions, daemon=True).start()

    def perform_actions(self):
        close_chrome_cleanly()

        # Introduce a delay before resuming scanning/selecting
        print("Adding delay before resuming scanning/selecting...")
        time.sleep(2)  # Delay in seconds; adjust as needed

        bring_application_to_focus()
        
# Minimize the terminal window
def minimize_terminal():
    if platform.system() == "Windows":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_MINIMIZE)  # Ensure the console is minimized
        except Exception as e:
            print(f"Error minimizing terminal on Windows: {e}")
            
  # Minimize the on-screen keyboard
def minimize_on_screen_keyboard():
    """Minimizes the on-screen keyboard if it's active."""
    try:
        retries = 5
        for attempt in range(retries):
            hwnd = win32gui.FindWindow("IPTip_Main_Window", None)  # Verify this class name
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                print(f"On-screen keyboard minimized on attempt {attempt + 1}.")
                return
            time.sleep(1)  # Wait before retrying
        print("On-screen keyboard not found after retries.")
    except Exception as e:
        print(f"Error minimizing on-screen keyboard: {e}")
    

import ctypes
import pyautogui
from pynput.keyboard import Controller

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Accessible Menu")
        self.geometry("960x540")  # Default, will adjust to screen size
        self.attributes("-fullscreen", True)
        self.configure(bg="black")
        self.current_frame = None
        self.buttons = []  # Holds buttons for scanning
        self.current_button_index = 0  # Current scanning index
        self.selection_enabled = True  # Flag to manage debounce for selection
        self.keyboard = Controller()  # Initialize the keyboard controller

        self.spacebar_pressed = False
        self.long_spacebar_pressed = False
        self.start_time = 0
        self.backward_time_delay = 2  # Delay in seconds when long holding space

        # Add Close and Minimize buttons
        self.create_window_controls()

        # Minimize terminal and keyboard
        minimize_terminal()
        minimize_on_screen_keyboard()
        
        # Start monitoring for Chrome in a separate thread
        threading.Thread(target=monitor_and_minimize, args=(self,), daemon=True).start()

        # Start monitoring for Chrome's state and application focus
        threading.Thread(target=monitor_app_focus, args=("Accessible Menu",), daemon=True).start()

        # Start monitoring the Start Menu
        threading.Thread(target=monitor_start_menu, daemon=True).start()

        # Start focus monitoring
        threading.Thread(target=self.simulate_direct_click_to_focus, daemon=True).start()

        # Delay key bindings to ensure focus
        threading.Timer(5, self.bind_keys_for_scanning).start()

        # Initialize the main menu
        print("Initializing the main menu...")
        self.show_frame(MainMenuPage)

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

    def simulate_direct_click_to_focus(self):
        """Simulates a click on the main menu title to bring the application into focus."""
        # (Existing method logic)
        pass

    def bind_keys_for_scanning(self):
        """Bind keyboard inputs for scanning."""
        # (Existing method logic)
        pass

    def show_frame(self, frame_class):
        """Show a specific frame."""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame_class(self)
        self.current_frame.pack(expand=True, fill="both")
        self.buttons = self.current_frame.buttons  # Update scanning buttons
        self.current_button_index = 0  # Reset scanning index      

    def simulate_direct_click_to_focus(self):
        """Simulates a click on the main menu title to bring the application into focus."""
        time.sleep(2)  # Allow system to stabilize
        try:
            # Find the location of the main menu title widget
            menu_title = self.nametowidget(".!mainmenupage.!label") # Assuming the title label widget is named "!label"
            x, y, width, height = menu_title.winfo_rootx(), menu_title.winfo_rooty(), menu_title.winfo_width(), menu_title.winfo_height()
            click_x = x + width // 2
            click_y = y + height // 2

            print(f"Simulating direct click at ({click_x}, {click_y}) on the main menu title.")

            # Move the mouse to the desired location
            ctypes.windll.user32.SetCursorPos(int(click_x), int(click_y))

            # Simulate a mouse click
            ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)  # Mouse left button down
            ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)  # Mouse left button up

        except Exception as e:
            print(f"Error simulating click on the main menu title: {e}")

    def bind_keys_for_scanning(self):
        self.bind("<KeyPress-space>", self.track_spacebar_hold)
        self.bind("<KeyRelease-space>", self.reset_spacebar_hold)
        self.bind("<KeyRelease-Return>", self.select_button)
        print("Key bindings activated.")

    def track_spacebar_hold(self, event):
        if not self.spacebar_pressed and not self.long_spacebar_pressed:
            self.spacebar_pressed = True
            self.start_time = time.time()

    def reset_spacebar_hold(self, event):
        if self.spacebar_pressed:
            self.spacebar_pressed = False
            if not self.long_spacebar_pressed:
                self.scan_forward()
            else:
                self.long_spacebar_pressed = False

    def show_frame(self, frame_class):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame_class(self)
        self.current_frame.pack(expand=True, fill="both")
        self.buttons = self.current_frame.buttons  # Update scanning buttons
        self.current_button_index = 0  # Reset scanning index

    def bind_keys_for_scanning(self):
        self.bind("<KeyPress-space>", self.track_spacebar_hold)
        self.bind("<KeyRelease-space>", self.reset_spacebar_hold)
        self.bind("<KeyRelease-Return>", self.select_button)
        print("Key bindings activated.")

        # Ensure the app is in focus
        print("Initializing the main menu...")
        self.show_frame(MainMenuPage)

        # Start key sequence listener
        self.sequencer = KeySequenceListener(self)

        # Start spacebar hold tracking in a separate thread
        threading.Thread(target=self.monitor_spacebar_hold, daemon=True).start()

    def monitor_spacebar_hold(self):
        while True:
            if self.spacebar_pressed and (time.time() - self.start_time >= 3.5):
                self.long_spacebar_pressed = True
                self.scan_backward()
                time.sleep(self.backward_time_delay)

    def track_spacebar_hold(self, event):
        if not self.spacebar_pressed and not self.long_spacebar_pressed:
            self.spacebar_pressed = True
            self.start_time = time.time()

    def reset_spacebar_hold(self, event):
        if self.spacebar_pressed:
            self.spacebar_pressed = False
            if not self.long_spacebar_pressed:
                self.scan_forward()
            else:
                self.long_spacebar_pressed = False
                self.start_time = time.time()

    def show_frame(self, frame_class):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame_class(self)
        self.current_frame.pack(expand=True, fill="both")
        self.buttons = self.current_frame.buttons  # Update scanning buttons
        self.current_button_index = 0  # Reset scanning index
        if self.buttons:
            self.highlight_button(0)

    import threading

    def scan_forward(self, event=None):
        """Advance to the next button and highlight it upon spacebar release."""
        if self.selection_enabled and self.buttons:
            # Disable selection temporarily to add delay
            self.selection_enabled = False

            self.current_button_index = (self.current_button_index + 1) % len(self.buttons)
            self.highlight_button(self.current_button_index)

            # Speak the button's text if the frame matches
            if isinstance(self.current_frame, (
                MainMenuPage, CommunicationPageMenu, StreamingShowsPageMenu, AnimePageMenu,
                CartoonsPageMenu, ComedyPageMenu, NickelodeonPageMenu, MoviesPageMenu,
                FantasyPageMenu, StarWarsPageMenu, SpiderManPageMenu, SettingsMenuPage,
                EntertainmentMenuPage, LiveStreamingPageMenu
            )):
                speak(self.buttons[self.current_button_index]["text"])

            # Re-enable selection after a delay
            threading.Timer(0.5, self.enable_selection).start()  # Adjust delay as needed


    def scan_backward(self):
        """Move to the previous button and highlight it."""
        if self.selection_enabled and self.buttons:
            # Disable selection temporarily to add delay
            self.selection_enabled = False

            self.current_button_index = len(self.buttons) - 1 if (self.current_button_index - 1) < 0 else (self.current_button_index - 1)
            self.highlight_button(self.current_button_index)

            # Speak the button's text if the frame matches
            if isinstance(self.current_frame, (
                MainMenuPage, CommunicationPageMenu, StreamingShowsPageMenu, AnimePageMenu,
                CartoonsPageMenu, ComedyPageMenu, NickelodeonPageMenu, MoviesPageMenu,
                FantasyPageMenu, StarWarsPageMenu, SpiderManPageMenu, SettingsMenuPage,
                EntertainmentMenuPage, LiveStreamingPageMenu
            )):
                speak(self.buttons[self.current_button_index]["text"])

            # Re-enable selection after a delay
            threading.Timer(0.5, self.enable_selection).start()  # Adjust delay as needed


    def enable_selection(self):
        """Re-enable scanning and selection after the delay."""
        self.selection_enabled = True


    def select_button(self, event=None):
        """Select the currently highlighted button upon Enter key release with debounce and delay."""
        if self.selection_enabled and self.buttons:
            self.selection_enabled = False  # Disable selection temporarily
            self.buttons[self.current_button_index].invoke()  # Invoke the button action

            # Add delay for both scanning and selection after Enter key
            threading.Timer(5, self.enable_selection).start()  # Re-enable selection after 2 seconds

            self.sequencer.current_index = 0
            self.sequencer.last_key_time = None

    def enable_selection(self):
        """Re-enable scanning and selection after the delay."""
        self.selection_enabled = True

    def highlight_button(self, index):
        for i in range(len(self.buttons)):
            if i == index:
                self.buttons[i].config(bg="yellow", fg="black")
            else:
                self.buttons[i].config(bg="light blue", fg="black")
        self.update()
        
# Base Frame for Menu Pages
class MenuFrame(tk.Frame):
    active_show = None  # Class-level variable to track the active show

    def __init__(self, parent, title):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.title = title
        self.buttons = []  # Store buttons for scanning
        self.create_title()

    def create_title(self):
        label = tk.Label(self, text=self.title, font=("Arial", 36), bg="black", fg="white")
        label.pack(pady=20)

    def create_button_grid(self, buttons):
        grid_frame = tk.Frame(self, bg="black")
        grid_frame.pack(expand=True, fill="both")

        rows = 3
        cols = 3
        for i, (text, command, speak_text) in enumerate(buttons):
            row, col = divmod(i, cols)
            btn = tk.Button(
                grid_frame,
                text=text,
                font=("Arial Black", 36),  # Increase font size
                bg="light blue",
                fg="black",
                activebackground="yellow",
                activeforeground="black",
                command=lambda c=command, s=speak_text: self.on_select(c, s),
                wraplength=700  # Set wrap length in pixels
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            self.buttons.append(btn)

        for i in range(rows):
            grid_frame.rowconfigure(i, weight=1)
        for j in range(cols):
            grid_frame.columnconfigure(j, weight=1)

    def on_select(self, command, speak_text):
        command()
        if speak_text:
            speak(speak_text)

    def open_in_chrome(self, show_name, default_url):
        """Open a URL in Chrome with remote debugging enabled."""
        last_watched = load_last_watched()
        url_to_open = last_watched.get(show_name, default_url)

        try:
            subprocess.run(
                ["start", "chrome", "--remote-debugging-port=9222", "--start-fullscreen", url_to_open],
                shell=True
            )
            print(f"Opened URL for {show_name}: {url_to_open}")
        except Exception as e:
            print(f"Error opening URL: {e}")
            return

        # Stop the previous tracking thread
        MenuFrame.active_show = None  # Reset the active show to stop the old thread
        time.sleep(1)  # Small delay to ensure previous thread exits

        # Start a new tracking thread for the current show
        MenuFrame.active_show = show_name
        threading.Thread(target=self.save_current_url, args=(show_name, default_url), daemon=True).start()


    import requests

    def get_active_chrome_url(self):
        """Retrieve the active URL from Chrome using the DevTools Protocol."""
        try:
            response = requests.get("http://localhost:9222/json")
            tabs = response.json()

            for tab in tabs:
                if tab.get("type") == "page" and tab.get("url") and tab.get("url").startswith("http"):
                    return tab["url"]  # Return the active or first valid tab's URL

            logging.error("No valid active Chrome tab found.")
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Failed to connect to Chrome DevTools: {e}")
            return None
        except Exception as e:
            logging.error(f"Error retrieving Chrome URL: {e}")
            return None

    def save_current_url(self, show_name, expected_url):
        """Periodically save the currently active Chrome URL for the active show."""
        print(f"Started tracking URL for: {show_name}")

        # Extract the base URL (everything up to the domain and path)
        base_url = "/".join(expected_url.split("/")[:4])

        while MenuFrame.active_show == show_name:  # Only save if this is the active show
            time.sleep(5)  # Check every 5 seconds

            # Fetch the current URL from Chrome
            current_url = self.get_active_chrome_url()
            print(f"Current URL fetched: {current_url}")

            # Match the base URL instead of the exact URL
            if current_url and current_url.startswith(base_url):
                last_watched = load_last_watched()
                last_watched[show_name] = current_url  # Save the dynamically updated URL
                save_last_watched(last_watched)
                print(f"Updated URL for {show_name}: {current_url}")
            else:
                print(f"No matching URL found for {show_name}. Current URL: {current_url}")

            # Stop periodic updates if Chrome is no longer running
            if not self.is_chrome_running():
                print(f"Chrome is no longer running. Stopping updates for {show_name}.")
                break

        print(f"Stopped tracking URL for: {show_name}")


    def is_chrome_running(self):
        """Check if Chrome is still running."""
        import psutil
        for process in psutil.process_iter(['name']):
            if process.info['name'] and 'chrome' in process.info['name'].lower():
                return True
        return False
    
    def open_and_click(self, show_name, default_url, x_offset=0, y_offset=0):
        """Open the given URL, click on the specified position, and ensure fullscreen mode."""
        # Use the same logic as open_in_chrome to open the URL
        self.open_in_chrome(show_name, default_url)
        time.sleep(5)  # Wait for the browser to open and load

        # Bring the browser window to the foreground
        hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        print("Brought Chrome to the foreground.")

        # Calculate click position with offsets
        screen_width, screen_height = pyautogui.size()
        click_x = (screen_width // 2) + x_offset
        click_y = (screen_height // 2) + y_offset

        # Perform the click
        pyautogui.click(click_x, click_y)
        print(f"Clicked at position: ({click_x}, {click_y})")

        # Allow time for interaction
        time.sleep(2)

    import keyboard

    def open_pluto(self, show_name, default_url):
        """Open Pluto TV link in Chrome, ensure focus, unmute, and fullscreen."""
        # Open the URL in Chrome
        self.open_in_chrome(show_name, default_url)
        time.sleep(7)  # Increase wait time for page and video player to load

        # Bring Chrome to the foreground
        hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        print("Brought Chrome to the foreground.")

        # Wait for the video player to load
        time.sleep(6)

        # Simulate 'm' keypress to unmute
        print("Sending 'm' keypress to unmute the video...")
        self.keyboard.press('m')
        time.sleep(0.1)
        self.keyboard.release('m')

        # Wait briefly before fullscreening
        time.sleep(2)

        # Simulate 'f' keypress to fullscreen
        print("Sending 'f' keypress to fullscreen the video...")
        self.keyboard.press('f')
        time.sleep(0.1)
        self.keyboard.release('f')

        print("Pluto.TV interaction complete.")
        
# Define Menu Classes
class MainMenuPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Main Menu")
        self.buttons = []  # Store buttons for scanning
        self.current_button_index = 0  # Initialize scanning index
        self.selection_enabled = True  # Flag to manage debounce for selection

        # Create the grid layout for 4 large buttons
        grid_frame = tk.Frame(self, bg="black")
        grid_frame.pack(expand=True, fill="both")

        # Define buttons with their commands and labels
        buttons = [
            ("Emergency", self.emergency_alert, "Emergency Alert"),
            ("Settings", lambda: parent.show_frame(SettingsMenuPage), "Settings Menu"),
            ("Communication", lambda: parent.show_frame(CommunicationPageMenu), "Communication Menu"),
            ("Entertainment", lambda: parent.show_frame(EntertainmentMenuPage), "Entertainment Menu"),
        ]

        for i, (text, command, speak_text) in enumerate(buttons):
            row, col = divmod(i, 2)  # Calculate row and column for 2x2 layout
            btn = tk.Button(
                grid_frame,
                text=text,
                font=("Arial Black", 36),
                bg="light blue",
                fg="black",
                activebackground="yellow",
                activeforeground="black",
                command=lambda c=command, s=speak_text: self.on_select(c, s),
                wraplength=850,  # Wrap text for better display
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)  # Adjust padding for spacing
            self.buttons.append(btn)  # Add button to scanning list

        # Configure grid to distribute space equally
        for i in range(2):  # Two rows
            grid_frame.rowconfigure(i, weight=1)
        for j in range(2):  # Two columns
            grid_frame.columnconfigure(j, weight=1)

        # Highlight the first button for scanning
        if self.buttons:
            self.highlight_button(0)

    def scan_forward(self, event=None):
        """Move to the next button and highlight it."""
        if self.selection_enabled and self.buttons:
            self.selection_enabled = False  # Disable selection temporarily to debounce
            self.current_button_index = (self.current_button_index + 1) % len(self.buttons)
            self.highlight_button(self.current_button_index)
            threading.Timer(0.5, self.enable_selection).start()  # Re-enable selection after a delay

    def highlight_button(self, index):
        """Highlight the current button and reset others."""
        for i, button in enumerate(self.buttons):
            if i == index:
                button.config(bg="yellow", fg="black")  # Highlight current button
            else:
                button.config(bg="light blue", fg="black")  # Reset others
        self.update()

    def select_button(self, event=None):
        """Invoke the currently highlighted button."""
        if self.selection_enabled and self.buttons:
            self.selection_enabled = False  # Disable selection temporarily to debounce
            self.buttons[self.current_button_index].invoke()  # Trigger the button's action
            threading.Timer(1, self.enable_selection).start()  # Re-enable selection after a delay

    def enable_selection(self):
        """Re-enable selection after a delay."""
        self.selection_enabled = True

    def on_select(self, command, speak_text):
        """Handle button selection logic."""
        command()
        if speak_text:
            speak(speak_text)

    def emergency_alert(self):
        """Trigger emergency alert."""
        ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)  # Volume up key
        for _ in range(50):  # Max volume
            ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAF, 0, 2, 0)
            time.sleep(0.05)

        def alert_loop():
            end_time = time.time() + 15
            while time.time() < end_time:
                speak("Help, help, help, help, help")
                time.sleep(2)

        threading.Thread(target=alert_loop, daemon=True).start()

import subprocess
import pyautogui
import time
import win32gui
import win32con

class SettingsMenuPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Settings")  # Set the title to "Settings"
        self.buttons = []  # Store buttons for scanning

        # Define buttons with actions and TTS
        buttons = [
            ("Back", lambda: parent.show_frame(MainMenuPage), "Back"),
            ("Volume Up", self.volume_up, "Increase volume"),
            ("Volume Down", self.volume_down, "Decrease volume"),
            ("Sleep Timer (60 min)", self.sleep_timer, "Set a 60-minute sleep timer"),
            ("Cancel Sleep Timer", self.cancel_sleep_timer, "Cancel the sleep timer"),
            ("Turn Display Off", self.turn_off_display, "Turn off the display"),
            ("Lock", self.lock_computer, "Lock the computer"),
            ("Restart", self.restart_computer, "Restart the computer"),
            ("Shut Down", self.shut_down_computer, "Shut down the computer"),         
        ]
        
        # Create button grid and bind keys for scanning/selecting
        self.create_button_grid(buttons, columns=3)  # Set columns to 3
        
    def create_button_grid(self, buttons, columns=5):
        """Creates a grid layout for buttons with a dynamic number of rows and columns."""
        grid_frame = tk.Frame(self, bg="black")
        grid_frame.pack(expand=True, fill="both")

        rows = (len(buttons) + columns - 1) // columns  # Calculate required rows
        for i, (text, command, speak_text) in enumerate(buttons):
            row, col = divmod(i, columns)
            btn = tk.Button(
                grid_frame, text=text, font=("Arial Black", 36), bg="light blue", fg="black",
                activebackground="yellow", activeforeground="black",
                command=lambda c=command, s=speak_text: self.on_select(c, s)
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            self.buttons.append(btn)  # Add button to scanning list

        for i in range(rows):
            grid_frame.rowconfigure(i, weight=1)
        for j in range(columns):
            grid_frame.columnconfigure(j, weight=1)

        self.bind("<KeyPress-space>", self.parent.track_spacebar_hold)
        self.bind("<KeyRelease-space>", self.parent.reset_spacebar_hold)
        self.bind("<KeyRelease-Return>", self.parent.select_button)
        
    def scan_forward(self, event=None):
        """Move to the next button and highlight it."""
        if self.selection_enabled and self.buttons:
            self.selection_enabled = False  # Disable selection temporarily to debounce
            self.current_button_index = (self.current_button_index + 1) % len(self.buttons)
            self.highlight_button(self.current_button_index)
            threading.Timer(0.5, self.enable_selection).start()  # Re-enable selection after a delay

    def highlight_button(self, index):
        """Highlight the current button and reset others."""
        for i, button in enumerate(self.buttons):
            if i == index:
                button.config(bg="yellow", fg="black")  # Highlight current button
            else:
                button.config(bg="light blue", fg="black")  # Reset others
        self.update()

    def select_button(self, event=None):
        """Invoke the currently highlighted button."""
        if self.selection_enabled and self.buttons:
            self.selection_enabled = False  # Disable selection temporarily to debounce
            self.buttons[self.current_button_index].invoke()  # Trigger the button's action
            threading.Timer(1, self.enable_selection).start()  # Re-enable selection after a delay

    def enable_selection(self):
        """Re-enable selection after a delay."""
        self.selection_enabled = True

    def on_select(self, command, speak_text):
        """Handle button selection logic."""
        command()
        if speak_text:
            speak(speak_text)
            
    def volume_up(self):
        """Increase system volume."""
        for _ in range(4):  # Increase volume by ~10%
            ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAF, 0, 2, 0)
            time.sleep(0.05)
        speak("Volume increased")

    def volume_down(self):
        """Decrease system volume."""
        for _ in range(4):  # Decrease volume by ~10%
            ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xAE, 0, 2, 0)
            time.sleep(0.05)
        speak("Volume decreased")
                  
    def turn_off_display(self):
        try:
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x112, 0xF170, 2)  # Turn off display
            speak("Display turned off")
        except Exception as e:
            speak("Failed to turn off display")
            print(f"Turn Off Display Error: {e}")

    def sleep_timer(self):
        """Set a 60-minute sleep timer."""
        try:
            # Set a sleep timer for 3600 seconds (60 minutes)
            subprocess.run("shutdown /s /t 3600", shell=True)
            speak("Sleep timer set for 60 minutes")
        except Exception as e:
            speak("Failed to set sleep timer")
            print(f"Error setting sleep timer: {e}")

    def cancel_sleep_timer(self):
        """Cancel the sleep timer."""
        try:
            # Cancel the shutdown timer
            subprocess.run("shutdown /a", shell=True)
            speak("Sleep timer canceled")
        except Exception as e:
            speak("Failed to cancel sleep timer")
            print(f"Error canceling sleep timer: {e}")

    def lock_computer(self):
        """Lock the computer."""
        ctypes.windll.user32.LockWorkStation()
        speak("Computer locked")

    def restart_computer(self):
        """Restart the computer."""
        subprocess.run("shutdown /r /t 0")
        speak("Restarting computer")
                        
    def shut_down_computer(self):
        """Shut down the computer."""
        subprocess.run("shutdown /s /t 0")
        speak("Shutting down the computer")

class EntertainmentMenuPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Entertainment")
        self.buttons = []  # Store buttons for scanning
        self.current_button_index = 0  # Initialize scanning index
        self.selection_enabled = True  # Flag for debounce during scanning

        # Define buttons with their labels, actions, and TTS text
        buttons = [
            ("Back", lambda: parent.show_frame(MainMenuPage), "Back to Main Menu"),
            ("Streaming Shows", lambda: parent.show_frame(StreamingShowsPageMenu), "Streaming Shows Menu"),
            ("Live Streams", lambda: parent.show_frame(LiveStreamingPageMenu), "Live Streams"), 
            ("Music", self.coming_soon, "Music (coming soon)"),
            ("Audio Books", self.coming_soon, "Audio Books (coming soon)"),
            ("Games", self.coming_soon, "Games (coming soon)"),
        ]
        self.create_button_grid(buttons, columns=2)  # Set columns to 2

    def create_button_grid(self, buttons, columns=5):
        """Creates a grid layout for buttons with a dynamic number of rows and columns."""
        grid_frame = tk.Frame(self, bg="black")
        grid_frame.pack(expand=True, fill="both")

        rows = (len(buttons) + columns - 1) // columns  # Calculate required rows
        for i, (text, command, speak_text) in enumerate(buttons):
            row, col = divmod(i, columns)
            btn = tk.Button(
                grid_frame, text=text, font=("Arial Black", 36), bg="light blue", fg="black",
                activebackground="yellow", activeforeground="black",
                command=lambda c=command, s=speak_text: self.on_select(c, s)
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            self.buttons.append(btn)  # Add button to scanning list

        for i in range(rows):
            grid_frame.rowconfigure(i, weight=1)
        for j in range(columns):
            grid_frame.columnconfigure(j, weight=1)

    def on_select(self, command, speak_text):
        """Handle button selection with scanning."""
        command()
        if speak_text:
            speak(speak_text)

    def coming_soon(self):
        """Notify that this feature is coming soon."""
        speak("This feature is coming soon")

class CommunicationPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Communication")
        buttons = [
            ("Back", lambda: parent.show_frame(MainMenuPage), None),
            ("Basic", lambda: parent.show_frame(BasicPageMenu), "Basic"),
            ("Needs", lambda: parent.show_frame(NeedsPageMenu), "Needs"),
            ("Feelings", lambda: parent.show_frame(FeelingsPageMenu), "Feelings"),
            ("Conversation", lambda: parent.show_frame(ConversationPageMenu), "Conversation"),
            ("Questions", lambda: parent.show_frame(QuestionsPageMenu), "Questions"),
            ("Quotes & Misc", lambda: parent.show_frame(QuotesPageMenu), "Quotes & Misc"),
            ("Rating", lambda: parent.show_frame(RatingPageMenu), "Rating"),
            ("Twitch", lambda: parent.show_frame(TwitchPageMenu), "Twitch"),
        ]
        self.create_button_grid(buttons)

class BasicPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Basic")
        buttons = [
            ("Back", lambda: self.parent.show_frame(CommunicationPageMenu), None),  # Add Back button
            ("Yes", lambda: None, "Yes"),
            ("No", lambda: None, "No"),
            ("Help Please", lambda: None, "Help Please"),
            ("Hello", lambda: None, "Hello"),
            ("Bye", lambda: None, "Goodbye"),
            ("Thank", lambda: None, "Thank you"),
            ("Love", lambda: None, "I love you"),
            ("Break", lambda: None, "I need a break"),
        ]
        self.create_button_grid(buttons)

class NeedsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Needs")
        buttons = [
            ("Back", lambda: self.parent.show_frame(CommunicationPageMenu), None),  # Add Back button
            ("Suction", lambda: None, "I need suction"),
            ("Hot", lambda: None, "I am hot"),
            ("Uncomfortable", lambda: None, "I am Uncomfortable"),
            ("Hungry", lambda: None, "I am hungry"),
            ("Thirsty", lambda: None, "I am Thirsty"),
            ("Pain", lambda: None, "I am in Pain"),
            ("Chair", lambda: None, "I want to get in the chair"),
            ("Bed", lambda: None, "I want to get in Bed"),
        ]
        self.create_button_grid(buttons)

class FeelingsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Feelings")
        buttons = [
            ("Back", lambda: self.parent.show_frame(CommunicationPageMenu), None),  # Add Back button
            ("Great", lambda: None, "Great"),
            ("Good", lambda: None, "Good"),
            ("Okay", lambda: None, "Okay"),
            ("Silly", lambda: None, "Silly"),
            ("Scared", lambda: None, "Scared"),
            ("Sad", lambda: None, "Sad"),
            ("Mad", lambda: None, "Mad"),
            ("Disappointed", lambda: None, "Disappointed"),
        ]
        self.create_button_grid(buttons)

class ConversationPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Conversation")
        buttons = [
            ("Back", lambda: self.parent.show_frame(CommunicationPageMenu), None),  # Add Back button
            ("Meet", lambda: None, "Nice to meet you"),
            ("Well", lambda: None, "I am doing well"),
            ("Name", lambda: None, "What is your name?"),
            ("HRU", lambda: None, "How are you?"),
            ("About You", lambda: None, "Tell me about yourself"),
            ("WRUD", lambda: None, "What are you doing?"),
            ("Intro", lambda: None, "Hi, my name is Ben and I'm nonverbal. I use this device to communicate with others. I love the color red. Spider-Man is my favorite hero. I love to laugh. My brother and sister-in-law can help if you need more information."),
            ("Explain", lambda: None, "Please explain."),
        ]
        self.create_button_grid(buttons)

class QuestionsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Questions")
        buttons = [
            ("Back", lambda: self.parent.show_frame(CommunicationPageMenu), None),  # Add Back button
            ("Weather", lambda: None, "What is it like outside?"),
            ("Doing", lambda: None, "What are we doing today?"),
            ("Help", lambda: None, "Can you help me?"),
            ("Talking About", lambda: None, "What are you talking about?"),
            ("Talk to Me", lambda: None, "Will you talk to me for a while?"),
            ("Time", lambda: None, "What time is it?"),
            ("Going", lambda: None, "Are we going somewhere?"),
            ("Something", lambda: None, "Can we do something?"),
        ]
        self.create_button_grid(buttons)

class QuotesPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Quotes & Misc")
        buttons = [
            ("Back", lambda: self.parent.show_frame(CommunicationPageMenu), None),  # Add Back button
            ("Smiling", lambda: None, "What the hell are you smiling at?"),
            ("Burns", lambda: None, "Oh, it's mister burns. Kill it!"),
            ("Hobo", lambda: None, "I'm not a stabbing hobo, I'm a singing hobo."),
            ("Meg", lambda: None, "Shut up, Meg"),
            ("STFU", lambda: None, "Shut the fuck up"),
            ("WTF", lambda: None, "What the fuck"),
            ("FU", lambda: None, "Fuck you."),
            ("BS", lambda: None, "That's bullshit"),
        ]
        self.create_button_grid(buttons)

class RatingPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Rating")
        buttons = [
            ("Back", lambda: self.parent.show_frame(CommunicationPageMenu), None),  # Add Back button
            ("0", lambda: None, "Zero out of ten"),
            ("1-2", lambda: None, "One or two out of ten"),
            ("3-4", lambda: None, "Three or four out of ten"),
            ("5-6", lambda: None, "Five or six out of ten"),
            ("7-8", lambda: None, "Seven or eight out of ten"),
            ("9", lambda: None, "Nine out of ten"),
            ("10", lambda: None, "Ten out of ten"),
            ("11", lambda: None, "Eleven out of ten"),
        ]
        self.create_button_grid(buttons)

class TwitchPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Twitch")
        buttons = [
            ("Back", lambda: self.parent.show_frame(CommunicationPageMenu), None),  # Add Back button
            ("Games", lambda: None, "What games are you playing?"),
            ("Character/Hero", lambda: None, "Who is your favorite character/hero and why do you like them?"),
            ("TTS", lambda: None, "You can use your points to use Text-to-Speech to talk to me. Make sure you include your name in the message so I know who I'm speaking to."),
            ("BEAMINBENNY", lambda: None, "Follow me on Instagram and YouTube at beaminbenny"),
            ("Shy", lambda: None, "Don't be shy, talk to me"),
            ("Bite", lambda: None, "I won't bite"),
            ("Ladies", lambda: None, "Where are the ladies at?"),
            ("Boring", lambda: None, "You all are boring"),
        ]
        self.create_button_grid(buttons)
        
class LiveStreamingPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Streaming Shows")
        buttons = [
            ("Back", lambda: parent.show_frame(EntertainmentMenuPage), None),
            ("ACROZEN STREAM", lambda: self.open_in_chrome("ACROZEN STREAM", "https://www.twitch.tv/acroz3n"), "ACROZEN"),
        ]
        self.create_button_grid(buttons)
   

class StreamingShowsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Streaming Shows")
        buttons = [
            ("Back", lambda: parent.show_frame(EntertainmentMenuPage), None),
            ("Anime", lambda: parent.show_frame(AnimePageMenu), "Anime"),
            ("Cartoons", lambda: parent.show_frame(CartoonsPageMenu), "Cartoons"),
            ("Comedy", lambda: parent.show_frame(ComedyPageMenu), "Comedy"),
            ("Nickelodeon", lambda: parent.show_frame(NickelodeonPageMenu), "Nickelodeon"),
            ("Movies", lambda: parent.show_frame(MoviesPageMenu), "Movies"),
            ("Fantasy", lambda: parent.show_frame(FantasyPageMenu), "Fantasy"),
            ("Star Wars", lambda: parent.show_frame(StarWarsPageMenu), "Star Wars"),
            ("Spider Man", lambda: parent.show_frame(SpiderManPageMenu), "Spider Man"),
        ]
        self.create_button_grid(buttons)


class AnimePageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Anime")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("Avatar", lambda: self.open_in_chrome("Avatar", "https://www.netflix.com/watch/70136344?trackId=14188376"), "Avatar"),
            ("One Punch Man", lambda: self.open_in_chrome("One Punch Man", "https://www.hulu.com/watch/34ebf58e-5a2a-4efa-8e4d-fb16039a3051"), "One Punch Man"),
            ("Dragon Ball Z", lambda: self.open_in_chrome("Dragon Ball Z", "https://www.hulu.com/watch/1693a9f8-1697-4fe2-b996-fb7dc63ec9cc"), "Dragon Ball Z"),
            ("Dragon Ball Super", lambda: self.open_in_chrome("Dragon Ball Super", "https://www.hulu.com/watch/32385ddb-b6fa-425a-ae79-ffe0298f2446"), "Dragon Ball Super"),
            ("Dragon Ball Super Broly", lambda: self.open_in_chrome("Dragon Ball Super Broly", "https://www.hulu.com/watch/dea31115-06f7-4a02-ab60-c00e36f1f378"), "Dragon Ball Super Broly"),
            ("Yu-Gi-Oh", lambda: self.open_in_chrome("Yu-Gi-Oh", "https://www.hulu.com/watch/1bc9d2c0-f71f-4f77-a28a-efc2abeced82"), "Yu-Gi-Oh"),
            ("DigiMon", lambda: self.open_in_chrome("DigiMon", "https://www.hulu.com/watch/aa9603ec-3688-4e02-b461-1fa4f407fbe9"), "DigiMon"),
            ("DBZ Abridged", lambda: self.open_in_chrome("DBZ Abridged", "https://www.youtube.com/watch?v=aRiHUsIY_bE&pp=ygUZZHJhZ29uYmFsbCB6IGFicmlkZ2UgZnVsbA%3D%3D"), "DBZ Abridged"),
        ]
        self.create_button_grid(buttons)

import pyautogui
import time

class CartoonsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Cartoons")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("Family Guy", lambda: self.open_in_chrome("Family Guy", "https://www.hulu.com/watch/e3e44e69-6b56-44e9-b083-cbcb7c9730a5"), "Family Guy"),
            ("Futurama", lambda: self.open_in_chrome("Futurama", "https://www.hulu.com/watch/c3728d56-fbfc-4509-a16d-19857f8b1daa"), "Futurama"),
            ("South Park", lambda: self.open_in_chrome("South Park", "https://play.max.com/video/watch/cf46936d-0a68-4a0b-aa2d-4a3a131be881"), "South Park"),
            ("The Simpsons", lambda: self.open_in_chrome("The Simpsons", "https://www.disneyplus.com/play/ffb14e5a-38db-4522-a559-3cfa52bcf4df"), "The Simpsons"),
            ("Invader Zim", lambda: self.open_and_click("Invader Zim", "https://www.paramountplus.com/shows/video/zD9DQ3XZRnHNeh_mieUpRmAlA0T2oTjz/"), "Invader Zim"),
            ("Aqua Teen", lambda: self.open_in_chrome("Aqua Teen", "https://play.max.com/video/watch/9c2a7469-5089-4229-9278-d1768494166b"), "Aqua Teen"),
            ("American Dad", lambda: self.open_in_chrome("American Dad", "https://www.hulu.com/watch/8b927330-f55e-461d-b067-6e401f20c526"), "American Dad"),
            ("Cartoons", lambda: self.open_and_click("Cartoons", "https://www.paramountplus.com/live-tv/stream/channels/adult-animation/OwFn_OQhGr_vm7uE077Slr_apTPYyoFM/#"), "Cartoons"),
        ]
        self.create_button_grid(buttons)
               
class ComedyPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Comedy")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("Jeff Dunham 2017", lambda: self.open_in_chrome("Jeff Dunham 2017", "https://www.netflix.com/watch/80158670?trackId=255824129"), "Jeff Dunham 2017"),
            ("Jeff Dunham 2019", lambda: self.open_in_chrome("Jeff Dunham 2019", "https://www.netflix.com/watch/81074113?trackId=255824129"), "Jeff Dunahm 2019"),
            ("Tom Segura 2016", lambda: self.open_in_chrome("Tom Segura 2016", "https://www.netflix.com/watch/80077923"), "Tom Segura 2016"),
            ("Tom Segura 2018", lambda: self.open_in_chrome("Tom Segura 2018", "https://www.netflix.com/watch/80187307"), "Tom Segura 2018"),
            ("Tom Segura 2020", lambda: self.open_in_chrome("Tom Segura 2020", "https://www.netflix.com/watch/81143584"), "Tom Segura 2020"),
            ("Tom Segura 2023", lambda: self.open_in_chrome("Tom Segura 2023", "https://www.netflix.com/watch/81605926"), "Tom Segura 2023"),
            ("Standup", lambda: self.open_in_chrome("Standup", "https://youtu.be/ctyzvJLoid0"), "Standup"),
            ("After Dark", lambda: self.open_in_chrome("After Dark", "https://www.youtube.com/watch?v=BAV48j4ubJg"), "Laugh After Dark"),
        ]
        self.create_button_grid(buttons)

import pyautogui
import time

from pynput.keyboard import Controller
import time
import win32gui
import win32con

class NickelodeonPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Nickelodeon")
        self.keyboard = Controller()  # Initialize the keyboard controller at the class level
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("iCarly", lambda: self.open_in_chrome("iCarly", "https://www.netflix.com/watch/70278748"), "iCarly"),
            ("Sam and Cat", lambda: self.open_in_chrome("Sam and Cat", "https://www.netflix.com/watch/80027804?trackId=255824129"), "Sam and Cat"),
            ("Victorious", lambda: self.open_in_chrome("Victorious", "https://www.netflix.com/watch/80026347"), "Victorious"),
            ("Drake & Josh", lambda: self.open_in_chrome("Drake & Josh", "https://www.netflix.com/watch/70136546?trackId=255824129"), "Drake & Josh"),
            ("Rugrats", lambda: self.open_in_chrome("Rugrats", "https://www.netflix.com/watch/70136846"), "Rugrats"),
            ("Sponge Bob", lambda: self.open_and_click("Sponge Bob", "https://www.paramountplus.com/shows/video/ZvEow_nZm5WAiLeMlEmISm3Deti40Ciu/"), "Sponge Bob"),
            ("The Thundermans", lambda: self.open_and_click("The Thundermans", "https://www.paramountplus.com/shows/video/12t8vYXTqn761xkHQ_Sgt5LF2c9qQj9_/"), "The Thundermans"),
            ("Nickelodeon", lambda: self.open_pluto("Nickelodeon", "https://pluto.tv/us/live-tv/5ca673e0d0bd6c2689c94ce3"), "Nickelodeon Stream"),
        ]
        self.create_button_grid(buttons)
        
from pynput.keyboard import Controller
import time
import win32gui
import win32con

class MoviesPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Movies")
        self.keyboard = Controller()  # Initialize the keyboard controller at the class level
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("Happy Gilmore", lambda: self.open_in_chrome("Happy Gilmore", "https://www.disneyplus.com/play/bf5b0d1a-b99b-492b-9748-86ff5a0669dc?distributionPartner=google"), "Happy Gilmore"),
            ("The Hot Chick", lambda: self.open_in_chrome("The Hot Chick", "https://www.hulu.com/watch/453bd143-b501-49d2-88b7-3fc87979e50b"), "The Hot Chick"),
            ("Billy Madison", lambda: self.open_in_chrome("Billy Madison", "https://www.disneyplus.com/play/0f6de803-ca80-4128-b39a-73b1e7304db1"), "Billy Madison"),
            ("Deadpool 1", lambda: self.open_in_chrome("Deadpool 1", "https://www.disneyplus.com/play/17854bdb-0121-4327-80a0-699fdecd1aaa"), "Deadpool 1"),
            ("Deadpool 2", lambda: self.open_in_chrome("Deadpool 2", "https://www.disneyplus.com/play/bdcd5a83-ad6e-428f-8c34-63a9cf695048"), "Deadpool 2"),
            ("Deadpool and Wolverine", lambda: self.open_in_chrome("Deadpool and Wolverine", "https://www.disneyplus.com/play/120ae1e6-2240-4924-a4ce-f8de6e28b0b1"), "Deadpool and Wolverine"),
            ("Comedy Movies", lambda: self.open_and_click("Comedy Movies", "https://www.paramountplus.com/live-tv/stream/channels/movies/N4zxkDj6cAJG3N2dZbUiUxKf3NM7ir__/"), "Comedy Stream"),
            ("Action Movies", lambda: self.open_pluto("Action Movies", "https://pluto.tv/us/live-tv/561d7d484dc7c8770484914a"), "Action Stream"),
        ]
        self.create_button_grid(buttons)
       
class FantasyPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Fantasy")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("LOTR: Fellowship", lambda: self.open_in_chrome("LOTR: Fellowship", "https://play.max.com/video/watch/26d05bd3-2f25-4f7d-b7de-8caa0610fd06/c99d6146-ac31-4dc9-9957-bd99e95a48d8"), "The Fellowship of the Ring"),
            ("LOTR: Two Towers", lambda: self.open_in_chrome("LOTR: Two Towers", "https://play.max.com/video/watch/2028f0f5-d18c-4a9d-8107-1e49d944e744/a82c4890-04e6-489e-97d8-b83d65dcbdbd"), "The Two Towers"),
            ("LOTR: Return of the King", lambda: self.open_in_chrome("LOTR: Return of the King", "https://play.max.com/video/watch/cfcbf3f2-3d0c-499f-b46f-9747b70efbbb/5284b373-2b7e-467e-baa6-d245d34dcf1a"), "Return of the King"),
            ("The Hobbit", lambda: self.open_in_chrome("The Hobbit", "https://play.max.com/video/watch/ad742ea8-0ba9-49c9-830a-5487e3728513/e7f9460f-f5fb-4e0e-95f1-3c2df66f2647"), "An Unexpected Journey"),
            ("The Hobbit 2", lambda: self.open_in_chrome("The Hobbit 2", "https://play.max.com/video/watch/072b9f21-8d3d-4da6-9061-5e2c9261c046/0ee2f5da-bbc5-4883-8339-c6998474f730"), "The Desolation of Smaug"),
            ("The Hobbit 3", lambda: self.open_in_chrome("The Hobbit 3", "https://play.max.com/video/watch/388607c1-85cf-4feb-872d-087d0f26d9fd/f2ef861f-ea19-422d-b29e-cbc8624b8cd2"), "Battle of the Five Armies"),
            ("Narnia 1", lambda: self.open_in_chrome("Narnia 1", "https://www.disneyplus.com/play/6b59eb41-8660-4d93-bc42-9521bebb47a3"), "Narnia"),
            ("Narnia 2", lambda: self.open_in_chrome("Narnia 2", "https://www.disneyplus.com/play/cfd042fc-db6e-43b6-b1b8-588624349f92"), "Narnia 2"),
        ]
        self.create_button_grid(buttons)


class StarWarsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Star Wars")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("Episode 1", lambda: self.open_in_chrome("Episode 1", "https://www.disneyplus.com/play/e0a9fee4-2959-4077-ad8c-8fab4fd6e4d1"), "The Phantom Menace"),
            ("Episode 2", lambda: self.open_in_chrome("Episode 2", "https://www.disneyplus.com/play/39cbdf17-1bbe-4de2-b4a4-8e342875c2c6"), "Attack of the Clones"),
            ("Episode 3", lambda: self.open_in_chrome("Episode 3", "https://www.disneyplus.com/play/eb1e2c5f-69bf-4240-a61f-7ffc4e0311b3"), "Revenge of the Sith"),
            ("Episode 4", lambda: self.open_in_chrome("Episode 4", "https://www.disneyplus.com/play/9a280e53-fcc0-4e17-a02c-b1f40913eb0b"), "A New Hope"),
            ("Episode 5", lambda: self.open_in_chrome("Episode 5", "https://www.disneyplus.com/play/0f5c5223-f4f6-46ef-ba8a-69cb0e17d8d3"), "The Empire Strikes Back"),
            ("Episode 6", lambda: self.open_in_chrome("Episode 6", "https://www.disneyplus.com/play/4b6e7cda-daa5-4f2d-9b61-35bbe562c69c"), "Return of the Jedi"),
            ("Episode 7", lambda: self.open_in_chrome("Episode 7", "https://www.disneyplus.com/play/2854a94d-3702-40bd-97a4-12d55a809188"), "The Force Awakens"),
            ("Episode 8", lambda: self.open_in_chrome("Episode 8", "https://www.disneyplus.com/play/50c1aff5-3051-4839-9ebf-e332c635e216"), "The Last Jedi"),
            ("Episode 9", lambda: self.open_in_chrome("Episode 9", "https://www.disneyplus.com/play/43f9c275-e7e8-4ab3-802d-00d06a8ad841"), "The Rise of Skywalker"),
        ]
        self.create_button_grid(buttons, columns=5)  # Set columns to 5

    def create_button_grid(self, buttons, columns=5):
        """Creates a grid layout for buttons with a dynamic number of rows and columns."""
        grid_frame = tk.Frame(self, bg="black")
        grid_frame.pack(expand=True, fill="both")

        rows = (len(buttons) + columns - 1) // columns  # Calculate required rows
        for i, (text, command, speak_text) in enumerate(buttons):
            row, col = divmod(i, columns)
            btn = tk.Button(
                grid_frame, text=text, font=("Arial Black", 36), bg="light blue", fg="black",
                activebackground="yellow", activeforeground="black",
                command=lambda c=command, s=speak_text: self.on_select(c, s)
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            self.buttons.append(btn)  # Add button to scanning list

        for i in range(rows):
            grid_frame.rowconfigure(i, weight=1)
        for j in range(columns):
            grid_frame.columnconfigure(j, weight=1)

    def on_select(self, command, speak_text):
        """Handle button selection with scanning."""
        command()
        if speak_text:
            speak(speak_text)

class SpiderManPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Spider Man")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("Spider-Man (2002)", lambda: self.open_in_chrome("Spider-Man (2002)", "https://www.disneyplus.com/play/0043a9c8-7e34-44e0-8128-e9419ae58868"), "Spider-Man (2002)"),
            ("Spider-Man 2", lambda: self.open_in_chrome("Spider-Man 2", "https://www.disneyplus.com/play/25ec8dd6-e574-45fa-9a62-97396cdfaf68"), "Spider-Man 2"),
            ("Spider-Man 3", lambda: self.open_in_chrome("Spider-Man 3", "https://www.disneyplus.com/play/5faa8ff9-91f6-4130-8357-afbe087cb8a4"), "Spider-Man 3"),
            ("The Amazing Spider-Man", lambda: self.open_in_chrome("The Amazing Spider-Man", "https://www.disneyplus.com/play/f43ffe63-2c96-4b6c-8fae-84d0d22d6466"), "The Amazing Spider-Man"),
            ("The Amazing Spider-Man 2", lambda: self.open_in_chrome("The Amazing Spider-Man 2", "https://www.disneyplus.com/play/c21c733a-18f4-4cdc-b1e8-1ff6b996c0a3"), "The Amazing Spider-Man 2"),
            ("Spider-Man: Homecoming", lambda: self.open_in_chrome("Spider-Man: Homecoming", "https://www.disneyplus.com/play/5b2b999a-045e-4d89-af52-390c257178db"), "Spider-Man: Homecoming"),
            ("Spider-Man: Far From Home", lambda: self.open_in_chrome("Spider-Man: Far From Home", "https://www.disneyplus.com/play/2ca3cca0-bd2b-4934-93c0-c03d27fb249e"), "Spider-Man: Far From Home"),
            ("Spider-Man", lambda: self.open_in_chrome("Spider-Man", "https://youtu.be/dtxfJD60FCQ"), "Spider-Man Stream"),
        ]
        self.create_button_grid(buttons)
    
    def on_select(self, command, speak_text):
        """Handle button selection with scanning."""
        command()
        if speak_text:
            speak(speak_text)

# Run the App
if __name__ == "__main__":
    app = App()
    app.mainloop()