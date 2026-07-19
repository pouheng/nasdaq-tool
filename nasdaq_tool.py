import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
import json
from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
import yfinance as yf
import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.ticker as mticker


try:
    from PIL import Image, ImageTk

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

NDX_SYMBOL = "^NDX"

POPULAR_STOCKS = [
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("GOOGL", "Alphabet"),
    ("AMZN", "Amazon"),
    ("NVDA", "NVIDIA"),
    ("META", "Meta"),
    ("TSLA", "Tesla"),
    ("AVGO", "Broadcom"),
    ("COST", "Costco"),
    ("CSCO", "Cisco"),
    ("INTC", "Intel"),
    ("AMD", "AMD"),
    ("NFLX", "Netflix"),
    ("ADBE", "Adobe"),
    ("PEP", "Pepsi"),
    ("QCOM", "Qualcomm"),
    ("TMUS", "T-Mobile"),
    ("AMAT", "Applied Materials"),
    ("BKNG", "Booking"),
    ("MU", "Micron"),
    ("MRVL", "Marvell"),
    ("PANW", "Palo Alto"),
    ("CRWD", "CrowdStrike"),
    ("SNPS", "Synopsys"),
]

WATCHLIST_DEFAULT = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "AVGO",
    "COST",
    "CSCO",
]
TECH_NEWS_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO"]


class NASDAQTool:
    def __init__(self, root):
        self.root = root
        self.root.title("NASDAQ-100 :: H4CK3R DASHBOARD")
        self.root.state("zoomed")
        self.root.minsize(1024, 600)

        self.help_positions = self._load_help_positions()
        self.ndx_period = "1y"
        self.sma_enabled = {"sma20": False, "sma50": False, "sma200": False}
        self.auto_refresh_id = None
        self.sidebar_visible = True
        self.current_theme_idx = 0
        self._custom_btns = []
        self._theme_colors = self._apply_theme_if_available()

        self.root.bind("<Control-t>", lambda e: self._cycle_theme())
        self.root.bind("<Control-T>", lambda e: self._cycle_theme())
        self.root.bind("<F12>", lambda e: self._toggle_coord_picker())

        self._build_layout()

        self.status_var = tk.StringVar(value="[+] System ready.")
        ttk.Label(
            root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        ).pack(fill=tk.X, side=tk.BOTTOM)

        self.refresh_chart()
        self._load_news()
        self._fetch_fear_greed()

    def _apply_theme_if_available(self):
        try:
            from theme import apply_theme

            colors = apply_theme(self.root)
            self.root.title("NASDAQ-100 :: H4CK3R DASHBOARD [THEMED]")
            return colors
        except ImportError:
            return {}

    def _cycle_theme(self):
        try:
            from theme import THEMES, apply_theme, get_theme_names

            names = get_theme_names()
            self.current_theme_idx = (self.current_theme_idx + 1) % len(names)
            new_name = names[self.current_theme_idx]
            self._theme_colors = apply_theme(self.root, new_name)
            self._recolor_all_buttons(self._theme_colors)
            self._restore_button_states()
            self.fig.patch.set_facecolor(self._theme_colors.get("bg_dark", "#0a0a0a"))
            self.stock_fig.patch.set_facecolor(
                self._theme_colors.get("bg_card", "#0d0d0d")
            )
            if hasattr(self, "stock_canvas"):
                self.stock_canvas.draw()
            if hasattr(self, "canvas"):
                self.canvas.draw()
            self._update_status(f"[~] Theme switched to {new_name}")
            self.root.title(f"NASDAQ-100 :: {new_name} DASHBOARD")
        except ImportError:
            self._update_status("[!] theme.py not found")

    def _recolor_all_buttons(self, c):
        for w in self.root.winfo_children():
            self._recolor_btn_tree(w, c)

    def _recolor_btn_tree(self, w, c):
        if isinstance(w, tk.Button):
            try:
                w.configure(
                    bg=c.get("btn_bg", "#111111"),
                    fg=c.get("fg_primary", "#00ff41"),
                    activebackground=c.get("btn_active", "#003300"),
                    activeforeground=c.get("fg_accent", "#00ffaa"),
                )
            except Exception:
                pass
        if isinstance(w, tk.Canvas):
            try:
                w.configure(
                    bg=c.get("bg_dark", "#0a0a0a"),
                    highlightbackground=c.get("bg_card", "#0d0d0d"),
                )
            except Exception:
                pass
        for child in w.winfo_children():
            self._recolor_btn_tree(child, c)

    def _restore_button_states(self):
        c = self._theme_colors
        self.panel_btn.configure(
            text="[≡ HIDE]" if self.sidebar_visible else "[≡ PANEL]",
            bg=c.get("btn_active", "#003300")
            if self.sidebar_visible
            else c.get("btn_bg", "#111111"),
        )
        if self.auto_refresh_id:
            self.auto_btn.configure(
                text="[AUTO 60s]",
                fg=c.get("fg_accent", "#00ffaa"),
                bg=c.get("btn_active", "#003300"),
            )
        else:
            self.auto_btn.configure(
                text="[AUTO OFF]",
                fg=c.get("fg_secondary", "#005f00"),
                bg=c.get("btn_bg", "#111111"),
            )
        for key, active in self.sma_enabled.items():
            self.sma_btns[key].configure(
                fg=c.get("fg_accent", "#00ff41")
                if active
                else c.get("fg_secondary", "#005f00"),
                bg=c.get("btn_active", "#003300")
                if active
                else c.get("btn_bg", "#111111"),
            )
        hl = getattr(self, "_help_active", False)
        self.help_btn.configure(
            text="✕" if hl else "?",
            bg=c.get("btn_active", "#003300") if hl else c.get("btn_bg", "#111111"),
            fg=c.get("fg_accent", "#00ffaa") if hl else c.get("fg_primary", "#00ff41"),
        )

    # ── Layout ─────────────────────────────────────────────

    def _build_layout(self):
        self.pw = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.pw.pack(fill=tk.BOTH, expand=True)

        self.sidebar = ttk.Frame(self.pw, width=380)
        self.pw.add(self.sidebar, weight=1)
        self._build_sidebar(self.sidebar)

        main = ttk.Frame(self.pw)
        self.pw.add(main, weight=3)
        self._build_main_area(main)

        self.root.update()
        self.pw.sashpos(0, 380)

    def _toggle_sidebar(self):
        if self.sidebar_visible:
            self.pw.forget(self.sidebar)
            self.sidebar_visible = False
            self.panel_btn.configure(text="[≡ PANEL]", bg="#003300")
        else:
            self.pw.insert(0, self.sidebar, weight=1)
            self.sidebar_visible = True
            self.root.update()
            self.pw.sashpos(0, 380)
            self.panel_btn.configure(text="[≡ HIDE]", bg="#330000")

    # ── Sidebar ────────────────────────────────────────────

    def _build_sidebar(self, parent):
        c = self._theme_colors

        outer = ttk.Frame(parent, padding=6)
        outer.pack(fill=tk.BOTH, expand=True)

        # Stock Select
        self.stock_select_frame = sf = ttk.LabelFrame(
            outer, text="> STOCK SELECT", padding=6
        )
        sf.pack(fill=tk.X, pady=(0, 3))

        symbol_list = [f"{sym}  |  {name}" for sym, name in POPULAR_STOCKS]
        self.symbol_var = tk.StringVar(value="AAPL  |  Apple")
        combo = ttk.Combobox(
            sf,
            textvariable=self.symbol_var,
            values=symbol_list,
            font=("Consolas", 9),
            height=12,
        )
        combo.pack(fill=tk.X, pady=(0, 4))
        combo.bind("<<ComboboxSelected>>", lambda e: self.lookup_stock())
        combo.bind("<Return>", lambda e: self.lookup_stock())

        br = ttk.Frame(sf)
        br.pack(fill=tk.X)
        self.lookup_btn = ttk.Button(br, text="[LOOK UP]", command=self.lookup_stock)
        self.lookup_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        self.clear_btn = ttk.Button(br, text="[CLR]", command=self.clear_results)
        self.clear_btn.pack(side=tk.LEFT)

        # Quick Icons
        self.quick_icons_frame = ic = ttk.LabelFrame(
            outer, text="> QUICK ICONS", padding=4
        )
        ic.pack(fill=tk.X, pady=(0, 3))
        for sym in ("AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO"):
            tk.Button(
                ic,
                text=sym,
                font=("Consolas", 10, "bold"),
                bg="#111111",
                fg=c.get("fg_primary", "#00ff41"),
                bd=1,
                relief=tk.RAISED,
                activebackground="#003300",
                activeforeground="#00ffaa",
                cursor="hand2",
                width=6,
                height=1,
                command=lambda s=sym: self.icon_click(s),
            ).pack(side=tk.LEFT, padx=2, pady=2)

        self.progress = ttk.Progressbar(outer, mode="indeterminate")

        # Vertical PanedWindow: Results / Watchlist / News
        vpw = ttk.PanedWindow(outer, orient=tk.VERTICAL)
        vpw.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        # --- Results ---
        self.results_frame = rf = ttk.LabelFrame(vpw, text="> RESULTS", padding=4)
        vpw.add(rf, weight=1)

        self.info_rows = {}
        for label, key in [
            ("ENTITY", "company"),
            ("PRICE", "price"),
            ("CHG", "change"),
            ("CHG%", "change_pct"),
            ("CLOSE", "prev_close"),
            ("OPEN", "open"),
            ("HIGH", "day_high"),
            ("LOW", "day_low"),
            ("VOL", "volume"),
            ("MCAP", "market_cap"),
            ("P/E", "pe_ratio"),
            ("52WH", "w52_high"),
            ("52WL", "w52_low"),
        ]:
            row = ttk.Frame(rf)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label, width=6, anchor=tk.E, font=("Consolas", 8)).pack(
                side=tk.LEFT, padx=(0, 3)
            )
            val = ttk.Label(row, text="--", anchor=tk.W, font=("Consolas", 8, "bold"))
            val.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.info_rows[key] = (label, val)

        ttk.Separator(rf, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(4, 2))
        ch = ttk.Frame(rf)
        ch.pack(fill=tk.X)
        ttk.Label(
            ch,
            text="1W",
            font=("Consolas", 7, "bold"),
            foreground=c.get("fg_secondary", "#005f00"),
        ).pack(side=tk.LEFT)
        self.chart_label_info = ttk.Label(ch, text="--", font=("Consolas", 7))
        self.chart_label_info.pack(side=tk.LEFT, padx=(4, 0))

        self.stock_fig = Figure(figsize=(4.2, 1.3), dpi=82)
        self.stock_fig.patch.set_facecolor(c.get("bg_card", "#0d0d0d"))
        self.stock_ax = self.stock_fig.add_subplot(111)
        self._style_mini_ax(self.stock_ax)
        self.stock_ax.text(
            0.5,
            0.5,
            "NO DATA",
            ha="center",
            va="center",
            transform=self.stock_ax.transAxes,
            fontsize=8,
            color=c.get("fg_secondary", "#005f00"),
        )
        self.stock_canvas = FigureCanvasTkAgg(self.stock_fig, master=rf)
        self.stock_canvas.get_tk_widget().pack(fill=tk.X, pady=(0, 2))
        self.stock_canvas.draw()

        # --- Watchlist ---
        self.watchlist_frame = wf = ttk.LabelFrame(vpw, text="> WATCHLIST", padding=4)
        vpw.add(wf, weight=0)

        self.watch_entries = {}
        for sym in WATCHLIST_DEFAULT:
            row = ttk.Frame(wf)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(
                row,
                text=sym,
                width=6,
                anchor=tk.W,
                font=("Consolas", 8, "bold"),
                foreground=c.get("fg_accent", "#00ffaa"),
            ).pack(side=tk.LEFT)
            prc = ttk.Label(row, text="--", width=9, anchor=tk.E, font=("Consolas", 8))
            prc.pack(side=tk.LEFT, padx=(3, 3))
            chg = ttk.Label(
                row, text="--", width=9, anchor=tk.E, font=("Consolas", 8, "bold")
            )
            chg.pack(side=tk.LEFT)
            self.watch_entries[sym] = (prc, chg)

        tk.Button(
            wf,
            text="[REFRESH]",
            font=("Consolas", 7, "bold"),
            bg="#111111",
            fg=c.get("fg_primary", "#00ff41"),
            bd=1,
            relief=tk.RAISED,
            activebackground="#003300",
            activeforeground="#00ffaa",
            cursor="hand2",
            command=self._refresh_watchlist,
        ).pack(pady=(2, 0))

        # --- News ---
        self.news_frame = nf = ttk.LabelFrame(vpw, text="> TECH NEWS", padding=4)
        vpw.add(nf, weight=1)

        nlf = ttk.Frame(nf)
        nlf.pack(fill=tk.BOTH, expand=True)
        nc = tk.Canvas(nlf, highlightthickness=0)
        ns = ttk.Scrollbar(nlf, orient=tk.VERTICAL, command=nc.yview)
        self.news_inner = ttk.Frame(nc)
        self.news_inner.bind(
            "<Configure>", lambda e: nc.configure(scrollregion=nc.bbox("all"))
        )
        nc.create_window((0, 0), window=self.news_inner, anchor=tk.NW, tags="inner")
        nc.configure(yscrollcommand=ns.set)
        nc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ns.pack(side=tk.RIGHT, fill=tk.Y)
        self._bind_mousewheel(nc)

        vpw.sashpos(0, 280)

    # ── Main area ──────────────────────────────────────────

    def _build_main_area(self, parent):
        toolbar = ttk.Frame(parent, padding=(10, 6, 10, 2))
        toolbar.pack(fill=tk.X)

        self.panel_btn = tk.Button(
            toolbar,
            text="[≡ HIDE]",
            font=("Consolas", 11, "bold"),
            bg="#330000",
            fg="#00ff41",
            bd=1,
            relief=tk.RAISED,
            activebackground="#005500",
            activeforeground="#00ffaa",
            cursor="hand2",
            padx=10,
            pady=2,
            command=self._toggle_sidebar,
        )
        self.panel_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.auto_btn = tk.Button(
            toolbar,
            text="[AUTO OFF]",
            font=("Consolas", 9, "bold"),
            bg="#111111",
            fg="#005f00",
            bd=1,
            relief=tk.RAISED,
            activebackground="#003300",
            activeforeground="#00ffaa",
            cursor="hand2",
            padx=6,
            pady=2,
            command=self._toggle_auto,
        )
        self.auto_btn.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(
            toolbar, text="> NASDAQ-100 INDEX", font=("Consolas", 18, "bold")
        ).pack(side=tk.LEFT)
        self.ndx_price_label = ttk.Label(toolbar, text="", font=("Consolas", 16))
        self.ndx_price_label.pack(side=tk.LEFT, padx=(14, 3))
        self.ndx_change_label = ttk.Label(toolbar, text="", font=("Consolas", 13))
        self.ndx_change_label.pack(side=tk.LEFT)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=(10, 6)
        )
        fgf = ttk.Frame(toolbar)
        fgf.pack(side=tk.LEFT)
        ttk.Label(
            fgf,
            text="F&G",
            font=("Consolas", 9, "bold"),
            foreground=self._theme_colors.get("fg_accent", "#00ffaa"),
        ).pack(side=tk.LEFT)
        self.fg_canvas = tk.Canvas(
            fgf,
            width=70,
            height=14,
            bg="#0d0d0d",
            highlightthickness=1,
            highlightbackground="#003300",
        )
        self.fg_canvas.pack(side=tk.LEFT, padx=(3, 3))
        self.fg_value_label = ttk.Label(fgf, text="--", font=("Consolas", 10, "bold"))
        self.fg_value_label.pack(side=tk.LEFT)
        self.fg_rating_label = ttk.Label(fgf, text="", font=("Consolas", 8))
        self.fg_rating_label.pack(side=tk.LEFT, padx=(3, 0))
        self.fg_alert_label = ttk.Label(
            fgf, text="", font=("Consolas", 8, "bold"), foreground="#ff3355"
        )
        self.fg_alert_label.pack(side=tk.LEFT, padx=(6, 0))
        self._draw_fg_bar(50, "#888888")

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=(6, 6)
        )
        self.help_btn = tk.Button(
            toolbar,
            text="?",
            font=("Consolas", 12, "bold"),
            bg="#111111",
            fg="#00ff41",
            bd=1,
            relief=tk.RAISED,
            activebackground="#003300",
            activeforeground="#00ffaa",
            cursor="hand2",
            width=2,
            height=1,
            pady=0,
            command=self._toggle_help,
        )
        self.help_btn.pack(side=tk.LEFT)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=(6, 6)
        )
        self.dca_btn = tk.Button(
            toolbar,
            text="[DCA]",
            font=("Consolas", 10, "bold"),
            bg="#111111",
            fg="#00ff41",
            bd=1,
            relief=tk.RAISED,
            activebackground="#003300",
            activeforeground="#00ffaa",
            cursor="hand2",
            padx=6,
            pady=2,
            command=self._open_dca_dialog,
        )
        self.dca_btn.pack(side=tk.LEFT)

        chart_frame = ttk.Frame(parent, padding=(10, 0, 10, 4))
        chart_frame.pack(fill=tk.BOTH, expand=True)

        pr = ttk.Frame(chart_frame)
        pr.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(pr, text="[period]", font=("Consolas", 8)).pack(
            side=tk.LEFT, padx=(0, 3)
        )
        self.period_btns = {}
        for lb, p in [
            ("1D", "1d"),
            ("5D", "5d"),
            ("1M", "1mo"),
            ("3M", "3mo"),
            ("6M", "6mo"),
            ("YTD", "ytd"),
            ("1Y", "1y"),
            ("3Y", "3y"),
            ("5Y", "5y"),
        ]:
            btn = ttk.Button(
                pr, text=lb, width=3, command=lambda pp=p: self._set_period(pp)
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.period_btns[p] = btn

        sr = ttk.Frame(chart_frame)
        sr.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(sr, text="[SMA]", font=("Consolas", 8)).pack(
            side=tk.LEFT, padx=(0, 3)
        )
        self.sma_btns = {}
        for lb, k in [("20", "sma20"), ("50", "sma50"), ("200", "sma200")]:
            btn = tk.Button(
                sr,
                text=lb,
                font=("Consolas", 8, "bold"),
                bg="#111111",
                fg="#005f00",
                bd=1,
                relief=tk.RAISED,
                activebackground="#003300",
                activeforeground="#00ffaa",
                cursor="hand2",
                width=3,
                pady=0,
                command=lambda kk=k: self._toggle_sma(kk),
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.sma_btns[k] = btn

        self.fig = Figure(figsize=(10, 5.5), dpi=96)
        self.fig.patch.set_facecolor(self._theme_colors.get("bg_dark", "#0a0a0a"))
        gs = self.fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.06)
        self.ax = self.fig.add_subplot(gs[0])
        self.ax_vol = self.fig.add_subplot(gs[1], sharex=self.ax)
        self._style_axes(self.ax)
        self._style_vol_axes(self.ax_vol)

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.get_tk_widget().configure(highlightthickness=0)

    def _style_axes(self, ax):
        c = self._theme_colors
        ax.set_facecolor(c.get("bg_card", "#0d0d0d"))
        ax.tick_params(colors=c.get("fg_primary", "#00ff41"), labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(c.get("fg_secondary", "#005f00"))
        ax.spines["bottom"].set_color(c.get("fg_secondary", "#005f00"))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax.grid(True, linestyle="--", alpha=0.3, color=c.get("fg_primary", "#00ff41"))
        ax.tick_params(labelbottom=False)

    def _style_vol_axes(self, ax):
        c = self._theme_colors
        ax.set_facecolor(c.get("bg_card", "#0d0d0d"))
        ax.tick_params(colors=c.get("fg_primary", "#00ff41"), labelsize=7)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.grid(True, linestyle="--", alpha=0.2, color=c.get("fg_primary", "#00ff41"))
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{x / 1e6:.0f}M")
        )

    def _style_mini_ax(self, ax):
        c = self._theme_colors
        ax.set_facecolor(c.get("bg_card", "#0d0d0d"))
        ax.tick_params(colors=c.get("fg_primary", "#00ff41"), labelsize=5)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.grid(True, linestyle="--", alpha=0.2, color=c.get("fg_primary", "#00ff41"))

    # ── Toggles ────────────────────────────────────────────

    def _toggle_auto(self):
        if self.auto_refresh_id:
            self.root.after_cancel(self.auto_refresh_id)
            self.auto_refresh_id = None
            self.auto_btn.configure(text="[AUTO OFF]", fg="#005f00", bg="#111111")
            self._update_status("[*] Auto-refresh stopped")
        else:
            self._schedule_auto()
            self.auto_btn.configure(text="[AUTO 60s]", fg="#00ff41", bg="#003300")
            self._update_status("[+] Auto-refresh every 60s")

    def _schedule_auto(self):
        self.auto_refresh_id = self.root.after(60000, self._auto_tick)

    def _auto_tick(self):
        self.refresh_chart()
        self._fetch_fear_greed()
        if self.auto_refresh_id:
            self._schedule_auto()

    def _toggle_sma(self, key):
        self.sma_enabled[key] = not self.sma_enabled[key]
        self.sma_btns[key].configure(
            fg="#00ff41" if self.sma_enabled[key] else "#005f00",
            bg="#003300" if self.sma_enabled[key] else "#111111",
        )
        self.refresh_chart()

    def _set_period(self, period):
        self.ndx_period = period
        for p, btn in self.period_btns.items():
            btn.configure(state=tk.NORMAL if p != period else tk.DISABLED)
        self.refresh_chart()

    # ── Chart ──────────────────────────────────────────────

    def refresh_chart(self):
        self._update_status(f"[~] Loading NASDAQ-100 ({self.ndx_period})...")
        threading.Thread(target=self._fetch_ndx, daemon=True).start()

    def _fetch_ndx(self):
        try:
            ticker = yf.Ticker(NDX_SYMBOL)
            df = ticker.history(period=self.ndx_period)
            info = ticker.info
            self.root.after(0, self._plot_ndx, df, info)
        except Exception as e:
            self.root.after(0, lambda: self._update_status(f"[!] Chart error: {e}"))

    def _plot_ndx(self, df, info):
        self.ax.clear()
        self.ax_vol.clear()
        self._style_axes(self.ax)
        self._style_vol_axes(self.ax_vol)
        c = self._theme_colors
        green = c.get("fg_green", "#00ff41")
        red = c.get("fg_red", "#ff3355")

        if df.empty:
            for ax in (self.ax, self.ax_vol):
                ax.text(
                    0.5,
                    0.5,
                    "NO DATA",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    fontsize=12,
                    color=c.get("fg_secondary", "#005f00"),
                )
            self.canvas.draw()
            self._update_status("[!] No data for ^NDX")
            return

        close = df["Close"]
        first, last_us = close.iloc[0], close.iloc[-1]
        color = green if last_us >= first else red

        self.ax.fill_between(df.index, close, close.min(), alpha=0.04, color=color)
        self.ax.plot(df.index, close, color=color, linewidth=2.0, label="^NDX Price")

        sma_colors = {"sma20": "#ffcc00", "sma50": "#33ccff", "sma200": "#ff33cc"}
        for key, active in self.sma_enabled.items():
            if active:
                pd = int(key.replace("sma", ""))
                if len(df) >= pd:
                    sma = close.rolling(window=pd).mean()
                    self.ax.plot(
                        df.index,
                        sma,
                        color=sma_colors[key],
                        linewidth=1.5,
                        alpha=0.9,
                        label=f"SMA {pd} ({'Short' if pd == 20 else 'Mid' if pd == 50 else 'Long'})",
                    )
        if any(self.sma_enabled.values()):
            self.ax.legend(
                loc="upper left",
                fontsize=8,
                facecolor=c.get("bg_dark", "#0a0a0a"),
                edgecolor=c.get("fg_secondary", "#005f00"),
                labelcolor=c.get("fg_primary", "#00ff41"),
                framealpha=0.8,
            )

        vol = df["Volume"]
        vc = [
            green if close.iloc[i] >= close.iloc[i - 1] else red
            for i in range(1, len(vol))
        ]
        vc.insert(0, green)
        self.ax_vol.bar(df.index, vol, color=vc, alpha=0.6, width=0.8)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        self.fig.autofmt_xdate(rotation=30, ha="right")

        price = info.get("regularMarketPrice", info.get("currentPrice", last_us))
        prev_close = info.get(
            "regularMarketPreviousClose", info.get("previousClose", first)
        )
        diff = price - prev_close
        diff_pct = (diff / prev_close) * 100
        color_hl = green if diff >= 0 else red
        sign = "+" if diff >= 0 else ""
        self.ndx_price_label.configure(text=f"${price:,.2f}")
        self.ndx_change_label.configure(
            text=f"{sign}{diff:,.2f} ({sign}{diff_pct:.2f}%)", foreground=color_hl
        )
        self.canvas.draw()
        self._setup_rect_selector()
        self._check_sma_alerts(close)
        self._update_status(f"[+] NDX | {self.ndx_period} | Last: ${price:,.2f}")

    def _set_fg_alert(self, msg, color="#ff3355"):
        self.fg_alert_label.configure(text=msg, foreground=color)
        self.root.after(8000, lambda: self.fg_alert_label.configure(text=""))

    def _check_sma_alerts(self, close):
        try:
            sma50 = close.rolling(window=50).mean().iloc[-1]
            sma200 = close.rolling(window=200).mean().iloc[-1]
            if pd.isna(sma50) or pd.isna(sma200):
                return
            price = close.iloc[-1]
            prev = close.iloc[-2]
            crossed_sma50 = prev >= sma50 and price < sma50
            below_sma50 = not crossed_sma50 and price < sma50
            crossed_sma200 = prev >= sma200 and price < sma200
            below_sma200 = not crossed_sma200 and price < sma200
            if crossed_sma50 or below_sma50:
                dist = ((sma50 - price) / sma50) * 100
                pct = min(dist * 3, 20)
                self._set_fg_alert(
                    f"{'🚨' if crossed_sma50 else '⚠'} SMA50 建議加倉 {pct:.0f}%"
                )
            if crossed_sma200 or below_sma200:
                dist = ((sma200 - price) / sma200) * 100
                pct = min(dist * 3, 30)
                self._set_fg_alert(
                    f"{'🚨' if crossed_sma200 else '⚠'} SMA200 建議加倉 {pct:.0f}%"
                )
        except Exception:
            pass

    # ── DCA Backtester ─────────────────────────────────────

    def _open_dca_dialog(self):
        d = tk.Toplevel(self.root)
        d.title("DCA Backtester")
        d.configure(bg="#0d0d0d")
        d.resizable(False, False)

        main = ttk.Frame(d, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="DCA 定投回測", font=("Consolas", 18, "bold")).pack(
            pady=(0, 12)
        )

        def hint(text):
            lbl = ttk.Label(
                main,
                text=text,
                font=("Consolas", 9),
                foreground="#005f00",
                padding=(0, 0, 0, 6),
            )
            lbl.pack(fill=tk.X)

        pf = ttk.Frame(main)
        pf.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(pf, text="標的", font=("Consolas", 11)).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.dca_symbol_var = tk.StringVar(value="^NDX")
        ttk.Entry(
            pf, textvariable=self.dca_symbol_var, width=16, font=("Consolas", 11)
        ).pack(side=tk.LEFT)
        hint("要回測的股票或指數代碼，預設 ^NDX（那斯達克 100）")

        rf = ttk.Frame(main)
        rf.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(rf, text="開始", font=("Consolas", 11)).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.dca_start = tk.StringVar(
            value=(datetime.today() - timedelta(days=1095)).strftime("%Y-%m-%d")
        )
        ttk.Entry(
            rf, textvariable=self.dca_start, width=14, font=("Consolas", 11)
        ).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(rf, text="結束", font=("Consolas", 11)).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.dca_end = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        ttk.Entry(rf, textvariable=self.dca_end, width=14, font=("Consolas", 11)).pack(
            side=tk.LEFT
        )
        hint("回測的時間範圍，格式 YYYY-MM-DD，或按下方快速按鈕")

        bf = ttk.Frame(main)
        bf.pack(fill=tk.X, pady=(0, 2))
        for lb, days in [("1Y", 365), ("3Y", 1095), ("5Y", 1825), ("MAX", 9999)]:

            def mk_cmd(d):
                def cmd():
                    if d >= 9999:
                        self.dca_start.set("2000-01-01")
                    else:
                        self.dca_start.set(
                            (datetime.today() - timedelta(days=d)).strftime("%Y-%m-%d")
                        )
                    self.dca_end.set(datetime.today().strftime("%Y-%m-%d"))

                return cmd

            ttk.Button(bf, text=lb, width=6, command=mk_cmd(days)).pack(
                side=tk.LEFT, padx=3
            )
        hint("快速填入：1 年 / 3 年 / 5 年 / 從 2000 年至今")

        ff = ttk.Frame(main)
        ff.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(ff, text="頻率", font=("Consolas", 11)).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.dca_freq = tk.StringVar(value="monthly")
        for lb, k in [("週", "weekly"), ("雙週", "biweekly"), ("月", "monthly")]:
            ttk.Radiobutton(ff, text=lb, variable=self.dca_freq, value=k).pack(
                side=tk.LEFT, padx=4
            )
        hint("每隔多久買一次：週 = 每 5 交易日，雙週 = 每 10 交易日，月 = 每 21 交易日")

        af = ttk.Frame(main)
        af.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(af, text="每期金額", font=("Consolas", 11)).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.dca_amount = tk.StringVar(value="1000")
        ttk.Entry(
            af, textvariable=self.dca_amount, width=12, font=("Consolas", 11)
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Label(
            af, text="USD", font=("Consolas", 10, "bold"), foreground="#00ffaa"
        ).pack(side=tk.LEFT)
        hint("每期投入的金額（美元），例如每月 1000 USD")

        def run():
            d.destroy()
            self._run_dca_backtest()

        ttk.Button(main, text="[RUN]", command=run).pack(pady=(10, 0))

        d.update_idletasks()
        gw, gh = d.winfo_width(), d.winfo_height()
        sw, sh = d.winfo_screenwidth(), d.winfo_screenheight()
        d.geometry(f"+{sw // 2 - gw // 2}+{sh // 2 - gh // 2}")
        d.transient(self.root)
        d.grab_set()
        d.focus_set()

    def _run_dca_backtest(self):
        symbol = self.dca_symbol_var.get().strip() or "^NDX"
        start = self.dca_start.get().strip()
        end = self.dca_end.get().strip()
        freq = self.dca_freq.get()
        try:
            amount = float(self.dca_amount.get())
        except ValueError:
            self._update_status("[!] 請輸入有效金額")
            return
        self._update_status(f"[~] DCA 回測中 ({symbol})...")
        threading.Thread(
            target=self._calc_dca, args=(symbol, start, end, freq, amount), daemon=True
        ).start()

    def _calc_dca(self, symbol, start, end, freq, amount):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end)
            if df.empty:
                self.root.after(0, lambda: self._update_status("[!] DCA: 無歷史數據"))
                return
            close = df["Close"]
            dates = list(close.index)

            if freq == "weekly":
                step = 5
            elif freq == "biweekly":
                step = 10
            else:
                step = 21

            invest_dates = dates[::step]
            if dates[-1] not in invest_dates:
                invest_dates.append(dates[-1])

            shares = 0.0
            total_cost = 0.0
            cost_curve = []
            value_curve = []
            for i, d in enumerate(close.index):
                if d in invest_dates:
                    price = close.loc[d]
                    if pd.notna(price) and price > 0:
                        shares += amount / price
                        total_cost += amount
                port_val = shares * close.loc[d]
                cost_curve.append((d, total_cost))
                value_curve.append((d, port_val))

            final_val = shares * close.iloc[-1]
            roi = ((final_val - total_cost) / total_cost) * 100

            self.root.after(
                0,
                self._show_dca_results,
                symbol,
                cost_curve,
                value_curve,
                roi,
                total_cost,
                final_val,
                shares,
            )
        except Exception as e:
            self.root.after(0, lambda: self._update_status(f"[!] DCA error: {e}"))

    def _show_dca_results(
        self, symbol, cost_curve, value_curve, roi, total_cost, final_val, shares
    ):
        r = tk.Toplevel(self.root)
        r.title("DCA Results")
        r.configure(bg="#0d0d0d")
        r.minsize(600, 420)

        fig = Figure(figsize=(6, 2.8), dpi=96)
        fig.patch.set_facecolor("#0d0d0d")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#0d0d0d")
        ax.tick_params(colors="#00ff41", labelsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#005f00")
        ax.spines["bottom"].set_color("#005f00")
        ax.grid(True, linestyle="--", alpha=0.3, color="#00ff41")

        cd = list(zip(*cost_curve))
        vd = list(zip(*value_curve))
        ax.fill_between(cd[0], cd[1], alpha=0.08, color="#ffcc00")
        ax.plot(cd[0], cd[1], color="#ffcc00", linewidth=1.5, label="累計投入")
        ax.plot(vd[0], vd[1], color="#00ff41", linewidth=1.8, label="資產價值")
        ax.legend(
            loc="upper left",
            fontsize=7,
            facecolor="#0d0d0d",
            edgecolor="#005f00",
            labelcolor="#00ff41",
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate(rotation=25, ha="right")

        canvas = FigureCanvasTkAgg(fig, master=r)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 0))
        canvas.draw()

        sf = ttk.Frame(r, padding=6)
        sf.pack(fill=tk.X)
        rc = "#00ff41" if roi >= 0 else "#ff3355"
        stats = (
            f"標的: {symbol}    投入: ${total_cost:,.0f}    "
            f"市值: ${final_val:,.0f}    "
            f"報酬率: {roi:+.2f}%    "
            f"累積股數: {shares:.4f}"
        )
        ttk.Label(sf, text=stats, font=("Consolas", 9, "bold"), foreground=rc).pack()

        ttk.Button(sf, text="[CLOSE]", command=r.destroy).pack(pady=(4, 0))

        r.update_idletasks()
        gw, gh = r.winfo_width(), r.winfo_height()
        sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()
        r.geometry(f"+{sw // 2 - gw // 2}+{sh // 2 - gh // 2}")
        r.transient(self.root)
        self._update_status(
            f"[+] DCA: {roi:+.2f}%  |  ${total_cost:,.0f} → ${final_val:,.0f}"
        )

    def _setup_rect_selector(self):
        try:
            self._rect_data = None
            self._rect_patch = None
            self._rect_text = None
            self.canvas.mpl_connect("button_press_event", self._on_rect_press)
            self.canvas.mpl_connect("motion_notify_event", self._on_rect_motion)
            self.canvas.mpl_connect("button_release_event", self._on_rect_release)
        except Exception:
            pass

    def _on_rect_press(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        if self._rect_patch:
            self._rect_patch.remove()
            self._rect_patch = None
        if self._rect_text:
            self._rect_text.remove()
            self._rect_text = None
        self._rect_data = (event.xdata, event.ydata)

    def _on_rect_motion(self, event):
        if self._rect_data is None or event.inaxes != self.ax:
            return
        x1, y1 = self._rect_data
        x2, y2 = event.xdata, event.ydata
        if None in (x1, y1, x2, y2):
            return
        c = self._theme_colors
        green = c.get("fg_green", "#00ff41")
        red = c.get("fg_red", "#ff3355")
        diff = y2 - y1
        pct = (diff / y1) * 100
        color = green if diff >= 0 else red
        xs = [x1, x1, x2, x2, x1]
        ys = [y1, y2, y2, y1, y1]
        if self._rect_patch:
            self._rect_patch.set_xy(list(zip(xs, ys)))
        else:
            self._rect_patch = self.ax.fill(
                xs,
                ys,
                alpha=0.12,
                color=c.get("fg_primary", "#00ff41"),
                edgecolor=c.get("fg_primary", "#00ff41"),
                linewidth=1,
            )[0]
        txt = f"${y1:,.2f} → ${y2:,.2f}\n{diff:+,.2f}  ({pct:+.2f}%)"
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        if self._rect_text:
            self._rect_text.set_text(txt)
            self._rect_text.set_position((cx, cy))
            self._rect_text.set_color(color)
            self._rect_text.set_bbox(
                dict(
                    boxstyle="round,pad=0.4",
                    facecolor="#0d0d0d",
                    edgecolor=color,
                    alpha=0.92,
                )
            )
        else:
            self._rect_text = self.ax.text(
                cx,
                cy,
                txt,
                ha="center",
                va="center",
                fontsize=9,
                fontfamily="Consolas",
                color=color,
                bbox=dict(
                    boxstyle="round,pad=0.4",
                    facecolor="#0d0d0d",
                    edgecolor=color,
                    alpha=0.92,
                ),
            )
        self.canvas.draw_idle()

    def _on_rect_release(self, event):
        if self._rect_data is None:
            return
        self._rect_data = None
        if self._rect_patch:
            self._rect_patch.remove()
            self._rect_patch = None
        if self._rect_text:
            label = self._rect_text
            self._rect_text = None
            self.root.after(5000, lambda: self._remove_rect_label(label))
        self.canvas.draw_idle()

    def _remove_rect_label(self, label):
        try:
            label.remove()
            self.canvas.draw_idle()
        except Exception:
            pass

    # ── Stock lookup ───────────────────────────────────────

    def icon_click(self, symbol):
        self.symbol_var.set(f"{symbol}  |  {dict(POPULAR_STOCKS).get(symbol, symbol)}")
        self.lookup_stock()

    def lookup_stock(self):
        raw = self.symbol_var.get().strip()
        symbol = (
            raw.split("  |  ")[0].strip().upper() if "  |  " in raw else raw.upper()
        )
        if not symbol:
            messagebox.showwarning("INPUT ERROR", "Please select a stock symbol.")
            return
        self.lookup_btn.configure(state=tk.DISABLED)
        self.clear_btn.configure(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=(0, 3))
        self.progress.start(10)
        self._update_status(f"[~] Fetching {symbol}...")
        threading.Thread(target=self._fetch_lookup, args=(symbol,), daemon=True).start()

    def _fetch_lookup(self, symbol):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1wk")
            self.root.after(0, self._display_lookup, symbol, info, hist)
        except Exception as e:
            self.root.after(0, lambda: self._update_status(f"[!] Error: {symbol}"))

    def _display_lookup(self, symbol, info, hist):
        self.progress.stop()
        self.progress.pack_forget()
        self.lookup_btn.configure(state=tk.NORMAL)
        self.clear_btn.configure(state=tk.NORMAL)
        c = self._theme_colors
        green = c.get("fg_green", "#00ff41")
        red = c.get("fg_red", "#ff3355")

        price = info.get("currentPrice", info.get("regularMarketPrice", "N/A"))
        prev = info.get("previousClose", info.get("regularMarketPreviousClose", "N/A"))
        diff = 0
        if isinstance(price, (int, float)) and isinstance(prev, (int, float)):
            diff = price - prev

        def fmt(v):
            if isinstance(v, (int, float)):
                if abs(v) >= 1_000_000_000:
                    return f"${v / 1_000_000_000:.2f}B"
                if abs(v) >= 1_000_000:
                    return f"${v / 1_000_000:.2f}M"
                if abs(v) >= 1_000:
                    return f"${v:,.2f}" if isinstance(v, float) else f"${v:,}"
                return f"${v:,.2f}" if isinstance(v, float) else f"${v:,}"
            return str(v)

        vals = {
            "company": (info.get("longName", info.get("shortName", symbol)))[:28],
            "price": fmt(price),
            "change": f"{'+' if diff >= 0 else ''}{diff:.2f}" if diff != 0 else "N/A",
            "change_pct": f"{'+' if diff >= 0 else ''}{(diff / prev) * 100:.2f}%"
            if diff and isinstance(prev, (int, float))
            else "N/A",
            "prev_close": fmt(prev),
            "open": fmt(info.get("open", info.get("regularMarketOpen", "N/A"))),
            "day_high": fmt(
                info.get("dayHigh", info.get("regularMarketDayHigh", "N/A"))
            ),
            "day_low": fmt(info.get("dayLow", info.get("regularMarketDayLow", "N/A"))),
            "volume": f"{info.get('volume', info.get('regularMarketVolume', 'N/A')):,}"
            if isinstance(info.get("volume"), (int, float))
            else str(info.get("volume", "N/A")),
            "market_cap": fmt(info.get("marketCap", "N/A")),
            "pe_ratio": f"{info.get('trailingPE', 'N/A'):.2f}"
            if isinstance(info.get("trailingPE"), (int, float))
            else str(info.get("trailingPE", "N/A")),
            "w52_high": fmt(info.get("fiftyTwoWeekHigh", "N/A")),
            "w52_low": fmt(info.get("fiftyTwoWeekLow", "N/A")),
        }
        clr = green if diff >= 0 else red
        for k, v in vals.items():
            self.info_rows[k][1].configure(text=v)
        self.info_rows["change"][1].configure(foreground=clr)
        self.info_rows["change_pct"][1].configure(foreground=clr)

        self._plot_mini_chart(symbol, hist, green, red)
        self._update_status(f"[+] {symbol} :: {fmt(price)} ({vals['change']})")

    def _plot_mini_chart(self, symbol, hist, green, red):
        self.stock_ax.clear()
        self._style_mini_ax(self.stock_ax)
        if hist is None or hist.empty:
            self.stock_ax.text(
                0.5,
                0.5,
                "NO DATA",
                ha="center",
                va="center",
                transform=self.stock_ax.transAxes,
                fontsize=8,
                color=self._theme_colors.get("fg_secondary", "#005f00"),
            )
            self.chart_label_info.configure(text="--")
            self.stock_canvas.draw()
            return
        close = hist["Close"]
        f, l = close.iloc[0], close.iloc[-1]
        lc = green if l >= f else red
        self.stock_ax.fill_between(hist.index, close, close.min(), alpha=0.08, color=lc)
        self.stock_ax.plot(hist.index, close, color=lc, linewidth=1.5)
        if len(close) >= 3:
            window = 3 if len(close) < 5 else 5
            sma5 = close.rolling(window=window).mean()
            self.stock_ax.plot(
                hist.index,
                sma5,
                color="#00ffff",
                linewidth=1.0,
                linestyle="--",
                alpha=0.85,
            )
            trend_msg = " (Above SMA)" if l >= sma5.iloc[-1] else " (Below SMA)"
        else:
            trend_msg = ""
        self.stock_fig.autofmt_xdate(rotation=20, ha="right")
        pct = ((l - f) / f) * 100
        self.chart_label_info.configure(
            text=f"{symbol}  {pct:+.2f}%{trend_msg}", foreground=lc
        )
        self.stock_canvas.draw()

    def clear_results(self):
        for k in self.info_rows:
            self.info_rows[k][1].configure(text="--", foreground="")
        self.stock_ax.clear()
        self._style_mini_ax(self.stock_ax)
        self.stock_ax.text(
            0.5,
            0.5,
            "NO DATA",
            ha="center",
            va="center",
            transform=self.stock_ax.transAxes,
            fontsize=8,
            color=self._theme_colors.get("fg_secondary", "#005f00"),
        )
        self.chart_label_info.configure(text="--")
        self.stock_canvas.draw()
        self._update_status("[*] Cleared.")

    # ── Watchlist ──────────────────────────────────────────

    def _refresh_watchlist(self):
        threading.Thread(target=self._fetch_watchlist, daemon=True).start()

    def _fetch_watchlist(self):
        for sym in WATCHLIST_DEFAULT:
            try:
                tk = yf.Ticker(sym)
                info = tk.info
                price = info.get("currentPrice", info.get("regularMarketPrice", "N/A"))
                prev = info.get("previousClose", info.get("regularMarketPreviousClose"))
                diff = 0
                if isinstance(price, (int, float)) and isinstance(prev, (int, float)):
                    diff = price - prev
                    pct = (diff / prev) * 100
                    s = "+" if diff >= 0 else ""
                    chg_txt = f"{s}{diff:.2f}"
                    pct_txt = f"{s}{pct:.2f}%"
                else:
                    chg_txt = "--"
                    pct_txt = ""
                self.root.after(
                    0,
                    self._update_watch_row,
                    sym,
                    f"${price:,.2f}" if isinstance(price, (int, float)) else str(price),
                    f"{chg_txt} {pct_txt}" if pct_txt else chg_txt,
                    self._theme_colors.get("fg_green", "#00ff41")
                    if diff >= 0
                    else self._theme_colors.get("fg_red", "#ff3355"),
                )
            except Exception:
                continue

    def _update_watch_row(self, sym, price_txt, chg_txt, color):
        if sym in self.watch_entries:
            self.watch_entries[sym][0].configure(text=price_txt)
            self.watch_entries[sym][1].configure(text=chg_txt, foreground=color)

    # ── Fear & Greed ───────────────────────────────────────

    def _fetch_fear_greed(self):
        threading.Thread(target=self._get_fear_greed, daemon=True).start()

    def _get_fear_greed(self):
        try:
            r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=8)
            entry = r.json()["data"][0]
            self.root.after(
                0,
                self._update_fear_greed,
                int(entry["value"]),
                entry["value_classification"],
            )
        except Exception:
            self.root.after(0, self._update_fear_greed, None, None)

    def _update_fear_greed(self, value, rating):
        if value is None:
            self.fg_value_label.configure(text="ERR")
            self.fg_rating_label.configure(text="")
            self._draw_fg_bar(50, "#888888")
            return
        self.fg_value_label.configure(text=str(value))
        self.fg_rating_label.configure(text=rating)
        self._draw_fg_bar(value, self._fg_color(value))
        if value is not None and value < 20:
            self._set_fg_alert("🚨 極度恐慌 今日定投加倉日", "#ff3355")

    def _fg_color(self, value):
        if value <= 25:
            return "#ff3355"
        if value <= 45:
            return "#ff6600"
        if value <= 55:
            return "#ffcc00"
        if value <= 75:
            return "#88cc00"
        return "#00ff41"

    def _draw_fg_bar(self, value, color):
        self.fg_canvas.delete("all")
        w = self.fg_canvas.winfo_width() or 70
        h = self.fg_canvas.winfo_height() or 14
        fw = max(2, int(w * value / 100))
        self.fg_canvas.create_rectangle(0, 0, fw, h, fill=color, outline="")
        self.fg_canvas.create_rectangle(fw, 0, w, h, fill="#1a1a1a", outline="")

    # ── Help System ────────────────────────────────────────

    HELP_SECTIONS = {
        "ndx": {
            "title": "📊 NASDAQ-100 指數",
            "desc": "那斯達克 100 指數（^NDX）收錄前 100 大非金融公司，以科技股為主。\n\n"
            "• 數字 = 目前指數點位\n• 旁邊 +/- 百分比 = 今日漲跌幅\n"
            "• 綠色 = 上漲 ｜ 紅色 = 下跌\n\n"
            "💡 新手：指數漲 → 科技股偏強；跌 → 市場偏弱",
        },
        "period": {
            "title": "⏱ 圖表週期",
            "desc": "切換圖表顯示的時間範圍：\n\n"
            "• 1D = 當日  • 5D = 五天\n"
            "• 1M / 3M / 6M = 一／三／六個月\n"
            "• YTD = 今年初至今\n• 1Y / 3Y / 5Y = 一／三／五年\n\n"
            "💡 新手：短線用 1D-1M，長線用 1Y-5Y",
        },
        "sma": {
            "title": "📉 移動平均線 (SMA)",
            "desc": "SMA = 簡單移動平均（過去 N 天的平均收盤價）\n\n"
            "• SMA20（黃線）≈ 一個月趨勢\n"
            "• SMA50（藍線）≈ 一季中期趨勢\n"
            "• SMA200（紅線）≈ 一年長期趨勢\n\n"
            "💡 新手：均線往上 = 偏多（適合持有）\n"
            "　 均線往下 = 偏空（謹慎操作）\n"
            "　 短線突破長線（黃金交叉）常被視為買訊",
        },
        "fng": {
            "title": "😨 恐慌貪婪指數",
            "desc": "衡量市場情緒，範圍 0（極度恐慌）～ 100（極度貪婪）\n\n"
            "• 0-25 🔴 極度恐慌 → 可能超賣，佈局機會\n"
            "• 26-45 🟠 恐慌 → 觀望\n"
            "• 46-55 🟡 中立 → 平穩\n"
            "• 56-75 🟢 貪婪 → 樂觀\n"
            "• 76-100 💚 極度貪婪 → 可能過熱，小心追高\n\n"
            "💡 新手：極度恐慌反而是長期買點",
        },
        "chart": {
            "title": "📈 即時走勢圖",
            "desc": "上半部 — 價格：折線為每日收盤價，顏色代表該週期漲跌\n\n"
            "下半部 — 成交量：柱狀圖高度代表交易量，顏色對應漲跌\n"
            "量放大 + 價上漲 = 強勢訊號\n\n"
            "💡 新手：量價配合是技術分析核心",
        },
        "panel": {
            "title": "🧰 左側面板",
            "desc": "① STOCK SELECT — 選股票代碼查即時報價\n"
            "② RESULTS — 13 項關鍵數據 + 1 週走勢圖\n"
            "③ WATCHLIST — 10 檔重點股即時監看\n"
            "④ TECH NEWS — 科技新聞，點標題用瀏覽器開啟\n\n"
            "面板寬度可拖曳邊界調整，按 [≡ HIDE] 隱藏",
        },
        "auto": {
            "title": "🔄 自動刷新",
            "desc": "開啟後每 60 秒自動更新：\n"
            "• NDX 圖表與指數報價\n• 恐慌貪婪指數\n\n"
            "適合放在螢幕旁持續監看。再按一次關閉。",
        },
        "stock_select": {
            "title": "🔍 股票查詢",
            "desc": "下拉選擇或輸入股票代碼，按 [LOOK UP] 查詢即時報價。\n\n"
            "• 輸入完按 Enter 或點 [LOOK UP]\n"
            "• [CLR] 清除結果\n\n"
            "💡 下方圖標按鈕可一鍵查詢熱門股",
        },
        "quick_icons": {
            "title": "⚡ 快速圖標",
            "desc": "一鍵查詢 8 檔熱門科技股的即時報價：\n\n"
            "AAPL · MSFT · GOOGL · AMZN\nNVDA · META · TSLA · AVGO\n\n"
            "💡 點擊後自動填入並查詢，結果顯示在 RESULTS",
        },
        "results": {
            "title": "📋 查詢結果",
            "desc": "顯示個股 13 項關鍵數據：\n\n"
            "• ENTITY — 公司名稱\n• PRICE — 現價\n"
            "• CHG / CHG% — 漲跌額／百分比\n"
            "• CLOSE / OPEN — 昨收／今開\n"
            "• HIGH / LOW — 日內高低\n"
            "• VOL — 成交量\n• MCAP — 市值\n"
            "• P/E — 本益比\n• 52WH / 52WL — 52 週高低\n\n"
            "下方 1W 迷你圖顯示過去一週走勢",
        },
        "watchlist": {
            "title": "👀 即時 Watchlist",
            "desc": "監看 10 檔重點股的即時報價與漲跌幅：\n\n"
            "AAPL · MSFT · GOOGL · AMZN · NVDA\nMETA · TSLA · AVGO · COST · CSCO\n\n"
            "• 綠色 = 上漲 ｜ 紅色 = 下跌\n"
            "• 按 [REFRESH] 手動更新所有報價\n\n"
            "💡 自動刷新開啟時 Watchlist 不會自動更新，需手動",
        },
        "news": {
            "title": "📰 科技新聞",
            "desc": "彙整 8 檔科技股的最新新聞，點擊可開啟瀏覽器閱讀全文。\n\n"
            "• 每則新聞含縮圖、標題與來源\n"
            "• 縮圖懶加載，節省網路流量\n"
            "• 最多顯示 20 則，依時間排序\n\n"
            "💡 點標題或縮圖皆可開啟",
        },
    }

    def _toggle_help(self):
        if getattr(self, "_help_active", False):
            self._dismiss_help()
        else:
            self._show_help()

    def _show_help(self):
        self._help_active = True
        self._help_popups = {}
        self.help_btn.configure(bg="#003300", fg="#00ffaa", text="✕")

        anchors = {
            "ndx": (self.ndx_price_label, "below", 0),
            "period": (
                list(self.period_btns.values())[0]
                if self.period_btns
                else self.period_btns,
                "below",
                0,
            ),
            "sma": (
                list(self.sma_btns.values())[0] if self.sma_btns else self.sma_btns,
                "above",
                0,
            ),
            "fng": (self.fg_canvas, "below", 0),
            "chart": (self.canvas.get_tk_widget(), "below", 0),
            "auto": (self.auto_btn, "above", 0),
            "panel": (self.panel_btn, "above", 0),
            "stock_select": (self.stock_select_frame, "above", 0),
            "quick_icons": (self.quick_icons_frame, "above", 0),
            "results": (self.results_frame, "above", 0),
            "watchlist": (self.watchlist_frame, "below", 0),
            "news": (self.news_frame, "below", 0),
        }

        for sid, (anchor, pos, dy) in anchors.items():
            cfg = self.HELP_SECTIONS[sid]
            popup = self._create_help_popup(anchor, cfg, sid, pos, dy)
            if popup:
                self._help_popups[sid] = popup

        self.root.bind("<Button-1>", self._on_help_bg_click, "+")

    def _dismiss_help(self):
        self._help_active = False
        self._drag_mode = False
        for p in getattr(self, "_help_popups", {}).values():
            try:
                p.destroy()
            except Exception:
                pass
        self._help_popups = {}
        try:
            self.root.unbind("<Button-1>", self._on_help_bg_click)
        except Exception:
            pass
        self.help_btn.configure(bg="#111111", fg="#00ff41", text="?")

    def _on_help_bg_click(self, event):
        if not getattr(self, "_help_active", False):
            return
        if getattr(self, "_drag_mode", False):
            return
        for p in self._help_popups.values():
            try:
                if int(p.winfo_rootx()) <= event.x_root <= int(p.winfo_rootx()) + int(
                    p.winfo_width()
                ) and int(p.winfo_rooty()) <= event.y_root <= int(
                    p.winfo_rooty()
                ) + int(p.winfo_height()):
                    return
            except Exception:
                continue
        self._dismiss_help()

    def _create_help_popup(self, anchor, cfg, sid, pos, dy=0):
        if not anchor or not anchor.winfo_exists():
            return None
        try:
            ax = anchor.winfo_rootx()
            ay = anchor.winfo_rooty()
            aw = anchor.winfo_width()
            ah = anchor.winfo_height()
        except Exception:
            return None

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#0d0d0d")

        if pos == "below":
            est_w = 250
        else:
            est_w = 280
        lines = cfg["desc"].count("\n") + 1
        est_h = max(lines * 14 + 50, 70)

        stored = self.help_positions.get(sid)
        if stored:
            px, py = stored
        else:
            if pos == "below":
                px = ax + (aw // 2) - (est_w // 2)
                py = ay + ah + 4 + dy
            elif pos == "above":
                px = ax + (aw // 2) - (est_w // 2)
                py = ay - est_h - 4 + dy

            sw = popup.winfo_screenwidth()
            sh = popup.winfo_screenheight()
            px = max(4, min(px, sw - est_w - 4))
            py = max(4, min(py, sh - est_h - 4))

        popup.geometry(f"{est_w}x{est_h}+{px}+{py}")

        tk.Label(
            popup,
            text=cfg["title"],
            anchor=tk.W,
            font=("Consolas", 10, "bold"),
            fg="#00ffaa",
            bg="#0d0d0d",
            padx=8,
        ).pack(fill=tk.X, pady=(4, 1))
        tk.Frame(popup, height=1, bg="#003300").pack(fill=tk.X, padx=8)
        tk.Label(
            popup,
            text=cfg["desc"],
            anchor=tk.W,
            justify=tk.LEFT,
            font=("Consolas", 8),
            fg="#cdd6f4",
            bg="#0d0d0d",
            padx=8,
        ).pack(fill=tk.BOTH, expand=True, pady=(2, 6))

        return popup

    # ── News ───────────────────────────────────────────────

    def _load_news(self):
        threading.Thread(target=self._fetch_news, daemon=True).start()

    def _fetch_news(self):
        seen = set()
        articles = []
        for sym in TECH_NEWS_TICKERS:
            try:
                for item in (yf.Ticker(sym).news) or []:
                    content = item.get("content")
                    if isinstance(content, str):
                        content = json.loads(content)
                    if content is None:
                        continue
                    uid = content.get("id", "")
                    if uid in seen:
                        continue
                    seen.add(uid)
                    articles.append(
                        {
                            "title": content.get("title", "Untitled"),
                            "url": (content.get("clickThroughUrl") or {}).get(
                                "url", ""
                            ),
                            "source": (content.get("provider") or {}).get(
                                "displayName", "Unknown"
                            ),
                            "time": content.get("pubDate", ""),
                            "thumbnail_url": (content.get("thumbnail") or {}).get(
                                "originalUrl", ""
                            ),
                        }
                    )
            except Exception:
                continue
            if len(articles) >= 30:
                break
        articles.sort(key=lambda a: a.get("time", ""), reverse=True)
        self.root.after(0, self._display_news, articles[:20])

    def _display_news(self, articles):
        for w in self.news_inner.winfo_children():
            w.destroy()
        self._news_thumb_refs = []
        if not articles:
            ttk.Label(self.news_inner, text="No news", font=("Consolas", 8)).pack(
                pady=6
            )
            return
        c = self._theme_colors
        fg = c.get("fg_primary", "#00ff41")
        dim = c.get("fg_secondary", "#005f00")
        bg = c.get("bg_card", "#0d0d0d")
        for i, art in enumerate(articles):
            title = art["title"][:80]
            source = art["source"]
            url = art["url"]
            tu = art.get("thumbnail_url", "")
            frame = tk.Frame(self.news_inner, bg=bg, cursor="hand2")
            frame.pack(fill=tk.X, pady=1, padx=1)
            row = tk.Frame(frame, bg=bg)
            row.pack(fill=tk.X, padx=1, pady=1)
            tl = tk.Label(row, bg="#1a1a1a", width=5, height=2, cursor="hand2")
            tl.pack(side=tk.LEFT, padx=(0, 4))
            tl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            tx = tk.Frame(row, bg=bg)
            tx.pack(side=tk.LEFT, fill=tk.X, expand=True)
            title_lb = tk.Label(
                tx,
                text=title,
                anchor=tk.W,
                justify=tk.LEFT,
                font=("Consolas", 8, "bold"),
                fg=fg,
                bg=bg,
                cursor="hand2",
                wraplength=240,
            )
            title_lb.pack(fill=tk.X)
            source_lb = tk.Label(
                tx,
                text=f"  [{source}]",
                anchor=tk.W,
                font=("Consolas", 6),
                fg=dim,
                bg=bg,
                cursor="hand2",
            )
            source_lb.pack(fill=tk.X)
            if url:
                h = lambda e, u=url: webbrowser.open(u)
                for w in (frame, row, tx, title_lb, source_lb):
                    w.bind("<Button-1>", h)
                    w.configure(cursor="hand2")
            if HAS_PIL and tu:
                self._news_thumb_refs.append((tl, tu, i))
        if HAS_PIL:
            threading.Thread(target=self._lazy_load_thumbs, daemon=True).start()

    def _lazy_load_thumbs(self):
        for tl, url, idx in self._news_thumb_refs:
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content))
                    img.thumbnail((50, 50))
                    photo = ImageTk.PhotoImage(img)
                    self.news_inner.after(0, self._set_thumb, tl, photo, idx)
            except Exception:
                continue

    def _set_thumb(self, tl, photo, idx):
        try:
            tl.config(image=photo, width=50, height=50)
            tl.image = photo
        except Exception:
            pass

    def _help_positions_path(self):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "help_positions.json"
        )

    def _load_help_positions(self):
        try:
            p = self._help_positions_path()
            if os.path.exists(p):
                with open(p) as f:
                    raw = json.load(f)
                return {k: tuple(v) for k, v in raw.items()}
        except Exception:
            pass
        return {}

    def _save_help_positions(self):
        try:
            p = self._help_positions_path()
            with open(p, "w") as f:
                json.dump(self.help_positions, f)
        except Exception:
            pass

    def _bind_mousewheel(self, widget):
        widget.bind(
            "<MouseWheel>", lambda e: widget.yview_scroll(-int(e.delta / 120), "units")
        )
        widget.bind("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind("<Button-5>", lambda e: widget.yview_scroll(1, "units"))

    # ── Drag Mode (help popups) ────────────────────────────

    def _toggle_coord_picker(self):
        if not getattr(self, "_help_active", False):
            self._update_status("[!] Open ? help first, then F12 to drag")
            return
        if getattr(self, "_drag_mode", False):
            self._disable_drag_mode()
        else:
            self._enable_drag_mode()

    def _enable_drag_mode(self):
        self._drag_mode = True
        self._update_status("[::] Drag popups to position  |  F12 done  |  Esc cancel")
        for sid, p in self._help_popups.items():
            self._make_draggable(p, sid)

    def _disable_drag_mode(self):
        self._drag_mode = False
        for p in self._help_popups.values():
            self._make_undraggable(p)
        lines = []
        for sid, p in self._help_popups.items():
            try:
                x = p.winfo_rootx()
                y = p.winfo_rooty()
                self.help_positions[sid] = (x, y)
                lines.append(f"{sid}: {x}, {y}")
            except Exception:
                continue
        text = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._save_help_positions()
        self._update_status(f"[+] Positions saved!  ({len(lines)} popups)")

    def _make_draggable(self, popup, sid):
        popup._drag_data = {"x": 0, "y": 0}
        popup._sid_label = tk.Label(
            popup,
            text=f"[{sid}]",
            font=("Consolas", 7),
            fg="#555555",
            bg="#0d0d0d",
            anchor=tk.W,
            padx=8,
        )
        popup._sid_label.pack(fill=tk.X, before=popup.winfo_children()[0])
        popup._sid_label.bind("<Button-1>", lambda e: self._drag_start(e, popup))
        popup._sid_label.bind("<B1-Motion>", lambda e: self._drag_move(e, popup))
        for child in popup.winfo_children():
            child.bind("<Button-1>", lambda e, p=popup: self._drag_start(e, p), "+")
            child.bind("<B1-Motion>", lambda e, p=popup: self._drag_move(e, p), "+")

    def _make_undraggable(self, popup):
        if hasattr(popup, "_sid_label"):
            try:
                popup._sid_label.destroy()
            except Exception:
                pass

    def _drag_start(self, event, popup):
        popup._drag_data["x"] = event.x_root
        popup._drag_data["y"] = event.y_root

    def _drag_move(self, event, popup):
        dx = event.x_root - popup._drag_data["x"]
        dy = event.y_root - popup._drag_data["y"]
        popup._drag_data["x"] = event.x_root
        popup._drag_data["y"] = event.y_root
        try:
            gx = popup.winfo_rootx() + dx
            gy = popup.winfo_rooty() + dy
            popup.geometry(f"+{gx}+{gy}")
        except Exception:
            pass

    # ── Util ───────────────────────────────────────────────

    def _update_status(self, msg):
        self.status_var.set(msg)


def main():
    root = tk.Tk()
    app = NASDAQTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
