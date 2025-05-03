#################################
# CSC 102 Defuse the Bomb Project
# GUI and Phase class definitions
# Team: 
#################################

from bomb_configs import RPi, OFF, Pull
# other imports
from tkinter import *
import tkinter
from threading import Thread
from time import sleep
from adafruit_ht16k33.segments import Seg7x4  # Import the 7-segment display library
import os, sys

if RPi:
    import digitalio, board
#########
# classes
#########
# the LCD display GUI
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg="black")
        # make the GUI fullscreen
        window.attributes("-fullscreen", True)
        # we need to know about the timer (7-segment display) to be able to pause/unpause it
        self._timer = None
        # we need to know about the pushbutton to turn off its LED when the program exits
        self._button = None
        # setup the initial "boot" GUI
        self.setupBoot()

    # sets up the LCD "boot" GUI
    def setupBoot(self):
        # set column weights
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)
        # the scrolling informative "boot" text
        self._lscroll = Label(self, bg="black", fg="white", font=("Courier New", 14), text="", justify=LEFT)
        self._lscroll.grid(row=0, column=0, columnspan=3, sticky=W)
        self.pack(fill=BOTH, expand=True)

    # sets up the LCD GUI
    def setup(self):
        # the timer
        self._ltimer = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Time left: ")
        self._ltimer.grid(row=1, column=0, columnspan=3, sticky=W)
        # the keypad passphrase
        self._lkeypad = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Keypad phase: ")
        self._lkeypad.grid(row=2, column=0, columnspan=3, sticky=W)
        # the jumper wires status
        self._lwires = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Wires phase: ")
        self._lwires.grid(row=3, column=0, columnspan=3, sticky=W)
        # the pushbutton status
        self._lbutton = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Button phase: ")
        self._lbutton.grid(row=4, column=0, columnspan=3, sticky=W)
        # the toggle switches status
        self._ltoggles = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Toggles phase: ")
        self._ltoggles.grid(row=5, column=0, columnspan=2, sticky=W)
        # the strikes left
        self._lstrikes = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Strikes left: ")
        self._lstrikes.grid(row=5, column=2, sticky=W)
        if (SHOW_BUTTONS):
            # the pause button (pauses the timer)
            self._bpause = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Pause", anchor=CENTER, command=self.pause)
            self._bpause.grid(row=6, column=0, pady=40)
            # the quit button
            self._bquit = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Quit", anchor=CENTER, command=self.quit)
            self._bquit.grid(row=6, column=2, pady=40)

    # lets us pause/unpause the timer (7-segment display)
    def setTimer(self, timer):
        self._timer = timer

    # lets us turn off the pushbutton's RGB LED
    def setButton(self, button):
        self._button = button

    # pauses the timer
    def pause(self):
        if (RPi):
            self._timer.pause()

    # setup the conclusion GUI (explosion/defusion)
    def conclusion(self, success=False):
        # destroy/clear widgets that are no longer needed
        self._lscroll["text"] = ""
        self._ltimer.destroy()
        self._lkeypad.destroy()
        self._lwires.destroy()
        self._lbutton.destroy()
        self._ltoggles.destroy()
        self._lstrikes.destroy()
        if (SHOW_BUTTONS):
            self._bpause.destroy()
            self._bquit.destroy()

        # reconfigure the GUI
        # the retry button
        self._bretry = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Retry", anchor=CENTER, command=self.retry)
        self._bretry.grid(row=1, column=0, pady=40)
        # the quit button
        self._bquit = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Quit", anchor=CENTER, command=self.quit)
        self._bquit.grid(row=1, column=2, pady=40)

    # re-attempts the bomb (after an explosion or a successful defusion)
    def retry(self):
        # re-launch the program (and exit this one)
        os.execv(sys.executable, ["python3"] + [sys.argv[0]])
        exit(0)

    # quits the GUI, resetting some components
    def quit(self):
        if (RPi):
            # turn off the 7-segment display
            self._timer._running = False
            self._timer._component.blink_rate = 0
            self._timer._component.fill(0)
            # turn off the pushbutton's LED
            for pin in self._button._rgb:
                pin.value = True
        # exit the application
        exit(0)

# template (superclass) for various bomb components/phases
class PhaseThread(Thread):
    def __init__(self, name, component=None, target=None):
        super().__init__(name=name, daemon=True)
        # phases have an electronic component (which usually represents the GPIO pins)
        self._component = component
        # phases have a target value (e.g., a specific combination on the keypad, the proper jumper wires to "cut", etc)
        self._target = target
        # phases can be successfully defused
        self._defused = False
        # phases can be failed (which result in a strike)
        self._failed = False
        # phases have a value (e.g., a pushbutton can be True/Pressed or False/Released, several jumper wires can be "cut"/False, etc)
        self._value = None
        # phase threads are either running or not
        self._running = False

# the timer phase
class Timer(PhaseThread):
    def __init__(self, component, initial_value=600, failure_callback=None, name="Timer"):
        super().__init__(name, component)
        self._value = initial_value  # countdown in seconds
        self._paused = False
        self._interval = 1
        self._min = ""
        self._sec = ""
        self._running = False
        self._component = component
        self._failure_callback = failure_callback  # Function to call when time runs out

    def run(self):
        self._running = True
        while self._running:
            if not self._paused:
                self._update() # Update minutes and seconds
                self._component.print(str(self)) # Display to the 7-segment display
                sleep(self._interval)
                if self._value == 0:
                    self._running = False
                    if self._failure_callback:
                        self._failure_callback()
                    break
                self._value -= 1
            else:
                sleep(0.1)

    def _update(self):
        """Update the minutes and seconds for the countdown."""
        self._min, self._sec = divmod(self._value, 60)
        self._min = str(self._min).zfill(2)  # Pad with zeros for formatting
        self._sec = str(self._sec).zfill(2)
        
    def pause(self):
        self._paused = not self._paused
        self._component.blink_rate = 2 if self._paused else 0

    def stop(self):
        self._running = False

    def __str__(self):
        return f"{self._min}:{self._sec}"


# the keypad phase
class Keypad(PhaseThread):
    def __init__(self, component, target, name="Keypad"):
        super().__init__(name, component, target)
        # the default value is an empty string
        self._value = ""

    # runs the thread
    def run(self):
        self._running = True
        while (self._running):
            # process keys when keypad key(s) are pressed
            if (self._component.pressed_keys):
                # debounce
                while (self._component.pressed_keys):
                    try:
                        # just grab the first key pressed if more than one were pressed
                        key = self._component.pressed_keys[0]
                    except:
                        key = ""
                    sleep(0.1)
                # log the key
                self._value += str(key)
                # the combination is correct -> phase defused
                if (self._value == self._target):
                    self._defused = True
                # the combination is incorrect -> phase failed (strike)
                elif (self._value != self._target[0:len(self._value)]):
                    self._failed = True
            sleep(0.1)

    # returns the keypad combination as a string
    def __str__(self):
        if (self._defused):
            return "DEFUSED"
        else:
            return self._value

# the jumper wires phase
class Wires(PhaseThread):
    def __init__(self, component, target, name="Wires"):
        super().__init__(name, component, target)
        self._value = []

    # runs the thread
    def run(self):
        self._running = True
        while self._running:
            # Assume component.cuts is list of cut wire identifiers
            current = list(self._component.cuts)
            self._value = current
            # correct set of wires cut => defused
            if set(current) == set(self._target):
                self._defused = True
                self._running = False
            # if any incorrect wire cut => fail
            elif any(w not in self._target for w in current):
                self._failed = True
                self._running = False
            sleep(0.1)
        

    # returns the jumper wires state as a string
    def __str__(self):
        return "DEFUSED" if self._defused else ",".join(map(str, self._value))


class Button(PhaseThread):
    def __init__(self, state_pin, rgb_pins, name="Button", flashes_per_sec=10):
        super().__init__(name)
        self._state_pin = state_pin
        self._r, self._g, self._b = rgb_pins
        self._hz = flashes_per_sec
        self._easy_mode = None

        if RPi:
            # Button wired between GPIO and 3.3 V → use pull-down
            self._state_pin.switch_to_input(pull=Pull.DOWN)
            # start with LED off
            for p in (self._r, self._g, self._b):
                p.switch_to_output(value=OFF)

    def run(self):
        self._running = True

        # name the flashes
        GREEN     = (OFF, ON,  OFF)
        OFF_COLOR = (OFF, OFF, OFF)
        RED       = (ON,  OFF, OFF)
        FLASHES   = [GREEN, OFF_COLOR, RED, OFF_COLOR]

        interval = 1 / self._hz
        idx      = 0

        while self._running and self._easy_mode is None:
            # 1) show this flash
            self._r.value, self._g.value, self._b.value = FLASHES[idx]

            # 2) read the button (HIGH = pressed under Pull.DOWN)
            pressed = RPi and self._state_pin.value

            if pressed:
                # did we catch green or red?
                is_green = (FLASHES[idx] == GREEN)
                # green → easy, red → hard
                self._easy_mode = is_green
                self._defused   = True

                # hold that color so it’s visible
                sleep(3)
                break

            # 3) advance & wait
            idx = (idx + 1) % len(FLASHES)
            sleep(interval)

        self._running = False

    def __str__(self):
        if self._defused:
            return "GREEN-easy" if self._easy_mode else "RED-hard"
        return "Pressed" if (RPi and not self._state_pin.value) else "Released"

class MazeToggles(PhaseThread):
    def __init__(self, component, name="MazeToggles"):
        super().__init__(name, component)
        self._value = ""                # will hold e.g. "1100"
        self._current_direction = None
        self._defused = False
        self._failed  = False
        self._running = False
        self._target_direction = None

    def set_target(self, direction):
        self._target_direction = direction

    def get_direction(self):
        return self._current_direction

    def run(self):
        # define the exact mapping from 4-bit code → direction
        mapping = {
            "1000": "North",
            "1100": "East",
            "1110": "South",
            "1111": "West"
        }

        self._running = True
        while self._running:
            # read the raw pin values (0/1) into a string, just like bomb_test.py does:
            code = "".join(str(int(pin.value)) for pin in self._component.toggles)
            self._value = code

            # map it to a direction (or None if it’s not one of our 4 patterns)
            self._current_direction = mapping.get(code)

            # check against the target
            if self._current_direction == self._target_direction:
                self._defused = True
                self._running = False
            elif self._current_direction is not None:
                self._failed = True
                self._running = False

            sleep(0.1)


# Function for handling the Twilight Passage challenge
def twilight_passage(window, toggles):
    """
    Screen for the Twilight Passage phase, where the player must flip the correct toggle to proceed.
    """
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window,
             text="🌌 Twilight Passage",
             font=("Helvetica", 24, "bold"),
             fg="#00ffcc",
             bg="#1e1e2f").pack(pady=(40, 10))

    tk.Label(window,
             text="You're facing NORTH. Flip the correct toggle to turn SOUTH and proceed.",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=20)

    direction_label = tk.Label(window, text="Current Direction: None",
                                font=("Helvetica", 16), fg="#00ffcc", bg="#1e1e2f")
    direction_label.pack(pady=20)

    # Function to update the direction label and check the toggle state
    def update_direction():
        direction = toggles.get_direction()
        if direction:
            direction_label.config(text=f"Current Direction: {direction}")
        else:
            direction_label.config(text="Current Direction: None")

        # Check if the direction is correct
        if toggles._defused:
            tk.Label(window,
                     text="🎉 Correct! You turned SOUTH and moved to the next challenge.",
                     font=("Helvetica", 16), fg="green", bg="#1e1e2f").pack(pady=20)
            window.after(2000, lambda: forgotten_fortress(window))  # Proceed to the next phase
        elif toggles._failed:
            tk.Label(window,
                     text="❌ Wrong toggle! Try again.",
                     font=("Helvetica", 16), fg="red", bg="#1e1e2f").pack(pady=20)

    # Continuously poll the toggles
    def poll_toggles():
        update_direction()
        if toggles._running:
            window.after(100, poll_toggles)

    poll_toggles()

# Function for handling the Forgotten Fortress challenge
def forgotten_fortress(window, toggles):
    """
    Screen for the Forgotten Fortress phase, where the player must flip the correct toggle to move West.
    """
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window,
             text="🏰 Forgotten Fortress",
             font=("Helvetica", 24, "bold"),
             fg="#00ffcc",
             bg="#1e1e2f").pack(pady=(40, 10))

    tk.Label(window,
             text="Hint: Move in the direction where the sun sets.",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=20)

    direction_label = tk.Label(window, text="Current Direction: None",
                                font=("Helvetica", 16), fg="#00ffcc", bg="#1e1e2f")
    direction_label.pack(pady=20)

    toggles.set_target("West")  # Set the target direction for this challenge

    # Function to update the direction label and check the toggle state
    def update_direction():
        direction = toggles.get_direction()
        if direction:
            direction_label.config(text=f"Current Direction: {direction}")
        else:
            direction_label.config(text="Current Direction: None")

        # Check if the direction is correct
        if toggles._defused:
            tk.Label(window,
                     text="🎉 Correct! You moved West and encountered a power barrier.",
                     font=("Helvetica", 16), fg="green", bg="#1e1e2f").pack(pady=20)
            window.after(2000, lambda: wire_puzzle(window))  # Proceed to the wire puzzle
        elif toggles._failed:
            tk.Label(window,
                     text="❌ Wrong toggle! Try again.",
                     font=("Helvetica", 16), fg="red", bg="#1e1e2f").pack(pady=20)

    # Continuously poll the toggles
    def poll_toggles():
        update_direction()
        if toggles._running:
            window.after(100, poll_toggles)

    poll_toggles()


# Function for handling the Phantom's Lair challenge
def phantom_lair(window, toggles):
    """
    Screen for the Phantom's Lair phase, where the player must flip the correct toggle to move East.
    """
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window,
             text="👻 Phantom's Lair",
             font=("Helvetica", 24, "bold"),
             fg="#00ffcc",
             bg="#1e1e2f").pack(pady=(40, 10))

    tk.Label(window,
             text="Hint: Move in the direction where the sun rises.",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=20)

    direction_label = tk.Label(window, text="Current Direction: None",
                                font=("Helvetica", 16), fg="#00ffcc", bg="#1e1e2f")
    direction_label.pack(pady=20)

    toggles.set_target("East")  # Set the target direction for this challenge

    # Function to update the direction label and check the toggle state
    def update_direction():
        direction = toggles.get_direction()
        if direction:
            direction_label.config(text=f"Current Direction: {direction}")
        else:
            direction_label.config(text="Current Direction: None")

        # Check if the direction is correct
        if toggles._defused:
            tk.Label(window,
                     text="🎉 Correct! You moved East and found a chest filled with food.",
                     font=("Helvetica", 16), fg="green", bg="#1e1e2f").pack(pady=20)
            window.after(2000, lambda: chest_puzzle(window))  # Proceed to the chest puzzle
        elif toggles._failed:
            tk.Label(window,
                     text="❌ Wrong toggle! Try again.",
                     font=("Helvetica", 16), fg="red", bg="#1e1e2f").pack(pady=20)

    # Continuously poll the toggles
    def poll_toggles():
        update_direction()
        if toggles._running:
            window.after(100, poll_toggles)

    poll_toggles()

# Function for the Wire Puzzle in Forgotten Fortress
def wire_puzzle(window):
    """
    Screen for the wire puzzle in the Forgotten Fortress phase.
    """
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window,
             text="⚡ Power Barrier Challenge",
             font=("Helvetica", 24, "bold"),
             fg="#ffcc00",
             bg="#1e1e2f").pack(pady=(40, 10))

    tk.Label(window,
             text="Cut the correct wires to deactivate the barrier.",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=20)

    # Add wire puzzle logic here
    # For example, display clickable wire buttons and validate the sequence


# Function for the Chest Puzzle in Phantom's Lair
def chest_puzzle(window):
    """
    Screen for the chest puzzle in the Phantom's Lair phase.
    """
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window,
             text="🗝️ Chest Puzzle",
             font=("Helvetica", 24, "bold"),
             fg="#00ffcc",
             bg="#1e1e2f").pack(pady=(40, 10))

    tk.Label(window,
             text="To unlock the chest, solve the following riddle:",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=20)

    riddle = "I speak without a mouth and hear without ears. I have no body, but I come alive with the wind. What am I?"
    tk.Label(window, text=riddle, font=("Helvetica", 14), fg="#ddddff", bg="#1e1e2f", wraplength=600).pack(pady=10)

    answer_entry = tk.Entry(window, font=("Helvetica", 14))
    answer_entry.pack(pady=10)

    def check_answer():
        answer = answer_entry.get().strip().lower()
        if answer == "echo":
            tk.Label(window,
                     text="✅ Correct! The chest opens and you're well-fed.",
                     font=("Helvetica", 16), fg="#00ff00", bg="#1e1e2f").pack(pady=20)
            window.after(2000, lambda: show_next_phase(window))  # Proceed to the next phase
        else:
            tk.Label(window,
                     text="❌ Incorrect answer. Try again.",
                     font=("Helvetica", 14), fg="red", bg="#1e1e2f").pack(pady=10)

    tk.Button(window,
              text="Submit Answer",
              font=("Helvetica", 14),
              command=check_answer).pack(pady=10)

class Toggles(PhaseThread):
    def __init__(self, component, target_direction, name="Toggles"):
        super().__init__(name, component, target_direction)
        self._value = [False, False, False, False]  # Initial state of toggles (North, East, South, West)
        self._current_direction = None  # The currently selected direction
        self._defused = False
        self._failed = False
        self._running = False

    def run(self):
        """
        Monitor the toggles to determine the selected direction and check against the target.
        """
        self._running = True
        while self._running:
            # Get the current state of the toggles
            current = list(self._component.toggles)
            self._value = current

            # Map toggles to directions
            directions = ["North", "East", "South", "West"]
            for i, state in enumerate(current):
                if state:  # If the toggle is ON
                    self._current_direction = directions[i]
                    break  # Only one direction can be active at a time
            else:
                self._current_direction = None  # No direction selected

            # Check if the direction matches the target
            if self._current_direction == self._target:
                self._defused = True
                self._running = False
            elif self._current_direction is not None and self._current_direction != self._target:
                self._failed = True
                self._running = False

            sleep(0.1)  # Sleep to prevent CPU overload

    def get_direction(self):
        """
        Returns the currently selected direction based on toggle state.
        """
        return self._current_direction

    def __str__(self):
        """
        Returns the toggle state as a string for debugging/feedback.
        """
        states = [(direction, "ON" if state else "OFF") for direction, state in zip(["North", "East", "South", "West"], self._value)]
        return " | ".join([f"{dir}: {state}" for dir, state in states])

# final phase handler
def run_final_phase(window):
    # Starts final phase (button puzzle, etc.)
    phase = FinalPhaseThread()
    phase.start()

    # Function to check if the final phase is done
    def check_completion():
        if phase.is_alive():
            window.after(100, check_completion)
        else:
            if phase.success:
                show_victory_screen(window)
            else:
                show_failure_screen(window)

    check_completion()
