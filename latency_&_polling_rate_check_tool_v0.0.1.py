import tkinter as tk
import time
import keyboard
import mouse

# -------------------------
# GLOBAL VARIABLES
# -------------------------

# Keyboard
last_key_time = None
keyboard_latency_fastest = float("inf")

# Mouse Movement Polling
last_move_time = None
poll_interval_fastest_ms = float("inf")
poll_rate_current_hz = 0
poll_rate_fastest_hz = 0

# SAFETY LIMITS
MIN_INTERVAL_MS = 0.010      # 0.01 ms = max 100,000 Hz (prevents float spikes)
MAX_REALISTIC_HZ = 8000      # cap fastest Hz to real-world limit

# Day/Night Mode
is_day_mode = True

# -------------------------
# KEYBOARD HANDLER
# -------------------------

def on_key(event):
    global last_key_time, keyboard_latency_fastest
    now = time.perf_counter()
    if last_key_time is not None:
        latency = (now - last_key_time) * 1000
        if 0 < latency < keyboard_latency_fastest:
            keyboard_latency_fastest = latency
    last_key_time = now
    return False

keyboard.hook(on_key)

# -------------------------
# MOUSE MOVE HANDLER
# -------------------------

def on_move(event):
    global last_move_time
    global poll_interval_fastest_ms
    global poll_rate_current_hz
    global poll_rate_fastest_hz

    now = time.perf_counter()
    if last_move_time is not None:
        interval = now - last_move_time
        ms = interval * 1000

        if ms >= MIN_INTERVAL_MS:
            hz = 1 / interval
            poll_rate_current_hz = hz

            if 0 < hz < MAX_REALISTIC_HZ and hz > poll_rate_fastest_hz:
                poll_rate_fastest_hz = hz

            if ms < poll_interval_fastest_ms:
                poll_interval_fastest_ms = ms

    last_move_time = now
    return False

mouse.hook(on_move)

# -------------------------
# GUI UPDATE LOOP
# -------------------------

def update_gui():
    if keyboard_latency_fastest != float("inf"):
        keyboard_fast_label.config(text=f"{keyboard_latency_fastest:.3f} ms")

    if poll_interval_fastest_ms != float("inf"):
        mouse_poll_fast_label.config(text=f"{poll_interval_fastest_ms:.3f} ms")

    poll_rate_label.config(text=f"{poll_rate_current_hz:.0f} Hz")
    fastest_hz_label.config(text=f"{poll_rate_fastest_hz:.0f} Hz")

    root.after(10, update_gui)

# -------------------------
# DAY/NIGHT MODE TOGGLE
# -------------------------

def toggle_day_night():
    global is_day_mode
    is_day_mode = not is_day_mode

    if is_day_mode:
        bg_color = "white"
        fg_color = "black"
        toggle_button.config(text="🌙 Night Mode")
    else:
        bg_color = "black"
        fg_color = "white"
        toggle_button.config(text="☀️ Day Mode")

    for widget in root.winfo_children():
        try:
            widget.config(bg=bg_color, fg=fg_color)
        except:
            try:
                for child in widget.winfo_children():
                    child.config(bg=bg_color, fg=fg_color)
            except:
                pass
    root.config(bg=bg_color)

# -------------------------
# TKINTER GUI SETUP
# -------------------------

root = tk.Tk()
root.title("Latency & Polling Rate Tool by github.com/L3XM4C v0.0.1")
root.geometry("500x350")
root.config(bg="white")

# Keyboard
tk.Label(root, text="Fastest Keyboard Latency:", font=("Arial", 14), bg="white").pack()
keyboard_fast_label = tk.Label(root, text="0.00 ms", font=("Arial", 18), bg="white")
keyboard_fast_label.pack()

# Mouse movement
tk.Label(root, text="Fastest Mouse Movement Interval:", font=("Arial", 14), bg="white").pack()
mouse_poll_fast_label = tk.Label(root, text="0.00 ms", font=("Arial", 18), bg="white")
mouse_poll_fast_label.pack()

tk.Label(root, text="Current Mouse Polling Rate:", font=("Arial", 14), bg="white").pack()
poll_rate_label = tk.Label(root, text="0 Hz", font=("Arial", 18), bg="white")
poll_rate_label.pack()

tk.Label(root, text="Fastest Mouse Polling Rate Detected:", font=("Arial", 14), bg="white").pack()
fastest_hz_label = tk.Label(root, text="0 Hz", font=("Arial", 18), bg="white")
fastest_hz_label.pack()

# Day/Night toggle button
toggle_button = tk.Button(root, text="🌙 Night Mode", font=("Arial", 14), command=toggle_day_night)
toggle_button.pack(pady=10)

# Start GUI update loop
root.after(10, update_gui)
root.mainloop()
