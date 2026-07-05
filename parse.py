#!/usr/bin/env python3
"""Parse and display any 03system.bin sub-table (trsr, item, shop, went, ...)."""

import argparse
import csv
import dataclasses
import io
import sys
from pathlib import Path

from parser.bar import parse_bar
from parser.registry import REGISTRY, FLAT_TABLES


def load_entry_bytes(path: Path, entry_name: str) -> bytes:
    raw = path.read_bytes()
    if raw[:4] == b"BAR\x01":
        bar = parse_bar(raw)
        entry = bar.find(entry_name)
        if entry is None:
            sys.exit(f"No '{entry_name}' entry found in {path}")
        return bar.read(entry)
    return raw


def entries_to_csv(entries) -> str:
    if not entries:
        return ""
    fieldnames = [f.name for f in dataclasses.fields(entries[0])]
    buf = io.StringIO()
    # QUOTE_ALL so a lone empty-string column (e.g. wmst's blank names) still
    # serializes as a non-blank line ("") instead of one csv.reader would skip.
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(fieldnames)
    for e in entries:
        row = []
        for name in fieldnames:
            value = getattr(e, name)
            if isinstance(value, bytes):
                value = value.hex()
            row.append(str(value))
        writer.writerow(row)
    return buf.getvalue()


def describe_composite(entry_name: str, table) -> str:
    if entry_name == "memt":
        return f"MEMT  —  {len(table.entries)} entries, {len(table.confs)} confs\n"
    if entry_name == "item":
        return f"ITEM  —  {len(table.entries)} items, {len(table.equipment)} equipment\n"
    if entry_name == "arif":
        sizes = [len(b.entries) for b in table.blocks]
        return f"ARIF  —  {len(table.blocks)} blocks (entries per block: {sizes})\n"
    if entry_name == "shop":
        return (
            f"SHOP  —  {len(table.shops)} shops, "
            f"{len(table.inventories)} inventories, {len(table.products)} products\n"
        )
    if entry_name == "went":
        sizes = [len(s.entries) for s in table.sets]
        return f"WENT  —  {len(table.sets)} weapon sets (entries per set: {sizes})\n"
    if entry_name == "lvup":
        sizes = [(c.name, len(c.levels)) for c in table.characters]
        return f"LVUP  —  {len(table.characters)} characters (levels per character: {sizes})\n"
    if entry_name == "ptya":
        sizes = [len(s.entries) for s in table.sets]
        return f"PTYA  —  {len(table.sets)} action sets (entries per set: {sizes})\n"
    if entry_name == "atkp":
        return f"ATKP  —  {len(table.entries)} entries, {len(table.footer)} footer bytes\n"
    if hasattr(table, "entries"):
        # Flat-entries tables with a non-scalar sub-field (e.g. a per-difficulty
        # list) aren't in FLAT_TABLES, but still print a plain count here.
        return f"{entry_name.upper()}  —  {len(table.entries)} entries\n"
    return f"{entry_name}: {table!r}\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse a KH2FM 03system.bin sub-table")
    ap.add_argument(
        "bin_file",
        nargs="?",
        default="data/03system.bin",
        help="BAR archive or raw sub-table .bin (default: data/03system.bin)",
    )
    ap.add_argument(
        "--entry",
        default="trsr",
        help=f"Sub-table to parse. One of: {', '.join(sorted(REGISTRY))} (default: trsr)",
    )
    ap.add_argument("--type", choices=["Chest", "Event"], default=None, help="(trsr only) filter by entry type")
    ap.add_argument("--csv", action="store_true", help="Output CSV instead of a summary")
    ap.add_argument(
        "--yaml",
        action="store_true",
        help="(trsr only) Output a TrsrList.yml-style mapping of id -> ItemId",
    )
    ap.add_argument("--output", type=Path, default=None, help="Write output to this file instead of stdout")
    args = ap.parse_args()

    path = Path(args.bin_file)
    if not path.exists():
        sys.exit(f"File not found: {path}")

    entry_name = args.entry
    if entry_name not in REGISTRY:
        sys.exit(f"Unknown entry '{entry_name}'. Available: {', '.join(sorted(REGISTRY))}")

    data = load_entry_bytes(path, entry_name)
    table = REGISTRY[entry_name].parse(data)

    if entry_name == "trsr":
        entries = table.entries
        if args.type is not None:
            entries = [e for e in entries if e.entry_type == args.type]

        chests = sum(1 for e in table.entries if e.entry_type == "Chest")
        events = sum(1 for e in table.entries if e.entry_type == "Event")
        filter_str = f"  filter={args.type}" if args.type else ""
        print(
            f"TRSR v{table.version}  —  {len(table.entries)} entries  "
            f"({chests} Chest, {events} Event){filter_str}",
            file=sys.stderr,
        )

        if args.yaml:
            lines = [f"{e.id}:\n  ItemId: {e.item}" for e in entries]
            out = "\n".join(lines) + "\n"
        elif args.csv:
            lines = ["id,item,type,world,room,room_index,event,global_index"]
            lines += [
                f"{e.id},{e.item},{e.entry_type},{e.world},"
                f"{e.room},{e.room_index},{e.event},{e.global_index}"
                for e in entries
            ]
            out = "\n".join(lines) + "\n"
        else:
            lines = [
                f"{'#':>4}  {'id':>6}  {'item':>6}  {'type':>5}  "
                f"{'world':>5}  {'room':>5}  {'ridx':>5}  {'event':>6}  {'gidx':>5}",
                "-" * 72,
            ]
            lines += [
                f"{i:>4}  {e.id:>6}  {e.item:>6}  {e.entry_type:>5}  "
                f"{e.world:>5}  {e.room:>5}  {e.room_index:>5}  {e.event:>6}  {e.global_index:>5}"
                for i, e in enumerate(entries)
            ]
            out = "\n".join(lines) + "\n"
    elif entry_name in FLAT_TABLES:
        entries = table.entries
        print(f"{entry_name.upper()}  —  {len(entries)} entries", file=sys.stderr)
        if args.csv:
            out = entries_to_csv(entries)
        else:
            fieldnames = [f.name for f in dataclasses.fields(entries[0])] if entries else []
            lines = ["  ".join(fieldnames)]
            lines += ["  ".join(str(getattr(e, name)) for name in fieldnames) for e in entries]
            out = "\n".join(lines) + "\n"
    else:
        if args.csv:
            sys.exit(
                f"'{entry_name}' is a composite table; --csv is only supported for: "
                f"{', '.join(sorted(FLAT_TABLES))}"
            )
        out = describe_composite(entry_name, table)

    if args.output is not None:
        args.output.write_text(out)
    else:
        print(out, end="")


if __name__ == "__main__":
    main()
