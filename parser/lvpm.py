"""LVPM level-parameter table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Lvpm/LvpmItem.cs).
No header (headerless Str_EntryFile) -- a plain run of 12-byte records.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

ENTRY_SIZE = 12
_ENTRY_FMT = "<HHHHHH"


@dataclass
class LvpmEntry:
    hp: int
    strength: int
    defense: int
    max_attack: int
    min_attack: int
    exp: int


@dataclass
class LvpmTable:
    entries: List[LvpmEntry]


def parse_lvpm(data: bytes) -> LvpmTable:
    count = len(data) // ENTRY_SIZE
    entries = []
    for i in range(count):
        base = i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(LvpmEntry(*fields))
    return LvpmTable(entries=entries)


def write_lvpm(table: LvpmTable) -> bytes:
    out = bytearray()
    for e in table.entries:
        out += struct.pack(_ENTRY_FMT, e.hp, e.strength, e.defense, e.max_attack, e.min_attack, e.exp)
    return bytes(out)
