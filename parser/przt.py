"""PRZT prize-table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Przt/PrztItem.cs).
Header: uint32 type | uint32 count. Entry size: 24 bytes.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 24
_ENTRY_FMT = "<H" + "B" * 10 + "HHHHHH"


@dataclass
class PrztEntry:
    id: int
    hp_s: int
    hp_l: int
    munny_l: int
    munny_m: int
    munny_s: int
    mp_s: int
    mp_l: int
    drive_s: int
    drive_l: int
    padding: int
    drop1: int
    drop1_chance: int
    drop2: int
    drop2_chance: int
    drop3: int
    drop3_chance: int


@dataclass
class PrztTable:
    type: int
    entries: List[PrztEntry]


def parse_przt(data: bytes) -> PrztTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(PrztEntry(*fields))
    return PrztTable(type=type_val, entries=entries)


def write_przt(table: PrztTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.id, e.hp_s, e.hp_l, e.munny_l, e.munny_m, e.munny_s, e.mp_s, e.mp_l,
            e.drive_s, e.drive_l, e.padding, e.drop1, e.drop1_chance,
            e.drop2, e.drop2_chance, e.drop3, e.drop3_chance,
        )
    return bytes(out)
