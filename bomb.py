#################################
# CSC 102 Defuse the Bomb Project
# Main program
# Team: 
#################################

# import the configs
import tkinter as tk
from tkinter import messagebox
import time
from bomb_configs import *
# import the phases
from bomb_phases import Timer, Keypad, Wires,Button, Toggles, Lcd

###########
# functions

def show_welcome_screen(window):
    for w in window.winfo_children():
        w.destroy()
        
    window.configure(bg="#1e1e2f")
    title = tk.Label(window, text="MAZE RUNNER", font=("Helvetica", 42, "bold"), fg="#00ffcc", bg="#1e1e2f")
    title.pack(pady=(60, 30))

    input_frame = tk.Frame (window, bg="#1e1e2f")
    input_frame.pack(pady=10)
    
    name_label = tk.Label(input_frame, text="Enter your name:", font=("Helvetica", 16), fg="#ffffff", bg="#1e1e2f")
    name_label.pack(anchor="w", padx=10,pady=(0,5))
    name_entry = tk.Entry(input_frame, font=("Helvetica", 16), width=25, bg="#f0f0f0", relief="flat", justify="center")
    name_entry.pack(padx=10)

    def on_start():
        global player_name
        player_name = name_entry.get().strip() or "Player"
        show_instructions(window)

    start_btn = tk.Button(window, text="Start Game", font=("Helvetica", 16, "bold"), bg="#00ffcc", fg="#000000", activebackground="#00ddaa",
        padx=20, pady=10, bd=0, command=on_start, cursor="hand2")
    start_btn.pack(pady=40)
    
def show_instructions(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    instr_text = (
        "Welcome, {}!\n\n"
        "Your goal: Escape the maze before time runs out.\n"
        "- Use the button and keypad to unlock doors.\n"
        "- Flip toggles to shift walls (riddles will guide you).\n"
        "- Cut wires to disable barriers.\n\n"
        "Click 'Continue' when you're ready."
    ).format(player_name)

    instr_label = tk.Label(
        window,
        text=instr_text,                # <<-- was instr
        font=("Helvetica", 15),
        fg="#ffffff",
        bg="#1e1e2f",
        justify="left",
        wraplength=600
    )
    instr_label.pack(padx=50, pady=(60, 30))

    cont_btn = tk.Button(
        window,
        text="Continue",
        font=("Helvetica", 16, "bold"),
        bg="#00ffcc",
        fg="#000000",
        activebackground="#00ddaa",
        cursor="hand2",                 # <<-- moved inside the call
        padx=20,
        pady=10,
        bd=0,
        command=lambda: show_entrance_screen(window)
    )
    cont_btn.pack(pady=30)


import tkinter as tk
import time
from bomb_phases import Button, Keypad, Lcd
from bomb_configs import NUM_STRIKES, NUM_PHASES
from tkinter import messagebox

# 1) Main “welcome” screen—now passes window into entrance_challenge
def show_entrance_screen(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    prompt = (
        "🚪 Welcome to the Maze Runner Challenge!\n\n"
        "The entrance is locked.\n"
        "To unlock it, press the BIG BUTTON when it flashes:\n\n"
        "🟢 GREEN for an *easy* riddle\n"
        "🔴 RED for a *hard* one\n\n"
        "Choose wisely. Good luck, runner!"
    )
    tk.Label(
        window,
        text=prompt,
        font=("Helvetica", 18),
        fg="#ffffff",
        bg="#1e1e2f",
        justify="center",
        wraplength=600
    ).pack(pady=50)

    tk.Button(
        window,
        text="Start Puzzle",
        font=("Helvetica", 16, "bold"),
        bg="#00ffcc",
        fg="#000000",
        activebackground="#00ddaa",
        cursor="hand2",
        padx=30,
        pady=12,
        bd=0,
        command=lambda: entrance_challenge(window)
    ).pack(pady=30)


# 2) Spawns the flash-button phase then swaps to the entry screen
def entrance_challenge(window):
    print("🔒 Maze Entrance Locked! Press GREEN=easy, RED=hard.")

    # run the flashing-button thread
    btn = Button(component_button_state, component_button_RGB)
    btn.start()
    btn.join()

    print(f"[ENTRANCE DEBUG] defused={btn._defused}, easy_mode={btn._easy_mode}")

    # pick text based on green/red
    target = "610"
    if btn._easy_mode:
        prompt = "Enter the decimal code on the keypad: 610"
    else:
        prompt = (
            "Convert this binary to decimal, then enter on keypad:\n"
            "1001100010  (hint: it equals 610)"
        )

    # show the in-window puzzle
    show_entrance_puzzle_screen(window, prompt, target)


# 3) In-window puzzle screen with Entry + Submit
def show_entrance_puzzle_screen(window, prompt, target):
    # clear old widgets
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    # riddle text
    tk.Label(
        window,
        text=prompt,
        font=("Helvetica", 18),
        fg="#ffffff",
        bg="#1e1e2f",
        justify="center",
        wraplength=600
    ).pack(pady=(80, 20))

    # entry box
    entry = tk.Entry(
        window,
        font=("Helvetica", 16),
        width=10,
        justify="center"
    )
    entry.pack(pady=(0, 30))
    entry.focus_set()

    # submit handler
    def on_submit():
        attempt = entry.get().strip()
        if attempt == target:
            # correct → boot bomb UI
            for w in window.winfo_children():
                w.destroy()
            global gui, strikes_left, active_phases
            gui           = Lcd(window)
            strikes_left  = NUM_STRIKES
            active_phases = NUM_PHASES
            gui.after(1000, bootup)
        else:
            # inline error
            tk.Label(
                window,
                text="❌ Wrong code—try again.",
                font=("Helvetica", 14),
                fg="#ff5555",
                bg="#1e1e2f"
            ).pack()
            window.after(1500, lambda: entrance_challenge(window))

    # submit button
    tk.Button(
        window,
        text="Submit",
        font=("Helvetica", 16, "bold"),
        bg="#00ffcc",
        fg="#000000",
        activebackground="#00ddaa",
        padx=20,
        pady=10,
        bd=0,
        cursor="hand2",
        command=on_submit
    ).pack()



    # Submit button callback
    def on_submit():
        attempt = entry.get().strip()
        if attempt == target:
            # success → clear and boot the bomb
            for w in window.winfo_children():
                w.destroy()
            global gui, strikes_left, active_phases
            gui           = Lcd(window)
            strikes_left  = NUM_STRIKES
            active_phases = NUM_PHASES
            gui.after(1000, bootup)
        else:
            # wrong → show a quick “try again” message and restart
            tk.Label(
                window,
                text="❌ Wrong code—try again.",
                font=("Helvetica", 16),
                fg="#ff5555",
                bg="#1e1e2f"
            ).pack(pady=(10, 0))
            window.after(1500, lambda: entrance_challenge())

    # Submit button
    tk.Button(
        window,
        text="Submit",
        font=("Helvetica", 16, "bold"),
        bg="#00ffcc",
        fg="#000000",
        activebackground="#00ddaa",
        padx=20,
        pady=10,
        bd=0,
        command=on_submit,
        cursor="hand2"
    ).pack(pady=10)
    
def show_toggle_screen(window):
    """Screen for the shifting-walls (Toggles) puzzle."""
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")
    # Display the riddle for the current toggles_target
    riddle = toggles_riddles[toggles_target.index(True)]
    tk.Label(window, text=riddle, font=("Helvetica", 18), fg="#fff", bg="#1e1e2f",
             justify="center", wraplength=600).pack(pady=40)
    tk.Button(window, text="Solve Toggles", font=("Helvetica",16),
              command=lambda: run_toggle_phase(window)).pack(pady=20)

def show_wires_screen(window):
    """Screen for the power-barrier (Wires) puzzle."""
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")
    hint = wires_hints.get(tuple(wires_target), "Cut the correct wires!")
    tk.Label(window, text=hint, font=("Helvetica", 18), fg="#fff", bg="#1e1e2f",
             justify="center", wraplength=600).pack(pady=40)
    tk.Button(window, text="Solve Wires", font=("Helvetica",16),
              command=lambda: run_wires_phase(window)).pack(pady=20)

def show_chest_screen(window):
    """Supply Chest: Button→Keypad bonus puzzle."""
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")
    tk.Label(window, text="🧭 Supply Chest Found!\n\nPress for a bonus puzzle…",
             font=("Helvetica",18), fg="#fff", bg="#1e1e2f",
             justify="center", wraplength=600).pack(pady=40)
    tk.Button(window, text="Begin Chest Puzzle", font=("Helvetica",16),
              command=lambda: run_chest_phase(window)).pack(pady=20)

def show_final_screen(window):
    """Final defuse/boom decision."""
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")
    tk.Label(window, text="🚪 Final Door Ahead!\nPress GREEN to defuse, RED to boom.",
             font=("Helvetica",18), fg="#fff", bg="#1e1e2f",
             justify="center", wraplength=600).pack(pady=40)
    # map directly to your Button‐only phase
    tk.Button(window, text="Press Button", font=("Helvetica",16),
              command=lambda: run_final_phase(window)).pack(pady=20)
    
def show_victory_screen(window):
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")
    tk.Label(window, text="🎉 YOU WIN!", font=("Helvetica", 28, "bold"),
             fg="#00ffcc", bg="#1e1e2f").pack(pady=40)
    tk.Label(window, text="You defused the final challenge and escaped the maze!",
             font=("Helvetica", 18), fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center").pack(pady=20)

def show_failure_screen(window):
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")
    tk.Label(window, text="💥 BOOM!", font=("Helvetica", 28, "bold"),
             fg="#ff5555", bg="#1e1e2f").pack(pady=40)
    tk.Label(window, text="The defusal failed. The maze collapses…",
             font=("Helvetica", 18), fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center").pack(pady=20)

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

    show_welcome_screen(window)
    window.mainloop()
