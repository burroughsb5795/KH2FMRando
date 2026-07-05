"""WMST world/map-name table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Wmst/WmstItem.cs).
No header (headerless Str_EntryFile) — the file is just a run of
32-byte null-terminated ASCII name records until end of data.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

ENTRY_SIZE = 32


@dataclass
class WmstEntry:
    name: str


@dataclass
class WmstTable:
    entries: List[WmstEntry]


def parse_wmst(data: bytes) -> WmstTable:
    entries = []
    count = len(data) // ENTRY_SIZE
    for i in range(count):
        base = i * ENTRY_SIZE
        raw = data[base:base + ENTRY_SIZE]
        name = raw.split(b"\x00", 1)[0].decode("ascii", "replace")
        entries.append(WmstEntry(name=name))
    return WmstTable(entries=entries)


def write_wmst(table: WmstTable) -> bytes:
    out = bytearray()
    for e in table.entries:
        raw = e.name.encode("ascii")[:ENTRY_SIZE].ljust(ENTRY_SIZE, b"\x00")
        out += raw
    return bytes(out)
