#!/usr/bin/env python3
"""Parse and display the TRSR treasure table from 03system.bin or trsr.bin."""

import argparse
import sys
from pathlib import Path

from parser.bar import parse_bar
from parser.trsr import parse_trsr


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse KH2FM TRSR treasure table")
    ap.add_argument(
        "bin_file",
        nargs="?",
        default="data/03system.bin",
        help="BAR archive or raw trsr.bin (default: data/03system.bin)",
    )
    ap.add_argument("--type", choices=["Chest", "Event"], default=None, help="Filter by entry type")
    ap.add_argument("--csv", action="store_true", help="Output CSV instead of table")
    ap.add_argument(
        "--yaml",
        action="store_true",
        help="Output a TrsrList.yml-style mapping of id -> ItemId instead of the table",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write output to this file instead of stdout",
    )
    args = ap.parse_args()

    path = Path(args.bin_file)
    if not path.exists():
        sys.exit(f"File not found: {path}")

    raw = path.read_bytes()
    if raw[:4] == b"BAR\x01":
        bar = parse_bar(raw)
        trsr_entry = bar.find("trsr")
        if trsr_entry is None:
            sys.exit(f"No 'trsr' entry found in {path}")
        raw = bar.read(trsr_entry)

    table = parse_trsr(raw)

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

    if args.output is not None:
        args.output.write_text(out)
    else:
        print(out, end="")


if __name__ == "__main__":
    main()
