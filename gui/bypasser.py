import platform
import tkinter as tk
from tkinter import filedialog
from gui.theme import COLORS, FONT, TITLE_FONT
from core.database import search_signatures
from core.logger import add_log


# ─── Platform detection ───────────────────────────────────────────────────────
IS_LINUX = platform.system() == "Linux"

COMPACT_HEIGHT_THRESHOLD = 680 if IS_LINUX else 700
COMPACT_WIDTH_THRESHOLD  = 480 if IS_LINUX else 500


class BypasserFrame(tk.Frame):
    def __init__(self, parent, bypass_callback):
        super().__init__(parent, bg=COLORS["bg"])

        self.bind_all("<Button-1>", self.on_click_outside)

        # ── State ──────────────────────────────────────────────────────────────
        self.bypass_callback = bypass_callback
        self.file_path       = None
        self.is_enabled      = False
        self.ready           = False
        self.current_mode    = None
        self.resize_after_id = None

        # ── Card ───────────────────────────────────────────────────────────────
        card = tk.Frame(self, bg=COLORS["panel"])
        card.pack(fill="both", expand=True, padx=10, pady=6)

        self.inner = tk.Frame(card, bg=COLORS["panel"])
        self.inner.pack(fill="both", expand=True, padx=14, pady=10)

        # Single stretching column
        self.inner.grid_columnconfigure(0, weight=1)

        # ── Title ──────────────────────────────────────────────────────────────
        tk.Label(
            self.inner,
            text="Bypass Simulator",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=TITLE_FONT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(2, 14))

        # ── Extension input ────────────────────────────────────────────────────
        self._field_label(self.inner, "Select File Extension", row=1)
        self.search_wrapper, self.search_entry = self._make_input(
            self.inner,
            placeholder="e.g.  exe   pdf   docx",
            icon="🔍",
            row=2,
        )
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # ── Magic number input ─────────────────────────────────────────────────
        self._field_label(self.inner, "Magic Number  (auto-filled or custom)", row=3)
        self.magic_wrapper, self.custom_magic = self._make_input(
            self.inner,
            placeholder="e.g.  4D5A  (HEX)",
            icon="⚙",
            row=4,
        )
        self.custom_magic.bind("<KeyRelease>", self.on_magic_search)

        # ── Modify button ──────────────────────────────────────────────────────
        self.modify_btn = self._make_button(
            self.inner,
            "⚡  No File Selected",
            self.safe_modify,
            "#1e293b",
            enabled=False,
        )
        self.modify_btn.grid(row=5, column=0, pady=(18, 0))

        # ── Status label ───────────────────────────────────────────────────────
        self.status_label = tk.Label(
            self.inner,
            text="Status: N/A",
            bg=COLORS["panel"],
            fg=COLORS["subtext"],
            font=("Segoe UI", 9),
            anchor="center",
        )
        self.status_label.grid(row=6, column=0, sticky="ew", pady=(10, 4))

        # ── Resize listener ────────────────────────────────────────────────────
        self.winfo_toplevel().bind("<Configure>", self.on_resize)
        self.after(250, self._mark_ready)

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

        is_compact = (
            height < COMPACT_HEIGHT_THRESHOLD or
            width  < COMPACT_WIDTH_THRESHOLD
        )
        mode = "compact" if is_compact else "full"

        if mode != self.current_mode:
            self.current_mode = mode
            self._apply_compact(mode == "compact")

        # Keep status label wraplength in sync
        self.status_label.config(wraplength=max(180, width // 2 - 40))

    def _apply_compact(self, enabled: bool):
        if enabled:
            self.inner.grid_slaves(row=0)[0].grid_configure(pady=(2, 6))
            self.modify_btn.grid_configure(pady=(8, 0))
            self.status_label.grid_configure(pady=(6, 2))
            for wrapper in (self.search_wrapper, self.magic_wrapper):
                wrapper.grid_configure(pady=(3, 6))
        else:
            self.inner.grid_slaves(row=0)[0].grid_configure(pady=(2, 14))
            self.modify_btn.grid_configure(pady=(18, 0))
            self.status_label.grid_configure(pady=(10, 4))
            for wrapper in (self.search_wrapper, self.magic_wrapper):
                wrapper.grid_configure(pady=(5, 12))

    # ══════════════════════════════════════════════════════════════════════════
    # WIDGET FACTORIES
    # ══════════════════════════════════════════════════════════════════════════

    def _field_label(self, parent, text: str, row: int):
        """Small section label with left accent bar."""
        frame = tk.Frame(parent, bg=COLORS["panel"])
        frame.grid(row=row, column=0, sticky="ew", pady=(6, 0))
        frame.grid_columnconfigure(1, weight=1)

        tk.Frame(frame, bg=COLORS["secondary"], width=3, height=14).grid(
            row=0, column=0, padx=(0, 6)
        )
        tk.Label(
            frame,
            text=text,
            bg=COLORS["panel"],
            fg=COLORS["subtext"],
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

    def _make_input(self, parent, placeholder: str, icon: str, row: int):
        """
        Styled input: dark well + left icon + divider + entry.
        Returns (wrapper_frame, entry_widget).
        """
        wrapper = tk.Frame(
            parent,
            bg="#0f172a",
            highlightthickness=1,
            highlightbackground="#1e293b",
        )
        wrapper.grid(row=row, column=0, sticky="ew", pady=(5, 12))
        wrapper.grid_columnconfigure(0, weight=1)

        inner = tk.Frame(wrapper, bg="#0f172a")
        inner.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        inner.grid_columnconfigure(2, weight=1)

        col = 0
        if icon:
            tk.Label(
                inner,
                text=icon,
                bg="#0f172a",
                fg="#334155",
                font=("Segoe UI", 11),
                padx=8,
            ).grid(row=0, column=col, sticky="ns")
            col += 1

            tk.Frame(inner, bg="#1e293b", width=1).grid(
                row=0, column=col, sticky="ns", pady=6
            )
            col += 1

        entry = tk.Entry(
            inner,
            bg="#0f172a",
            fg=COLORS["text"],
            insertbackground=COLORS["secondary"],
            relief="flat",
            font=("Segoe UI", 10),
            bd=0,
        )
        entry.grid(row=0, column=col, sticky="ew", padx=10, pady=8)
        inner.grid_columnconfigure(col, weight=1)

        self._add_placeholder(entry, placeholder)

        entry.bind(
            "<FocusIn>",
            lambda e: wrapper.config(highlightbackground=COLORS["secondary"]),
            add="+",
        )
        entry.bind(
            "<FocusOut>",
            lambda e: wrapper.config(highlightbackground="#1e293b"),
            add="+",
        )

        return wrapper, entry

    def _make_button(self, parent, text: str, command, color: str, enabled: bool = True):
        fg     = "#020617" if enabled else COLORS["subtext"]
        cursor = "hand2"   if enabled else "arrow"

        btn = tk.Label(
            parent,
            text=text,
            bg=color,
            fg=fg,
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=10,
            cursor=cursor,
            anchor="center",
        )

        def on_enter(e):
            if self.is_enabled:
                btn.config(bg=self._lighten(COLORS["primary"], 0.15))

        def on_leave(e):
            if self.is_enabled:
                btn.config(bg=COLORS["primary"])

        def on_click(e):
            if not self.is_enabled:
                return
            btn.config(bg=self._lighten(COLORS["primary"], 0.30))
            parent.after(100, lambda: btn.config(bg=COLORS["primary"]))
            command()

        btn.bind("<Enter>",    on_enter)
        btn.bind("<Leave>",    on_leave)
        btn.bind("<Button-1>", on_click)

        return btn

    # ══════════════════════════════════════════════════════════════════════════
    # PLACEHOLDER
    # ══════════════════════════════════════════════════════════════════════════

    def _add_placeholder(self, entry: tk.Entry, text: str):
        entry.placeholder = text
        entry.insert(0, text)
        entry.config(fg=COLORS["subtext"])

        def on_focus_in(e):
            if entry.get() == text:
                entry.delete(0, tk.END)
                entry.config(fg=COLORS["text"])

        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, text)
                entry.config(fg=COLORS["subtext"])

        entry.bind("<FocusIn>",  on_focus_in,  add="+")
        entry.bind("<FocusOut>", on_focus_out, add="+")

    # ══════════════════════════════════════════════════════════════════════════
    # COLOR HELPER
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _lighten(color: str, factor: float = 0.1) -> str:
        color = color.lstrip("#")
        r, g, b = (int(color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ══════════════════════════════════════════════════════════════════════════
    # SEARCH — EXTENSION
    # ══════════════════════════════════════════════════════════════════════════

    def on_search(self, event):
        query = self.search_entry.get().strip()
        self.hide_magic_suggestions()

        if not query or query == getattr(self.search_entry, "placeholder", ""):
            self.hide_suggestions()
            return

        results = search_signatures(query.lower())
        if results:
            self.show_suggestions(results)
        else:
            self.hide_suggestions()

    def show_suggestions(self, results):
        self.hide_suggestions()

        self.popup = tk.Toplevel(self)
        self.popup.overrideredirect(True)
        self.popup.configure(bg="#000000")

        x      = self.search_wrapper.winfo_rootx()
        y      = self.search_wrapper.winfo_rooty() + self.search_wrapper.winfo_height()
        width  = max(220, self.search_wrapper.winfo_width())
        height = min(len(results), 5) * 38

        self.popup.geometry(f"{width}x{height}+{x}+{y}")
        self._build_popup_list(
            self.popup,
            results,
            fmt=lambda m, ex, cat, risk: f"  .{ex}   —   {cat}",
            on_select=lambda m, ex, cat, risk: self.select_suggestion(m, ex),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # SEARCH — MAGIC
    # ══════════════════════════════════════════════════════════════════════════

    def on_magic_search(self, event):
        query = self.custom_magic.get().strip()
        self.hide_suggestions()

        if not query or query == getattr(self.custom_magic, "placeholder", ""):
            self.hide_magic_suggestions()
            return

        results = search_signatures(query.lower())
        if results:
            self.show_magic_suggestions(results)
        else:
            self.hide_magic_suggestions()

    def show_magic_suggestions(self, results):
        self.hide_magic_suggestions()

        self.magic_popup = tk.Toplevel(self)
        self.magic_popup.overrideredirect(True)
        self.magic_popup.configure(bg="#000000")

        x      = self.magic_wrapper.winfo_rootx()
        y      = self.magic_wrapper.winfo_rooty() + self.magic_wrapper.winfo_height()
        width  = max(220, self.magic_wrapper.winfo_width())
        height = min(len(results), 5) * 38

        self.magic_popup.geometry(f"{width}x{height}+{x}+{y}")
        self._build_popup_list(
            self.magic_popup,
            results,
            fmt=lambda m, ex, cat, risk: f"  {m}   —   .{ex}",
            on_select=lambda m, ex, cat, risk: self.select_magic(m),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # POPUP LIST BUILDER
    # ══════════════════════════════════════════════════════════════════════════

    def _build_popup_list(self, window, results, fmt, on_select):
        container = tk.Frame(
            window,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground="#334155",
        )
        container.pack(fill="both", expand=True, padx=1, pady=1)

        for row in results:
            magic, ext, category, risk = row

            item = tk.Frame(container, bg=COLORS["panel"])
            item.pack(fill="x")

            try:
                is_high_risk = risk and int(risk) > 5
            except (ValueError, TypeError):
                is_high_risk = False

            accent = COLORS.get("danger", "#ef4444") if is_high_risk else COLORS.get("secondary", "#38bdf8")
            tk.Frame(item, bg=accent, width=3).pack(side="left", fill="y")

            label = tk.Label(
                item,
                text=fmt(magic, ext, category, risk),
                bg=COLORS["panel"],
                fg=COLORS["subtext"],
                anchor="w",
                padx=10,
                pady=9,
                font=("Segoe UI", 9),
            )
            label.pack(side="left", fill="x", expand=True)

            def on_enter(e, w=item, l=label):
                w.config(bg="#1e293b")
                l.config(bg="#1e293b", fg=COLORS["text"])

            def on_leave(e, w=item, l=label):
                w.config(bg=COLORS["panel"])
                l.config(bg=COLORS["panel"], fg=COLORS["subtext"])

            cb = lambda e, r=row: on_select(*r)

            for w in (item, label):
                w.bind("<Enter>",    on_enter)
                w.bind("<Leave>",    on_leave)
                w.bind("<Button-1>", cb)

    # ══════════════════════════════════════════════════════════════════════════
    # SELECT HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def select_suggestion(self, magic, ext):
        self.search_entry.config(fg=COLORS["text"])
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, ext)
        self.hide_suggestions()

    def select_magic(self, magic):
        self.custom_magic.config(fg=COLORS["text"])
        self.custom_magic.delete(0, tk.END)
        self.custom_magic.insert(0, magic)
        self.hide_magic_suggestions()

    # ══════════════════════════════════════════════════════════════════════════
    # HIDE POPUPS
    # ══════════════════════════════════════════════════════════════════════════

    def hide_suggestions(self):
        if hasattr(self, "popup") and self.popup.winfo_exists():
            self.popup.destroy()

    def hide_magic_suggestions(self):
        if hasattr(self, "magic_popup") and self.magic_popup.winfo_exists():
            self.magic_popup.destroy()

    # ══════════════════════════════════════════════════════════════════════════
    # CLICK OUTSIDE
    # ══════════════════════════════════════════════════════════════════════════

    def on_click_outside(self, event):
        widget = event.widget

        if hasattr(self, "popup") and self.popup.winfo_exists():
            if widget not in (self.search_entry,) and \
               not str(widget).startswith(str(self.popup)):
                self.hide_suggestions()

        if hasattr(self, "magic_popup") and self.magic_popup.winfo_exists():
            if widget not in (self.custom_magic,) and \
               not str(widget).startswith(str(self.magic_popup)):
                self.hide_magic_suggestions()

    # ══════════════════════════════════════════════════════════════════════════
    # FILE HANDLING
    # ══════════════════════════════════════════════════════════════════════════

    def set_file(self, path):
        self.file_path = path

        if path:
            self.is_enabled = True
            self.modify_btn.config(
                text="⚡  Modify File",
                bg=COLORS["primary"],
                fg="#020617",
                cursor="hand2",
            )
        else:
            self.is_enabled = False
            self.modify_btn.config(
                text="⚡  No File Selected",
                bg="#334155",
                fg=COLORS["subtext"],
                cursor="arrow",
            )

    # ══════════════════════════════════════════════════════════════════════════
    # MODIFY
    # ══════════════════════════════════════════════════════════════════════════

    def modify_file(self):
        ext   = self.search_entry.get().strip()
        magic = self.custom_magic.get().strip()

        if ext   == getattr(self.search_entry,  "placeholder", ""):
            ext   = ""
        if magic == getattr(self.custom_magic,  "placeholder", ""):
            magic = ""

        if not ext or not magic:
            self.status_label.config(
                text="Status: Extension & Magic required",
                fg=COLORS["warning"],
            )
            return

        magic = magic.upper()

        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(f"{ext.upper()} files", f"*.{ext}"), ("All files", "*.*")],
        )

        if not save_path:
            self.status_label.config(text="Status: Save cancelled", fg=COLORS["warning"])
            add_log("Save cancelled by user", show_ui=True)
            return

        success = self.bypass_callback(magic, ext, save_path, self.file_path)

        if success:
            self.status_label.config(text=f"Saved → {save_path}", fg=COLORS["primary"])
            add_log(f"File modified & saved: {save_path}")
        else:
            self.status_label.config(text="Modification Failed", fg=COLORS["danger"])
            add_log("File modification failed")

    def safe_modify(self):
        if not self.is_enabled:
            return
        self.modify_file()