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
            speak_queue.task_done()  # Mark the None task as done before breaking
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
        
class KeySequenceListener:
    def __init__(self, app):
        self.app = app
        self.sequence = ["space", "space", "space"]  # Define the key sequence
        self.current_index = 0
        self.last_key_time = None
        self.timeout = 8  # Timeout for completing the sequence (seconds)
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
            
# Create main app window
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

        self.spacebar_pressed = False
        self.long_spacebar_pressed = False
        self.start_time = 0
        self.backward_time_delay = 2.5 # Delay in seconds when long holding space

        # Bind keys for scanning and selecting
        self.bind("<KeyPress-space>", self.track_spacebar_hold)
        self.bind("<KeyRelease-space>", self.reset_spacebar_hold)
        self.bind("<KeyRelease-Return>", self.select_button)

        # Ensure the app is in focus
        print("Initializing the main menu...")
        self.show_frame(HomePageMenu)

        # Start key sequence listener
        self.sequencer = KeySequenceListener(self)

        # Minimize terminal
        minimize_terminal()

        # Start spacebar hold tracking in a separate thread
        threading.Thread(target=self.monitor_spacebar_hold, daemon=True).start()

    def monitor_spacebar_hold(self):
        while True:
            if self.spacebar_pressed and (time.time() - self.start_time >= 4):
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

    def scan_backward(self):
        """Move to the previous button and highlight it."""
        if self.buttons:
            # Move to the next button in the list
            self.current_button_index = len(self.buttons) - 1 if (self.current_button_index - 1) <= -1 else (self.current_button_index - 1)

            # Highlight the new button
            self.highlight_button(self.current_button_index)

            # Speak the button's text for HomePageMenu and StreamingShowsPageMenu
            if isinstance(self.current_frame, (HomePageMenu, StreamingShowsPageMenu, AnimePageMenu, CartoonsPageMenu, ComedyPageMenu, NickelodeonPageMenu, MoviesPageMenu, FantasyPageMenu, StarWarsPageMenu, SpiderManPageMenu)):
                speak(self.buttons[self.current_button_index]["text"])

    def scan_forward(self, event=None):
        """Advance to the next button and highlight it upon spacebar release."""
        if self.buttons:
            # Move to the next button in the list
            self.current_button_index = (self.current_button_index + 1) % len(self.buttons)

            # Highlight the new button
            self.highlight_button(self.current_button_index)

            # Speak the button's text for HomePageMenu and StreamingShowsPageMenu
            if isinstance(self.current_frame, (HomePageMenu, StreamingShowsPageMenu, AnimePageMenu, CartoonsPageMenu, ComedyPageMenu, NickelodeonPageMenu, MoviesPageMenu, FantasyPageMenu, StarWarsPageMenu, SpiderManPageMenu)):
                speak(self.buttons[self.current_button_index]["text"])

    def select_button(self, event=None):
        """Select the currently highlighted button upon Enter key release with debounce."""
        if self.selection_enabled and self.buttons:
            self.selection_enabled = False  # Disable selection temporarily
            self.buttons[self.current_button_index].invoke()  # Invoke the button action
            threading.Timer(1, self.enable_selection).start()  # Re-enable selection after 1 seconds

            self.sequencer.current_index = 0
            self.sequencer.last_key_time = None

    def enable_selection(self):
        """Re-enable button selection after the debounce interval."""
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
                grid_frame, text=text, font=("Arial", 24), bg="light blue", fg="black",
                activebackground="yellow", activeforeground="black",
                command=lambda c=command, s=speak_text: self.on_select(c, s)
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            self.buttons.append(btn)  # Add button to scanning list

        for i in range(rows):
            grid_frame.rowconfigure(i, weight=1)
        for j in range(cols):
            grid_frame.columnconfigure(j, weight=1)

    def on_select(self, command, speak_text):
        command()
        if speak_text:
            speak(speak_text)
            
    def open_in_chrome(self, url):
        """Open the given URL in Chrome."""
        try:
            if platform.system() == "Windows":
                subprocess.run(["start", "chrome", url], shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-a", "Google Chrome", url])
            elif platform.system() == "Linux":
                subprocess.run(["google-chrome", url])
            else:
                print("Unsupported platform for opening URLs.")
        except Exception as e:
            print(f"Error opening URL: {e}")

# Define Menu Classes
class HomePageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Home")
        buttons = [
            ("Basic", lambda: self.parent.show_frame(BasicPageMenu), "Basic"),
            ("Needs", lambda: self.parent.show_frame(NeedsPageMenu), "Needs"),
            ("Feelings", lambda: self.parent.show_frame(FeelingsPageMenu), "Feelings"),
            ("Conversation", lambda: self.parent.show_frame(ConversationPageMenu), "Conversation"),
            ("Questions", lambda: self.parent.show_frame(QuestionsPageMenu), "Questions"),
            ("Quotes & Misc", lambda: self.parent.show_frame(QuotesPageMenu), "Quotes & Misc"),
            ("Rating", lambda: self.parent.show_frame(RatingPageMenu), "Rating"),
            ("Twitch", lambda: self.parent.show_frame(TwitchPageMenu), "Twitch"),
            ("Streaming Shows", lambda: self.parent.show_frame(StreamingShowsPageMenu), "Streaming Shows"),
        ]
        self.create_button_grid(buttons)

class BasicPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Basic")
        buttons = [
            ("Back", lambda: self.parent.show_frame(HomePageMenu), None),  # Add Back button
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
            ("Back", lambda: self.parent.show_frame(HomePageMenu), None),  # Add Back button
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
            ("Back", lambda: self.parent.show_frame(HomePageMenu), None),  # Add Back button
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
            ("Back", lambda: self.parent.show_frame(HomePageMenu), None),  # Add Back button
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
            ("Back", lambda: self.parent.show_frame(HomePageMenu), None),  # Add Back button
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
            ("Back", lambda: self.parent.show_frame(HomePageMenu), None),  # Add Back button
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
            ("Back", lambda: self.parent.show_frame(HomePageMenu), None),  # Add Back button
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
            ("Back", lambda: self.parent.show_frame(HomePageMenu), None),  # Add Back button
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

class StreamingShowsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Streaming Shows")
        buttons = [
            ("Back", lambda: parent.show_frame(HomePageMenu), None),
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
            ("Avatar", lambda: self.open_in_chrome("https://www.netflix.com/watch/70136344?trackId=14188376"), "Avatar"),
            ("Pokemon", lambda: self.open_in_chrome("https://www.netflix.com/watch/70295998?trackId=14170286"), "Pokemon"),
            ("Dragon Ball Z", lambda: self.open_in_chrome("https://www.hulu.com/watch/ed6a5ead-0ebc-4b61-b05a-9d2d0aaf8fff"), "Dragon Ball Z"),
            ("Dragon Ball Super", lambda: self.open_in_chrome("https://www.hulu.com/watch/32385ddb-b6fa-425a-ae79-ffe0298f2446"), "Dragon Ball Super"),
            ("Dragon Ball Super Broly", lambda: self.open_in_chrome("https://www.hulu.com/watch/dea31115-06f7-4a02-ab60-c00e36f1f378"), "Dragon Ball Super Broly"),
            ("Yu-Gi-Oh", lambda: self.open_in_chrome("https://www.hulu.com/watch/a7a2805c-7d67-4cdc-86b3-721c11f85a73"), "Yu-Gi-Oh"),
            ("DigiMon", lambda: self.open_in_chrome("https://www.hulu.com/watch/aa9603ec-3688-4e02-b461-1fa4f407fbe9"), "DigiMon"),
            ("DBZ Abridged", lambda: self.open_in_chrome("https://www.youtube.com/watch?v=aRiHUsIY_bE&pp=ygUZZHJhZ29uYmFsbCB6IGFicmlkZ2UgZnVsbA%3D%3D"), "DBZ Abridged"),
        ]
        self.create_button_grid(buttons)

import pyautogui
import time

class CartoonsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Cartoons")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("Family Guy", lambda: self.open_in_chrome("https://www.hulu.com/watch/e3e44e69-6b56-44e9-b083-cbcb7c9730a5"), "Family Guy"),
            ("Futurama", lambda: self.open_in_chrome("https://www.hulu.com/watch/c3728d56-fbfc-4509-a16d-19857f8b1daa"), "Futurama"),
            ("South Park", lambda: self.open_in_chrome("https://play.max.com/video/watch/cf46936d-0a68-4a0b-aa2d-4a3a131be881"), "South Park"),
            ("The Simpsons", lambda: self.open_in_chrome("https://www.disneyplus.com/play/ffb14e5a-38db-4522-a559-3cfa52bcf4df"), "The Simpsons"),
            ("Bobs Burgers", lambda: self.open_in_chrome("https://www.hulu.com/watch/ed5bdafa-0eee-4f10-8675-5cd8afc7780f"), "Bob's Burgers"),
            ("Aqua Teen", lambda: self.open_in_chrome("https://play.max.com/video/watch/9c2a7469-5089-4229-9278-d1768494166b"), "Aqua Teen"),
            ("Rick and Morty", lambda: self.open_in_chrome("https://www.hulu.com/watch/f88cfbf8-c514-4126-a3ee-da0413f79af6"), "Rick and Morty"),
            ("Cartoons", lambda: self.open_and_click("https://www.paramountplus.com/live-tv/stream/channels/adult-animation/OwFn_OQhGr_vm7uE077Slr_apTPYyoFM/#"), "Cartoons"),
        ]
        self.create_button_grid(buttons)
        
    def open_and_click(self, url, x_offset=0, y_offset=0):
        """Open the given URL, click on the specified position, and ensure fullscreen mode."""
        self.open_in_chrome(url)
        time.sleep(5)  # Wait for the browser to open and load
        
        # Bring the browser window to the foreground
        hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        
        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        
        # Calculate click position with offsets
        click_x = (screen_width // 2) + x_offset
        click_y = (screen_height // 2) + y_offset
        
        # Perform the click
        pyautogui.click(click_x, click_y)
        print(f"Clicked at position: ({click_x}, {click_y})")
        
        # Re-enable fullscreen mode
        time.sleep(1)  # Small delay before sending F11
        pyautogui.press('f11')
        print("Fullscreen mode toggled.")

        
class ComedyPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Comedy")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("Jeff Dunham 2017", lambda: self.open_in_chrome("https://www.netflix.com/watch/80158670?trackId=255824129"), "Jeff Dunham 2017"),
            ("Jeff Dunham 2019", lambda: self.open_in_chrome("https://www.netflix.com/watch/81074113?trackId=255824129"), "Jeff Dunahm 2019"),
            ("Tom Segura 2016", lambda: self.open_in_chrome("https://www.netflix.com/watch/80077923"), "Tom Segura 2016"),
            ("Tom Segura 2018", lambda: self.open_in_chrome("https://www.netflix.com/watch/80187307"), "Tom Segura 2018"),
            ("Tom Segura 2020", lambda: self.open_in_chrome("https://www.netflix.com/watch/81143584"), "Tom Segura 2020"),
            ("Tom Segura 2023", lambda: self.open_in_chrome("https://www.netflix.com/watch/81605926"), "Tom Segura 2023"),
            ("Standup", lambda: self.open_in_chrome("https://youtu.be/ctyzvJLoid0"), "Standup"),
            ("After Dark", lambda: self.open_in_chrome("https://www.youtube.com/watch?v=BAV48j4ubJg"), "Laugh After Dark"),
        ]
        self.create_button_grid(buttons)

import pyautogui
import time

class NickelodeonPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Nickelodeon")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("iCarly", lambda: self.open_and_click("https://www.paramountplus.com/shows/video/_i3rbgwWS2D0DoNTKea72VSK3A_5ui4C/"), "iCarly"),
            ("Sam and Cat", lambda: self.open_in_chrome("https://www.netflix.com/watch/80027804?trackId=255824129"), "Sam and Cat"),
            ("Victorious", lambda: self.open_and_click("https://www.paramountplus.com/shows/video/8kmpIwDkzJgV_bFy2on1GzqP90K4dRLS/"), "Victorious"),
            ("Drake & Josh", lambda: self.open_and_click("https://www.paramountplus.com/shows/video/tVMt3l8M0EwRBcnSmrF2xPqDtxk4_m2c/"), "Drake & Josh"),
            ("Rugrats", lambda: self.open_and_click("https://www.paramountplus.com/shows/video/uOkB1qnYXZXeAM34djVYNHje2_gK4mmO/"), "Rugrats"),
            ("Sponge Bob", lambda: self.open_and_click("https://www.paramountplus.com/shows/video/ZvEow_nZm5WAiLeMlEmISm3Deti40Ciu/"), "Sponge Bob"),
            ("Blues Clues", lambda: self.open_and_click("https://www.paramountplus.com/shows/video/YZqYwu9sJNARDyM1huzbEwC5jzeW6sXB/"), "Blues Clues"),
            ("Nikelodeon", lambda: self.open_and_click("https://www.paramountplus.com/live-tv/stream/channels/kids-family-fun/jK9BvWTFtIm356HTdbDdfAzqlgzOlFtD/"), "Nickelodeon Stream"),
        ]
        self.create_button_grid(buttons)
        
    def open_and_click(self, url, x_offset=0, y_offset=0):
        """Open the given URL, click on the specified position, and ensure fullscreen mode."""
        self.open_in_chrome(url)
        time.sleep(5)  # Wait for the browser to open and load
        
        # Bring the browser window to the foreground
        hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        
        # Get screen dimensions
        screen_width, screen_height = pyautogui.size()
        
        # Calculate click position with offsets
        click_x = (screen_width // 2) + x_offset
        click_y = (screen_height // 2) + y_offset
        
        # Perform the click
        pyautogui.click(click_x, click_y)
        print(f"Clicked at position: ({click_x}, {click_y})")
        
        # Re-enable fullscreen mode
        time.sleep(1)  # Small delay before sending F11
        pyautogui.press('f11')
        print("Fullscreen mode toggled.")

        
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
            ("Happy Gilmore", lambda: self.open_in_chrome("https://www.disneyplus.com/play/bf5b0d1a-b99b-492b-9748-86ff5a0669dc?distributionPartner=google"), "Happy Gilmore"),
            ("The Hot Chick", lambda: self.open_in_chrome("https://www.hulu.com/watch/453bd143-b501-49d2-88b7-3fc87979e50b"), "The Hot Chick"),
            ("Billy Madison", lambda: self.open_in_chrome("https://www.disneyplus.com/play/0f6de803-ca80-4128-b39a-73b1e7304db1"), "Billy Madison"),
            ("Deadpool 1", lambda: self.open_in_chrome("https://www.disneyplus.com/play/17854bdb-0121-4327-80a0-699fdecd1aaa"), "Deadpool 1"),
            ("Deadpool 2", lambda: self.open_in_chrome("https://www.disneyplus.com/play/bdcd5a83-ad6e-428f-8c34-63a9cf695048"), "Deadpool 2"),
            ("Deadpool and Wolverine", lambda: self.open_in_chrome("https://www.disneyplus.com/play/120ae1e6-2240-4924-a4ce-f8de6e28b0b1"), "Deadpool and Wolverine"),
            ("Comedy Movies", lambda: self.open_pluto("https://pluto.tv/us/live-tv/5a4d3a00ad95e4718ae8d8db"), "Comedy Stream"),
            ("Action Movies", lambda: self.open_pluto("https://pluto.tv/us/live-tv/561d7d484dc7c8770484914a"), "Action Stream"),
        ]
        self.create_button_grid(buttons)

    def open_pluto(self, url):
        """Open Pluto TV link in Chrome, unmute, and fullscreen using robust key simulation."""
        self.open_in_chrome(url)  # Open the Pluto.TV link in Chrome
        time.sleep(5)  # Allow time for the browser and video player to load

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

        
class FantasyPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Fantasy")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("LOTR: Fellowship", lambda: self.open_in_chrome("https://play.max.com/video/watch/26d05bd3-2f25-4f7d-b7de-8caa0610fd06/c99d6146-ac31-4dc9-9957-bd99e95a48d8"), "The Fellowship of the Ring"),
            ("LOTR: Two Towers ", lambda: self.open_in_chrome("https://play.max.com/video/watch/2028f0f5-d18c-4a9d-8107-1e49d944e744/a82c4890-04e6-489e-97d8-b83d65dcbdbd"), "The Two Towers"),
            ("LOTR: Return of the King", lambda: self.open_in_chrome("https://play.max.com/video/watch/cfcbf3f2-3d0c-499f-b46f-9747b70efbbb/5284b373-2b7e-467e-baa6-d245d34dcf1a"), "Return of the King"),
            ("The Hobbit", lambda: self.open_in_chrome("https://play.max.com/video/watch/ad742ea8-0ba9-49c9-830a-5487e3728513/e7f9460f-f5fb-4e0e-95f1-3c2df66f2647"), "An Unexpected Journey"),
            ("The Hobbit 2", lambda: self.open_in_chrome("https://play.max.com/video/watch/072b9f21-8d3d-4da6-9061-5e2c9261c046/0ee2f5da-bbc5-4883-8339-c6998474f730"), "The Desolation of Smaug"),
            ("The Hobbit 3", lambda: self.open_in_chrome("https://play.max.com/video/watch/388607c1-85cf-4feb-872d-087d0f26d9fd/f2ef861f-ea19-422d-b29e-cbc8624b8cd2"), "Battle of the Five Armies"),
            ("Narnia 1", lambda: self.open_in_chrome("https://www.disneyplus.com/play/6b59eb41-8660-4d93-bc42-9521bebb47a3"), "Narnia"),
            ("Narnia 2", lambda: self.open_in_chrome("https://www.disneyplus.com/play/cfd042fc-db6e-43b6-b1b8-588624349f92"), "Narnia 2"),
        ]
        self.create_button_grid(buttons)


class StarWarsPageMenu(MenuFrame):
    def __init__(self, parent):
        super().__init__(parent, "Star Wars")
        buttons = [
            ("Back", lambda: parent.show_frame(StreamingShowsPageMenu), None),
            ("A New Hope", lambda: self.open_in_chrome("https://www.disneyplus.com/play/9a280e53-fcc0-4e17-a02c-b1f40913eb0b"), "A New Hope"),
            ("The Empire Strikes Back", lambda: self.open_in_chrome("https://www.disneyplus.com/play/0f5c5223-f4f6-46ef-ba8a-69cb0e17d8d3"), "The Empire Strikes Back"),
            ("Return of the Jedi", lambda: self.open_in_chrome("https://www.disneyplus.com/play/4b6e7cda-daa5-4f2d-9b61-35bbe562c69c"), "Return of the Jedi"),
            ("The Phantom Menace", lambda: self.open_in_chrome("https://www.disneyplus.com/play/e0a9fee4-2959-4077-ad8c-8fab4fd6e4d1"), "The Phantom Menace"),
            ("Attack of the Clones", lambda: self.open_in_chrome("https://www.disneyplus.com/play/39cbdf17-1bbe-4de2-b4a4-8e342875c2c6"), "Attack of the Clones"),
            ("Revenge of the Sith", lambda: self.open_in_chrome("https://www.disneyplus.com/play/eb1e2c5f-69bf-4240-a61f-7ffc4e0311b3"), "Revenge of the Sith"),
            ("The Force Awakens", lambda: self.open_in_chrome("https://www.disneyplus.com/play/2854a94d-3702-40bd-97a4-12d55a809188"), "The Force Awakens"),
            ("The Last Jedi", lambda: self.open_in_chrome("https://www.disneyplus.com/play/50c1aff5-3051-4839-9ebf-e332c635e216"), "The Last Jedi"),
            ("The Rise of Skywalker", lambda: self.open_in_chrome("https://www.disneyplus.com/play/43f9c275-e7e8-4ab3-802d-00d06a8ad841"), "The Rise of Skywalker"),
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
                grid_frame, text=text, font=("Arial", 24), bg="light blue", fg="black",
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
            ("Spider-Man (2002)", lambda: self.open_in_chrome("https://www.disneyplus.com/play/0043a9c8-7e34-44e0-8128-e9419ae58868"), "Spider-Man (2002)"),
            ("Spider-Man 2", lambda: self.open_in_chrome("https://www.disneyplus.com/play/25ec8dd6-e574-45fa-9a62-97396cdfaf68"), "Spider-Man 2"),
            ("Spider-Man 3", lambda: self.open_in_chrome("https://www.disneyplus.com/play/5faa8ff9-91f6-4130-8357-afbe087cb8a4"), "Spider-Man 3"),
            ("The Amazing Spider-Man", lambda: self.open_in_chrome("https://www.disneyplus.com/play/f43ffe63-2c96-4b6c-8fae-84d0d22d6466"), "The Amazing Spider-Man"),
            ("The Amazing Spider-Man 2", lambda: self.open_in_chrome("https://www.disneyplus.com/play/c21c733a-18f4-4cdc-b1e8-1ff6b996c0a3"), "The Amazing Spider-Man 2"),
            ("Spider-Man: Homecoming", lambda: self.open_in_chrome("https://www.disneyplus.com/play/5b2b999a-045e-4d89-af52-390c257178db"), "Spider-Man: Homecoming"),
            ("Spider-Man: Far From Home", lambda: self.open_in_chrome("https://www.disneyplus.com/play/2ca3cca0-bd2b-4934-93c0-c03d27fb249e"), "Spider-Man: Far From Home"),
            ("Spider-Man", lambda: self.open_in_chrome("https://youtu.be/dtxfJD60FCQ"), "Spider-Man Stream"),
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