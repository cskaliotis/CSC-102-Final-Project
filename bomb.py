#################################
# CSC 102 Defuse the Bomb Project
# Main program
# Team: 
#################################

# import the configs
import tkinter as tk
import time
from bomb_configs import *
# import the phases
from bomb_phases import Timer, Keypad, Wires,Button, Toggles, Lcd

###########
# functions

def show_welcome_screen(window):
    for w in window.winfo_children():
        w.destroy()
    title = tk.Label(window, text="MAZE RUNNER", font=("Helvetica", 36))
    title.pack(pady=40)
    name_label = tk.Label(window, text="Enter your name:", font=("Helvetica", 14))
    name_label.pack(pady=(0,10))
    name_entry = tk.Entry(window, font=("Helvetica", 14))
    name_entry.pack()

    def on_start():
        global player_name
        player_name = name_entry.get().strip() or "Player"
        show_instructions(window)

    start_btn = tk.Button(window, text="Start", font=("Helvetica", 16),
                          command=on_start)
    start_btn.pack(pady=30)
def show_instructions(window):
    for w in window.winfo_children():
        w.destroy()
    instr = (
        "Welcome, {}!\n\n"
        "Your goal: Escape the maze before time runs out.\n"
        "- Use the button and keypad to unlock doors.\n"
        "- Flip toggles to shift walls (riddles will guide you).\n"
        "- Cut wires to disable barriers.\n\n"
        "Click 'Continue' when you're ready."
    ).format(player_name)
    label = tk.Label(window, text=instr, font=("Helvetica", 14), justify="left")
    label.pack(padx=40, pady=40)

    cont_btn = tk.Button(window, text="Continue", font=("Helvetica", 16),
                         command=entrance_challenge)
    cont_btn.pack(pady=20)

def entrance_challenge():
    print("🔒 Maze Entrance Locked!")
    print("Press the big button when it flashes GREEN for an EASY riddle, or RED for a HARD one.")

    # Launch the Button puzzle
    btn = Button(component_button_state,
                 component_button_RGB,
                 button_target,
                 button_color,
                 None)  # pass `timer` if you want button to interact with it
    btn.start()
    while not (btn._defused or btn._failed):
        time.sleep(0.1)

    # Configure Keypad based on button result
    if btn._defused:
        print("You got GREEN! Easy riddle loaded.")
        Keypad.keyword = entry_easy_keyword
        Keypad.rot     = entry_easy_rot
    else:
        print("Oops—you hit RED! Hard riddle loaded.")
        Keypad.keyword = entry_hard_keyword
        Keypad.rot     = entry_hard_rot

    # Run the Keypad puzzle whose answer is the entry code
    print("Enter the door code on the keypad:")
    kd = Keypad(component_keypad, keypad_target)
    kd.start()
    while not (kd._defused or kd._failed):
        time.sleep(0.1)

    if kd._defused:
        print("✅ Correct! The entrance unlocks. Good luck.")
        gui.after(1000, bootup)
        return True
    else:
        print("❌ Wrong code. Try the entrance puzzle again.\n")
        return entrance_challenge()

# generates the bootup sequence on the LCD
def bootup(n=0):
    # if we're not animating (or we're at the end of the bootup text)
    if (not ANIMATE or n == len(boot_text)):
        # if we're not animating, render the entire text at once (and don't process \x00)
        if (not ANIMATE):
            gui._lscroll["text"] = boot_text.replace("\x00", "")
        # configure the remaining GUI widgets
        gui.setup()
        # setup the phase threads, execute them, and check their statuses
        if (RPi):
            setup_phases()
            check_phases()
    # if we're animating
    else:
        # add the next character (but don't render \x00 since it specifies a longer pause)
        if (boot_text[n] != "\x00"):
            gui._lscroll["text"] += boot_text[n]

        # scroll the next character after a slight delay (\x00 is a longer delay)
        gui.after(25 if boot_text[n] != "\x00" else 750, bootup, n + 1)

# sets up the phase threads
def setup_phases():
    global timer, keypad, wires, button, toggles
    
    # setup the timer thread
    timer = Timer(component_7seg, COUNTDOWN)
    # bind the 7-segment display to the LCD GUI so that it can be paused/unpaused from the GUI
    gui.setTimer(timer)
    # setup the keypad thread
    keypad = Keypad(component_keypad, keypad_target)
    # setup the jumper wires thread
    wires = Wires(component_wires, wires_target)
    # setup the pushbutton thread
    button = Button(component_button_state, component_button_RGB, button_target, button_color, timer)
    # bind the pushbutton to the LCD GUI so that its LED can be turned off when we quit
    gui.setButton(button)
    # setup the toggle switches thread
    toggles = Toggles(component_toggles, toggles_target)

    # start the phase threads
    timer.start()
    keypad.start()
    wires.start()
    button.start()
    toggles.start()

# checks the phase threads
def check_phases():
    global active_phases
    
    # check the timer
    if (timer._running):
        # update the GUI
        gui._ltimer["text"] = f"Time left: {timer}"
    else:
        # the countdown has expired -> explode!
        # turn off the bomb and render the conclusion GUI
        turn_off()
        gui.after(100, gui.conclusion, False)
        # don't check any more phases
        return
    # check the keypad
    if (keypad._running):
        # update the GUI
        gui._lkeypad["text"] = f"Combination: {keypad}"
        # the phase is defused -> stop the thread
        if (keypad._defused):
            keypad._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (keypad._failed):
            strike()
            # reset the keypad
            keypad._failed = False
            keypad._value = ""
    # check the wires
    if (wires._running):
        # update the GUI
        gui._lwires["text"] = f"Wires: {wires}"
        # the phase is defused -> stop the thread
        if (wires._defused):
            wires._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (wires._failed):
            strike()
            # reset the wires
            wires._failed = False
    # check the button
    if (button._running):
        # update the GUI
        gui._lbutton["text"] = f"Button: {button}"
        # the phase is defused -> stop the thread
        if (button._defused):
            button._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (button._failed):
            strike()
            # reset the button
            button._failed = False
    # check the toggles
    if (toggles._running):
        # update the GUI
        gui._ltoggles["text"] = f"Toggles: {toggles}"
        # the phase is defused -> stop the thread
        if (toggles._defused):
            toggles._running = False
            active_phases -= 1
        # the phase has failed -> strike
        elif (toggles._failed):
            strike()
            # reset the toggles
            toggles._failed = False

    # note the strikes on the GUI
    gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    # too many strikes -> explode!
    if (strikes_left == 0):
        # turn off the bomb and render the conclusion GUI
        turn_off()
        gui.after(1000, gui.conclusion, False)
        # stop checking phases
        return

    # the bomb has been successfully defused!
    if (active_phases == 0):
        # turn off the bomb and render the conclusion GUI
        turn_off()
        gui.after(100, gui.conclusion, True)
        # stop checking phases
        return

    # check the phases again after a slight delay
    gui.after(100, check_phases)

# handles a strike
def strike():
    global strikes_left
    
    # note the strike
    strikes_left -= 1

# turns off the bomb
def turn_off():
    # stop all threads
    timer._running = False
    keypad._running = False
    wires._running = False
    button._running = False
    toggles._running = False

    # turn off the 7-segment display
    component_7seg.blink_rate = 0
    component_7seg.fill(0)
    # turn off the pushbutton's LED
    for pin in button._rgb:
        pin.value = True

######
# MAIN
######

######
# MAIN
######
if __name__ == "__main__":
    window = tk.Tk()
    window.geometry("800x600")
    window.title("Maze Runner")
    gui = Lcd(window)

    strikes_left   = NUM_STRIKES
    active_phases  = NUM_PHASES

    show_welcome_screen(window)

    window.mainloop()
