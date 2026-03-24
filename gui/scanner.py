import os
import platform
import tkinter as tk
from tkinter import filedialog, messagebox
from gui.theme import COLORS, FONT, TITLE_FONT, HEADING_PADX, HEADING_PADY
from core.file_handler import get_extension, get_magic_number
from core.detector import analyze_file
from core.logger import add_log

try:
    from tkinterdnd2 import DND_FILES
except:
    DND_FILES = None


IS_LINUX   = platform.system() == "Linux"
IS_WINDOWS = platform.system() == "Windows"
IS_MAC     = platform.system() == "Darwin"

# Height threshold — full window height, fine to use directly
COMPACT_HEIGHT_THRESHOLD = 600 if IS_LINUX else 630

# Panel-width threshold — only relevant in "narrow" layout where
# the scanner spans the full window width (so threshold is window-scale)
COMPACT_PANEL_NARROW_THRESHOLD = 500 if IS_LINUX else 550


class ScannerFrame(tk.Frame):
    def __init__(self, parent, scan_callback, result_callback=None):
        super().__init__(parent, bg=COLORS["bg"])
        self.ready       = False
        self._layout     = "wide"   # set externally by home.py via set_layout()

        self.scan_callback   = scan_callback
        self.result_callback = result_callback
        self.file_path       = ""
        self.current_mode    = None
        self.resize_after_id = None

        # ── Card ──────────────────────────────────────────────────────────────
        self.card = tk.Frame(self, bg=COLORS["panel"])
        self.card.pack(fill="both", expand=True, padx=10, pady=10)
        self.card.grid_columnconfigure(0, weight=1)

        # ── Title ─────────────────────────────────────────────────────────────
        tk.Label(
            self.card, text="Original File",
            bg=COLORS["panel"], fg=COLORS["text"],
            font=TITLE_FONT, anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=HEADING_PADX, pady=HEADING_PADY)

        # ── Drop zone ─────────────────────────────────────────────────────────
        self.drop_zone = tk.Frame(
            self.card, bg="#020617",
            highlightthickness=2, highlightbackground=COLORS["secondary"],
            height=100,
        )
        self.drop_zone.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 2))
        self.drop_zone.grid_propagate(False)
        self.drop_zone.grid_columnconfigure(0, weight=1)

        tk.Label(
            self.drop_zone, text="⬇ DROP FILE HERE",
            bg="#020617", fg=COLORS["secondary"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, sticky="nsew")
        self.drop_zone.grid_rowconfigure(0, weight=1)

        # ── OR ────────────────────────────────────────────────────────────────
        self.or_label = tk.Label(
            self.card, text="OR",
            bg=COLORS["panel"], fg=COLORS["subtext"],
            font=("Segoe UI", 10, "bold"),
        )
        self.or_label.grid(row=2, column=0, pady=(2, 2))

        # ── Browse ────────────────────────────────────────────────────────────
        self.browse_button = self._make_button(
            self.card, "📁 Browse", self.browse_file, COLORS["secondary"]
        )
        self.browse_button.grid(row=3, column=0, pady=(2, 12))

        # ── File info labels ───────────────────────────────────────────────────
        self.file_name_label = tk.Label(
            self.card, text="📁 No file selected",
            bg=COLORS["panel"], fg=COLORS["text"],
            anchor="center", wraplength=300,
            cursor="hand2",
        )
        self.file_name_label.grid(row=4, column=0, sticky="ew", pady=(5, 2))

        self.orig_magic_label = tk.Label(
            self.card, text="Magic Number: N/A",
            bg=COLORS["panel"], fg=COLORS["text"],
            anchor="center", wraplength=300,
        )
        self.orig_magic_label.grid(row=5, column=0, sticky="ew", pady=2)

        self.orig_ext_label = tk.Label(
            self.card, text="Extension: N/A",
            bg=COLORS["panel"], fg=COLORS["text"],
            anchor="center", wraplength=300,
        )
        self.orig_ext_label.grid(row=6, column=0, sticky="ew", pady=(2, 5))

        self._wrap_labels = [
            self.file_name_label,
            self.orig_magic_label,
            self.orig_ext_label,
        ]

        # ── Scan button ────────────────────────────────────────────────────────
        self.scan_button = self._make_button(
            self.card, "⚡ Scan File", self.scan_file, COLORS["primary"]
        )
        self.scan_button.grid(row=7, column=0, pady=(25, 12))

        # ── DnD ───────────────────────────────────────────────────────────────
        if DND_FILES:
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<DragEnter>>", lambda e: self.drop_zone.config(bg="#1e293b"))
            self.drop_zone.dnd_bind("<<DragLeave>>", lambda e: self.drop_zone.config(bg="#020617"))
            self.drop_zone.dnd_bind("<<Drop>>",      self.drop_file)

        self.winfo_toplevel().bind("<Configure>", self.on_resize)
        self.after(400, self._mark_ready)

    # ══════════════════════════════════════════════════════════════════════════
    # PUBLIC API — called by home.py after every layout switch
    # ══════════════════════════════════════════════════════════════════════════

    def set_layout(self, layout: str):
        self._layout = layout
        print(f"[SCANNER] set_layout → {layout}")
        if self.ready:
            self.apply_resize()

    def _mark_ready(self):
        self.ready = True
        print(f"[SCANNER] _mark_ready, layout={self._layout}")
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
        win.update_idletasks()
        height = win.winfo_height()
        width  = win.winfo_width()

        print(f"[SCANNER] apply_resize: layout={self._layout} win={width}x{height} "
              f"H_thresh={COMPACT_HEIGHT_THRESHOLD} W_thresh={COMPACT_PANEL_NARROW_THRESHOLD}")

        if self._layout == "wide":
            # In wide mode panels are ~1/3 width — no width problem.
            # But height can still be too short, so check that.
            is_compact = height < COMPACT_HEIGHT_THRESHOLD
        else:
            # narrow: scanner is full-width, check both
            is_compact = (
                height < COMPACT_HEIGHT_THRESHOLD or
                width  < COMPACT_PANEL_NARROW_THRESHOLD
            )

        print(f"[SCANNER] is_compact={is_compact} current_mode={self.current_mode}")

        mode = "compact" if is_compact else "full"

        if mode != self.current_mode:
            self.current_mode = mode
            self._apply_compact(is_compact)

        # Wraplength: use panel width when available, else window width
        self.card.update_idletasks()
        panel_w = self.card.winfo_width()
        wrap = max(160, (panel_w if panel_w > 1 else width) - 40)
        for lbl in self._wrap_labels:
            lbl.config(wraplength=wrap)

        if not is_compact:
            drop_h = max(80, min(140, height // 6))
            self.drop_zone.config(height=drop_h)

    # ══════════════════════════════════════════════════════════════════════════
    # COMPACT MODE
    # ══════════════════════════════════════════════════════════════════════════

    def _apply_compact(self, enabled: bool):
        if not hasattr(self, "scan_button"):
            return

        if enabled:
            self.drop_zone.grid_remove()
            self.or_label.grid_remove()
            self.scan_button.grid_configure(pady=(10, 10))
        else:
            self.drop_zone.grid(    row=1, column=0, sticky="ew", padx=10, pady=(10, 2))
            self.or_label.grid(     row=2, column=0,               pady=(2, 2))
            self.browse_button.grid(row=3, column=0,               pady=(2, 12))
            self.scan_button.grid_configure(pady=(25, 12))

    # ══════════════════════════════════════════════════════════════════════════
    # BUTTON
    # ══════════════════════════════════════════════════════════════════════════

    def _make_button(self, parent, text, command, color):
        btn = tk.Label(
            parent, text=text, bg=color, fg="#020617",
            font=("Segoe UI", 10, "bold"), padx=14, pady=8, cursor="hand2",
        )
        lighter = self._lighten(color, 0.15)
        flash   = self._lighten(color, 0.30)
        btn.bind("<Enter>",    lambda e: btn.config(bg=lighter))
        btn.bind("<Leave>",    lambda e: btn.config(bg=color))
        btn.bind("<Button-1>", lambda e: self._click_flash(btn, color, flash, command))
        return btn

    def _click_flash(self, btn, base_color, flash_color, command):
        btn.config(bg=flash_color)
        self.after(100, lambda: btn.config(bg=base_color))
        command()

    @staticmethod
    def _lighten(color: str, factor: float = 0.1) -> str:
        color = color.lstrip("#")
        r, g, b = (int(color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ══════════════════════════════════════════════════════════════════════════
    # FILE HANDLING
    # ══════════════════════════════════════════════════════════════════════════

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.set_file(path)

    # ══════════════════════════════════════════════════════════════════════════
    # TOOLTIP
    # ══════════════════════════════════════════════════════════════════════════

    def _show_tooltip(self, widget, text: str):
        """Styled tooltip with left accent bar and fade-in effect."""
        self._tooltip = tk.Toplevel(self)
        self._tooltip.overrideredirect(True)
        self._tooltip.configure(bg="#0f172a")
        self._tooltip.attributes("-alpha", 0.0)   # start transparent

        # Outer border frame
        border = tk.Frame(self._tooltip, bg=COLORS["secondary"], padx=1, pady=1)
        border.pack()

        # Inner content
        inner = tk.Frame(border, bg="#0f172a")
        inner.pack()

        # Left accent bar
        tk.Frame(inner, bg=COLORS["secondary"], width=3).pack(side="left", fill="y")

        tk.Label(
            inner,
            text=f"  {text}  ",
            bg="#0f172a",
            fg=COLORS["text"],
            font=("Segoe UI", 9),
            padx=6,
            pady=5,
        ).pack(side="left")

        # Position below the widget
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 6
        self._tooltip.geometry(f"+{x}+{y}")

        # Fade in
        self._fade_in_tooltip(0.0)

    def _fade_in_tooltip(self, alpha: float):
        if not hasattr(self, "_tooltip") or not self._tooltip.winfo_exists():
            return
        alpha = min(alpha + 0.08, 1.0)
        self._tooltip.attributes("-alpha", alpha)
        if alpha < 1.0:
            self._tooltip.after(16, lambda: self._fade_in_tooltip(alpha))

    def _hide_tooltip(self):
        if hasattr(self, "_tooltip") and self._tooltip.winfo_exists():
            self._tooltip.destroy()

    def _bind_tooltip(self, widget, full_name: str):
        """Bind hover: tooltip + subtle label highlight."""
        widget.bind(
            "<Enter>",
            lambda e: (
                widget.config(fg=COLORS["secondary"]),
                self._show_tooltip(widget, full_name),
            ),
            add="+",
        )
        widget.bind(
            "<Leave>",
            lambda e: (
                widget.config(fg=COLORS["text"]),
                self._hide_tooltip(),
            ),
            add="+",
        )
    # ══════════════════════════════════════════════════════════════════════════
    # FILE HANDLING
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _truncate_name(name: str, max_len: int = 35) -> str:
        """Keep extension intact, truncate the stem in the middle with ellipsis."""
        if len(name) <= max_len:
            return name
        stem, _, ext = name.rpartition(".")
        if not stem:
            return name[:max_len - 1] + "…"
        ext_part  = f".{ext}"
        available = max_len - len(ext_part) - 1
        if available < 6:
            return name[:max_len - 1] + "…"
        half = available // 2
        return f"{stem[:half]}…{stem[-(available - half):]}{ext_part}"

    def set_file(self, path: str):
        self.file_path   = path
        raw_name         = os.path.basename(path)
        display_name     = self._truncate_name(raw_name)

        self.file_name_label.config(text=f"📁 {display_name}")

        # Only show tooltip if name was actually truncated
        self._hide_tooltip()
        if display_name != raw_name:
            self._bind_tooltip(self.file_name_label, raw_name)
        else:
            # Remove any previous tooltip bindings
            self.file_name_label.unbind("<Enter>")
            self.file_name_label.unbind("<Leave>")

        ext   = get_extension(path)
        magic = get_magic_number(path)

        self.orig_magic_label.config(
            text=f"Magic Number: {magic[:8] if magic else 'Unknown'}"
        )
        self.orig_ext_label.config(
            text=f"Extension: {ext if ext else 'Unknown'}"
        )
        if hasattr(self, "set_file_callback"):
            self.set_file_callback(path)

    # ══════════════════════════════════════════════════════════════════════════
    # SCAN
    # ══════════════════════════════════════════════════════════════════════════

    def scan_file(self):
        if not self.file_path:
            add_log("Scan attempted without file", show_ui=True)
            messagebox.showwarning("No File", "Please select a file first!")
            return
        add_log("Scan started", show_ui=True)
        try:
            result = analyze_file(self.file_path)
        except Exception as e:
            add_log(f"[ERROR] {str(e)}", show_ui=True)
            return
        add_log(
            f"Scan completed → Status={result.get('status')} | Risk={result.get('risk_score')}",
            show_ui=True,
        )
        if self.result_callback:
            self.result_callback(result)

    # ══════════════════════════════════════════════════════════════════════════
    # DnD
    # ══════════════════════════════════════════════════════════════════════════

    def drop_file(self, event):
        path = event.data.strip("{}")
        self.drop_zone.config(bg="#020617")
        self.set_file(path)