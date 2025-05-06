#################################
# CSC 102 Defuse the Bomb Project
# Main Program


import tkinter as tk
from tkinter import ttk
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
from pathlib import Path       

toggle_code_to_dir = {
    "1000": "North",
    "1100": "East",
    "1110": "South",
    "1111": "West",
}

def int_to_index_list(val, width):
    return [i for i in range(width)
            if (val >> (width - 1 - i)) & 1]

wires_target_list = int_to_index_list(_wires_target_int, width=len(component_wires))


def indices_to_letters(indices):
    return [chr(ord('A') + i) for i in indices]

def generate_wire_riddle(target_indices):
    labels = indices_to_letters(target_indices)
    if len(labels) == 1:
        return f"Cut wire {labels[0]} to deactivate the barrier."
    return f"Cut wires {', '.join(labels[:-1])} and {labels[-1]} to deactivate the barrier."


window = tk.Tk()
window.title("Maze Runner")
window.geometry("800x600")
window.configure(bg="#1e1e2f")

# ---------- image cache ----------
window.imgs = SimpleNamespace()

def _load_png(filename: str) -> tk.PhotoImage:
    """Load a PNG (raise helpful error if missing)."""
    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path.resolve()}")
    return tk.PhotoImage(file=path)

# cache the three images so they stay in memory
window.imgs.circuit      = _load_png("circuit.png")
window.imgs.right_answer = _load_png("rightanswer.png")
window.imgs.wrong_answer = _load_png("wrong_answer.png")
# ---------------------------------

# Top bar for serial
top_frame = tk.Frame(window, bg="#1e1e2f")
top_frame.pack(side="top", fill="x")
serial_label = tk.Label(
    top_frame, text=f"Serial: {serial}",
    font=("Courier New", 12, "bold"),
    fg="red", bg="#1e1e2f"
)
serial_label.pack(side="right", padx=10, pady=5)
time_label = tk.Label(
    top_frame, text="",  # set in start_game
    font=("Courier New", 12, "bold"),
    fg="#00ff00", bg="#1e1e2f"
)
time_label.pack(side="left", padx=10, pady=5)
window.timer_label = time_label 

# Middle frame for all your puzzle screens
content_frame = tk.Frame(window, bg="#1e1e2f")
content_frame.pack(expand=True, fill="both")

bottom_frame = tk.Frame(window, bg="#1e1e2f")
bottom_frame.pack(side="bottom", fill="x")
progress = ttk.Progressbar(
    bottom_frame,
    orient="horizontal",
    mode="determinate",
    maximum=COUNTDOWN
)
progress.pack(fill="x", padx=10, pady=5)

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







def update_timer(window, display):
    mins, secs = divmod(window.remaining, 60)
    time_str = f"{mins:02d}:{secs:02d}"
    window.timer_label.config(text=f"Time Left: {time_str}")
    display.print(time_str)
    progress['value'] = window.remaining
    if window.remaining > 0:
        window.remaining -= 1
        window.after(1000, update_timer, window, display)
    else:
        show_failure_screen()

def start_game():
    # initialize countdown
    window.remaining = COUNTDOWN

    # hardware timer + LCD
    timer = Timer(component_7seg, initial_value=COUNTDOWN,
                  failure_callback=show_failure_screen)
    lcd = Lcd(window)
    lcd.setTimer(timer)
    timer.start()

    # kick off the UI timer
    update_timer(window, component_7seg)

    # first puzzle
    show_entrance_screen()




def show_welcome_screen():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="MAZE RUNNER",
             font=("Helvetica", 42, "bold"),
             fg="#00ffcc",
             bg="#1e1e2f")\
      .pack(pady=(60,30))

    input_frame = tk.Frame(content_frame, bg="#1e1e2f")
    input_frame.pack(pady=10)
    tk.Label(input_frame,
             text="Enter your name:",
             font=("Helvetica",16),
             fg="#ffffff",
             bg="#1e1e2f")\
      .pack(anchor="w", padx=10, pady=(0,5))
    name_entry = tk.Entry(input_frame,
                          font=("Helvetica",16),
                          width=25,
                          bg="#f0f0f0",
                          relief="flat",
                          justify="center")
    name_entry.pack(padx=10)

    def on_start():
        global player_name
        player_name = name_entry.get().strip() or "Player"
        show_instructions()

    tk.Button(content_frame,
              text="Start Game",
              font=("Helvetica",16,"bold"),
              bg="#00ffcc", fg="#000000",
              activebackground="#00ddaa",
              padx=20, pady=10, bd=0,
              command=on_start,
              cursor="hand2")\
      .pack(pady=40)

def show_instructions():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    instr = (
        f"Welcome, {player_name}!\n\n"
        "Your goal: Escape the maze before time runs out.\n"
        "- Use the button and keypad to unlock doors.\n"
        "- Flip toggles to shift walls (riddles will guide you).\n"
        "- Cut wires to disable barriers.\n\n"
        "Click 'Continue' when you're ready."
    )
    tk.Label(content_frame,
             text=instr,
             font=("Helvetica",15),
             fg="#ffffff",
             bg="#1e1e2f",
             justify="left",
             wraplength=600)\
      .pack(padx=50, pady=(60,30))

    tk.Button(content_frame,
              text="Continue",
              font=("Helvetica",16,"bold"),
              bg="#00ffcc", fg="#000000",
              activebackground="#00ddaa",
              padx=20, pady=10, bd=0,
              command=start_game)\
      .pack(pady=30)
    
def ensure_timer_support(window):
    if not hasattr(window, "bomb_display"):
        window.bomb_display = tk.Label(window)
    if not hasattr(window, "game_over"):
        window.game_over = lambda: show_failure_screen(window)



def show_entrance_screen():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text=(
               "🚪 Welcome to the Maze Runner Challenge!\n\n"
               "Press the BIG BUTTON when it flashes:\n"
               "🟢 GREEN = easy riddle\n"
               "🔴 RED   = hard   riddle"
             ),
             font=("Helvetica",18),
             fg="#ffffff", bg="#1e1e2f",
             justify="center", wraplength=600)\
      .pack(pady=50)

    tk.Button(content_frame,
              text="Start Puzzle",
              font=("Helvetica",16,"bold"),
              bg="#00ffcc", fg="#000000",
              activebackground="#00ddaa",
              padx=30, pady=12, bd=0,
              command=lambda: entrance_challenge())\
      .pack(pady=30)

def entrance_challenge():
    btn = Button(component_button_state, component_button_RGB)
    btn.start(); btn.join()
    if btn._easy_mode:
        prompt = "Enter the decimal code on the keypad: 610"
    else:
        prompt = ("Convert this binary to decimal, then enter on keypad:\n"
                  "1001100010")
    target = "610"
    show_entrance_puzzle_screen(prompt, target)

def show_entrance_puzzle_screen(prompt, target):
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text=prompt,
             font=("Helvetica",18),
             fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=(80,20))

    status = tk.Label(content_frame,
                      text="Entered: ",
                      font=("Courier New",20),
                      fg="#00ffcc", bg="#1e1e2f")
    status.pack(pady=(0,30))

    kd = Keypad(component_keypad, target)
    kd.start()

    def poll_keypad():
        status.config(text=f"Entered: {kd._value}")
        if kd._defused:
            for w in content_frame.winfo_children(): w.destroy()
            show_twilight_passage()
            return
        if kd._failed:
            status.config(text="❌ Wrong code — resetting…")
            window.after(1500, entrance_challenge)
            return
        window.after(100, poll_keypad)

    poll_keypad()

    
def show_twilight_passage():
    for w in content_frame.winfo_children(): w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="🌌 Twilight Passage",
             font=("Helvetica",24,"bold"),
             fg="#00ffcc", bg="#1e1e2f")\
      .pack(pady=(40,10))
    tk.Label(content_frame,
             text="Hint: Turn 180° from NORTH (i.e. SOUTH) on the toggles.",
             font=("Helvetica",16),
             fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=20)

    status = tk.Label(content_frame,
                      text="Toggle code: 0000 → None",
                      font=("Courier New",18),
                      fg="#00ffcc", bg="#1e1e2f")
    status.pack(pady=20)

    def poll_twilight():
        bits = "".join("1" if p.value else "0" for p in component_toggles)
        direction = toggle_code_to_dir.get(bits)
        status.config(text=f"Toggle code: {bits} → {direction or 'None'}")
        if direction == "South":
            tk.Label(content_frame,
                     text="🎉 Correct! You're heading south…",
                     font=("Helvetica",16), fg="green", bg="#1e1e2f")\
              .pack(pady=20)
            window.after(1500, show_circuit_puzzle)
        else:
            window.after(100, poll_twilight)

    poll_twilight()




# Door‑selection puzzle that shows a Boolean circuit diagram and two potential algebraic answers.  
# Click the correct picture to proceed.
def show_circuit_puzzle():
   
    # 0) Clear the centre pane
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    # 1) Show the problem diagram
    tk.Label(content_frame,
             image=window.imgs.circuit,
             bg="#1e1e2f").pack(pady=20)

    tk.Label(content_frame,
             text="Which door displays the *correct* Boolean expression for this circuit?",
             font=("Helvetica", 18),
             fg="#ffffff", bg="#1e1e2f",
             wraplength=650, justify="center").pack(pady=10)

    door_frame = tk.Frame(content_frame, bg="#1e1e2f")
    door_frame.pack(pady=15)


    def make_door(col: int, img: tk.PhotoImage, correct: bool):
        lbl = tk.Label(door_frame, image=img, cursor="hand2",
                       bg="#1e1e2f", borderwidth=0)
        lbl.grid(row=0, column=col, padx=40)

        def on_click(_event=None):
            # remove any previous feedback label
            for child in content_frame.pack_slaves():
                if getattr(child, "_feedback", False):
                    child.destroy()

            if correct:
                show_forgotten_fortress()
            else:
                fb = tk.Label(content_frame,
                              text="❌ Wrong door!  Try again.",
                              fg="#ff5555", bg="#1e1e2f",
                              font=("Helvetica", 14))
                fb._feedback = True
                fb.pack(pady=6)
                # auto‑hide after 1.5 s
                window.after(1500, fb.destroy)

        lbl.bind("<Button-1>", on_click)

    # 3) Build the two doors (left one is correct here)
    make_door(0, window.imgs.right_answer, correct=True)
    make_door(1, window.imgs.wrong_answer, correct=False)

class WiresComponent:
    def __init__(self, pins):
        self._pins = pins

    @property
    def cuts(self):
        # Indices of pins that have been cut (pin.value is True)
        return [i for i, pin in enumerate(self._pins) if pin.value]




def show_forgotten_fortress():
    for w in content_frame.winfo_children(): w.destroy()
    content_frame.configure(bg="#1e1e2f")

    # show serial at top of content as well
    tk.Label(content_frame,
             text=f"Serial: {serial}",
             font=("Courier New",12),
             fg="#ffffff", bg="#1e1e2f")\
      .pack(anchor="ne", padx=10, pady=(10,0))

    tk.Label(content_frame,
             text="🏰 Forgotten Fortress",
             font=("Helvetica",24,"bold"),
             fg="#00ffcc", bg="#1e1e2f")\
      .pack(pady=(40,10))
    tk.Label(content_frame,
             text="Riddle: Go where the sun sets.",
             font=("Helvetica",16),
             fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=20)

    status = tk.Label(content_frame,
                      text="Toggle code: 0000 → None",
                      font=("Courier New",18),
                      fg="#00ffcc", bg="#1e1e2f")
    status.pack(pady=20)

    # 5) Poll toggles until West
    def poll_fortress():
        bits = "".join("1" if p.value else "0" for p in component_toggles)
        direction = toggle_code_to_dir.get(bits)
        status.config(text=f"Toggle code: {bits} → {direction or 'None'}")
        if direction == "West":
            tk.Label(content_frame,
                     text="🎉 Correct! You head west and encounter a power barrier…",
                     font=("Helvetica",16), fg="green", bg="#1e1e2f")\
              .pack(pady=20)
            window.after(1500, show_wires_screen)
        else:
            window.after(100, poll_fortress)

    poll_fortress()



def show_wires_screen():
    for w in content_frame.winfo_children(): w.destroy()
    content_frame.configure(bg="#1e1e2f")

    # show serial
    tk.Label(content_frame,
             text=f"Serial: {serial}",
             font=("Courier New",12),
             fg="#ffffff", bg="#1e1e2f")\
      .pack(anchor="ne", padx=10, pady=(10,0))

    hint = generate_wire_riddle(wires_target_list)
    tk.Label(content_frame,
             text="⚡ Power Barrier Activated!",
             font=("Helvetica",24,"bold"),
             fg="#00ffcc", bg="#1e1e2f")\
      .pack(pady=(40,10))
    tk.Label(content_frame,
             text=hint,
             font=("Helvetica",16),
             fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=20)

    status = tk.Label(content_frame,
                      text="Cuts: []",
                      font=("Courier New",18),
                      fg="#00ffcc", bg="#1e1e2f")
    status.pack(pady=20)

    def poll_wires():
        cuts = [i for i,p in enumerate(component_wires) if p.value]
        letters = indices_to_letters(cuts)
        status.config(text=f"Cuts: {letters}")
        if cuts == wires_target_list:
            tk.Label(content_frame,
                     text="✅ Barrier deactivated!",
                     font=("Helvetica",16), fg="green", bg="#1e1e2f")\
              .pack(pady=20)
            window.after(1500, show_phantoms_lair)
        else:
            window.after(100, poll_wires)

    poll_wires()

def show_phantoms_lair():
    """
    Phantom’s Lair – player must set toggle switches to EAST (1100)
    to leave the room.  No GUI button.
    """
    # clear centre frame
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    # room title
    tk.Label(content_frame,
             text="👻 You’ve entered the Phantom's Lair!",
             font=("Helvetica", 20, "bold"),
             fg="#ffffff", bg="#1e1e2f")\
        .pack(pady=(40, 10))

    # riddle / hint
    tk.Label(content_frame,
             text="Hint → The sun rises in the EAST.\n"
                  "Flip the toggles until they read EAST (1100).",
             font=("Helvetica", 16),
             fg="#ffff99", bg="#1e1e2f",
             wraplength=600, justify="center")\
        .pack(pady=10)

    # live status of toggle code
    status = tk.Label(content_frame,
                      text="Toggle code: 0000 → None",
                      font=("Courier New", 18),
                      fg="#00ffcc", bg="#1e1e2f")
    status.pack(pady=20)

    # polling loop
    def poll_lair():
        bits = "".join("1" if p.value else "0" for p in component_toggles)
        direction = toggle_code_to_dir.get(bits)
        status.config(text=f"Toggle code: {bits} → {direction or 'None'}")
        if direction == "East":
            tk.Label(content_frame,
                     text="✅ Passage opens to the EAST!",
                     font=("Helvetica", 16), fg="green", bg="#1e1e2f")\
                .pack(pady=20)
            window.after(1500, show_mystic_hollow)
        else:
            window.after(100, poll_lair)

    poll_lair()


    
def show_chest_and_riddle():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="🧰 You found a chest filled with food!",
             font=("Helvetica", 18), fg="#00ffcc", bg="#1e1e2f")\
      .pack(pady=20)
    tk.Label(content_frame,
             text="🎉 Your life has been extended!",
             font=("Helvetica", 16), fg="#00ff00", bg="#1e1e2f")\
      .pack(pady=10)
    tk.Label(content_frame,
             text="To open the chest, solve this riddle:",
             font=("Helvetica", 16), fg="#ffffff", bg="#1e1e2f")\
      .pack(pady=20)

    riddle = ("I speak without a mouth and hear without ears. "
              "I have nobody, but I come alive with the wind. What am I?")
    tk.Label(content_frame,
             text=riddle,
             font=("Helvetica", 14), fg="#ddddff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=10)

    entry = tk.Entry(content_frame, font=("Helvetica", 14))
    entry.pack(pady=10)

    tk.Button(content_frame,
              text="Submit Answer",
              font=("Helvetica", 14),
              command=lambda: check_riddle_answer(entry.get()))\
      .pack(pady=10)
    tk.Button(content_frame,
              text="Skip Puzzle",
              font=("Helvetica", 14),
              command=show_flash_button_wall)\
      .pack(pady=5)


def check_riddle_answer(answer):
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    if answer.lower().strip() == "echo":
        tk.Label(content_frame,
                 text="✅ Correct! The chest opens and you're well-fed.",
                 font=("Helvetica", 16), fg="#00ff00", bg="#1e1e2f")\
          .pack(pady=20)
        window.after(2000, show_flash_button_wall)
    else:
        tk.Label(content_frame,
                 text="❌ That's not the right answer. Try again or skip.",
                 font=("Helvetica", 14), fg="red", bg="#1e1e2f")\
          .pack(pady=10)

def show_flash_button_wall():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="🚪 A wall blocks your path. Flash the hidden button to open it!",
             font=("Helvetica", 16), fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=30)

    tk.Button(content_frame,
              text="Flash Button",
              font=("Helvetica", 14),
              command=show_easy_puzzle)\
      .pack(pady=20)
    
def show_easy_puzzle():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="🧩 Easy Puzzle:\nWhat number comes next?\n2, 4, 6, 8, ?",
             font=("Helvetica", 16), fg="#ffffff", bg="#1e1e2f")\
      .pack(pady=20)

    entry = tk.Entry(content_frame, font=("Helvetica", 14))
    entry.pack(pady=10)

    tk.Button(content_frame,
              text="Submit",
              font=("Helvetica", 14),
              command=lambda: check_easy_puzzle(entry.get()))\
      .pack(pady=10)


def check_easy_puzzle(answer):
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    if answer.strip() == "10":
        tk.Label(content_frame,
                 text="✅ Correct!",
                 font=("Helvetica", 16), fg="#00ff00", bg="#1e1e2f")\
          .pack(pady=20)
        window.after(1500, show_hard_puzzle)
    else:
        tk.Label(content_frame,
                 text="❌ Try again!",
                 font=("Helvetica", 14), fg="red", bg="#1e1e2f")\
          .pack(pady=10)

def show_hard_puzzle():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    riddle = ("🧠 Hard Puzzle:\n"
              "I have keys but no locks. I have space but no room. "
              "You can enter but can’t go outside. What am I?")
    tk.Label(content_frame,
             text=riddle,
             font=("Helvetica", 16), fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=30)

    entry = tk.Entry(content_frame, font=("Helvetica", 14))
    entry.pack(pady=10)

    tk.Button(content_frame,
              text="Submit",
              font=("Helvetica", 14),
              command=lambda: check_hard_puzzle(entry.get()))\
      .pack(pady=10)


def check_hard_puzzle(answer):
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    if answer.lower().strip() == "keyboard":
        tk.Label(content_frame,
                 text="🎉 You solved all puzzles! Moving to Mystic Hollow…",
                 font=("Helvetica", 16), fg="#00ff00", bg="#1e1e2f")\
          .pack(pady=20)
        window.after(1500, show_mystic_hollow)
    else:
        tk.Label(content_frame,
                 text="❌ Not quite. Try again!",
                 font=("Helvetica", 14), fg="red", bg="#1e1e2f")\
          .pack(pady=10)


def show_mystic_hollow():
    """
    Mystic Hollow – Bomb Challenge:
    Flashes the physical button red/green, waits for the user to press it,
    then defuses (green) or explodes (red).
    """
    # 1) Clear only the center UI
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    # 2) Prompt text
    tk.Label(content_frame,
             text="💣 Mystic Hollow – The Bomb Challenge!",
             font=("Helvetica", 20, "bold"),
             fg="#ff6666", bg="#1e1e2f")\
      .pack(pady=30)
    tk.Label(content_frame,
             text="Only one flash will save you...\nPress the button when it glows GREEN to defuse, RED means BOOM!",
             font=("Helvetica", 16),
             fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=10)

    # 3) Start the hardware Button phase (flashing red/green)
    btn = Button(component_button_state, component_button_RGB)
    btn.start()
    btn.join()

    # 4) Branch on the last color lit:
    if btn._easy_mode:
        # _easy_mode==True corresponds to GREEN flashing
        defuse_success()
    else:
        # RED flashing
        explode_fail()

        

def show_chest_screen(window):
    """Supply Chest: Button→Keypad bonus puzzle."""
    for w in window.winfo_children(): w.destroy()
    window.configure(bg="#1e1e2f")
    tk.Label(window, text="🧭 Supply Chest Found!\n\nPress for a bonus puzzle…",
             font=("Helvetica",18), fg="#fff", bg="#1e1e2f",
             justify="center", wraplength=600).pack(pady=40)
    tk.Button(window, text="Begin Chest Puzzle", font=("Helvetica",16),
              command=lambda: run_chest_phase(window)).pack(pady=20)


def defuse_success():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="✅ Bomb defused! You’re a hero.",
             font=("Helvetica", 18), fg="#00ff00", bg="#1e1e2f")\
      .pack(pady=40)
    window.after(2000, show_victory_screen)


def explode_fail():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="💥 BOOM! You triggered the bomb.",
             font=("Helvetica", 18, "bold"), fg="red", bg="#1e1e2f")\
      .pack(pady=40)
    tk.Button(content_frame,
              text="Retry Mystic Hollow",
              font=("Helvetica", 14),
              command=show_mystic_hollow)\
      .pack(pady=20)

def show_final_screen():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="🚪 Final Door Ahead!\nPress 🟢 to defuse, 🔴 to boom.",
             font=("Helvetica", 18), fg="#ffffff", bg="#1e1e2f",
             justify="center", wraplength=600)\
      .pack(pady=40)
    tk.Button(content_frame,
              text="Press Button",
              font=("Helvetica", 16),
              command=defuse_success)\
      .pack(pady=10)
    
def show_victory_screen():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="🎉 YOU WIN!",
             font=("Helvetica", 28, "bold"), fg="#00ffcc", bg="#1e1e2f")\
      .pack(pady=40)
    tk.Label(content_frame,
             text="You defused the final challenge and escaped the maze!",
             font=("Helvetica", 18), fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=20)


def show_failure_screen():
    for w in content_frame.winfo_children():
        w.destroy()
    content_frame.configure(bg="#1e1e2f")

    tk.Label(content_frame,
             text="💥 BOOM!",
             font=("Helvetica", 28, "bold"), fg="#ff5555", bg="#1e1e2f")\
      .pack(pady=40)
    tk.Label(content_frame,
             text="The defusal failed. The maze collapses…",
             font=("Helvetica", 18), fg="#ffffff", bg="#1e1e2f",
             wraplength=600, justify="center")\
      .pack(pady=20)

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
    show_welcome_screen()      
    window.mainloop()
