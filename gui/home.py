import sys
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinterdnd2 import TkinterDnD
import customtkinter as ctk
import os
import platform

from core.logger import add_log, set_log_widget, LOG_FILE, clear_memory
from core.bypass_engine import apply_bypass
from gui.scanner import ScannerFrame
from gui.bypasser import BypasserFrame
from gui.result import ResultFrame
from gui.theme import COLORS
from core.detector import detect_file


IS_LINUX = platform.system() == "Linux"

# Window width below which we go from 3-col → stacked layout
STACK_THRESHOLD = 900 if IS_LINUX else 950


# =========================================================
# BACKEND
# =========================================================

def scan_handler(file_path):
    result = detect_file(file_path)
    add_log(f"Scanned file: {os.path.basename(file_path)}")
    add_log(
        f"SCAN DETAILS → Magic={result.get('magic_number')} | "
        f"Ext={result.get('extension')} | Status={result.get('status')}",
        show_ui=False,
    )
    return result


def bypass_handler(magic, ext, save_path, file_path):
    if not file_path:
        add_log("[ERROR] No file selected for bypass")
        return False
    success = apply_bypass(file_path, magic, ext, save_path)
    if success:
        add_log("Bypass applied successfully")
        add_log(f"Bypass details → Magic={magic}, Ext={ext}", show_ui=False)
    else:
        add_log("Bypass failed", show_ui=True)
        add_log(f"Bypass failed → Magic={magic}, Ext={ext}", show_ui=False)
    return success


# =========================================================
# HELPERS
# =========================================================

def _lighten(color: str, factor: float = 0.15) -> str:
    color = color.lstrip("#")
    r, g, b = (int(color[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def create_button(parent, text, command, color):
    btn = tk.Label(
        parent, text=text, bg=color, fg="#020617",
        font=("Segoe UI", 10, "bold"), padx=14, pady=8, cursor="hand2",
    )
    btn.bind("<Enter>",    lambda e: btn.config(bg=_lighten(color, 0.20)))
    btn.bind("<Leave>",    lambda e: btn.config(bg=color))
    btn.bind("<Button-1>", lambda e: [
        btn.config(bg=_lighten(color, 0.35)),
        parent.after(100, lambda: btn.config(bg=color)),
        command(),
    ])
    return btn


def load_logs(logs_text):
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs_text.configure(state="normal")
            logs_text.insert(tk.END, "".join(f.readlines()[-50:]))
            logs_text.configure(state="disabled")


def clear_logs(logs_text):
    logs_text.configure(state="normal")
    logs_text.delete(1.0, tk.END)
    logs_text.configure(state="disabled")
    clear_memory()

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# =========================================================
# MAIN
# =========================================================

def start_app():
    root = TkinterDnD.Tk()
    root.title("HexSentinel – Malicious File Detection & Evasion Simulator")
    icon_path = resource_path("icon.ico")
    if platform.system() == "Windows":
        root.iconbitmap(icon_path)
    else:
        # Linux/Mac → use PNG instead
        if os.path.exists(icon_path.replace(".ico", ".png")):
            root.iconphoto(True, tk.PhotoImage(file=icon_path.replace(".ico", ".png")))
    root.configure(bg=COLORS["bg"])
    root.geometry("1200x700")
    root.minsize(700, 480)

    ttk.Style().theme_use("clam")
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Row 0 = panels, Row 1 = logs
    root.grid_rowconfigure(0, weight=3)
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # ── Panel container ───────────────────────────────────────────────────────
    container = tk.Frame(root, bg=COLORS["bg"])
    container.grid(row=0, column=0, sticky="nsew")

    # Wrapper frames — the layout manager moves these around
    left   = tk.Frame(container, bg=COLORS["bg"])
    center = tk.Frame(container, bg=COLORS["bg"])
    right  = tk.Frame(container, bg=COLORS["bg"])

    for f in (left, center, right):
        f.grid_rowconfigure(0, weight=1)
        f.grid_columnconfigure(0, weight=1)

    # ── Widgets ───────────────────────────────────────────────────────────────
    result_frame   = ResultFrame(center)
    scanner_frame  = ScannerFrame(left,  scan_handler, result_frame.update_result)
    bypasser_frame = BypasserFrame(right, bypass_handler)

    result_frame.grid(  row=0, column=0, sticky="nsew")
    scanner_frame.grid( row=0, column=0, sticky="nsew")
    bypasser_frame.grid(row=0, column=0, sticky="nsew")

    scanner_frame.set_file_callback = bypasser_frame.set_file

    # ── Log panel ─────────────────────────────────────────────────────────────
    logs_frame = tk.Frame(root, bg=COLORS["panel"])
    logs_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    logs_frame.grid_rowconfigure(1, weight=1)
    logs_frame.grid_columnconfigure(0, weight=1)

    header = tk.Frame(logs_frame, bg=COLORS["panel"])
    header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))

    tk.Label(
        header, text="Logs / History",
        bg=COLORS["panel"], fg=COLORS["text"],
        font=("Segoe UI", 11, "bold"),
    ).pack(side="left")

    logs_text = scrolledtext.ScrolledText(
        logs_frame, height=7,
        bg="#020617", fg=COLORS["text"],
        insertbackground=COLORS["text"],
        font=("Consolas", 9), state="disabled",
        relief="flat", borderwidth=0,
    )
    set_log_widget(logs_text)
    logs_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

    create_button(header, "🧹 Clear", lambda: clear_logs(logs_text), COLORS["danger"]).pack(side="right")
    # load_logs(logs_text)

    # ── Responsive layout manager ─────────────────────────────────────────────
    current_layout = [None]   # mutable cell so the closure can write to it
    resize_job     = [None]

    def apply_layout():
        root.update_idletasks()
        w = root.winfo_width()

        layout = "wide" if w >= STACK_THRESHOLD else "narrow"
        layout_changed = layout != current_layout[0]

        if layout_changed:
            current_layout[0] = layout

            # Detach all three wrappers
            for f in (left, center, right):
                f.grid_forget()

            for i in range(4):
                container.grid_columnconfigure(i, weight=0)
                container.grid_rowconfigure(i, weight=0)

            if layout == "wide":
                for i in range(3):
                    container.grid_columnconfigure(i, weight=1)
                container.grid_rowconfigure(0, weight=1)
                left.grid(  row=0, column=0, sticky="nsew", padx=(10, 4), pady=10)
                center.grid(row=0, column=1, sticky="nsew", padx=4,       pady=10)
                right.grid( row=0, column=2, sticky="nsew", padx=(4, 10), pady=10)
            else:
                container.grid_columnconfigure(0, weight=1)
                container.grid_columnconfigure(1, weight=1)
                container.grid_rowconfigure(0, weight=1)
                container.grid_rowconfigure(1, weight=1)
                left.grid(  row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=(10, 4))
                center.grid(row=1, column=0, sticky="nsew", padx=(10, 4), pady=(4, 10))
                right.grid( row=1, column=1, sticky="nsew", padx=(4, 10), pady=(4, 10))

        # Always notify scanner — even if layout string didn't change,
        # the window HEIGHT may have changed and compact needs to re-evaluate.
        scanner_frame.set_layout(layout)

    def on_root_resize(event):
        if event.widget is not root:
            return
        if resize_job[0]:
            root.after_cancel(resize_job[0])
        resize_job[0] = root.after(150, apply_layout)

    root.bind("<Configure>", on_root_resize)
    root.after(300, apply_layout)   # initial pass after widgets settle

    root.mainloop()


if __name__ == "__main__":
    start_app()