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
    """Minimize the app when Chrome is running and restore focus when Chrome closes."""
    app_title = "Accessible Menu"  # Replace with the exact title of your app window
    hwnd = win32gui.FindWindow(None, app_title)
    if not hwnd:
        print("Application window not found.")
        return

    app_minimized = False  # Track app's state

    while True:
        try:
            if is_chrome_running():
                if not app_minimized:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    print("Chrome detected. Application minimized.")
                    app_minimized = True
            else:
                if app_minimized:
                    print("Chrome closed. Restoring application...")
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    time.sleep(0.1)  # Ensure window state is updated
                    win32gui.SetForegroundWindow(hwnd)
                    print("Application restored to focus.")
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
    """Log all active window titles for debugging."""
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
    """Bring the application to focus and ensure it's restored."""
    try:
        # Replace "Accessible Menu" with the exact title of your app window
        app_hwnd = win32gui.FindWindow(None, "Accessible Menu")
        if app_hwnd:
            # Restore the application window if minimized
            win32gui.ShowWindow(app_hwnd, win32con.SW_RESTORE)
            time.sleep(0.1)  # Small delay to ensure the window state is updated
            # Bring the window to the foreground
            win32gui.SetForegroundWindow(app_hwnd)
            print("Application successfully brought to focus.")
        else:
            print("Application window not found.")
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
        """Perform actions after detecting the key sequence."""
        close_chrome_cleanly()

        # Delay to ensure Chrome is fully closed
        print("Waiting for Chrome to close...")
        time.sleep(2)  # Adjust delay as needed

        # Bring the application into focus
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

    def bind_keys_for_scanning(self):
        """Bind keyboard inputs for scanning globally."""
        self.bind("<KeyPress-space>", self.track_spacebar_hold)
        self.bind("<KeyRelease-space>", self.reset_spacebar_hold)
        self.bind("<KeyRelease-Return>", self.select_button)
        print("Global key bindings re-applied.")

        # Force focus on the application
        self.focus_set()
        self.focus_force()

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
        """Switch to the specified frame, ensuring proper cleanup of the previous frame."""
        # Clean up the current frame if it exists
        if self.current_frame:
            if hasattr(self.current_frame, "unload"):  # Call the unload method if it exists
                self.current_frame.unload()
            self.current_frame.destroy()  # Destroy the current frame to prevent errors

        # Create and display the new frame
        self.current_frame = frame_class(self)
        self.current_frame.pack(expand=True, fill="both")

        # Update scanning buttons for the new frame
        self.buttons = getattr(self.current_frame, "buttons", [])  # Safely get buttons if they exist
        self.current_button_index = 0  # Reset scanning index

        # Highlight the first button, if buttons are available
        if self.buttons:
            self.highlight_button(0)

    import threading

    def scan_forward(self, event=None):
        """Advance to the next button and highlight it upon spacebar release."""
        if not self.selection_enabled or not self.buttons:
            return

        self.selection_enabled = False  # Disable selection temporarily
        self.current_button_index = (self.current_button_index + 1) % len(self.buttons)
        self.highlight_button(self.current_button_index)
           
        # Speak the button's text if the frame matches
        if isinstance(self.current_frame, (
            MainMenuPage, CommunicationPageMenu, EntertainmentMenuPage, MoviesPageMenu,
            ComedyMovieFranchisesPage, HangoverMoviesPage, HaroldKumarMoviesPage, ScaryMoviesPage,
            AdamSandlerMoviesPage, SethRogenMoviesPage, KevinSmithMoviesPage, MikeMyersMovies,
            AnimatedMoviesPage, PixarMoviesPage, ToyStorySeriesPage, IncrediblesSeriesPage,
            ShrekSeriesPage, CarsSeriesPage, DisneyMoviesClassicsPage, FrozenSeriesPage,
            RugratsMoviesPage, KungFuPandaSeriesPage, IceAgeSeriesPage, StandupSpecialsPage,
            ActionMoviesPage, RockyMoviesPage, MatrixMoviesPage, JohnWickMoviesPage,
            KarateKidMoviesPage, TerminatorMoviesPage, FastFuriousMoviesPage, CreedMoviesPage,
            MissionImpossibleMoviesPage, SuperheroMoviesPage, SpiderManTobeyPage, SpiderManAndrewPage,
            SpiderManTomPage, DeadpoolMoviesPage, XMenMoviesPage, DarkKnightMoviesPage,
            AvengersMoviesPage, IronManMoviesPage, ClassicComedyPage, StarWarsPageMenu,
            LordOfTheRingsPage, ShowsPageMenu, AnimeSeriesPage, Cartoons90sPage, AdultAnimatedComedyPage,
            KidsCartoonsPage, NickelodeonSitcomsPage, LiveStreamingPageMenu
        )):
            speak(self.buttons[self.current_button_index]["text"])

        # Re-enable selection after a short delay
        threading.Timer(0.5, self.enable_selection).start()

    def scan_backward(self, event=None):
        """Move to the previous button and highlight it."""
        if not self.selection_enabled or not self.buttons:
            return

        self.selection_enabled = False  # Disable selection temporarily
        self.current_button_index = (self.current_button_index - 1) % len(self.buttons)
        self.highlight_button(self.current_button_index)

        # Speak the button's text if the frame matches
        if isinstance(self.current_frame, (
            MainMenuPage, CommunicationPageMenu, EntertainmentMenuPage, MoviesPageMenu,
            ComedyMovieFranchisesPage, HangoverMoviesPage, HaroldKumarMoviesPage, ScaryMoviesPage,
            AdamSandlerMoviesPage, SethRogenMoviesPage, KevinSmithMoviesPage, MikeMyersMovies,
            AnimatedMoviesPage, PixarMoviesPage, ToyStorySeriesPage, IncrediblesSeriesPage,
            ShrekSeriesPage, CarsSeriesPage, DisneyMoviesClassicsPage, FrozenSeriesPage,
            RugratsMoviesPage, KungFuPandaSeriesPage, IceAgeSeriesPage, StandupSpecialsPage,
            ActionMoviesPage, RockyMoviesPage, MatrixMoviesPage, JohnWickMoviesPage,
            KarateKidMoviesPage, TerminatorMoviesPage, FastFuriousMoviesPage, CreedMoviesPage,
            MissionImpossibleMoviesPage, SuperheroMoviesPage, SpiderManTobeyPage, SpiderManAndrewPage,
            SpiderManTomPage, DeadpoolMoviesPage, XMenMoviesPage, DarkKnightMoviesPage,
            AvengersMoviesPage, IronManMoviesPage, ClassicComedyPage, StarWarsPageMenu,
            LordOfTheRingsPage, ShowsPageMenu, AnimeSeriesPage, Cartoons90sPage, AdultAnimatedComedyPage,
            KidsCartoonsPage, NickelodeonSitcomsPage, LiveStreamingPageMenu
        )):
            speak(self.buttons[self.current_button_index]["text"])

        # Re-enable selection after a short delay
        threading.Timer(0.5, self.enable_selection).start()

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

        # Re-enable fullscreen mode
        pyautogui.press('f11')
        print("Fullscreen mode toggled.")

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
        """Advance to the next button and highlight it upon spacebar release."""
        if not self.selection_enabled or not self.buttons:
            print("Selection not enabled or no buttons available.")
            return

        # Disable selection temporarily
        self.selection_enabled = False
        self.current_button_index = (self.current_button_index + 1) % len(self.buttons)
        self.highlight_button(self.current_button_index)
        speak(self.buttons[self.current_button_index]["text"])  # Speak button text

        # Re-enable selection after a delay
        threading.Timer(0.5, self.enable_selection).start()

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
            ("Movies Menu", lambda: parent.show_frame(MoviesPageMenu), "Movies Menu"),
            ("Shows Menu", lambda: parent.show_frame(ShowsPageMenu), "Shows Menu"),
            ("Live Streams", lambda: parent.show_frame(LiveStreamingPageMenu), "Live Streams"), 
            ("Music", self.coming_soon, "Music (coming soon)"),
            ("Audio Books", self.coming_soon, "Audio Books (coming soon)"),
            ("Games", self.coming_soon, "Games (coming soon)"),
            ("Trivia", self.coming_soon, "Trivia (coming soon)"),
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
            ("Keyboard", lambda: parent.show_frame(lambda p=parent: KeyboardFrame(p, navigate_back_callback=lambda: parent.show_frame(CommunicationPageMenu))), "Keyboard"),
            ("Basic", lambda: parent.show_frame(BasicPageMenu), "Basic"),
            ("Needs", lambda: parent.show_frame(NeedsPageMenu), "Needs"),
            ("Conversation", lambda: parent.show_frame(ConversationPageMenu), "Conversation"),
            ("Questions", lambda: parent.show_frame(QuestionsPageMenu), "Questions"),
            ("Quotes & Misc", lambda: parent.show_frame(QuotesPageMenu), "Quotes & Misc"),
            ("Feelings", lambda: parent.show_frame(FeelingsPageMenu), "Feelings"),
            ("Twitch", lambda: parent.show_frame(TwitchPageMenu), "Twitch"),
        ]
        self.create_button_grid(buttons) 

import tkinter as tk
import threading
import time
import pyttsx3  # For Text-to-Speech functionality

class KeyboardFrame(tk.Frame):
    def __init__(self, parent, navigate_back_callback):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.navigate_back_callback = navigate_back_callback
        self.current_text = tk.StringVar()
        self.current_row_index = 0
        self.current_button_index = 0
        self.in_row_selection_mode = True
        self.spacebar_pressed = False
        self.scanning_thread = None
        self.backward_loop_started = False  # Track backward loop state

        self.tts_engine = pyttsx3.init()  # Initialize TTS engine

        self.row_titles = [
            "Controls", "A-F", "G-L", "M-R", "S-X", "Y-3", "4-9"
        ]
        self.rows = [
            ["Play", "Back", "Space", "Del Letter", "Del Word", "Clear"],
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
            font=("Arial", 36),
            bg="light blue",
            command=self.read_text_tts
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
                    font=("Arial", 48),
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

    def bind_keys(self):
        """Bind keys for scanning and selecting."""
        self.bind_all("<KeyPress-space>", self.start_scanning)
        self.bind_all("<KeyRelease-space>", self.stop_scanning)
        self.bind_all("<KeyRelease-Return>", self.select_button)

    def unbind_keys(self):
        """Unbind keys specific to KeyboardFrame."""
        self.unbind_all("<KeyPress-space>")
        self.unbind_all("<KeyRelease-space>")
        self.unbind_all("<KeyRelease-Return>")
        print("Keys unbound for KeyboardFrame")

    def start_scanning(self, event):
        """Start scanning when the spacebar is pressed."""
        if not self.spacebar_pressed:
            self.spacebar_pressed = True
            self.scanning_thread = threading.Thread(target=self.scan, daemon=True)
            self.scanning_thread.start()

    def stop_scanning(self, event):
        """Stop scanning when the spacebar is released."""
        self.spacebar_pressed = False

    def scan_forward(self):
        """Scan forward through rows or buttons based on the mode."""
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

            # Highlight and TTS for each button
            self.highlight_button(self.current_button_index, prev_button_index)
            if self.current_button_index == 0:  # Back to the start, return to row mode
                self.in_row_selection_mode = True
                self.highlight_row(self.current_row_index)
                self.speak_row_title(self.current_row_index)
            else:
                self.speak_button_label(self.current_button_index)

    def scan_backward(self):
        """Scan backward through buttons, ensuring a full loop before returning to row selection mode."""
        if self.in_row_selection_mode:
            # Backward scan through rows
            prev_row_index = self.current_row_index
            self.current_row_index = (self.current_row_index - 1) % len(self.rows)
            self.highlight_row(self.current_row_index, prev_row_index)
            self.speak_row_title(self.current_row_index)
        else:
            # Backward scan through buttons in the current row
            prev_button_index = self.current_button_index
            self.current_button_index -= 1

            # If reaching before the first button, loop to the last button
            if self.current_button_index < 0:
                self.current_button_index = len(self.rows[self.current_row_index]) - 1
                if self.backward_loop_started:  # If loop started, return to row select mode
                    print("Backward scan completed. Returning to row selection mode.")
                    self.in_row_selection_mode = True
                    self.backward_loop_started = False
                    self.highlight_row(self.current_row_index)
                    self.speak_row_title(self.current_row_index)
                    return
                else:
                    # Mark that the loop has started
                    self.backward_loop_started = True

            # Highlight and TTS for each button
            self.highlight_button(self.current_button_index, prev_button_index)
            self.speak_button_label(self.current_button_index)

    def scan(self):
        """Scan rows or buttons based on the mode."""
        time.sleep(0.3)  # Debounce for short taps
        if not self.spacebar_pressed or not self.winfo_exists():
            return  # Exit if the spacebar is not pressed or the frame is destroyed

        self.scan_forward()  # Perform a single forward scan for short press

        time.sleep(2)  # Wait before backward scanning starts
        while self.spacebar_pressed and self.winfo_exists():
            self.scan_backward()
            time.sleep(2)

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

    def select_button(self, event=None):
        """Handle selection of a row or button and transition appropriately."""
        if self.in_row_selection_mode:
            # Transition to Button Select Mode
            self.in_row_selection_mode = False
            self.current_button_index = 0  # Reset to the first button in the selected row
            self.backward_loop_started = False  # Reset backward loop tracking

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
            self.backward_loop_started = False  # Reset backward loop tracking

    def handle_button_press(self, char):
        """Handle the action for a button press."""
        if char == "Back":
            self.unload()
            self.navigate_back_callback()
        elif char == "Play":
            self.read_text_tts()
        elif char == "Space":
            self.current_text.set(self.current_text.get() + " ")
        elif char == "Clear":
            self.current_text.set("")
        elif char == "Del Char":
            self.current_text.set(self.current_text.get()[:-1])
        elif char == "Del Wrd":
            words = self.current_text.get().split()
            self.current_text.set(" ".join(words[:-1]))
        else:
            self.current_text.set(self.current_text.get() + char)

    def unload(self):
        """Clean up before destroying the frame."""
        self.stop_scanning(None)
        self.unbind_keys()
        self.spacebar_pressed = False
        self.current_row_index = 0
        self.current_button_index = 0
        self.in_row_selection_mode = True

    def read_text_tts(self):
        """Read the current text with TTS."""
        text = self.current_text.get()
        if text:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()

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

import pyautogui
import time
from pynput.keyboard import Controller
import time
import win32gui
import win32con

class LiveStreamingPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Streaming Shows")
        self.keyboard = Controller()  # Initialize the keyboard controller at the class level
        buttons = [
            ("Back", lambda: parent.show_frame(EntertainmentMenuPage), None),
            ("ACROZEN STREAM", lambda: self.open_in_chrome("ACROZEN STREAM", "https://www.twitch.tv/acroz3n"), "ACROZEN"),
            ("Action Movies TV", lambda: self.open_pluto("Action Movies", "https://pluto.tv/us/live-tv/561d7d484dc7c8770484914a?fullscreen=true"), "Action Movies TV"),
            ("Comedy Movies TV", lambda: self.open_pluto("Comedy Movies", "https://pluto.tv/us/live-tv/5a4d3a00ad95e4718ae8d8db?fullscreen=true"), "Comedy Movies TV"),
            ("Comedy Animation", lambda: self.open_pluto("Comedy Animation", "https://pluto.tv/us/live-tv/5f99e24636d67d0007a94e6d?fullscreen=true"), "Comedy Animation TV"),
            ("Adult Cartoons TV", lambda: self.open_in_chrome("ACROZEN STREAM", "https://www.twitch.tv/acroz3n"), "ACROZEN"),
            ("Sports TV", lambda: self.open_in_chrome("ACROZEN STREAM", "https://www.twitch.tv/acroz3n"), "ACROZEN"),
            ("Sports TV", lambda: self.open_and_click("ACROZEN STREAM", "https://www.twitch.tv/acroz3n"), "ACROZEN"),
        ]

        self.create_button_grid(buttons) 

class EntertainmentMenuPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Entertainment")
        self.buttons = []  # Store buttons for scanning
        self.current_button_index = 0  # Initialize scanning index
        self.selection_enabled = True  # Flag for debounce during scanning

        # Define buttons with their labels, actions, and TTS text
        buttons = [
            ("Back", lambda: parent.show_frame(MainMenuPage), "Back to Main Menu"),
            ("Movies Menu", lambda: parent.show_frame(MoviesPageMenu), "Movies Menu"),
            ("Shows Menu", lambda: parent.show_frame(ShowsPageMenu), "Shows Menu"),
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

class MoviesPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Movies Menu")
        buttons = [
            ("Back", lambda: parent.show_frame(EntertainmentMenuPage), "Back"),
            ("Comedy Movie Franchises", lambda: parent.show_frame(ComedyMovieFranchisesPage), "Comedy Movie Franchises"),
            ("Animated Movies", lambda: parent.show_frame(AnimatedMoviesPage), "Animated Movies"),
            ("Stand-up Comedy Specials", lambda: parent.show_frame(StandupSpecialsPage), "Stand-up Comedy Specials"),
            ("Action Movie Series", lambda: parent.show_frame(ActionMoviesPage), "Action Movie Series"),
            ("Superhero Movies", lambda: parent.show_frame(SuperheroMoviesPage), "Superhero Movies"),
            ("Classic Comedy", lambda: parent.show_frame(ClassicComedyPage), "Classic Comedy"),
            ("Star Wars", lambda: parent.show_frame(StarWarsPageMenu), "Star Wars"),
            ("Lord of the Rings", lambda: parent.show_frame(LordOfTheRingsPage), "Lord of the Rings"),
        ]
        self.create_button_grid(buttons)

class SuperheroMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Superhero Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("Spider-Man (Tobey Maguire series)", lambda: parent.show_frame(SpiderManTobeyPage), "Spider-Man (Tobey Maguire series)"),
            ("Spider-Man (Andrew Garfield series)", lambda: parent.show_frame(SpiderManAndrewPage), "Spider-Man (Andrew Garfield series)"),
            ("Spider-Man (Tom Holland series)", lambda: parent.show_frame(SpiderManTomPage), "Spider-Man (Tom Holland series)"),
            ("Deadpool", lambda: parent.show_frame(DeadpoolMoviesPage), "Deadpool"),
            ("X-Men Movies", lambda: parent.show_frame(XMenMoviesPage), "X-Men Movies"),
            ("The Dark Knight Trilogy", lambda: parent.show_frame(DarkKnightMoviesPage), "The Dark Knight Trilogy"),
            ("Avengers Movies", lambda: parent.show_frame(AvengersMoviesPage), "Avengers Movies"),
            ("Iron Man Trilogy", lambda: parent.show_frame(IronManMoviesPage), "Iron Man Trilogy"),
        ]
        self.create_button_grid(buttons)

class SpiderManTobeyPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Spider-Man (Tobey Maguire series)")
        buttons = [
            ("Back", lambda: parent.show_frame(SuperheroMoviesPage), "Back"),
            ("Spider-Man 1", lambda: self.open_in_chrome("Spider-Man 1", "https://www.disneyplus.com/play/0043a9c8-7e34-44e0-8128-e9419ae58868"), "Spider-Man 1"),
            ("Spider-Man 2", lambda: self.open_in_chrome("Spider-Man 2", "https://www.disneyplus.com/play/25ec8dd6-e574-45fa-9a62-97396cdfaf68"), "Spider-Man 2"),
            ("Spider-Man 3", lambda: self.open_in_chrome("Spider-Man 3", "https://www.disneyplus.com/play/5faa8ff9-91f6-4130-8357-afbe087cb8a4"), "Spider-Man 3"),
        ]
        self.create_button_grid(buttons)

class SpiderManAndrewPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Spider-Man (Andrew Garfield series)")
        buttons = [
            ("Back", lambda: parent.show_frame(SuperheroMoviesPage), "Back"),
            ("The Amazing Spider-Man", lambda: self.open_in_chrome("The Amazing Spider-Man", "https://www.disneyplus.com/play/f43ffe63-2c96-4b6c-8fae-84d0d22d6466"), "The Amazing Spider-Man"),
            ("The Amazing Spider-Man 2", lambda: self.open_in_chrome("The Amazing Spider-Man 2", "https://www.disneyplus.com/play/c21c733a-18f4-4cdc-b1e8-1ff6b996c0a3"), "The Amazing Spider-Man 2"),
        ]
        self.create_button_grid(buttons)

class SpiderManTomPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Spider-Man (Tom Holland series)")
        buttons = [
            ("Back", lambda: parent.show_frame(SuperheroMoviesPage), "Back"),
            ("Spider-Man: Homecoming", lambda: self.open_in_chrome("Spider-Man: Homecoming", "https://www.disneyplus.com/play/5b2b999a-045e-4d89-af52-390c257178db"), "Spider-Man: Homecoming"),
            ("Spider-Man: Far From Home", lambda: self.open_in_chrome("Spider-Man: Far From Home", "https://www.disneyplus.com/play/2ca3cca0-bd2b-4934-93c0-c03d27fb249e"), "Spider-Man: Far From Home"),
            ("Spider-Man: No Way Home", lambda: self.open_in_chrome("Spider-Man: No Way Home", "N/A"), "Coming Soon"),
        ]
        self.create_button_grid(buttons)

class DeadpoolMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Deadpool Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(SuperheroMoviesPage), "Back"),
            ("Deadpool 1", lambda: self.open_in_chrome("Deadpool 1", "https://www.disneyplus.com/play/17854bdb-0121-4327-80a0-699fdecd1aaa"), "Deadpool 1"),
            ("Deadpool 2", lambda: self.open_in_chrome("Deadpool 2", "https://www.disneyplus.com/play/bdcd5a83-ad6e-428f-8c34-63a9cf695048"), "Deadpool 2"),
            ("Deadpool 3", lambda: self.open_in_chrome("Deadpool 3", "https://www.disneyplus.com/play/120ae1e6-2240-4924-a4ce-f8de6e28b0b1"), "Deadpool 3"),
        ]
        self.create_button_grid(buttons)

class XMenMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "X-Men Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(SuperheroMoviesPage), "Back"),
            ("X-Men", lambda: self.open_in_chrome("X-Men", "https://www.disneyplus.com/play/962f2f09-4468-4fb1-aef7-5b38e1f019db"), "X-Men"),
            ("X2", lambda: self.open_in_chrome("X2", "https://www.disneyplus.com/play/032e7431-88c7-4ff6-a3f3-eb9f554e95c7"), "X2"),
            ("X-Men: The Last Stand", lambda: self.open_in_chrome("X-Men The Last Stand", "https://www.disneyplus.com/play/e0f6bbed-cea5-41c1-b787-478f21255898"), "X-Men: The Last Stand"),
        ]
        self.create_button_grid(buttons)

class DarkKnightMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "The Dark Knight Trilogy")
        buttons = [
            ("Back", lambda: parent.show_frame(SuperheroMoviesPage), "Back"),
            ("Batman Begins", lambda: self.open_in_chrome("Batman Begins", "https://play.max.com/video/watch/28517d19-4c00-46e0-b139-b506cbcc4b40/ad9dfba7-864a-4104-9054-fa7957d74f40"), "Batman Begins"),
            ("The Dark Knight", lambda: self.open_in_chrome("The Dark Knight", "N/A"), "Coming Soon"),
            ("The Dark Knight Rises", lambda: self.open_in_chrome("The Dark Knight Rises", "https://play.max.com/movie/6ce5965d-cdb2-4f9c-b22b-ae7a091d95a8"), "The Dark Knight Rises"),
        ]
        self.create_button_grid(buttons)

class AvengersMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Avengers Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(SuperheroMoviesPage), "Back"),
            ("The Avengers", lambda: self.open_in_chrome("The Avengers", "https://www.disneyplus.com/play/3a5596d6-5133-4a8e-8d21-00e1531a4e0f"), "The Avengers"),
            ("Avengers: Age of Ultron", lambda: self.open_in_chrome("Avengers Age of Ultron", "https://www.disneyplus.com/play/39740da6-d484-471b-8dd7-a70c6151d705"), "Avengers: Age of Ultron"),
            ("Avengers: Infinity War", lambda: self.open_in_chrome("Avengers Infinity War", "https://www.disneyplus.com/play/9a136e06-852a-41bf-b71d-fa061cb43225"), "Avengers: Infinity War"),
            ("Avengers: Endgame", lambda: self.open_in_chrome("Avengers Endgame", "https://www.disneyplus.com/play/b39aa962-be56-4b09-a536-98617031717f"), "Avengers: Endgame"),
        ]
        self.create_button_grid(buttons)

class IronManMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Iron Man Trilogy")
        buttons = [
            ("Back", lambda: parent.show_frame(SuperheroMoviesPage), "Back"),
            ("Iron Man", lambda: self.open_in_chrome("Iron Man", "https://www.disneyplus.com/play/3ac839c4-864b-41ed-ad98-043d6b4ac564"), "Iron Man"),
            ("Iron Man 2", lambda: self.open_in_chrome("Iron Man 2", "https://www.disneyplus.com/play/e631253b-f3a7-49e4-a484-8aa538ba491f"), "Iron Man 2"),
            ("Iron Man 3", lambda: self.open_in_chrome("Iron Man 3", "https://www.disneyplus.com/play/741b5fda-91e0-4e6e-811d-fa9c9d0b326b"), "Iron Man 3"),
        ]
        self.create_button_grid(buttons)

class ActionMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Action Movie Series")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("Rocky Series", lambda: parent.show_frame(RockyMoviesPage), "Rocky Series"),
            ("The Matrix Series", lambda: parent.show_frame(MatrixMoviesPage), "The Matrix Series"),
            ("John Wick Series", lambda: parent.show_frame(JohnWickMoviesPage), "John Wick Series"),
            ("The Karate Kid Series", lambda: parent.show_frame(KarateKidMoviesPage), "The Karate Kid Series"),
            ("The Terminator Series", lambda: parent.show_frame(TerminatorMoviesPage), "The Terminator Series"),
            ("Fast & Furious Franchise", lambda: parent.show_frame(FastFuriousMoviesPage), "Fast & Furious Franchise"),
            ("Creed Series", lambda: parent.show_frame(CreedMoviesPage), "Creed Series"),
            ("Mission: Impossible Series", lambda: parent.show_frame(MissionImpossibleMoviesPage), "Mission: Impossible Series"),
        ]
        self.create_button_grid(buttons)

class RockyMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Rocky Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(ActionMoviesPage), "Back"),
            ("Rocky", lambda: self.open_in_chrome("Rocky", "https://example.com/rocky-1"), "Rocky"),
            ("Rocky II", lambda: self.open_in_chrome("Rocky II", "https://example.com/rocky-2"), "Rocky II"),
            ("Rocky III", lambda: self.open_in_chrome("Rocky III", "https://example.com/rocky-3"), "Rocky III"),
            ("Rocky IV", lambda: self.open_in_chrome("Rocky IV", "https://example.com/rocky-4"), "Rocky IV"),
            ("Rocky V", lambda: self.open_in_chrome("Rocky V", "https://example.com/rocky-5"), "Rocky V"),
            ("Rocky Balboa", lambda: self.open_in_chrome("Rocky Balboa", "https://example.com/rocky-balboa"), "Rocky Balboa"),
        ]
        self.create_button_grid(buttons)

class CreedMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Creed Series")
        buttons = [
            ("Back", lambda: parent.show_frame(ActionMoviesPage), "Back"),
            ("Creed", lambda: self.open_in_chrome("Creed", "https://example.com/creed-1"), "Creed"),
            ("Creed II", lambda: self.open_in_chrome("Creed II", "https://example.com/creed-2"), "Creed II"),
            ("Creed III", lambda: self.open_in_chrome("Creed III", "https://example.com/creed-3"), "Creed III"),
        ]
        self.create_button_grid(buttons)

class MatrixMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "The Matrix Series")
        buttons = [
            ("Back", lambda: parent.show_frame(ActionMoviesPage), "Back"),
            ("The Matrix", lambda: self.open_in_chrome("The Matrix", "https://example.com/the-matrix"), "The Matrix"),
            ("The Matrix Reloaded", lambda: self.open_in_chrome("The Matrix Reloaded", "https://example.com/the-matrix-reloaded"), "The Matrix Reloaded"),
            ("The Matrix Revolutions", lambda: self.open_in_chrome("The Matrix Revolutions", "https://example.com/the-matrix-revolutions"), "The Matrix Revolutions"),
            ("The Matrix Resurrections", lambda: self.open_in_chrome("The Matrix Resurrections", "https://example.com/the-matrix-resurrections"), "The Matrix Resurrections"),
        ]
        self.create_button_grid(buttons)

class JohnWickMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "John Wick Series")
        buttons = [
            ("Back", lambda: parent.show_frame(ActionMoviesPage), "Back"),
            ("John Wick", lambda: self.open_in_chrome("John Wick", "https://example.com/john-wick"), "John Wick"),
            ("John Wick: Chapter 2", lambda: self.open_in_chrome("John Wick Chapter 2", "https://example.com/john-wick-2"), "John Wick: Chapter 2"),
            ("John Wick: Chapter 3 - Parabellum", lambda: self.open_in_chrome("John Wick Chapter 3", "https://example.com/john-wick-3"), "John Wick: Chapter 3 - Parabellum"),
            ("John Wick: Chapter 4", lambda: self.open_in_chrome("John Wick Chapter 4", "https://example.com/john-wick-4"), "John Wick: Chapter 4"),
        ]
        self.create_button_grid(buttons)

class KarateKidMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "The Karate Kid Series")
        buttons = [
            ("Back", lambda: parent.show_frame(ActionMoviesPage), "Back"),
            ("The Karate Kid", lambda: self.open_in_chrome("The Karate Kid", "https://example.com/karate-kid"), "The Karate Kid"),
            ("The Karate Kid Part II", lambda: self.open_in_chrome("The Karate Kid Part II", "https://example.com/karate-kid-2"), "The Karate Kid Part II"),
            ("The Karate Kid Part III", lambda: self.open_in_chrome("The Karate Kid Part III", "https://example.com/karate-kid-3"), "The Karate Kid Part III"),
            ("The Next Karate Kid", lambda: self.open_in_chrome("The Next Karate Kid", "https://example.com/next-karate-kid"), "The Next Karate Kid"),
            ("Cobra Kai", lambda: self.open_in_chrome("Cobra Kai Season 1", "https://example.com/cobra-kai-1"), "Cobra Kai"),
        ]
        self.create_button_grid(buttons)

class TerminatorMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "The Terminator Series")
        buttons = [
            ("Back", lambda: parent.show_frame(ActionMoviesPage), "Back"),
            ("The Terminator", lambda: self.open_in_chrome("The Terminator", "https://example.com/terminator-1"), "The Terminator"),
            ("Terminator 2: Judgment Day", lambda: self.open_in_chrome("Terminator 2", "https://example.com/terminator-2"), "Terminator 2: Judgment Day"),
            ("Terminator 3: Rise of the Machines", lambda: self.open_in_chrome("Terminator 3", "https://example.com/terminator-3"), "Terminator 3: Rise of the Machines"),
            ("Terminator Salvation", lambda: self.open_in_chrome("Terminator Salvation", "https://example.com/terminator-salvation"), "Terminator Salvation"),
            ("Terminator Genisys", lambda: self.open_in_chrome("Terminator Genisys", "https://example.com/terminator-genisys"), "Terminator Genisys"),
            ("Terminator: Dark Fate", lambda: self.open_in_chrome("Terminator Dark Fate", "https://example.com/terminator-dark-fate"), "Terminator: Dark Fate"),
        ]
        self.create_button_grid(buttons)

class FastFuriousMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Fast & Furious Franchise")
        buttons = [
            ("Back", lambda: parent.show_frame(ActionMoviesPage), "Back"),
            ("The Fast and the Furious", lambda: self.open_in_chrome("Fast and Furious", "https://example.com/fast-furious-1"), "The Fast and the Furious"),
            ("2 Fast 2 Furious", lambda: self.open_in_chrome("2 Fast 2 Furious", "https://example.com/fast-furious-2"), "2 Fast 2 Furious"),
            ("The Fast and the Furious: Tokyo Drift", lambda: self.open_in_chrome("Tokyo Drift", "https://example.com/fast-furious-tokyo"), "The Fast and the Furious: Tokyo Drift"),
            ("Fast & Furious", lambda: self.open_in_chrome("Fast & Furious", "https://example.com/fast-furious-4"), "Fast & Furious"),
            ("Fast Five", lambda: self.open_in_chrome("Fast Five", "https://example.com/fast-five"), "Fast Five"),
            ("Furious 6", lambda: self.open_in_chrome("Furious 6", "https://example.com/furious-6"), "Furious 6"),
            ("Furious 7", lambda: self.open_in_chrome("Furious 7", "https://example.com/furious-7"), "Furious 7"),
            ("The Fate of the Furious", lambda: self.open_in_chrome("Fate of the Furious", "https://example.com/furious-8"), "The Fate of the Furious"),
            ("F9", lambda: self.open_in_chrome("F9", "https://example.com/f9"), "F9"),
        ]
        self.create_button_grid(buttons)

class MissionImpossibleMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Mission: Impossible Series")
        buttons = [
            ("Back", lambda: parent.show_frame(ActionMoviesPage), "Back"),
            ("Mission: Impossible", lambda: self.open_in_chrome("Mission Impossible", "https://example.com/mission-impossible-1"), "Mission: Impossible"),
            ("Mission: Impossible 2", lambda: self.open_in_chrome("Mission Impossible 2", "https://example.com/mission-impossible-2"), "Mission: Impossible 2"),
            ("Mission: Impossible III", lambda: self.open_in_chrome("Mission Impossible III", "https://example.com/mission-impossible-3"), "Mission: Impossible III"),
            ("Mission: Impossible - Ghost Protocol", lambda: self.open_in_chrome("Ghost Protocol", "https://example.com/mission-impossible-4"), "Mission: Impossible - Ghost Protocol"),
            ("Mission: Impossible - Rogue Nation", lambda: self.open_in_chrome("Rogue Nation", "https://example.com/mission-impossible-5"), "Mission: Impossible - Rogue Nation"),
            ("Mission: Impossible - Fallout", lambda: self.open_in_chrome("Fallout", "https://example.com/mission-impossible-6"), "Mission: Impossible - Fallout"),
            ("Mission: Impossible - Dead Reckoning Part One", lambda: self.open_in_chrome("Dead Reckoning Part One", "https://example.com/mission-impossible-7"), "Mission: Impossible - Dead Reckoning Part One"),
        ]
        self.create_button_grid(buttons)

class ComedyMovieFranchisesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Comedy Movie Franchises")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("The Hangover Movies", lambda: parent.show_frame(HangoverMoviesPage), "The Hangover Movies"),
            ("Harold & Kumar Movies", lambda: parent.show_frame(HaroldKumarMoviesPage), "Harold & Kumar Movies"),
            ("Scary Movie Series", lambda: parent.show_frame(ScaryMoviesPage), "Scary Movie Series"),
            ("Adam Sandler Movies", lambda: parent.show_frame(AdamSandlerMoviesPage), "Adam Sandler Movies"),
            ("Seth Rogen Movies", lambda: parent.show_frame(SethRogenMoviesPage), "Seth Rogen Movies"),
            ("Kevin Smith Movies", lambda: parent.show_frame(KevinSmithMoviesPage), "Kevin Smith Movies"),
            ("Mike Myers Movies", lambda: parent.show_frame(MikeMyersMovies), "Mike Myers Movies"),
        ]
        self.create_button_grid(buttons)

class HangoverMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "The Hangover Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(ComedyMovieFranchisesPage), "Back"),
            ("The Hangover", lambda: self.open_in_chrome("The Hangover", "https://example.com/the-hangover-1"), "The Hangover"),
            ("The Hangover Part II", lambda: self.open_in_chrome("The Hangover Part II", "https://example.com/the-hangover-2"), "The Hangover Part II"),
            ("The Hangover Part III", lambda: self.open_in_chrome("The Hangover Part III", "https://example.com/the-hangover-3"), "The Hangover Part III"),
        ]
        self.create_button_grid(buttons)

class HaroldKumarMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Harold & Kumar Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(ComedyMovieFranchisesPage), "Back"),
            ("Harold & Kumar Go to White Castle", lambda: self.open_in_chrome("Harold & Kumar Go to White Castle", "https://example.com/harold-kumar-1"), "Harold & Kumar Go to White Castle"),
            ("Harold & Kumar Escape from Guantanamo Bay", lambda: self.open_in_chrome("Harold & Kumar Escape from Guantanamo Bay", "https://example.com/harold-kumar-2"), "Harold & Kumar Escape from Guantanamo Bay"),
            ("A Very Harold & Kumar Christmas", lambda: self.open_in_chrome("A Very Harold & Kumar Christmas", "https://example.com/harold-kumar-3"), "A Very Harold & Kumar Christmas"),
        ]
        self.create_button_grid(buttons)

class ScaryMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Scary Movie Series")
        buttons = [
            ("Back", lambda: parent.show_frame(ComedyMovieFranchisesPage), "Back"),
            ("Scary Movie", lambda: self.open_in_chrome("Scary Movie", "https://example.com/scary-movie-1"), "Scary Movie"),
            ("Scary Movie 2", lambda: self.open_in_chrome("Scary Movie 2", "https://example.com/scary-movie-2"), "Scary Movie 2"),
            ("Scary Movie 3", lambda: self.open_in_chrome("Scary Movie 3", "https://example.com/scary-movie-3"), "Scary Movie 3"),
            ("Scary Movie 4", lambda: self.open_in_chrome("Scary Movie 4", "https://example.com/scary-movie-4"), "Scary Movie 4"),
            ("Scary Movie 5", lambda: self.open_in_chrome("Scary Movie 5", "https://example.com/scary-movie-5"), "Scary Movie 5"),
        ]
        self.create_button_grid(buttons)

class StandupSpecialsPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Comedy")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), None),
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

class MikeMyersMovies(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Wayne's World Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(ComedyMovieFranchisesPage), "Back"),
            ("Wayne's World", lambda: self.open_in_chrome("Wayne's World", "https://example.com/waynes-world-1"), "Wayne's World"),
            ("Wayne's World 2", lambda: self.open_in_chrome("Wayne's World 2", "https://example.com/waynes-world-2"), "Wayne's World 2"),
            ("Austin Powers: International Man of Mystery", lambda: self.open_in_chrome("Austin Powers: International Man of Mystery", "https://example.com/austin-powers-1"), "Austin Powers: International Man of Mystery"),
            ("Austin Powers: The Spy Who Shagged Me", lambda: self.open_in_chrome("Austin Powers: The Spy Who Shagged Me", "https://example.com/austin-powers-2"), "Austin Powers: The Spy Who Shagged Me"),
            ("Austin Powers in Goldmember", lambda: self.open_in_chrome("Austin Powers in Goldmember", "https://example.com/austin-powers-3"), "Austin Powers in Goldmember"),
            ("The Cat in the Hat", lambda: self.open_in_chrome("The Cat in the Hat", "https://example.com/austin-powers-3"), "The Cat in the Hat"),
        ]
        self.create_button_grid(buttons)

class KevinSmithMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Kevin Smith Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(ComedyMovieFranchisesPage), "Back"),
            ("Clerks", lambda: self.open_in_chrome("Clerks", "https://example.com/clerks-1"), "Clerks"),
            ("Clerks II", lambda: self.open_in_chrome("Clerks II", "https://example.com/clerks-2"), "Clerks II"),
            ("Clerks III", lambda: self.open_in_chrome("Clerks III", "https://example.com/clerks-3"), "Clerks III"),
            ("Dogma", lambda: self.open_in_chrome("Dogma", "https://example.com/dogma"), "Dogma"),
            ("Mallrats", lambda: self.open_in_chrome("Mallrats", "https://example.com/mallrats"), "Mallrats"),
            ("Jay and Silent Bob Strike Back", lambda: self.open_in_chrome("Jay and Silent Bob Strike Back", "https://example.com/jay-and-silent-bob"), "Jay and Silent Bob Strike Back"),
            ("Jay and Silent Bob Reboot", lambda: self.open_in_chrome("Jay and Silent Bob Reboot", "https://example.com/jay-and-silent-bob-reboot"), "Jay and Silent Bob Reboot"),
            ("Chasing Amy", lambda: self.open_in_chrome("Chasing Amy", "https://example.com/chasing-amy"), "Chasing Amy"),
        ]
        self.create_button_grid(buttons)

class AdamSandlerMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Adam Sandler Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("Happy Gilmore", lambda: self.open_in_chrome("Happy Gilmore", "https://example.com/happy-gilmore"), "Happy Gilmore"),
            ("Billy Madison", lambda: self.open_in_chrome("Billy Madison", "https://example.com/billy-madison"), "Billy Madison"),
            ("Little Nicky", lambda: self.open_in_chrome("Little Nicky", "https://example.com/little-nicky"), "Little Nicky"),
            ("Big Daddy", lambda: self.open_in_chrome("Big Daddy", "https://example.com/big-daddy"), "Big Daddy"),
            ("Waterboy", lambda: self.open_in_chrome("Waterboy", "https://example.com/waterboy"), "Waterboy"),
            ("Click", lambda: self.open_in_chrome("Click", "https://example.com/click"), "Click"),
            ("50 First Dates", lambda: self.open_in_chrome("50 First Dates", "https://example.com/50-first-dates"), "50 First Dates"),
            ("Grown Ups", lambda: self.open_in_chrome("Grown Ups", "https://example.com/grown-ups"), "Grown Ups"),
        ]
        self.create_button_grid(buttons)

class SethRogenMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Seth Rogen Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("Pineapple Express", lambda: self.open_in_chrome("Pineapple Express", "https://example.com/pineapple-express"), "Pineapple Express"),
            ("Paul", lambda: self.open_in_chrome("Paul", "https://example.com/paul"), "Paul"),
            ("Sausage Party", lambda: self.open_in_chrome("Sausage Party", "https://example.com/sausage-party"), "Sausage Party"),
            ("Superbad", lambda: self.open_in_chrome("Superbad", "https://example.com/superbad"), "Superbad"),
            ("This Is the End", lambda: self.open_in_chrome("This Is the End", "https://example.com/this-is-the-end"), "This Is the End"),
            ("Knocked Up", lambda: self.open_in_chrome("Knocked Up", "https://example.com/knocked-up"), "Knocked Up"),
            ("Neighbors", lambda: self.open_in_chrome("Neighbors", "https://example.com/neighbors"), "Neighbors"),
            ("The Interview", lambda: self.open_in_chrome("The Interview", "https://example.com/the-interview"), "The Interview"),
        ]
        self.create_button_grid(buttons)

class ActionMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Action Movie Series")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("Rocky Series", lambda: parent.show_frame(RockySeriesPage), "Rocky Series"),
            ("The Matrix Series", lambda: self.open_in_chrome("The Matrix", "https://example.com/the-matrix"), "The Matrix Series"),
            ("John Wick Series", lambda: self.open_in_chrome("John Wick", "https://example.com/john-wick"), "John Wick Series"),
            ("The Karate Kid Series", lambda: self.open_in_chrome("The Karate Kid", "https://example.com/the-karate-kid"), "The Karate Kid Series"),
            ("The Terminator Series", lambda: self.open_in_chrome("The Terminator", "https://example.com/the-terminator"), "The Terminator Series"),
            ("Fast & Furious Franchise", lambda: self.open_in_chrome("Fast & Furious", "https://example.com/fast-and-furious"), "Fast & Furious Franchise"),
            ("Creed Series", lambda: self.open_in_chrome("Creed", "https://example.com/creed"), "Creed Series"),
            ("Mission: Impossible Series", lambda: self.open_in_chrome("Mission: Impossible", "https://example.com/mission-impossible"), "Mission: Impossible Series"),
        ]
        self.create_button_grid(buttons)

class AnimatedMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Animated Movie Series")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("Pixar Movies", lambda: parent.show_frame(PixarMoviesPage), "Pixar Movies"),
            ("Shrek Series", lambda: parent.show_frame(ShrekSeriesPage), "Shrek Series"),
            ("Cars Series", lambda: parent.show_frame(CarsSeriesPage), "Cars Series"),
            ("Disney Movies Classics", lambda: parent.show_frame(DisneyMoviesClassicsPage), "Disney Movies Classics"),
            ("The Iron Giant", lambda: self.open_in_chrome("The Iron Giant", "https://example.com/the-iron-giant"), "The Iron Giant"),
            ("Rugrats Movies", lambda: parent.show_frame(RugratsMoviesPage), "Rugrats Movies"),
            ("Kung Fu Panda Series", lambda: parent.show_frame(KungFuPandaSeriesPage), "Kung Fu Panda Series"),
            ("Ice Age Series", lambda: parent.show_frame(IceAgeSeriesPage), "Ice Age Series"),
        ]
        self.create_button_grid(buttons)

class PixarMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Pixar Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(AnimatedMoviesPage), "Back"),
            ("Toy Story Series", lambda: parent.show_frame(ToyStorySeriesPage), "Toy Story Series"),
            ("Finding Nemo", lambda: self.open_in_chrome("Finding Nemo", "https://example.com/finding-nemo"), "Finding Nemo"),
            ("Inside Out", lambda: self.open_in_chrome("Inside Out", "https://example.com/inside-out"), "Inside Out"),
            ("Coco", lambda: self.open_in_chrome("Coco", "https://example.com/coco"), "Coco"),
            ("Up", lambda: self.open_in_chrome("Up", "https://example.com/up"), "Up"),
            ("Ratatouille", lambda: self.open_in_chrome("Ratatouille", "https://example.com/ratatouille"), "Ratatouille"),
            ("Wall-E", lambda: self.open_in_chrome("Wall-E", "https://example.com/wall-e"), "Wall-E"),
            ("The Incredibles Series", lambda: parent.show_frame(IncrediblesSeriesPage), "The Incredibles Series"),
        ]
        self.create_button_grid(buttons)

class IncrediblesSeriesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "The Incredibles Series")
        buttons = [
            ("Back", lambda: parent.show_frame(PixarMoviesPage), "Back"),
            ("The Incredibles", lambda: self.open_in_chrome("The Incredibles", "https://example.com/the-incredibles"), "The Incredibles"),
            ("Incredibles 2", lambda: self.open_in_chrome("Incredibles 2", "https://example.com/incredibles-2"), "Incredibles 2"),
        ]
        self.create_button_grid(buttons)

class ToyStorySeriesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Toy Story Series")
        buttons = [
            ("Back", lambda: parent.show_frame(PixarMoviesPage), "Back"),
            ("Toy Story", lambda: self.open_in_chrome("Toy Story", "https://example.com/toy-story"), "Toy Story"),
            ("Toy Story 2", lambda: self.open_in_chrome("Toy Story 2", "https://example.com/toy-story-2"), "Toy Story 2"),
            ("Toy Story 3", lambda: self.open_in_chrome("Toy Story 3", "https://example.com/toy-story-3"), "Toy Story 3"),
            ("Toy Story 4", lambda: self.open_in_chrome("Toy Story 4", "https://example.com/toy-story-4"), "Toy Story 4"),
        ]
        self.create_button_grid(buttons)

class ShrekSeriesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Shrek Series")
        buttons = [
            ("Back", lambda: parent.show_frame(AnimatedMoviesPage), "Back"),
            ("Shrek", lambda: self.open_in_chrome("Shrek", "https://example.com/shrek"), "Shrek"),
            ("Shrek 2", lambda: self.open_in_chrome("Shrek 2", "https://example.com/shrek-2"), "Shrek 2"),
            ("Shrek the Third", lambda: self.open_in_chrome("Shrek the Third", "https://example.com/shrek-the-third"), "Shrek the Third"),
            ("Shrek Forever After", lambda: self.open_in_chrome("Shrek Forever After", "https://example.com/shrek-forever-after"), "Shrek Forever After"),
        ]
        self.create_button_grid(buttons)

class CarsSeriesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Cars Series")
        buttons = [
            ("Back", lambda: parent.show_frame(AnimatedMoviesPage), "Back"),
            ("Cars", lambda: self.open_in_chrome("Cars", "https://example.com/cars"), "Cars"),
            ("Cars 2", lambda: self.open_in_chrome("Cars 2", "https://example.com/cars-2"), "Cars 2"),
            ("Cars 3", lambda: self.open_in_chrome("Cars 3", "https://example.com/cars-3"), "Cars 3"),
        ]
        self.create_button_grid(buttons)

class DisneyMoviesClassicsPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Disney Movies Classics")
        buttons = [
            ("Back", lambda: parent.show_frame(AnimatedMoviesPage), "Back"),
            ("The Lion King", lambda: self.open_in_chrome("The Lion King", "https://example.com/the-lion-king"), "The Lion King"),
            ("Aladdin", lambda: self.open_in_chrome("Aladdin", "https://example.com/aladdin"), "Aladdin"),
            ("Beauty and the Beast", lambda: self.open_in_chrome("Beauty and the Beast", "https://example.com/beauty-and-the-beast"), "Beauty and the Beast"),
            ("The Little Mermaid", lambda: self.open_in_chrome("The Little Mermaid", "https://example.com/the-little-mermaid"), "The Little Mermaid"),
            ("Frozen Series", lambda: parent.show_frame(FrozenSeriesPage), "Frozen Series"),
        ]
        self.create_button_grid(buttons)

class RugratsMoviesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Rugrats Movies")
        buttons = [
            ("Back", lambda: parent.show_frame(AnimatedMoviesPage), "Back"),
            ("The Rugrats Movie", lambda: self.open_in_chrome("The Rugrats Movie", "https://example.com/rugrats-movie"), "The Rugrats Movie"),
            ("Rugrats in Paris", lambda: self.open_in_chrome("Rugrats in Paris", "https://example.com/rugrats-in-paris"), "Rugrats in Paris"),
            ("Rugrats Go Wild", lambda: self.open_in_chrome("Rugrats Go Wild", "https://example.com/rugrats-go-wild"), "Rugrats Go Wild"),
        ]
        self.create_button_grid(buttons)

class FrozenSeriesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Frozen Series")
        buttons = [
            ("Back", lambda: parent.show_frame(DisneyMoviesClassicsPage), "Back"),
            ("Frozen", lambda: self.open_in_chrome("Frozen", "https://example.com/frozen"), "Frozen"),
            ("Frozen II", lambda: self.open_in_chrome("Frozen II", "https://example.com/frozen-ii"), "Frozen II"),
        ]
        self.create_button_grid(buttons)

class KungFuPandaSeriesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Kung Fu Panda Series")
        buttons = [
            ("Back", lambda: parent.show_frame(AnimatedMoviesPage), "Back"),
            ("Kung Fu Panda", lambda: self.open_in_chrome("Kung Fu Panda", "https://example.com/kung-fu-panda"), "Kung Fu Panda"),
            ("Kung Fu Panda 2", lambda: self.open_in_chrome("Kung Fu Panda 2", "https://example.com/kung-fu-panda-2"), "Kung Fu Panda 2"),
            ("Kung Fu Panda 3", lambda: self.open_in_chrome("Kung Fu Panda 3", "https://example.com/kung-fu-panda-3"), "Kung Fu Panda 3"),
        ]
        self.create_button_grid(buttons)

class IceAgeSeriesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Ice Age Series")
        buttons = [
            ("Back", lambda: parent.show_frame(AnimatedMoviesPage), "Back"),
            ("Ice Age", lambda: self.open_in_chrome("Ice Age", "https://example.com/ice-age"), "Ice Age"),
            ("Ice Age: The Meltdown", lambda: self.open_in_chrome("Ice Age: The Meltdown", "https://example.com/ice-age-the-meltdown"), "Ice Age: The Meltdown"),
            ("Ice Age: Dawn of the Dinosaurs", lambda: self.open_in_chrome("Ice Age: Dawn of the Dinosaurs", "https://example.com/ice-age-dawn-of-the-dinosaurs"), "Ice Age: Dawn of the Dinosaurs"),
            ("Ice Age: Continental Drift", lambda: self.open_in_chrome("Ice Age: Continental Drift", "https://example.com/ice-age-continental-drift"), "Ice Age: Continental Drift"),
            ("Ice Age: Collision Course", lambda: self.open_in_chrome("Ice Age: Collision Course", "https://example.com/ice-age-collision-course"), "Ice Age: Collision Course"),
        ]
        self.create_button_grid(buttons)

class ClassicComedyPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Classic Comedy")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("Airplane!", lambda: self.open_in_chrome("Airplane!", "https://example.com/airplane"), "Airplane!"),
            ("Spaceballs", lambda: self.open_in_chrome("Spaceballs", "https://example.com/spaceballs"), "Spaceballs"),
            ("Tommy Boy", lambda: self.open_in_chrome("Tommy Boy", "https://example.com/tommy-boy"), "Tommy Boy"),
            ("The Princess Bride", lambda: self.open_in_chrome("The Princess Bride", "https://example.com/the-princess-bride"), "The Princess Bride"),
            ("There's Something About Mary", lambda: self.open_in_chrome("There's Something About Mary", "https://example.com/something-about-mary"), "There's Something About Mary"),
            ("Wedding Crashers", lambda: self.open_in_chrome("Wedding Crashers", "https://example.com/wedding-crashers"), "Wedding Crashers"),
            ("Dumb and Dumber", lambda: self.open_in_chrome("Dumb and Dumber", "https://example.com/dumb-and-dumber"), "Dumb and Dumber"),
            ("Ferris Bueller's Day Off", lambda: self.open_in_chrome("Ferris Bueller", "https://example.com/ferris-bueller"), "Ferris Bueller's Day Off"),
        ]
        self.create_button_grid(buttons)

class StarWarsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Star Wars")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("Star Wars 1", lambda: self.open_in_chrome("Star Wars 1", "https://example.com/star-wars-1"), "Star Wars 1"),
            ("Star Wars 2", lambda: self.open_in_chrome("Star Wars 2", "https://example.com/star-wars-2"), "Star Wars 2"),
            ("Star Wars 3", lambda: self.open_in_chrome("Star Wars 3", "https://example.com/star-wars-3"), "Star Wars 3"),
            ("Star Wars 4", lambda: self.open_in_chrome("Star Wars 4", "https://example.com/star-wars-4"), "Star Wars 4"),
            ("Star Wars 5", lambda: self.open_in_chrome("Star Wars 5", "https://example.com/star-wars-5"), "Star Wars 5"),
            ("Star Wars 6", lambda: self.open_in_chrome("Star Wars 6", "https://example.com/star-wars-6"), "Star Wars 6"),
            ("Star Wars 7", lambda: self.open_in_chrome("Star Wars 7", "https://example.com/star-wars-7"), "Star Wars 7"),
            ("Star Wars 8", lambda: self.open_in_chrome("Star Wars 8", "https://example.com/star-wars-8"), "Star Wars 8"),
            ("Star Wars 9", lambda: self.open_in_chrome("Star Wars 9", "https://example.com/star-wars-8"), "Star Wars 9"),
        ]
        self.create_button_grid(buttons)

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

class LordOfTheRingsPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Lord of the Rings")
        buttons = [
            ("Back", lambda: parent.show_frame(MoviesPageMenu), "Back"),
            ("The Fellowship of the Ring", lambda: self.open_in_chrome("The Fellowship of the Ring", "https://example.com/fellowship-of-the-ring"), "The Fellowship of the Ring"),
            ("The Two Towers", lambda: self.open_in_chrome("The Two Towers", "https://example.com/the-two-towers"), "The Two Towers"),
            ("The Return of the King", lambda: self.open_in_chrome("The Return of the King", "https://example.com/return-of-the-king"), "The Return of the King"),
        ]
        self.create_button_grid(buttons)

class ShowsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Shows Menu")
        buttons = [
            ("Back", lambda: parent.show_frame(EntertainmentMenuPage), "Back"),
            ("Anime Series", lambda: parent.show_frame(AnimeSeriesPage), "Anime Series"),
            ("90s/2000s Cartoons", lambda: parent.show_frame(Cartoons90sPage), "90s/2000s Cartoons"),
            ("Adult Animated Comedy", lambda: parent.show_frame(AdultAnimatedComedyPage), "Adult Animated Comedy"),
            ("Kids Cartoons", lambda: parent.show_frame(KidsCartoonsPage), "Kids Cartoons"),
            ("Live Nickelodeon Sitcoms", lambda: parent.show_frame(NickelodeonSitcomsPage), "Live Nickelodeon Sitcoms"),
        ]
        self.create_button_grid(buttons)

class AnimeSeriesPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Anime Series")
        buttons = [
            ("Back", lambda: parent.show_frame(ShowsPageMenu), "Back"),
            ("Dragon Ball Z", lambda: self.open_in_chrome("Dragon Ball Z", "https://example.com/dragon-ball-z"), "Dragon Ball Z"),
            ("Dragon Ball GT", lambda: self.open_in_chrome("Dragon Ball GT", "https://example.com/dragon-ball-gt"), "Dragon Ball GT"),
            ("Dragon Ball Super", lambda: self.open_in_chrome("Dragon Ball Super", "https://example.com/dragon-ball-super"), "Dragon Ball Super"),
            ("Pokemon (Original)", lambda: self.open_in_chrome("Pokemon (Original)", "https://example.com/pokemon"), "Pokemon (Original)"),
            ("Jojo's Bizarre Adventure", lambda: self.open_in_chrome("Jojo's Bizarre Adventure", "https://example.com/jojos-bizarre-adventure"), "Jojo's Bizarre Adventure"),
            ("Naruto", lambda: self.open_in_chrome("Naruto", "https://example.com/naruto"), "Naruto"),
            ("One Piece", lambda: self.open_in_chrome("One Piece", "https://example.com/one-piece"), "One Piece"),
            ("Attack on Titan", lambda: self.open_in_chrome("Attack on Titan", "https://example.com/attack-on-titan"), "Attack on Titan"),
        ]
        self.create_button_grid(buttons)

class Cartoons90sPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "90s/2000s Cartoons")
        buttons = [
            ("Back", lambda: parent.show_frame(ShowsPageMenu), "Back"),
            ("Rocket Power", lambda: self.open_in_chrome("Rocket Power", "https://example.com/rocket-power"), "Rocket Power"),
            ("Rugrats", lambda: self.open_in_chrome("Rugrats", "https://example.com/rugrats"), "Rugrats"),
            ("SpongeBob SquarePants", lambda: self.open_in_chrome("SpongeBob SquarePants", "https://example.com/spongebob"), "SpongeBob SquarePants"),
            ("Jimmy Neutron", lambda: self.open_in_chrome("Jimmy Neutron", "https://example.com/jimmy-neutron"), "Jimmy Neutron"),
            ("My Life as a Teenage Robot", lambda: self.open_in_chrome("My Life as a Teenage Robot", "https://example.com/teenage-robot"), "My Life as a Teenage Robot"),
            ("Invader Zim", lambda: self.open_in_chrome("Invader Zim", "https://example.com/invader-zim"), "Invader Zim"),
            ("Spider-Man (90s)", lambda: self.open_in_chrome("Spider-Man (90s)", "https://example.com/spider-man-90s"), "Spider-Man (90s)"),
            ("X-Men", lambda: self.open_in_chrome("X-Men", "https://example.com/x-men"), "X-Men"),
        ]
        self.create_button_grid(buttons)

class AdultAnimatedComedyPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Adult Animated Comedy")
        buttons = [
            ("Back", lambda: parent.show_frame(ShowsPageMenu), "Back"),
            ("Family Guy", lambda: self.open_in_chrome("Family Guy", "https://example.com/family-guy"), "Family Guy"),
            ("American Dad", lambda: self.open_in_chrome("American Dad", "https://example.com/american-dad"), "American Dad"),
            ("Futurama", lambda: self.open_in_chrome("Futurama", "https://example.com/futurama"), "Futurama"),
            ("South Park", lambda: self.open_in_chrome("South Park", "https://example.com/south-park"), "South Park"),
            ("Aqua Teen Hunger Force", lambda: self.open_in_chrome("Aqua Teen Hunger Force", "https://example.com/aqua-teen"), "Aqua Teen Hunger Force"),
            ("Beavis and Butthead", lambda: self.open_in_chrome("Beavis and Butthead", "https://example.com/beavis-and-butthead"), "Beavis and Butthead"),
            ("Rick and Morty", lambda: self.open_in_chrome("Rick and Morty", "https://example.com/rick-and-morty"), "Rick and Morty"),
            ("Hoops", lambda: self.open_in_chrome("Hoops", "https://example.com/hoops"), "Hoops"),
        ]
        self.create_button_grid(buttons)

class KidsCartoonsPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Kids Cartoons")
        buttons = [
            ("Back", lambda: parent.show_frame(ShowsPageMenu), "Back"),
            ("Blue's Clues", lambda: self.open_in_chrome("Blue's Clues", "https://example.com/blues-clues"), "Blue's Clues"),
            ("Dora the Explorer", lambda: self.open_in_chrome("Dora the Explorer", "https://example.com/dora"), "Dora the Explorer"),
            ("Avatar: The Last Airbender", lambda: self.open_in_chrome("Avatar: The Last Airbender", "https://example.com/avatar"), "Avatar: The Last Airbender"),
            ("SpongeBob SquarePants", lambda: self.open_in_chrome("SpongeBob SquarePants", "https://example.com/spongebob"), "SpongeBob SquarePants"),
            ("Jimmy Neutron", lambda: self.open_in_chrome("Jimmy Neutron", "https://example.com/jimmy-neutron"), "Jimmy Neutron"),
            ("Rugrats", lambda: self.open_in_chrome("Rugrats", "https://example.com/rugrats"), "Rugrats"),
            ("Invader Zim", lambda: self.open_in_chrome("Invader Zim", "https://example.com/invader-zim"), "Invader Zim"),
            ("My Life as a Teenage Robot", lambda: self.open_in_chrome("My Life as a Teenage Robot", "https://example.com/teenage-robot"), "My Life as a Teenage Robot"),
        ]
        self.create_button_grid(buttons)

class NickelodeonSitcomsPage(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Live Nickelodeon Sitcoms")
        buttons = [
            ("Back", lambda: parent.show_frame(ShowsPageMenu), "Back"),
            ("Drake and Josh", lambda: self.open_in_chrome("Drake and Josh", "https://example.com/drake-and-josh"), "Drake and Josh"),
            ("iCarly", lambda: self.open_in_chrome("iCarly", "https://example.com/icarly"), "iCarly"),
            ("Victorious", lambda: self.open_in_chrome("Victorious", "https://example.com/victorious"), "Victorious"),
            ("Zoey 101", lambda: self.open_in_chrome("Zoey 101", "https://example.com/zoey-101"), "Zoey 101"),
            ("Ned's Declassified School Survival Guide", lambda: self.open_in_chrome("Ned's Declassified", "https://example.com/neds-declassified"), "Ned's Declassified School Survival Guide"),
            ("Sam and Cat", lambda: self.open_in_chrome("Sam and Cat", "https://example.com/sam-and-cat"), "Sam and Cat"),
            ("The Amanda Show", lambda: self.open_in_chrome("The Amanda Show", "https://example.com/amanda-show"), "The Amanda Show"),
            ("The Thundermans", lambda: self.open_in_chrome("The Thundermans", "https://example.com/thundermans"), "The Thundermans"),
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