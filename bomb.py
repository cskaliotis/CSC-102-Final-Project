#################################
# CSC 102 Defuse the Bomb Project
# Main Program


import tkinter as tk
import time
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd, MazeToggles
from bomb_configs import (
    component_7seg,
    component_button_state,
    component_button_RGB,
    component_keypad,
    component_toggles,
    component_wires,
    wires_target as _wires_target_int,
    COUNTDOWN,
    NUM_STRIKES,
    NUM_PHASES,
    RPi,
    serial
)
from types import SimpleNamespace
from time import sleep


window = tk.Tk()
window.geometry("800x600")
window.title("Maze Runner")

# Top bar for serial
top_frame = tk.Frame(window, bg="#1e1e2f")
top_frame.pack(side="top", fill="x")
serial_label = tk.Label(
    top_frame,
    text=f"Serial: {serial}",
    font=("Courier New", 12, "bold"),
    fg="red",        # show in red on black
    bg="#1e1e2f"
)
serial_label.pack(side="right", padx=10, pady=5)

# Middle frame for all your puzzle screens
content_frame = tk.Frame(window, bg="#1e1e2f")
content_frame.pack(expand=True, fill="both")

# Bottom bar for progress
bottom_frame = tk.Frame(window, bg="#1e1e2f")
bottom_frame.pack(side="bottom", fill="x")
progress = ttk.Progressbar(
    bottom_frame,
    orient="horizontal",
    mode="determinate",
    maximum=COUNTDOWN
)
progress.pack(fill="x", padx=10, pady=5)

toggle_code_to_dir = {
    "1000": "North",
    "1100": "East",
    "1110": "South",
    "1111": "West",
}
###########
# functions

class ToggleComponent:
    """
    Wrap the raw GPIO pin objects so that:
      - raw_pins = [DigitalInOut(...), …]
      - toggles returns a list of booleans in the same order,
        *inverting* pin.value so that a flipped switch (which
        pulls the pin HIGH) shows up as True.
    """
    def __init__(self, pins):
        self._pins = pins

    @property
    def toggles(self):
        # Print raw pin.value for debugging
        raw = [pin.value for pin in self._pins]
        print(f"[DEBUG] raw pin values = {raw}")
        inv  = [not v for v in raw]
        print(f"[DEBUG] interpreted toggles = {inv}")
        return inv



# convert integer bitmask to list of wire indices
def int_to_index_list(val, width):
    return [i for i in range(width) if (val >> (width - 1 - i)) & 1]

# List of wire indices that need to be cut to defuse the barrier
wires_target_list = int_to_index_list(_wires_target_int, width=len(component_wires))

# Riddle hints for the wires phase
wires_hints = {
    tuple(wires_target_list): "Cut the wires whose letters appear first in the serial."
}


def update_timer(window, display):
    # Debug: confirm this is being called
    print(f"[TIMER DEBUG] remaining={window.remaining}")
    
    mins, secs = divmod(window.remaining, 60)
    time_str = f"{mins:02d}:{secs:02d}"

    # Update the GUI label with the remaining time
    window.timer_label.config(text=f"Time Left: {time_str}")
    
    # Update the 7-segment display with the remaining time
    display.print(time_str)  # Assuming 'display' is the 7-segment object
    
    if window.remaining > 0:
        window.remaining -= 1
        # schedule the next tick
        window.after(1000, update_timer, window, display)
    else:
        # out of time!
        show_failure_screen(window)

def start_game(window):
    print("[DEBUG] start_game() called")
    # 1) Countdown timer + LCD
    timer = Timer(
        component_7seg,
        initial_value=COUNTDOWN,
        failure_callback=lambda: show_failure_screen(window)
    )
    lcd = Lcd(window)
    lcd.setTimer(timer)
    timer.start()

    # 2) Immediately go to the first puzzle
    show_entrance_screen(window)





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
        cursor="hand2",               
        padx=20,
        pady=10,
        bd=0,
        command=lambda: start_game(window)
    )
    cont_btn.pack(pady=30)

def ensure_timer_support(window):
    if not hasattr(window, "bomb_display"):
        window.bomb_display = tk.Label(window)
    if not hasattr(window, "game_over"):
        window.game_over = lambda: show_failure_screen(window)



def show_entrance_screen(window):
    # clear everything
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")

    window.remaining = 600  # seconds


    # now render the entrance UI
    prompt = (
        "🚪 Welcome to the Maze Runner Challenge!\n\n"
        "The entrance is locked.\n"
        "To unlock it, press the BIG BUTTON when it flashes:\n\n"
        "🟢 GREEN for an *easy* riddle\n"
        "🔴 RED for a *hard* one\n\n"
        "Choose wisely. Good luck, runner!"
    )
    tk.Label(window, text=prompt, font=("Helvetica", 18), fg="#fff", bg="#1e1e2f",
             justify="center", wraplength=600).pack(pady=50)

    tk.Button(window,
              text="Start Puzzle",
              font=("Helvetica", 16, "bold"),
              bg="#00ffcc", fg="#000",
              activebackground="#00ddaa",
              cursor="hand2",
              padx=30, pady=12, bd=0,
              command=lambda: entrance_challenge(window)
    ).pack(pady=30)




def entrance_challenge(window):
    """
    Flash the red/green button, wait for a press, then launch the keypad screen.
    """
    # Start the flashing‐LED Button thread and wait for the press
    btn = Button(component_button_state, component_button_RGB)
    btn.start()
    btn.join()

    # Swap the riddle mapping so green = easy, red = hard (or vice versa as you like):
    if btn._easy_mode:   # GREEN
        prompt = "Enter the decimal code on the keypad: 610"
    else:                # RED
        prompt = ("Convert this binary to decimal, then enter on keypad:\n"
                  "1001100010")
    target = "610"
    
    # Now hand off to the keypad‐UI
    show_entrance_puzzle_screen(window, prompt, target)




def show_entrance_puzzle_screen(window, prompt, target):
    """
    Prompt the player with a keypad challenge.  `target` is the digit string
    that defuses the lock (e.g., "610").
    """
    # ─── clear previous widgets ─────────────────────────────────────────────
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    # ─── riddle / instructions ─────────────────────────────────────────────
    tk.Label(window,
             text=prompt,
             font=("Helvetica", 18),
             fg="#ffffff",
             bg="#1e1e2f",
             wraplength=600,
             justify="center").pack(pady=(80, 20))

    # live echo of what the physical keypad thread is reading
    status = tk.Label(window,
                      text="Entered: ",
                      font=("Courier New", 20),
                      fg="#00ffcc",
                      bg="#1e1e2f")
    status.pack(pady=(0, 30))

    kd = Keypad(component_keypad, target)
    kd.start()

    def poll_keypad():
        status.config(text=f"Entered: {kd._value}")

        if kd._defused:
            for w in window.winfo_children():
                w.destroy()
            show_twilight_passage(window)
            return       

        elif kd._failed:
            status.config(text="❌ Wrong code — resetting…")
            window.after(1500, lambda: entrance_challenge(window))
            return       # ← stop here as well

        # still not defused or failed? keep polling
        window.after(100, poll_keypad)

    poll_keypad()

    
def show_twilight_passage(window):
    """
    Twilight Passage:
    Reads the physical 4-way toggle switches directly (0000→1000→1100→1110→1111)
    and advances when the user sets the toggles to South ("1110").
    """
    # Clear previous UI
    for w in window.winfo_children():
        w.destroy()
    window.configure(bg="#1e1e2f")

    # Static UI
    tk.Label(window, text="🌌 Twilight Passage", font=("Helvetica",24,"bold"), fg="#00ffcc", bg="#1e1e2f").pack(pady=(40,10))
    tk.Label(window, text="Hint: Turn 180° from NORTH (i.e. SOUTH) on the toggles.", font=("Helvetica",16), fg="#ffffff", bg="#1e1e2f", wraplength=600, justify="center").pack(pady=20)
    status = tk.Label(window, text="Toggle code: 0000 → None", font=("Courier New",18), fg="#00ffcc", bg="#1e1e2f")
    status.pack(pady=20)

    # Poll for toggle state
    def poll_twilight():
        bits = "".join("1" if pin.value else "0" for pin in component_toggles)
        direction = toggle_code_to_dir.get(bits)
        status.config(text=f"Toggle code: {bits} → {direction or 'None'}")
        if direction == "South":
            tk.Label(window, text="🎉 Correct! You're heading south…", font=("Helvetica",16), fg="green", bg="#1e1e2f").pack(pady=20)
            window.after(1500, lambda: show_circuit_puzzle(window))
        else:
            window.after(100, poll_twilight)
    poll_twilight()


    
def show_circuit_puzzle(window):
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")
    tk.Label(window,
             text="🛠  Solve (A AND B) OR ¬C\nSelect the correct door:",
             font=("Helvetica", 18), fg="white", bg="#1e1e2f",
             wraplength=600).pack(pady=30)

    def choose(door):
        if door == "Door 1":    # replace with your actual correct door
            show_forgotten_fortress(window)
        else:
            tk.Label(window, text="❌ Wrong door! Try again.",
                     fg="red", bg="#1e1e2f").pack(pady=10)

    frm = tk.Frame(window, bg="#1e1e2f"); frm.pack(pady=20)
    tk.Button(frm, text="Door 1", command=lambda: choose("Door 1")).grid(row=0, column=0, padx=10)
    tk.Button(frm, text="Door 2", command=lambda: choose("Door 2")).grid(row=0, column=1, padx=10)

class WiresComponent:
    def __init__(self, pins):
        self._pins = pins

    @property
    def cuts(self):
        # Indices of pins that have been cut (pin.value is True)
        return [i for i, pin in enumerate(self._pins) if pin.value]



def show_forgotten_fortress(window):
    """
    Forgotten Fortress:
    Displays the serial, waits for toggles to read West ('1111'),
    then transitions to the wire-cutting screen.
    """
    # 1) Clear UI
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")

    # 2) Show serial at top right
    tk.Label(window,
             text=f"Serial: {serial}",
             font=("Courier New", 12), fg="#ffffff", bg="#1e1e2f")
    
    # 3) Display title & riddle
    tk.Label(window,
             text="🏰 Forgotten Fortress",
             font=("Helvetica", 24, "bold"), fg="#00ffcc", bg="#1e1e2f").pack(pady=(40, 10))
    tk.Label(window,
             text="Riddle: Go where the sun sets.",
             font=("Helvetica", 16), fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center").pack(pady=20)

    # 4) Status label for toggle code
    status = tk.Label(window,
                      text="Toggle code: 0000 → None",
                      font=("Courier New", 18), fg="#00ffcc", bg="#1e1e2f")
    status.pack(pady=20)

    # 5) Poll toggles until West
    def poll_fortress():
        bits = "".join("1" if pin.value else "0" for pin in component_toggles)
        direction = toggle_code_to_dir.get(bits)
        status.config(text=f"Toggle code: {bits} → {direction or 'None'}")
        if direction == "West":
            tk.Label(window,
                     text="🎉 Correct! You head west and encounter a power barrier…",
                     font=("Helvetica", 16), fg="green", bg="#1e1e2f").pack(pady=20)
            window.after(1500, lambda: show_wires_screen(window))
        else:
            window.after(100, poll_fortress)

    poll_fortress()



def show_wires_screen(window):
    """
    Wires Puzzle:
    Displays the serial and a clear riddle hint, then monitors physical wires
    until the correct set (wires_target_list) is cut, defusing the barrier.
    """
    # 1) Clear UI
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")

    # 2) Show serial at top right
    tk.Label(window,
             text=f"Serial: {serial}",
             font=("Courier New", 12), fg="#ffffff", bg="#1e1e2f")

    # 3) Show barrier prompt & riddle hint
    hint = wires_hints.get(tuple(wires_target_list),
                           "Cut the correct wire(s) to deactivate the barrier.")
    tk.Label(window,
             text="⚡ Power Barrier Activated!",
             font=("Helvetica", 24, "bold"), fg="#00ffcc", bg="#1e1e2f").pack(pady=(40, 10))
    tk.Label(window,
             text=hint,
             font=("Helvetica", 16), fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center").pack(pady=20)

    # 4) Status label to show cut wires by letter
    status = tk.Label(window,
                      text="Cuts: []",
                      font=("Courier New", 18), fg="#00ffcc", bg="#1e1e2f")
    status.pack(pady=20)

    # 5) Poll loop: read raw wires, convert indices to letters, check target
    def poll_wires():
        cut_indices = [i for i, pin in enumerate(component_wires) if pin.value]
        # Convert 0->'A', 1->'B', etc.
        cut_letters = [chr(ord('A') + i) for i in cut_indices]
        status.config(text=f"Cuts: {cut_letters}")
        if cut_indices == wires_target_list:
            tk.Label(window,
                     text="✅ Barrier deactivated!",
                     font=("Helvetica", 16), fg="green", bg="#1e1e2f").pack(pady=20)
            window.after(1500, lambda: show_phantoms_lair(window))
        else:
            window.after(100, poll_wires)

    poll_wires()





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
