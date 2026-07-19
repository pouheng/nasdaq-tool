import tkinter as tk
from tkinter import ttk

THEMES = {
    "H4CK3R": {
        "label": "H4CK3R",
        "bg_dark": "#0a0a0a",
        "bg_card": "#0d0d0d",
        "bg_input": "#151515",
        "fg_primary": "#00ff41",
        "fg_secondary": "#005f00",
        "fg_accent": "#00ffaa",
        "fg_green": "#00ff41",
        "fg_red": "#ff3355",
        "fg_yellow": "#ffcc00",
        "btn_bg": "#111111",
        "btn_active": "#003300",
        "select_bg": "#002200",
    },
    "MATRIX": {
        "label": "MATRIX",
        "bg_dark": "#000000",
        "bg_card": "#000000",
        "bg_input": "#0a0a0a",
        "fg_primary": "#00cc00",
        "fg_secondary": "#003300",
        "fg_accent": "#66ff66",
        "fg_green": "#00cc00",
        "fg_red": "#ff0000",
        "fg_yellow": "#cccc00",
        "btn_bg": "#080808",
        "btn_active": "#001a00",
        "select_bg": "#001a00",
    },
    "DRACULA": {
        "label": "DRACULA",
        "bg_dark": "#282a36",
        "bg_card": "#2d2f3e",
        "bg_input": "#363849",
        "fg_primary": "#f8f8f2",
        "fg_secondary": "#6272a4",
        "fg_accent": "#ff79c6",
        "fg_green": "#50fa7b",
        "fg_red": "#ff5555",
        "fg_yellow": "#f1fa8c",
        "btn_bg": "#3a3d54",
        "btn_active": "#44475a",
        "select_bg": "#44475a",
    },
    "NORD": {
        "label": "NORD",
        "bg_dark": "#2e3440",
        "bg_card": "#353c4a",
        "bg_input": "#3b4252",
        "fg_primary": "#d8dee9",
        "fg_secondary": "#616e88",
        "fg_accent": "#88c0d0",
        "fg_green": "#a3be8c",
        "fg_red": "#bf616a",
        "fg_yellow": "#ebcb8b",
        "btn_bg": "#434c5e",
        "btn_active": "#4c566a",
        "select_bg": "#4c566a",
    },
    "SOLARIZED": {
        "label": "SOLARIZED",
        "bg_dark": "#002b36",
        "bg_card": "#073642",
        "bg_input": "#083f4b",
        "fg_primary": "#839496",
        "fg_secondary": "#586e75",
        "fg_accent": "#2aa198",
        "fg_green": "#859900",
        "fg_red": "#dc322f",
        "fg_yellow": "#b58900",
        "btn_bg": "#094752",
        "btn_active": "#0b525f",
        "select_bg": "#0b525f",
    },
    "MONOKAI": {
        "label": "MONOKAI",
        "bg_dark": "#272822",
        "bg_card": "#2c2d27",
        "bg_input": "#34352e",
        "fg_primary": "#f8f8f2",
        "fg_secondary": "#75715e",
        "fg_accent": "#a6e22e",
        "fg_green": "#a6e22e",
        "fg_red": "#f92672",
        "fg_yellow": "#e6db74",
        "btn_bg": "#3d3e37",
        "btn_active": "#494a42",
        "select_bg": "#494a42",
    },
}

FONT_FIXED = "Consolas"
FONT_UI = "Consolas"


def get_theme_names():
    return list(THEMES.keys())


def apply_theme(root, theme_name="H4CK3R"):
    colors = THEMES.get(theme_name, THEMES["H4CK3R"])
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=colors["bg_dark"])

    style.configure(
        ".",
        background=colors["bg_dark"],
        foreground=colors["fg_primary"],
        troughcolor=colors["bg_card"],
        selectbackground=colors["select_bg"],
        fieldbackground=colors["bg_input"],
        font=(FONT_UI, 10),
    )
    style.configure("TFrame", background=colors["bg_dark"])
    style.configure(
        "TLabel",
        background=colors["bg_dark"],
        foreground=colors["fg_primary"],
        font=(FONT_UI, 10),
    )
    style.configure(
        "TButton",
        background=colors["btn_bg"],
        foreground=colors["fg_primary"],
        bordercolor=colors["bg_card"],
        focuscolor="none",
        relief=tk.RAISED,
        font=(FONT_UI, 10, "bold"),
    )
    style.map(
        "TButton",
        background=[("active", colors["btn_active"]), ("pressed", colors["bg_card"])],
        foreground=[("active", colors["fg_accent"])],
    )
    style.configure(
        "TEntry",
        fieldbackground=colors["bg_input"],
        foreground=colors["fg_primary"],
        insertcolor=colors["fg_primary"],
        bordercolor=colors["bg_card"],
        font=(FONT_UI, 10),
    )
    style.map("TEntry", fieldbackground=[("focus", colors["bg_card"])])
    style.configure(
        "TCombobox",
        fieldbackground=colors["bg_input"],
        foreground=colors["fg_primary"],
        arrowcolor=colors["fg_primary"],
        font=(FONT_UI, 10),
    )
    style.map("TCombobox", fieldbackground=[("focus", colors["bg_card"])])
    style.configure(
        "TNotebook",
        background=colors["bg_dark"],
        foreground=colors["fg_primary"],
        tabmargins=[0, 0, 0, 0],
    )
    style.configure(
        "TNotebook.Tab",
        background=colors["btn_bg"],
        foreground=colors["fg_primary"],
        padding=[12, 4],
        focuscolor="none",
        font=(FONT_UI, 9),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", colors["bg_card"]), ("active", colors["btn_active"])],
        foreground=[("selected", colors["fg_accent"])],
    )
    style.configure(
        "TLabelframe",
        background=colors["bg_dark"],
        foreground=colors["fg_accent"],
        bordercolor=colors["bg_card"],
        relief=tk.FLAT,
        font=(FONT_UI, 9, "bold"),
    )
    style.configure(
        "TLabelframe.Label",
        background=colors["bg_dark"],
        foreground=colors["fg_accent"],
        font=(FONT_UI, 9, "bold"),
    )
    style.configure(
        "Horizontal.TProgressbar",
        background=colors["fg_accent"],
        troughcolor=colors["bg_card"],
        bordercolor=colors["bg_dark"],
        lightcolor=colors["fg_accent"],
        darkcolor=colors["fg_accent"],
    )
    style.configure(
        "Vertical.TScrollbar",
        background=colors["bg_input"],
        troughcolor=colors["bg_dark"],
        bordercolor=colors["bg_dark"],
        arrowcolor=colors["fg_primary"],
    )
    style.map("Vertical.TScrollbar", background=[("active", colors["btn_active"])])
    style.configure("TPanedwindow", background=colors["bg_dark"])
    style.configure("Sash", sashthickness=3, sashpad=0, handlepad=0)
    style.map("Sash", background=[("active", colors["fg_accent"])])

    for widget in root.winfo_children():
        _apply_theme_to_widget(widget, colors)

    _apply_matplotlib_style(colors)

    return colors


def _apply_theme_to_widget(widget, colors):
    if isinstance(widget, tk.Text):
        widget.configure(
            bg=colors["bg_input"],
            fg=colors["fg_primary"],
            insertbackground=colors["fg_primary"],
            selectbackground=colors["select_bg"],
            selectforeground=colors["fg_primary"],
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=colors["bg_card"],
            highlightcolor=colors["fg_accent"],
            padx=8,
            pady=8,
            font=(FONT_FIXED, 10),
        )
    if isinstance(widget, tk.Canvas):
        widget.configure(
            bg=colors["bg_dark"],
            highlightthickness=0,
            highlightbackground=colors["bg_card"],
        )
    if isinstance(widget, tk.Listbox):
        widget.configure(
            bg=colors["bg_input"],
            fg=colors["fg_primary"],
            selectbackground=colors["select_bg"],
            selectforeground=colors["fg_accent"],
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=colors["bg_card"],
            font=(FONT_FIXED, 10),
        )

    for child in widget.winfo_children():
        _apply_theme_to_widget(child, colors)


def _apply_matplotlib_style(colors):
    try:
        import matplotlib.pyplot as plt

        plt.rcParams.update(
            {
                "figure.facecolor": colors["bg_dark"],
                "axes.facecolor": colors["bg_card"],
                "axes.edgecolor": colors["fg_secondary"],
                "axes.labelcolor": colors["fg_primary"],
                "axes.grid": True,
                "grid.alpha": 0.25,
                "grid.color": colors["fg_primary"],
                "xtick.color": colors["fg_primary"],
                "ytick.color": colors["fg_primary"],
                "text.color": colors["fg_primary"],
                "font.family": FONT_FIXED,
            }
        )
    except ImportError:
        pass
