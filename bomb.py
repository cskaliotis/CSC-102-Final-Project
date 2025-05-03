#################################
# CSC 102 Defuse the Bomb Project
# Main program
# Team: 
#################################

# import the configs
import tkinter as tk
import time
from bomb_phases import Timer, Keypad, Wires,Button, Toggles, Lcd
from bomb_configs import (component_button_state,
    component_button_RGB,
    component_keypad,
    component_wires,
    wires_target as _wires_target_int,
    NUM_STRIKES,
    NUM_PHASES,
    RPi
)
from time import sleep

###########
# functions

def int_to_index_list(val, width=5):
    return [i for i in range(width) if (val >> (width - 1 - i)) & 1]

wires_target = int_to_index_list(_wires_target_int)

wires_hints = {
    tuple(wires_target): "Cut the wires whose letters appear first in the serial."
}


def update_timer(window):
    # Debug: confirm this is being called
    print(f"[TIMER DEBUG] remaining={window.remaining}")
    mins, secs = divmod(window.remaining, 60)
    window.timer_label.config(text=f"Time Left: {mins:02d}:{secs:02d}")
    if window.remaining > 0:
        window.remaining -= 1
        # schedule the next tick
        window.after(1000, update_timer, window)
    else:
        # out of time!
        show_failure_screen(window)
    
def show_welcome_screen(window):
    """
    Displays the welcome screen where the user can enter their name and start the game.
    Clears any existing widgets, sets the background, and adds necessary labels and buttons.
    """
    # Clear existing widgets from the window
    for w in window.winfo_children():
        w.destroy()

    # Set the background color for the window
    window.configure(bg="#1e1e2f")

    # Title label
    title = tk.Label(window, text="MAZE RUNNER", font=("Helvetica", 42, "bold"), fg="#00ffcc", bg="#1e1e2f")
    title.pack(pady=(60, 30))  # Adjust padding for title

    # Input frame for better structure
    input_frame = tk.Frame(window, bg="#1e1e2f")
    input_frame.pack(pady=10)

    # Name input label
    name_label = tk.Label(input_frame, text="Enter your name:", font=("Helvetica", 16), fg="#ffffff", bg="#1e1e2f")
    name_label.pack(anchor="w", padx=10, pady=(0, 5))

    # Name entry box
    name_entry = tk.Entry(input_frame, font=("Helvetica", 16), width=25, bg="#f0f0f0", relief="flat", justify="center")
    name_entry.pack(padx=10)

    # Function for starting the game
    def on_start():
        global player_name
        # Get the entered name or default to "Player"
        player_name = name_entry.get().strip() or "Player"
        show_instructions(window)  # Proceed to instructions screen

    # Start game button
    start_btn = tk.Button(window, text="Start Game", font=("Helvetica", 16, "bold"), bg="#00ffcc", fg="#000000", 
                          activebackground="#00ddaa", padx=20, pady=10, bd=0, command=on_start, cursor="hand2")
    start_btn.pack(pady=40)  # Adjust padding for button

    
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
    tk.Label(window,
             text=prompt,
             font=("Helvetica", 18),
             fg="#ffffff",
             bg="#1e1e2f",
             justify="center",
             wraplength=600).pack(pady=50)

    tk.Button(window,
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


def ensure_timer_support(window):
    if not hasattr(window, "bomb_display"):
        # invisible label simply satisfies Timer(component=…) for now
        window.bomb_display = tk.Label(window)
    if not hasattr(window, "game_over"):
        # called if the Timer thread signals failure
        def _fail():
            show_failure_screen(window)
        window.game_over = _fail

def entrance_challenge(window):
    # Debug: Confirm the function is reached
    print("[DEBUG] entrance_challenge reached")

    def run_button_thread():
        # Run the flashing-button thread
        btn = Button(component_button_state, component_button_RGB)
        btn.start()
        btn.join()  # blocks until you press

        # Start the countdown timer
        timer = Timer(component=window.bomb_display, failure_callback=window.game_over)
        timer.start()

        # Pick your riddle
        target = "610"
        if btn._easy_mode:
            prompt = "Enter the decimal code on the keypad: 610"
        else:
            prompt = "Convert this binary to decimal, then enter on keypad:\n1001100010"

        # Transition to the keypad screen
        show_entrance_puzzle_screen(window, prompt, target)

    # Run the button thread in a non-blocking manner
    window.after(100, run_button_thread)


def show_entrance_puzzle_screen(window, prompt, target):
    # clear old widgets
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    # riddle text
    tk.Label(window,
             text=prompt,
             font=("Helvetica", 18),
             fg="#ffffff",
             bg="#1e1e2f",
             justify="center",
             wraplength=600).pack(pady=(80, 20))

    # echo label for hardware keypad
    status = tk.Label(window,
                      text="Entered: ",
                      font=("Courier New", 20),
                      fg="#00ffcc",
                      bg="#1e1e2f")
    status.pack(pady=(0, 30))

    # start the hardware Keypad thread
    kd = Keypad(component_keypad, target)
    kd.start()

    # poll it
    def poll_keypad():
        status.config(text=f"Entered: {kd._value}")
        if kd._defused:
            # correct → clear and boot bomb UI
            for w in window.winfo_children():
                w.destroy()
            show_twilight_passage(window)  
        elif kd._failed:
            status.config(text="❌ Wrong code—resetting…")
            window.after(1500, lambda: entrance_challenge(window))
        else:
            window.after(100, poll_keypad)

    poll_keypad()
    
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

from bomb_phases import twilight_passage, forgotten_fortress, phantom_lair

def show_twilight_passage(window):
    toggles.set_target("South")
    twilight_passage(window, toggles)

def show_forgotten_fortress(window):
    toggles.set_target("West")
    forgotten_fortress(window, toggles)

def show_phantom_lair(window):
    toggles.set_target("East")
    phantom_lair(window, toggles)

def show_twilight_passage(window, toggles):
    """
    Screen for the Twilight Passage phase, where the player must flip the correct toggle to proceed.
    """
    for w in window.winfo_children():
        w.destroy()
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
            window.after(2000, lambda: show_circuit_puzzle(window))  # Proceed to the next phase
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

    # Toggle button to flip direction
    def on_toggle_south():
        for w in window.winfo_children():
            w.destroy()
        window.configure(bg="#1e1e2f")
        tk.Label(window,
                 text="🔄 Direction: SOUTH\nYou're heading south down the Twilight Passage.",
                 font=("Helvetica", 18),
                 fg="#ffffff",
                 bg="#1e1e2f").pack(pady=30)
        tk.Label(window,
                 text="You're stopped by two doors...\nSolve the circuit puzzle to proceed.",
                 font=("Helvetica", 16),
                 fg="#ffffff",
                 bg="#1e1e2f").pack(pady=20)

        # Challenge screen with doors
        tk.Label(window,
                 text="What’s the circuit’s Boolean expression?",
                 font=("Helvetica", 18, "bold"),
                 fg="#00ffcc",
                 bg="#1e1e2f").pack(pady=20)

        tk.Label(window,
                 text="Door 1: (A AND B) OR (C AND NOT D)\nDoor 2: (A OR B) AND (C OR D)",
                 font=("Helvetica", 15),
                 fg="#ffffff",
                 bg="#1e1e2f",
                 justify="center").pack(pady=10)

        answer_entry = tk.Entry(window, font=("Courier New", 16), width=35, justify="center")
        answer_entry.pack(pady=10)

        def check_answer():
            answer = answer_entry.get().replace(" ", "").upper()
            if answer in ["(AANDB)OR(CANDNOTD)", "(AAND B)OR(CANDNOTD)"]:
                tk.Label(window,
                         text="✅ Correct! You enter the Forgotten Fortress.",
                         font=("Helvetica", 16),
                         fg="#00ffcc",
                         bg="#1e1e2f").pack(pady=20)
                window.after(2000, lambda: show_forgotten_fortress(window))
            else:
                tk.Label(window,
                         text="❌ Wrong expression. Try again.",
                         font=("Helvetica", 14),
                         fg="#ff6666",
                         bg="#1e1e2f").pack(pady=10)

        tk.Button(window,
                  text="Submit Answer",
                  font=("Helvetica", 14, "bold"),
                  bg="#00ffcc",
                  fg="#000000",
                  command=check_answer).pack(pady=20)

    tk.Button(window,
              text="Toggle SOUTH",
              font=("Helvetica", 16, "bold"),
              bg="#00ffcc",
              fg="#000000",
              padx=20,
              pady=10,
              command=on_toggle_south).pack(pady=40)

# Placeholder for next room logic
def show_forgotten_fortress(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")
    
    tk.Label(window, text="🏰 You’ve entered the Forgotten Fortress!",
             font=("Helvetica", 20, "bold"), 
             fg="#ffffff", 
             bg="#1e1e2f").pack(pady=30)
    
    tk.Label(window, text="You're surrounded by ancient walls...\nA riddle echoes: 'Go where the sun sets.'",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=20)

    tk.Label(window, text="Which direction will you go?",
             font=("Helvetica", 16),
             fg="#00ffcc",
             bg="#1e1e2f").pack(pady=10)
    
    def choose_direction(direction):
        for w in window.winfo_children():
            w.destroy()
        window.configure(bg="#1e1e2f")

        if direction.lower() == "west":
            tk.Label(window,
                     text="💥 You tripped over a power barrier!",
                     font=("Helvetica", 20, "bold"),
                     fg="#ff6666",
                     bg="#1e1e2f").pack(pady=30)

            tk.Label(window,
                     text="⚡ Solve the wires puzzle to deactivate it.",
                     font=("Helvetica", 16),
                     fg="#ffffff",
                     bg="#1e1e2f").pack(pady=10)

            # Small delay then show wires
            window.after(1500, lambda: show_wires_screen(window))
        else:
            tk.Label(window,
                     text="🚫 Wrong way. The path is blocked.",
                     font=("Helvetica", 16),
                     fg="#ff6666",
                     bg="#1e1e2f").pack(pady=30)

            tk.Button(window,
                      text="Try Another Direction",
                      font=("Helvetica", 14, "bold"),
                      bg="#00ffcc",
                      fg="#000000",
                      command=lambda: show_forgotten_fortress(window)).pack(pady=20)

    # Direction buttons
    for dir in ["North", "South", "East", "West"]:
        tk.Button(window,
                  text=dir,
                  font=("Helvetica", 14),
                  width=10,
                  command=lambda d=dir: choose_direction(d)).pack(pady=5)


    # Continue your game flow here (e.g., wires, keypad, etc.)

def show_wires_screen(window):
    """Power‑barrier room – player must cut the correct wires."""
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    hint = wires_hints.get(tuple(wires_target), "Cut the correct wires!")
    tk.Label(window, text=hint, font=("Helvetica", 18),
             fg="#ffffff", bg="#1e1e2f", wraplength=600).pack(pady=30)

    # -------- clickable wire buttons (useful for dev/testing) --------
    dev_frame = tk.Frame(window, bg="#1e1e2f")
    dev_frame.pack(pady=10)
    cut_order = []          # remembers the order player clicks

    def toggle_wire(idx, btn):
        if idx in cut_order:
            cut_order.remove(idx)
            btn.config(relief="raised", bg="grey30")
        else:
            cut_order.append(idx)
            btn.config(relief="sunken", bg="#cc0000")

    for i in range(5):
        b = tk.Button(dev_frame, text=f"Wire {i+1}", width=8,
                      font=("Helvetica", 14), bg="grey30", fg="#ffffff")
        b.config(command=lambda i=i, btn=b: toggle_wire(i, btn))
        b.grid(row=0, column=i, padx=4, pady=4)

    tk.Button(window, text="Cut!", font=("Helvetica", 16, "bold"),
              bg="#00ffcc", fg="#000000",
              command=lambda: run_wires_phase(window, cut_order)
    ).pack(pady=25)
def run_wires_phase(window):
    # Simulate getting user input - replace this part with real input logic
    user_input = [1, 2, 3]  # example placeholder, change to actual wire input logic

    if tuple(user_input) == tuple(wires_target):  # wire order is correct
        for w in window.winfo_children():
            w.destroy()
        window.configure(bg="#1e1e2f")
        tk.Label(window,
                 text="✅ Wires deactivated! Power barrier down.",
                 font=("Helvetica", 18),
                 fg="#00ff00",
                 bg="#1e1e2f").pack(pady=30)

        # Proceed to Phantom’s Lair after short pause
        window.after(2000, lambda: show_phantoms_lair(window))

    else:
        tk.Label(window,
                 text="❌ Incorrect wire pattern! Try again.",
                 font=("Helvetica", 16),
                 fg="red",
                 bg="#1e1e2f").pack(pady=10)

def run_wires_phase(window, gui_order):
    """
    Starts (or consults) the Wires phase thread, then polls until
    defused/failed.  On the Pi we rely on GPIO; in GUI test mode we
    judge by gui_order.
    """
    # --- create the thread only once ---
    if not hasattr(run_wires_phase, "thread"):
        run_wires_phase.thread = Wires(component_wires, wires_target)
        run_wires_phase.thread.start()
    phase = run_wires_phase.thread

    # --- helpers decide success/failure ---
    def is_defused():
        return phase._defused if RPi else gui_order == wires_target

    def is_failed():
        return phase._failed if RPi else (bool(gui_order) and gui_order != wires_target)

    # --- act on the outcome ---
    if is_defused():
        show_phantoms_lair(window)        # advance to next room
    elif is_failed():
        tk.Label(window, text="❌ Incorrect wire pattern! Try again.",
                 font=("Helvetica", 14), fg="red", bg="#1e1e2f").pack(pady=10)
        window.after(1500, lambda: show_wires_screen(window))
    else:
        window.after(100, lambda: run_wires_phase(window, gui_order))

def show_phantoms_lair(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window,
             text="👻 You’ve entered the Phantom's Lair!",
             font=("Helvetica", 20, "bold"),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=40)

    tk.Label(window,
             text="Hint: The sun rises in the...",
             font=("Helvetica", 16),
             fg="#ffff99",
             bg="#1e1e2f").pack(pady=10)

    tk.Button(window,
              text="Go East",
              font=("Helvetica", 16),
              command=lambda: show_chest_and_riddle(window)).pack(pady=30)
    
def show_chest_and_riddle(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window,
             text="🧰 You found a chest filled with food!",
             font=("Helvetica", 18),
             fg="#00ffcc",
             bg="#1e1e2f").pack(pady=20)

    tk.Label(window,
             text="🎉 Your life has been extended!",
             font=("Helvetica", 16),
             fg="#00ff00",
             bg="#1e1e2f").pack(pady=10)

    tk.Label(window,
             text="To open the chest, solve this riddle:",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=20)

    riddle = "I speak without a mouth and hear without ears. I have nobody, but I come alive with the wind. What am I?"
    tk.Label(window, text=riddle, font=("Helvetica", 14), fg="#ddddff", bg="#1e1e2f", wraplength=600).pack(pady=10)

    answer_entry = tk.Entry(window, font=("Helvetica", 14))
    answer_entry.pack(pady=10)

    tk.Button(window, text="Submit Answer", font=("Helvetica", 14),
              command=lambda: check_riddle_answer(window, answer_entry.get())).pack(pady=10)

    tk.Button(window, text="Skip Puzzle", font=("Helvetica", 14),
              command=lambda: show_flash_button_wall(window)).pack(pady=10)

def check_riddle_answer(window, answer):
    if answer.lower().strip() == "echo":
        for w in window.winfo_children():
            w.destroy()
        tk.Label(window,
                 text="✅ Correct! The chest opens and you're well-fed.",
                 font=("Helvetica", 16),
                 fg="#00ff00",
                 bg="#1e1e2f").pack(pady=20)
        window.after(2000, lambda: show_flash_button_wall(window))
    else:
        tk.Label(window,
                 text="❌ That's not the right answer. Try again or skip.",
                 font=("Helvetica", 14),
                 fg="red",
                 bg="#1e1e2f").pack(pady=10)

def show_flash_button_wall(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window,
             text="🚪 A wall blocks your path. Flash the hidden button to open it!",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f",
             wraplength=600).pack(pady=30)

    tk.Button(window, text="Flash Button",
              font=("Helvetica", 14),
              command=lambda: show_easy_puzzle(window)).pack(pady=20)
    
def show_easy_puzzle(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window, text="🧩 Easy Puzzle:\nWhat number comes next?\n2, 4, 6, 8, ?", 
             font=("Helvetica", 16), fg="#ffffff", bg="#1e1e2f").pack(pady=20)

    answer_entry = tk.Entry(window, font=("Helvetica", 14))
    answer_entry.pack(pady=10)

    tk.Button(window, text="Submit",
              font=("Helvetica", 14),
              command=lambda: check_easy_puzzle(window, answer_entry.get())).pack(pady=10)

def check_easy_puzzle(window, answer):
    if answer.strip() == "10":
        for w in window.winfo_children():
            w.destroy()
        tk.Label(window, text="✅ Correct!", font=("Helvetica", 16), fg="#00ff00", bg="#1e1e2f").pack(pady=20)
        window.after(1500, lambda: show_hard_puzzle(window))
    else:
        tk.Label(window, text="❌ Try again!", font=("Helvetica", 14), fg="red", bg="#1e1e2f").pack(pady=10)

def show_hard_puzzle(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window,
             text="🧠 Hard Puzzle:\nI have keys but no locks. I have space but no room. You can enter but can’t go outside. What am I?",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f",
             wraplength=600).pack(pady=30)

    answer_entry = tk.Entry(window, font=("Helvetica", 14))
    answer_entry.pack(pady=10)

    tk.Button(window, text="Submit",
              font=("Helvetica", 14),
              command=lambda: check_hard_puzzle(window, answer_entry.get())).pack(pady=10)
    
def check_hard_puzzle(window, answer):
    if answer.lower().strip() == "keyboard":
        for w in window.winfo_children():
            w.destroy()
        tk.Label(window,
                 text="🎉 You solved all puzzles! Moving to the next point...",
                 font=("Helvetica", 16),
                 fg="#00ff00",
                 bg="#1e1e2f").pack(pady=20)
        window.after(2000, lambda: show_point_d(window))  # Create show_point_d later
    else:
        tk.Label(window,
                 text="❌ Not quite. Try again!",
                 font=("Helvetica", 14),
                 fg="red",
                 bg="#1e1e2f").pack(pady=10)
        

def show_chest_screen(window):
    """Supply Chest: Button→Keypad bonus puzzle."""
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")
    tk.Label(window, text="🧭 Supply Chest Found!\n\nPress for a bonus puzzle…",
             font=("Helvetica",18), fg="#fff", bg="#1e1e2f",
             justify="center", wraplength=600).pack(pady=40)
    tk.Button(window, text="Begin Chest Puzzle", font=("Helvetica",16),
              command=lambda: run_chest_phase(window)).pack(pady=20)

#placeholder for point D 
def show_mystic_hollow(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    tk.Label(window, text="💣 Mystic Hollow – The Bomb Challenge!",
             font=("Helvetica", 20, "bold"),
             fg="#ff6666",
             bg="#1e1e2f").pack(pady=30)

    tk.Label(window, text="Only one button defuses the bomb...",
             font=("Helvetica", 16),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=10)

    tk.Label(window, text="Press GREEN to defuse, RED to explode.",
             font=("Helvetica", 14),
             fg="#ffff99",
             bg="#1e1e2f").pack(pady=10)

    button_frame = tk.Frame(window, bg="#1e1e2f")
    button_frame.pack(pady=30)

    tk.Button(button_frame,
              text="🟢 Defuse",
              font=("Helvetica", 16, "bold"),
              bg="#00cc66",
              fg="#ffffff",
              width=10,
              command=lambda: defuse_success(window)).grid(row=0, column=0, padx=20)

    tk.Button(button_frame,
              text="🔴 Explode",
              font=("Helvetica", 16, "bold"),
              bg="#cc0000",
              fg="#ffffff",
              width=10,
              command=lambda: explode_fail(window)).grid(row=0, column=1, padx=20)

def defuse_success(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")
    
    tk.Label(window, text="✅ Bomb defused! You’re a hero.",
             font=("Helvetica", 18),
             fg="#00ff00",
             bg="#1e1e2f").pack(pady=40)

    window.after(2000, lambda: show_final_screen(window))  # Final win screen


def explode_fail(window):
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")
    
    tk.Label(window, text="💥 BOOM! You triggered the bomb.",
             font=("Helvetica", 18, "bold"),
             fg="red",
             bg="#1e1e2f").pack(pady=40)

    tk.Label(window, text="But… a second chance awaits you.",
             font=("Helvetica", 14),
             fg="#ffffff",
             bg="#1e1e2f").pack(pady=10)

    tk.Button(window, text="Retry Mystic Hollow",
              font=("Helvetica", 14),
              command=lambda: show_mystic_hollow(window)).pack(pady=20)

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

def on_timer_failure():
    show_failure_screen(window)

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
