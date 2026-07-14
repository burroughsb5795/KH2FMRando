#!/usr/bin/env python3
"""Spoiler viewer for a built TrsrList.yml -- shows which item ended up in
which chest, grouped by world.

TrsrList.yml only carries id -> ItemId (that's all OpenKH's listpatch needs),
not which world/room a chest belongs to -- so this re-parses the vanilla
trsr table straight from data/03system.bin for that metadata and joins it
against whatever TrsrList.yml you point it at.

Usage:
    python scripts/spoiler_viewer.py [path/to/TrsrList.yml]
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parser.bar import parse_bar
from parser.trsr import parse_trsr, TrsrEntry
from scripts.paths import resource_root, output_root

# data/03system.bin is user-supplied (copyrighted game data, never bundled),
# so it's looked up next to the exe, like output/ -- not in the bundled
# resource dir.
DEFAULT_BIN = output_root() / "data" / "03system.bin"
DEFAULT_YML = output_root() / "output" / "TrsrList.yml"
ITEM_LIST_PATH = resource_root() / "presets" / "itemList.yml"
ITEM_NAMES_PATH = resource_root() / "config" / "itemid.txt"
TRSR_LIST_PATH = output_root() / "presets" / "trsrList.yml"

# Verified against OpenKH.Patcher's worldIndexMap (OpenKh.Patcher/
# PatcherProcessor.cs), not guessed -- world 6 is Olympus Coliseum, not
# "The Underworld" as an earlier, unverified project note once assumed.
WORLD_NAMES = {
    0: "World Zz (dummy)",
    1: "End of the World",
    2: "Twilight Town",
    3: "Destiny Islands",
    4: "Hollow Bastion",
    5: "Beast's Castle",
    6: "Olympus Coliseum",
    7: "Agrabah",
    8: "The Land of Dragons",
    9: "100 Acre Wood",
    10: "Pride Lands",
    11: "Atlantica",
    12: "Disney Castle",
    13: "Timeless River",
    14: "Halloween Town",
    15: "World Map",
    16: "Port Royal",
    17: "Space Paranoids",
    18: "The World That Never Was",
}


def load_chest_metadata(bin_path: Path) -> dict[int, TrsrEntry]:
    """id -> TrsrEntry (world/room/etc), parsed straight from the bin."""
    bar = parse_bar(bin_path.read_bytes())
    entry = bar.find("trsr")
    if entry is None:
        raise ValueError(f"No 'trsr' entry found in {bin_path}")
    table = parse_trsr(bar.read(entry))
    return {e.id: e for e in table.entries}

def load_indeces(path: Path) -> dict[int, int]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return {chest_id: i for i, (chest_id, fields) in enumerate(data.items())}

def load_item_categories(path: Path) -> dict[int, int]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    return {item_id: fields["Category"] for item_id, fields in data.items()}


def load_item_names(path: Path) -> dict[int, str]:
    """id -> name, from a tab-separated "Id\\tItem" dump. Blank lines and the
    header row are skipped; malformed rows are skipped rather than raising,
    since this is display-only data with no bearing on the shuffle itself."""
    if not path.exists():
        return {}
    names: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 2:
            continue
        id_str, name = parts
        if not id_str.strip().isdigit():
            continue
        names[int(id_str)] = name.strip()
    return names


class SpoilerViewer:
    def __init__(self, root: tk.Tk, initial_path: Path | None = None):
        self.root = root
        root.title("KH2FM Rando -- Chest Spoiler Viewer")
        root.geometry("760x560")

        self.categories = load_item_categories(ITEM_LIST_PATH)
        self.item_names = load_item_names(ITEM_NAMES_PATH)
        self.indeces = load_indeces(TRSR_LIST_PATH)
        self.chest_meta: dict[int, TrsrEntry] = {}
        try:
            self.chest_meta = load_chest_metadata(DEFAULT_BIN)
        except FileNotFoundError:
            messagebox.showwarning(
                "data/03system.bin not found",
                "Couldn't find data/03system.bin, so chests can't be grouped by "
                "world/room -- item IDs will still be shown. Copy the OpenKH-"
                "extracted bin into data/ to get world/room info.",
            )

        pad = {"padx": 8, "pady": 6}

        top = ttk.Frame(root)
        top.pack(fill="x", **pad)
        ttk.Button(top, text="Open TrsrList.yml...", command=self.open_file).pack(side="left")
        ttk.Button(top, text="Reload", command=self.reload).pack(side="left", padx=(6, 0))
        self.path_var = tk.StringVar(value="(none loaded)")
        ttk.Label(top, textvariable=self.path_var).pack(side="left", padx=(8, 0))

        search_frame = ttk.Frame(root)
        search_frame.pack(fill="x", **pad)
        ttk.Label(search_frame, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self.apply_filter())
        ttk.Entry(search_frame, textvariable=self.filter_var).pack(side="left", fill="x", expand=True, padx=(6, 0))

        tree_frame = ttk.Frame(root)
        tree_frame.pack(fill="both", expand=True, **pad)
        columns = ("item_name", "item_id", "category", "room", "index")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings")
        self.tree.heading("#0", text="World / Chest")
        self.tree.heading("item_name", text="Item")
        self.tree.heading("item_id", text="Item ID")
        self.tree.heading("category", text="Category")
        self.tree.heading("room", text="Room")
        self.tree.heading("index", text="Index")
        self.tree.column("#0", width=260)
        self.tree.column("item_name", width=220)
        self.tree.column("item_id", width=70, anchor="center")
        self.tree.column("category", width=80, anchor="center")
        self.tree.column("room", width=70, anchor="center")
        self.tree.column("index", width=80, anchor="center")
        scrollbar = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.status_var = tk.StringVar(value="Load a TrsrList.yml to begin.")
        ttk.Label(root, textvariable=self.status_var).pack(fill="x", padx=8, pady=(0, 8))

        self._rows: list[tuple] = []  # (world_name, chest_id, item_id, item_name, category, room)
        self._loaded_path: Path | None = None

        start_path = initial_path or (DEFAULT_YML if DEFAULT_YML.exists() else None)
        if start_path:
            self.load_yaml(start_path)

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open TrsrList.yml",
            initialdir=str(output_root() / "output"),
            filetypes=[("YAML files", "*.yml *.yaml"), ("All files", "*.*")],
        )
        if path:
            self.load_yaml(Path(path))

    def reload(self) -> None:
        if self._loaded_path is not None:
            self.load_yaml(self._loaded_path)

    def load_yaml(self, path: Path) -> None:
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except Exception as exc:
            messagebox.showerror("Failed to load", str(exc))
            return

        self._loaded_path = path
        self.path_var.set(str(path))

        rows = []
        unresolved = 0
        for chest_id, fields in data.items():
            item_id = fields.get("ItemId", 0)
            meta = self.chest_meta.get(chest_id)
            index = self.indeces.get(chest_id, 0)
            if meta is None:
                world_name = "Unknown World"
                room = "?"
                unresolved += 1
            else:
                world_name = WORLD_NAMES.get(meta.world, f"Unknown World {meta.world}")
                room = meta.room
            category = self.categories.get(item_id, "-")
            item_name = self.item_names.get(item_id, f"Unknown Item {item_id}")
            rows.append((world_name, chest_id, item_id, item_name, category, room, index))

        self._rows = rows
        note = f" ({unresolved} unresolved)" if unresolved else ""
        self.status_var.set(f"Loaded {len(rows)} chests{note}")
        self.apply_filter()

    def apply_filter(self) -> None:
        query = self.filter_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())

        by_world: dict[str, list[tuple]] = {}
        for world_name, chest_id, item_id, item_name, category, room, index in self._rows:
            haystack = f"{world_name} {chest_id} {item_id} {item_name} {category} {index}".lower()
            if query and query not in haystack:
                continue
            by_world.setdefault(world_name, []).append((chest_id, item_id, item_name, category, room, index))

        for world_name in sorted(by_world):
            chests = by_world[world_name]
            world_node = self.tree.insert(
                "", "end", text=f"{world_name}  ({len(chests)} chests)", open=bool(query),
            )
            for chest_id, item_id, item_name, category, room, index in sorted(chests):
                self.tree.insert(
                    world_node, "end", text=f"Chest {chest_id}",
                    values=(item_name, item_id, category, room, index),
                )

def main() -> None:
    initial = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    root = tk.Tk()
    SpoilerViewer(root, initial_path=initial)
    root.mainloop()


if __name__ == "__main__":
    main()
