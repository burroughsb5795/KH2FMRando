#!/usr/bin/env python3
"""Repack a TRSR CSV (from parse_trsr --csv) back into a binary trsr.bin."""

import argparse
import csv
import sys
from pathlib import Path

from parser.trsr import TrsrEntry, TrsrTable, write_trsr


def main() -> None:
    ap = argparse.ArgumentParser(description="Pack a TRSR CSV back into binary form")
    ap.add_argument(
        "csv_file",
        nargs="?",
        default="-",
        help="CSV file to read (default: stdin)",
    )
    ap.add_argument(
        "-o", "--output",
        default="trsr.bin",
        help="Output file (default: trsr.bin)",
    )
    ap.add_argument(
        "--version",
        type=int,
        default=3,
        help="TRSR version field (default: 3)",
    )
    args = ap.parse_args()

    src = sys.stdin if args.csv_file == "-" else open(args.csv_file, newline="")
    reader = csv.DictReader(src)

    required = {"id", "item", "type", "world", "room", "room_index", "event", "global_index"}
    if reader.fieldnames and not required.issubset(set(reader.fieldnames)):
        missing = required - set(reader.fieldnames)
        sys.exit(f"CSV missing columns: {missing}")

    entries = []
    for row in reader:
        entries.append(TrsrEntry(
            id=int(row["id"]),
            item=int(row["item"]),
            type=int(row["type"]),
            world=int(row["world"]),
            room=int(row["room"]),
            room_index=int(row["room_index"]),
            event=int(row["event"]),
            global_index=int(row["global_index"]),
        ))

    if src is not sys.stdin:
        src.close()

    table = TrsrTable(version=args.version, entries=entries)
    out = Path(args.output)
    out.write_bytes(write_trsr(table))
    print(f"Wrote {len(entries)} entries → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
