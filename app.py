"""Native desktop interface for Shuffle Card Deck (Python 3 / Tkinter)."""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from shuffle_core import ALGORITHMS, ORDERED_DECK, BenchmarkResult, run_benchmark, validate_rounds

BG = "#0E131C"
PANEL = "#171F2B"
PANEL2 = "#1D2735"
STROKE = "#2C3A4D"
TEXT = "#F0F5FD"
MUTED = "#9AA9BF"
MINT = "#70E5BA"
BLUE = "#77B8FE"
YELLOW = "#F5C878"
RED = "#FF888E"
ACCENTS = (MINT, BLUE, YELLOW)
FONT = "Segoe UI"


class ShuffleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shuffle Card Deck — Benchmark Lab")
        self.geometry("1260x800")
        self.minsize(1000, 680)
        self.configure(bg=BG)
        self.results: dict[str, BenchmarkResult] = {}
        self.last_algorithm: str | None = None
        self.approved_rounds = 100
        self.rounds_var = tk.StringVar(value="100")
        self.error_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready to shuffle")
        self.selected_var = tk.StringVar(value="No algorithm selected")
        self.started_var = tk.StringVar(value="—")
        self.ended_var = tk.StringVar(value="—")
        self.total_var = tk.StringVar(value="—")
        self.speed_var = tk.StringVar(value="—")
        self.best_var = tk.StringVar(value="Run a benchmark to see the comparison")
        self.preview_var = tk.StringVar(value="52 cards · Unshuffled")
        self.events: queue.SimpleQueue = queue.SimpleQueue()
        self.busy = False
        self._buttons: list[tk.Button] = []
        self._layout()
        self.after(70, self._poll)

    @staticmethod
    def _label(parent, text, size=10, color=TEXT, bold=False, **kwargs):
        return tk.Label(parent, text=text, font=(FONT, size, "bold" if bold else "normal"),
                        fg=color, bg=parent.cget("bg"), **kwargs)

    @staticmethod
    def _panel(parent, **kwargs):
        return tk.Frame(parent, bg=PANEL, highlightbackground=STROKE, highlightthickness=1, **kwargs)

    def _layout(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=28, pady=22)
        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x", pady=(0, 12))
        title_row = tk.Frame(header, bg=BG)
        title_row.pack(side="left")
        self._label(title_row, "♠", 30, MINT, True).pack(side="left", padx=(0, 12))
        text_col = tk.Frame(title_row, bg=BG)
        text_col.pack(side="left")
        self._label(text_col, "SHUFFLE CARD DECK", 21, TEXT, True).pack(anchor="w")
        self._label(text_col, "Desktop benchmark lab  /  52 cards  /  Fisher–Yates shuffle", 10, MUTED).pack(anchor="w", pady=(3, 0))
        status = tk.Frame(header, bg=PANEL2, padx=13, pady=9)
        status.pack(side="right")
        self._label(status, "●", 12, MINT).pack(side="left", padx=(0, 9))
        tk.Label(status, textvariable=self.status_var, bg=PANEL2, fg=TEXT,
                 font=(FONT, 10)).pack(side="left")

        layout = tk.Frame(outer, bg=BG)
        layout.pack(fill="both", expand=True)
        layout.grid_columnconfigure(0, minsize=338)
        layout.grid_columnconfigure(1, weight=1)
        layout.grid_rowconfigure(0, weight=1)
        left = self._panel(layout)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 17))
        right = tk.Frame(layout, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=3)
        right.grid_rowconfigure(1, weight=2)
        right.grid_columnconfigure(0, weight=1)

        self._make_controls(left)
        results = self._panel(right)
        results.grid(row=0, column=0, sticky="nsew", pady=(0, 16))
        self._make_results(results)
        preview = self._panel(right)
        preview.grid(row=1, column=0, sticky="nsew")
        self._make_preview(preview)
        self.after_idle(lambda: self._draw_cards(ORDERED_DECK))

    def _make_controls(self, parent):
        content = tk.Frame(parent, bg=PANEL)
        content.pack(fill="both", expand=True, padx=23, pady=23)
        self._label(content, "RUN A TEST", 13, TEXT, True).pack(anchor="w")
        self._label(content, "Compare how quickly different random\nnumber generators can shuffle a deck.",
                    10, MUTED, justify="left").pack(anchor="w", pady=(7, 24))
        self._label(content, "NUMBER OF ROUNDS", 9, MUTED, True).pack(anchor="w")
        round_line = tk.Frame(content, bg=PANEL)
        round_line.pack(fill="x", pady=(8, 5))
        self.round_input = tk.Entry(round_line, textvariable=self.rounds_var, font=(FONT, 16, "bold"),
                                    fg=TEXT, bg=PANEL2, insertbackground=TEXT, relief="flat",
                                    highlightbackground=STROKE, highlightcolor=MINT,
                                    highlightthickness=1, justify="left")
        self.round_input.pack(side="left", fill="x", expand=True, ipady=8)
        self.round_input.bind("<FocusOut>", self._rounds_changed)
        self.round_input.bind("<Return>", self._rounds_changed)
        self._label(content, "From 1 to 10,000 complete shuffles", 9, MUTED).pack(anchor="w")
        tk.Label(content, textvariable=self.error_var, bg=PANEL, fg=RED,
                 font=(FONT, 9), justify="left", wraplength=270).pack(anchor="w", pady=(7, 11))
        self._label(content, "CHOOSE AN ALGORITHM", 9, MUTED, True).pack(anchor="w", pady=(0, 10))
        for i, (algorithm, detail) in enumerate((
            ("Built-in Random", "Python standard generator"),
            ("Xorshift32", "Lightweight 32-bit generator"),
            ("WELL512a", "512-bit state generator"),
        )):
            button = tk.Button(content, text=f"{algorithm}\n{detail}",
                               command=lambda a=algorithm: self.start(a),
                               bg=PANEL2, fg=TEXT, activebackground=STROKE,
                               activeforeground=TEXT, font=(FONT, 10, "bold"),
                               justify="left", anchor="w", padx=15, pady=10,
                               cursor="hand2", relief="flat", bd=0,
                               highlightbackground=ACCENTS[i], highlightthickness=1)
            button.pack(fill="x", pady=(0, 9))
            self._buttons.append(button)

        foot = tk.Frame(content, bg=PANEL)
        foot.pack(fill="x", pady=(12, 0))
        tk.Button(foot, text="Clear results", command=self._clear_confirm,
                  font=(FONT, 9, "bold"), fg=MUTED, bg=PANEL2,
                  relief="flat", padx=14, pady=9, cursor="hand2").pack(side="left")
        self._label(content, "The same Fisher–Yates shuffle is used for\nall algorithms. Lower time is better.",
                    9, MUTED, justify="left").pack(anchor="w", pady=(22, 0))

    def _make_results(self, parent):
        content = tk.Frame(parent, bg=PANEL)
        content.pack(fill="both", expand=True, padx=23, pady=20)
        top = tk.Frame(content, bg=PANEL)
        top.pack(fill="x")
        self._label(top, "BENCHMARK RESULTS", 13, TEXT, True).pack(side="left")
        self._label(top, "LAST RUN", 9, MUTED, True).pack(side="right")
        self._label(content, "The times below cover full 52-card shuffles, not just random-number calls.",
                    9, MUTED).pack(anchor="w", pady=(6, 10))

        time_area = tk.Frame(content, bg=PANEL)
        time_area.pack(fill="x", pady=(0, 12))
        for c in range(4):
            time_area.grid_columnconfigure(c, weight=1)
        for i, (caption, var) in enumerate((
            ("START", self.started_var), ("END", self.ended_var),
            ("TOTAL", self.total_var), ("PER SHUFFLE", self.speed_var))):
            group = tk.Frame(time_area, bg=PANEL2, padx=11, pady=12)
            group.grid(row=0, column=i, sticky="ew", padx=(0, 8) if i < 3 else 0)
            self._label(group, caption, 8, MUTED, True).pack(anchor="w")
            tk.Label(group, textvariable=var, fg=MINT if i == 2 else TEXT,
                     bg=PANEL2, font=(FONT, 11, "bold")).pack(anchor="w", pady=(5, 0))

        table_wrap = tk.Frame(content, bg=PANEL)
        table_wrap.pack(fill="x")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Shuffle.Treeview", font=(FONT, 10), rowheight=30,
                        background=PANEL2, fieldbackground=PANEL2, foreground=TEXT,
                        borderwidth=0, relief="flat")
        style.configure("Shuffle.Treeview.Heading", font=(FONT, 9, "bold"),
                        background=STROKE, foreground=TEXT, borderwidth=0, padding=9)
        style.map("Shuffle.Treeview", background=[("selected", "#314F5D")],
                  foreground=[("selected", TEXT)])
        self.tree = ttk.Treeview(table_wrap, columns=("algorithm", "start", "end", "time"),
                                 show="headings", height=3, style="Shuffle.Treeview", selectmode="browse")
        for key, title, width in (("algorithm", "ALGORITHM", 155), ("start", "STARTED", 95),
                                  ("end", "ENDED", 95), ("time", "TOTAL (MS)", 100)):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=78, stretch=True,
                             anchor="w" if key == "algorithm" else "center")
        self.tree.pack(fill="x")
        self.tree.bind("<<TreeviewSelect>>", self._table_selected)
        self._label(content, "SPEED COMPARISON", 9, MUTED, True).pack(anchor="w", pady=(12, 4))
        self.chart = tk.Canvas(content, bg=PANEL, highlightthickness=0, height=116)
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", lambda _: self._draw_chart())
        tk.Label(content, textvariable=self.best_var, font=(FONT, 9), bg=PANEL,
                 fg=MUTED, anchor="w").pack(fill="x", pady=(4, 0))

    def _make_preview(self, parent):
        content = tk.Frame(parent, bg=PANEL)
        content.pack(fill="both", expand=True, padx=23, pady=18)
        top = tk.Frame(content, bg=PANEL)
        top.pack(fill="x")
        self._label(top, "DECK PREVIEW", 13, TEXT, True).pack(side="left")
        tk.Label(top, textvariable=self.preview_var, font=(FONT, 9),
                 fg=MUTED, bg=PANEL).pack(side="right")
        self._label(content, "First cards from the most recent completed shuffle", 9, MUTED).pack(anchor="w", pady=(6, 8))
        self.cards = tk.Canvas(content, bg=PANEL, highlightthickness=0, height=140)
        self.cards.pack(fill="both", expand=True)
        self.cards.bind("<Configure>", lambda _: self._draw_cards(self.current_deck))
        self.current_deck = ORDERED_DECK

    def _draw_cards(self, deck):
        self.cards.delete("all")
        width = self.cards.winfo_width()
        height = self.cards.winfo_height()
        if width < 40:
            return
        gap = 8
        count = min(10, max(4, int((width + gap) // 65)))
        card_width = min(61, (width - gap * (count - 1)) / count)
        card_height = min(94, max(69, height - 13))
        span = count * card_width + (count - 1) * gap
        first_x = max(0, (width - span) / 2)
        y = max(4, (height - card_height) / 2)
        for i, card in enumerate(deck[:count]):
            x = first_x + i * (card_width + gap)
            red = "♥" in card or "♦" in card
            color = "#D35F68" if red else "#263549"
            self.cards.create_rectangle(x, y, x + card_width, y + card_height,
                                        fill="#F5F7FA", outline="#D5DFEA", width=1)
            self.cards.create_text(x + 10, y + 13, text=card,
                                   fill=color, font=(FONT, 12, "bold"), anchor="w")
            self.cards.create_text(x + card_width / 2, y + card_height / 2 + 3,
                                   text=card[-1], fill=color, font=(FONT, 26, "bold"))

    def _draw_chart(self):
        self.chart.delete("all")
        w = self.chart.winfo_width()
        if w < 150:
            return
        bar_left = 120
        max_width = max(40, w - bar_left - 88)
        times = [self.results[a].milliseconds for a in ALGORITHMS if a in self.results]
        largest = max(times) if times else 1
        for i, algorithm in enumerate(ALGORITHMS):
            y = i * 34 + 18
            value = self.results.get(algorithm)
            label = ("Built-in", "Xorshift32", "WELL512a")[i]
            self.chart.create_text(0, y, text=label, fill=TEXT, anchor="w", font=(FONT, 9, "bold"))
            self.chart.create_rectangle(bar_left, y - 7, bar_left + max_width, y + 7,
                                        fill=PANEL2, outline="")
            if value:
                size = max(3, max_width * value.milliseconds / largest)
                self.chart.create_rectangle(bar_left, y - 7, bar_left + size, y + 7,
                                            fill=ACCENTS[i], outline="")
                text = f"{value.milliseconds:.2f} ms"
            else:
                text = "Not run"
            self.chart.create_text(w - 4, y, text=text, fill=MUTED,
                                   anchor="e", font=(FONT, 9))

    def _rounds_changed(self, _event=None) -> bool:
        if self.busy:
            self.rounds_var.set(str(self.approved_rounds))
            return False
        raw = self.rounds_var.get().strip()
        try:
            candidate = validate_rounds(raw)
        except ValueError as exc:
            self.error_var.set(str(exc))
            return False
        self.error_var.set("")
        if candidate == self.approved_rounds:
            return True
        if self.results:
            response = messagebox.askokcancel(
                "Change benchmark rounds?",
                "Changing the number of rounds will clear all existing results.\n\n"
                "OK: Clear results and use the new number.\n"
                "Cancel: Keep the current rounds and results.",
                parent=self,
            )
            if not response:
                self.rounds_var.set(str(self.approved_rounds))
                return False
            self._clear_results()
        self.approved_rounds = candidate
        self.rounds_var.set(str(candidate))
        return True

    def start(self, algorithm):
        if self.busy:
            return
        if not self._rounds_changed():
            if not self.error_var.get():
                self.status_var.set("Round change cancelled")
            return
        self.busy = True
        self.error_var.set("")
        self.status_var.set(f"Running {algorithm}…")
        for button in self._buttons:
            button.configure(state="disabled", cursor="arrow")
        self.round_input.configure(state="disabled")
        worker = threading.Thread(target=self._run_background,
                                  args=(algorithm, self.approved_rounds), daemon=True)
        worker.start()

    def _run_background(self, algorithm, rounds):
        try:
            result = run_benchmark(algorithm, rounds)
            self.events.put(("result", result))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                self.busy = False
                for button in self._buttons:
                    button.configure(state="normal", cursor="hand2")
                self.round_input.configure(state="normal")
                if kind == "result":
                    self._receive_result(value)
                else:
                    self.status_var.set("Benchmark failed")
                    messagebox.showerror("Benchmark error", value, parent=self)
        except queue.Empty:
            pass
        self.after(70, self._poll)

    def _receive_result(self, result):
        self.results[result.algorithm] = result
        self.last_algorithm = result.algorithm
        self.current_deck = result.last_deck
        self.preview_var.set(f"Last shuffle · {result.algorithm}")
        self._draw_cards(self.current_deck)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for name in ALGORITHMS:
            res = self.results.get(name)
            if res:
                self.tree.insert("", "end", iid=name,
                                 values=(name, res.started.strftime("%H:%M:%S.%f")[:-3],
                                         res.finished.strftime("%H:%M:%S.%f")[:-3],
                                         f"{res.milliseconds:,.3f}"))
        self.tree.selection_set(result.algorithm)
        self.tree.focus(result.algorithm)
        self._show_result(result)
        self._draw_chart()
        champion = min(self.results.values(), key=lambda r: r.elapsed_ns)
        self.best_var.set(f"Fastest measured so far: {champion.algorithm} · {champion.milliseconds:.3f} ms"
                          "   (results vary by machine and run)")
        self.status_var.set(f"Finished {result.algorithm}")

    def _table_selected(self, _event=None):
        selected = self.tree.selection()
        if selected and selected[0] in self.results:
            self._show_result(self.results[selected[0]])

    def _show_result(self, result):
        self.selected_var.set(result.algorithm)
        self.started_var.set(result.started.strftime("%H:%M:%S.%f")[:-3])
        self.ended_var.set(result.finished.strftime("%H:%M:%S.%f")[:-3])
        self.total_var.set(f"{result.milliseconds:.3f} ms")
        self.speed_var.set(f"{result.microseconds_per_shuffle:.2f} μs")

    def _clear_confirm(self):
        if self.busy:
            return
        if self.results and messagebox.askokcancel("Clear benchmark results?",
                    "Clear the benchmark table and return the deck to its original order?",
                    parent=self):
            self._clear_results()
            self.status_var.set("Results cleared")

    def _clear_results(self):
        self.results.clear()
        self.last_algorithm = None
        for var in (self.started_var, self.ended_var, self.total_var, self.speed_var):
            var.set("—")
        self.best_var.set("Run a benchmark to see the comparison")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.current_deck = ORDERED_DECK
        self.preview_var.set("52 cards · Unshuffled")
        self._draw_cards(self.current_deck)
        self._draw_chart()


def main():
    app = ShuffleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
