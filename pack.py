#!/usr/bin/env python3
"""Repack a CSV (from parse.py --csv) back into a binary 03system.bin sub-table."""

import argparse
import csv
import dataclasses
import sys
from pathlib import Path

from parser.registry import FLAT_TABLES


# parse.py's trsr --csv writes the human-readable entry_type ("Chest"/"Event")
# into the "type" column instead of the raw int; map it back on the way in.
_STRING_ENUMS = {"Chest": 0, "Event": 1}


def row_to_entry(entry_cls, row: dict) -> object:
    kwargs = {}
    for f in dataclasses.fields(entry_cls):
        raw = row[f.name]
        if f.type == "float":
            kwargs[f.name] = float(raw)
        elif f.type == "bytes":
            kwargs[f.name] = bytes.fromhex(raw)
        elif f.type == "str":
            kwargs[f.name] = raw
        elif raw in _STRING_ENUMS:
            kwargs[f.name] = _STRING_ENUMS[raw]
        else:
            kwargs[f.name] = int(raw)
    return entry_cls(**kwargs)


def main() -> None:
    ap = argparse.ArgumentParser(description="Pack a 03system.bin sub-table CSV back into binary form")
    ap.add_argument("csv_file", nargs="?", default="-", help="CSV file to read (default: stdin)")
    ap.add_argument(
        "--entry",
        default="trsr",
        help=f"Sub-table to pack. One of: {', '.join(sorted(FLAT_TABLES))} (default: trsr)",
    )
    ap.add_argument("-o", "--output", default=None, help="Output file (default: <entry>.bin)")
    ap.add_argument(
        "--header",
        type=int,
        default=None,
        help="Table header value (version/type field); defaults to the observed US FM value",
    )
    args = ap.parse_args()

    entry_name = args.entry
    if entry_name not in FLAT_TABLES:
        sys.exit(f"'{entry_name}' does not support CSV packing. Available: {', '.join(sorted(FLAT_TABLES))}")

    spec = FLAT_TABLES[entry_name]

    src = sys.stdin if args.csv_file == "-" else open(args.csv_file, newline="")
    reader = csv.DictReader(src)

    required = {f.name for f in dataclasses.fields(spec.entry_cls)}
    if reader.fieldnames and not required.issubset(set(reader.fieldnames)):
        missing = required - set(reader.fieldnames)
        sys.exit(f"CSV missing columns: {missing}")

    entries = [row_to_entry(spec.entry_cls, row) for row in reader]

    if src is not sys.stdin:
        src.close()

    table_kwargs = {"entries": entries}
    if spec.header_field:
        table_kwargs[spec.header_field] = args.header if args.header is not None else spec.default_header
    table = spec.table_cls(**table_kwargs)

    output = args.output or f"{entry_name}.bin"
    out = Path(output)
    out.write_bytes(spec.write(table))
    print(f"Wrote {len(entries)} entries → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
