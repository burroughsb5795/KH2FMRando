#!/usr/bin/env python3
"""Minimal desktop GUI for the KH2FM randomizer pipeline.

Wraps scripts/run.py's build() in a window: enter or randomize a seed,
choose which tables to randomize, and get a ready-to-load OpenKH mod zip.
The build runs on a background thread so the window doesn't freeze; log
lines and the final result are marshalled back to the main thread through
a queue (tkinter widgets aren't safe to touch from another thread).

Usage:
    python scripts/gui.py
"""

from __future__ import annotations

import queue
import random
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import run

TABLES = [
    ("trsr", "Treasures (chests)"),
    ("lvup", "Level-up rewards"),
    ("fmlv", "Drive form levels"),
    ("bons", "Event bonuses"),
]


class RandomizerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("KH2FM Item Randomizer")
        root.resizable(False, False)

        self.queue: queue.Queue = queue.Queue()
        self.result_path: Path | None = None

        pad = {"padx": 8, "pady": 6}

        seed_frame = ttk.Frame(root)
        seed_frame.grid(row=0, column=0, sticky="ew", **pad)
        ttk.Label(seed_frame, text="Seed:").pack(side="left")
        self.seed_var = tk.StringVar()
        ttk.Entry(seed_frame, textvariable=self.seed_var, width=16).pack(side="left", padx=(6, 6))
        ttk.Button(seed_frame, text="Random", command=self.randomize_seed).pack(side="left")

        tables_frame = ttk.LabelFrame(root, text="Randomize")
        tables_frame.grid(row=1, column=0, sticky="ew", **pad)
        self.table_vars: dict[str, tk.BooleanVar] = {}
        for table_name, label in TABLES:
            var = tk.BooleanVar(value=True)
            self.table_vars[table_name] = var
            ttk.Checkbutton(tables_frame, text=label, variable=var).pack(anchor="w")

        self.generate_button = ttk.Button(root, text="Generate Mod", command=self.on_generate)
        self.generate_button.grid(row=2, column=0, sticky="ew", **pad)

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(root, textvariable=self.status_var).grid(row=3, column=0, sticky="w", padx=8)

        log_frame = ttk.Frame(root)
        log_frame.grid(row=4, column=0, sticky="nsew", **pad)
        self.log_text = tk.Text(log_frame, width=64, height=16, state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.reveal_button = ttk.Button(
            root, text="Show Built Mod", command=self.reveal_output, state="disabled",
        )
        self.reveal_button.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 8))

        self.randomize_seed()
        self.root.after(100, self.poll_queue)

    def randomize_seed(self) -> None:
        self.seed_var.set(str(random.SystemRandom().randrange(2**32)))

    def log(self, line: str) -> None:
        """Passed to run.build() as its log callback -- called from the
        worker thread, so it only ever queues; the queue poll on the main
        thread is what actually touches widgets."""
        self.queue.put(("log", line))

    def on_generate(self) -> None:
        seed_text = self.seed_var.get().strip()
        if not seed_text:
            self.randomize_seed()
            seed_text = self.seed_var.get()
        try:
            seed = int(seed_text)
        except ValueError:
            messagebox.showerror("Invalid seed", "Seed must be a whole number.")
            return

        disabled = frozenset(t for t, _ in TABLES if not self.table_vars[t].get())

        self.generate_button.configure(state="disabled")
        self.reveal_button.configure(state="disabled")
        self.result_path = None
        self.status_var.set("Building...")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        thread = threading.Thread(target=self._build_worker, args=(seed, disabled), daemon=True)
        thread.start()

    def _build_worker(self, seed: int, disabled: frozenset) -> None:
        try:
            zip_path = run.build(seed, disabled_tables=disabled, log=self.log)
            self.queue.put(("done", zip_path))
        except Exception as exc:
            self.queue.put(("error", str(exc)))

    def poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self.log_text.configure(state="normal")
                    self.log_text.insert("end", payload + "\n")
                    self.log_text.see("end")
                    self.log_text.configure(state="disabled")
                elif kind == "done":
                    self.result_path = payload
                    self.status_var.set(f"Built: {payload.name}")
                    self.generate_button.configure(state="normal")
                    self.reveal_button.configure(state="normal")
                elif kind == "error":
                    self.status_var.set("Build failed -- see log.")
                    self.log_text.configure(state="normal")
                    self.log_text.insert("end", f"ERROR: {payload}\n")
                    self.log_text.configure(state="disabled")
                    self.generate_button.configure(state="normal")
                    messagebox.showerror("Build failed", payload)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)

    def reveal_output(self) -> None:
        if self.result_path is None:
            return
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(self.result_path)])
        elif sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{self.result_path}"])
        else:
            subprocess.run(["xdg-open", str(self.result_path.parent)])


def main() -> None:
    root = tk.Tk()
    RandomizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
