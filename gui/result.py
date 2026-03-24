import platform
import tkinter as tk
from gui.theme import COLORS, TITLE_FONT, HEADING_PADX, HEADING_PADY


# ─── Platform detection ───────────────────────────────────────────────────────
IS_LINUX = platform.system() == "Linux"

COMPACT_HEIGHT_THRESHOLD = 680 if IS_LINUX else 700
COMPACT_WIDTH_THRESHOLD  = 480 if IS_LINUX else 500


class ResultFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])

        self.ready          = False
        self.current_mode   = None
        self.resize_after_id = None

        # ── Main container ─────────────────────────────────────────────────────
        self.container = tk.Frame(self, bg=COLORS["panel"])
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        self.container.grid_columnconfigure(0, weight=1)

        # ── Title ──────────────────────────────────────────────────────────────
        tk.Label(
            self.container,
            text="Scan Result",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=TITLE_FONT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=HEADING_PADX, pady=HEADING_PADY)

        # ── Info grid (Magic / Extension / Status) ─────────────────────────────
        self.info_frame = tk.Frame(self.container, bg=COLORS["panel"])
        self.info_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        self.info_frame.columnconfigure(1, weight=1)

        def info_row(row, key_text):
            tk.Label(
                self.info_frame,
                text=key_text,
                bg=COLORS["panel"],
                fg=COLORS["subtext"],
                anchor="w",
                width=14,           # fixed key column so values always align
            ).grid(row=row, column=0, sticky="w", pady=3)

            val = tk.Label(
                self.info_frame,
                text="—",
                bg=COLORS["panel"],
                fg=COLORS["text"],
                anchor="w",
            )
            val.grid(row=row, column=1, sticky="ew", padx=(10, 0))
            return val

        self.magic_value  = info_row(0, "Magic Number")
        self.ext_value    = info_row(1, "Extension")
        self.status_value = info_row(2, "Status")
        self.status_value.config(fg=COLORS["secondary"])

        # ── Thin separator ─────────────────────────────────────────────────────
        self.separator = tk.Frame(self.container, bg="#1e293b", height=1)
        self.separator.grid(row=2, column=0, sticky="ew", padx=10, pady=(4, 8))

        # ── Analysis section label ─────────────────────────────────────────────
        self.analysis_title = tk.Label(
            self.container,
            text="Analysis",
            bg=COLORS["panel"],
            fg=COLORS["subtext"],
            anchor="w",
            font=("Segoe UI", 9, "bold"),
        )
        self.analysis_title.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 6))

        # ── Analysis detail frame ──────────────────────────────────────────────
        self.analysis_frame = tk.Frame(self.container, bg=COLORS["panel"])
        self.analysis_frame.grid(row=4, column=0, sticky="nsew", padx=15, pady=(0, 10))
        self.analysis_frame.columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(4, weight=1)

        def analysis_row(row, key_text, bold=False, wrap=True):
            tk.Label(
                self.analysis_frame,
                text=key_text,
                bg=COLORS["panel"],
                fg=COLORS["subtext"],
                anchor="w",
                font=("Segoe UI", 8, "bold"),
            ).grid(row=row * 2, column=0, sticky="ew", pady=(6, 0))

            font = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
            val = tk.Label(
                self.analysis_frame,
                text="—",
                bg=COLORS["panel"],
                fg=COLORS["text"],
                font=font,
                anchor="w",
                justify="left",
                wraplength=400 if wrap else 0,
            )
            val.grid(row=row * 2 + 1, column=0, sticky="ew", pady=(0, 2))
            return val

        self.detected_label = analysis_row(0, "Detected Format", bold=True, wrap=False)
        self.reason_label   = analysis_row(1, "Analysis Reason",  bold=False, wrap=True)
        # self.yara_label     = analysis_row(2, "YARA Matches",     bold=False, wrap=False)

        # ── Resize listener ────────────────────────────────────────────────────
        self.winfo_toplevel().bind("<Configure>", self.on_resize)
        self.after(250, self._mark_ready)

        self.reset_view()

    # ══════════════════════════════════════════════════════════════════════════
    # RESPONSIVE
    # ══════════════════════════════════════════════════════════════════════════

    def _mark_ready(self):
        self.ready = True
        self.apply_resize()

    def on_resize(self, event):
        if not self.ready:
            return
        if event.widget is not self.winfo_toplevel():
            return
        if self.resize_after_id:
            self.after_cancel(self.resize_after_id)
        self.resize_after_id = self.after(150, self.apply_resize)

    def apply_resize(self):
        win    = self.winfo_toplevel()
        width  = win.winfo_width()
        height = win.winfo_height()

        # Keep reason label wraplength in sync so text never overflows
        wrap = max(180, width // 2 - 60)
        self.reason_label.config(wraplength=wrap)

        # Compact: hide the separator and shrink analysis section padding
        is_compact = (
            height < COMPACT_HEIGHT_THRESHOLD or
            width  < COMPACT_WIDTH_THRESHOLD
        )
        mode = "compact" if is_compact else "full"

        if mode != self.current_mode:
            self.current_mode = mode
            self._apply_compact(mode == "compact")

    def _apply_compact(self, enabled: bool):
        if enabled:
            # Remove separator padding to reclaim vertical space
            self.separator.grid_configure(pady=(2, 4))
            self.analysis_title.grid_configure(pady=(0, 2))
            self.analysis_frame.grid_configure(pady=(0, 4))
            # Tighten info rows
            for child in self.info_frame.winfo_children():
                child.grid_configure(pady=1)
        else:
            self.separator.grid_configure(pady=(4, 8))
            self.analysis_title.grid_configure(pady=(0, 6))
            self.analysis_frame.grid_configure(pady=(0, 10))
            for child in self.info_frame.winfo_children():
                child.grid_configure(pady=3)

    # ══════════════════════════════════════════════════════════════════════════
    # DATA
    # ══════════════════════════════════════════════════════════════════════════

    def reset_view(self):
        self.magic_value.config(text="—")
        self.ext_value.config(text="—")
        self.status_value.config(text="—", fg=COLORS["secondary"])
        self.detected_label.config(text="—")
        self.reason_label.config(text="Run a scan to see analysis details.")
        # self.yara_label.config(text="—")

    def update_result(self, result: dict):
        self.magic_value.config(text=result.get("magic_number", "—"))

        detected = result.get("detected", "unknown")
        self.ext_value.config(text=detected.upper())

        status     = result.get("status",     "UNKNOWN")
        risk_score = result.get("risk_score",  0)

        status_lower = status.lower()
        if status_lower == "malicious":
            color = COLORS["danger"]
        elif status_lower == "suspicious":
            color = COLORS["warning"]
        elif status_lower in ("safe", "legit"):
            color = COLORS["primary"]
        else:
            color = COLORS["secondary"]

        self.status_value.config(
            text=f"{status}  (Risk: {risk_score})",
            fg=color,
        )

        # YARA
        yara_matches = result.get("yara", [])
        yara_text = (
            "\n".join(f"🔴 {m.get('rule', 'unknown')}" for m in yara_matches)
            if yara_matches else "—"
        )

        self.detected_label.config(text=result.get("detected_format", "UNKNOWN"))
        self.reason_label.config(text=result.get("reason", "No analysis available."))
        # self.yara_label.config(text=yara_text)