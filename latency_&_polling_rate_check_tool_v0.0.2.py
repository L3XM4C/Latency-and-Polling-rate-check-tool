import tkinter as tk
from collections import deque
import time
import mouse
import keyboard
import statistics

# ---------- CONFIG ----------
MOVE_WINDOW = 300             # recent move timestamps
MIN_SAMPLES_FOR_REPORT = 6    # minimum samples to report Hz
MIN_INTERVAL_US = 50          # ignore intervals shorter than 50 µs
MAX_REALISTIC_HZ = 8000       # absolute maximum Hz
MAX_INTERVAL_MS_TO_CONSIDER = 100.0  # ignore very large intervals
# ----------------------------

# state
move_timestamps_ns = deque(maxlen=MOVE_WINDOW)

last_key_ns = None
keyboard_fastest_ms = float('inf')

fastest_move_hz = 0.0  # max of current estimated polling rate

# helpers
def ns_now():
    return time.perf_counter_ns()

# ---------- event handlers ----------
def on_move(e):
    try:
        t = ns_now()
        move_timestamps_ns.append(t)
    except Exception:
        pass

def on_key(e):
    global last_key_ns, keyboard_fastest_ms
    try:
        t = ns_now()
        if last_key_ns is not None:
            interval_us = (t - last_key_ns) / 1000.0
            interval_ms = interval_us / 1000.0
            if interval_ms > 0:
                if interval_ms < keyboard_fastest_ms:
                    keyboard_fastest_ms = interval_ms
        last_key_ns = t
    except Exception:
        pass

# ---------- aggregation ----------
def estimate_mouse_polling():
    """
    Returns:
        median_ms: median of recent intervals
        current_hz: 1000 / median_ms
    """
    if len(move_timestamps_ns) < MIN_SAMPLES_FOR_REPORT:
        return (None, None)
    intervals_ms = []
    for i in range(1, len(move_timestamps_ns)):
        diff_ns = move_timestamps_ns[i] - move_timestamps_ns[i-1]
        us = diff_ns / 1000.0
        ms = us / 1000.0
        if us >= MIN_INTERVAL_US and ms < MAX_INTERVAL_MS_TO_CONSIDER:
            intervals_ms.append(ms)
    if len(intervals_ms) < MIN_SAMPLES_FOR_REPORT - 1:
        return (None, None)
    median_ms = statistics.median(intervals_ms)
    if median_ms <= 0:
        return (None, None)
    current_hz = 1000.0 / median_ms
    if current_hz > MAX_REALISTIC_HZ:
        current_hz = MAX_REALISTIC_HZ
    return median_ms, current_hz

# ---------- GUI ----------
root = tk.Tk()
root.title("Latency & Polling Rate Tool by github.com/L3XM4C v0.0.2")
root.geometry("520x350")

# keyboard
tk.Label(root, text="Fastest Keyboard Latency:", font=("Arial", 12)).pack(pady=(8,0))
keyboard_fast_label = tk.Label(root, text="N/A", font=("Arial", 16))
keyboard_fast_label.pack()

# mouse movement interval
tk.Label(root, text="Median Mouse Move Interval (ms):", font=("Arial", 12)).pack(pady=(8,0))
mouse_move_med_label = tk.Label(root, text="N/A", font=("Arial", 16))
mouse_move_med_label.pack()

tk.Label(root, text="Current Estimated Polling Rate (Hz):", font=("Arial", 12)).pack(pady=(8,0))
mouse_poll_label = tk.Label(root, text="N/A", font=("Arial", 16))
mouse_poll_label.pack()

tk.Label(root, text="Fastest Mouse Polling Rate Detected (Hz):", font=("Arial", 12)).pack(pady=(8,0))
mouse_poll_fast_label = tk.Label(root, text="N/A", font=("Arial", 16))
mouse_poll_fast_label.pack()

# ---------- day/night toggle ----------
def toggle_day_night():
    global day_mode
    day_mode = not day_mode
    if day_mode:
        root.configure(bg="white")
        for widget in root.winfo_children():
            widget.configure(bg="white", fg="black")
        toggle_btn.configure(bg="white")
    else:
        root.configure(bg="black")
        for widget in root.winfo_children():
            widget.configure(bg="black", fg="white")
        toggle_btn.configure(bg="black")

day_mode = True
sun_img = tk.PhotoImage(width=20, height=20)
moon_img = tk.PhotoImage(width=20, height=20)
toggle_btn = tk.Button(root, image=sun_img, command=toggle_day_night, bg="white")
toggle_btn.pack(pady=(10,0))

# ---------- listeners ----------
mouse.hook(on_move)
keyboard.hook(on_key)

# ---------- periodic update ----------
def gui_update():
    global fastest_move_hz

    # keyboard fastest
    if keyboard_fastest_ms != float('inf') and keyboard_fastest_ms is not None:
        keyboard_fast_label.config(text=f"{keyboard_fastest_ms:.3f} ms")
    else:
        keyboard_fast_label.config(text="N/A")

    # mouse polling
    median_ms, current_hz = estimate_mouse_polling()
    if median_ms is not None:
        mouse_move_med_label.config(text=f"{median_ms:.3f} ms")
        mouse_poll_label.config(text=f"{current_hz:.1f} Hz")
        # update fastest detected as max of current_hz
        if current_hz > fastest_move_hz:
            fastest_move_hz = current_hz
    else:
        mouse_move_med_label.config(text="N/A")
        mouse_poll_label.config(text="N/A")

    if fastest_move_hz > 0:
        mouse_poll_fast_label.config(text=f"{fastest_move_hz:.1f} Hz")
    else:
        mouse_poll_fast_label.config(text="N/A")

    root.after(80, gui_update)  # update ~12.5 times/sec

root.after(80, gui_update)
root.mainloop()
