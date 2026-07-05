"""BONS bonus-event table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Bons/BonsItem.cs).
Header: uint32 type | uint32 count. Entry size: 16 bytes.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 16
_ENTRY_FMT = "<BBBBBBBBHH4s"


@dataclass
class BonsEntry:
    id: int
    character: int
    hp: int
    mp: int
    drive: int
    item_slot: int
    acc_slot: int
    armor_slot: int
    item1: int
    item2: int
    padding: bytes


@dataclass
class BonsTable:
    type: int
    entries: List[BonsEntry]


def parse_bons(data: bytes) -> BonsTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(BonsEntry(*fields))
    return BonsTable(type=type_val, entries=entries)


def write_bons(table: BonsTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.id, e.character, e.hp, e.mp, e.drive, e.item_slot, e.acc_slot,
            e.armor_slot, e.item1, e.item2, e.padding,
        )
    return bytes(out)
