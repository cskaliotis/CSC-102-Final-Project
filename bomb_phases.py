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
    def __init__(self, component, initial_value, name="Timer"):
        super().__init__(name, component)
        # the default value is the specified initial value
        self._value = initial_value
        # is the timer paused?
        self._paused = False
        # initialize the timer's minutes/seconds representation
        self._min = ""
        self._sec = ""
        # by default, each tick is 1 second
        self._interval = 1

    # runs the thread
    def run(self):
        self._running = True
        while (self._running):
            if (not self._paused):
                # update the timer and display its value on the 7-segment display
                self._update()
                self._component.print(str(self))
                # wait 1s (default) and continue
                sleep(self._interval)
                # the timer has expired -> phase failed (explode)
                if (self._value == 0):
                    self._running = False
                self._value -= 1
            else:
                sleep(0.1)

    # updates the timer (only internally called)
    def _update(self):
        self._min = f"{self._value // 60}".zfill(2)
        self._sec = f"{self._value % 60}".zfill(2)

    # pauses and unpauses the timer
    def pause(self):
        # toggle the paused state
        self._paused = not self._paused
        # blink the 7-segment display when paused
        self._component.blink_rate = (2 if self._paused else 0)

    # returns the timer as a string (mm:ss)
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
  
# the toggle switches phase
class Toggles(PhaseThread):
    def __init__(self, component, target, name="Toggles"):
        super().__init__(name, component, target)
        self._value = []  # The current state of the toggles (on/off)
        self._defused = False
        self._failed = False
        self._running = False

    # runs the thread
    def run(self):
        self._running = True
        while self._running:
            # Assume component.toggles is a list or array representing the state of each toggle switch
            current = list(self._component.toggles)
            self._value = current
            
            # Correct set of toggles => defused
            if current == self._target:
                self._defused = True
                self._running = False
            # If any incorrect toggle state => fail (strike)
            elif any(current[i] != self._target[i] for i in range(len(self._target))):
                self._failed = True
                self._running = False
            
            sleep(0.1)  # Sleep to prevent CPU overload

    def defuse(self):
        """Forcefully mark the phase as defused (e.g., upon correct answer in GUI)."""
        self._defused = True
        self._running = False

    def fail(self):
        """Forcefully mark the phase as failed."""
        self._failed = True
        self._running = False

    def is_defused(self):
        return self._defused

    def is_failed(self):
        return self._failed

    # returns the toggle switches state as a string
    def __str__(self):
        if self._defused:
            return "DEFUSED"  # The correct state, bomb defused
        elif self._failed:
            return "FAILED"  # Incorrect toggle state, failure
        else:
            # Display current toggle state as ON/OFF for each pin
            toggle_state = [("ON" if state else "OFF") for state in self._value]
            return " | ".join(toggle_state)  # Output toggle states as a string

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
