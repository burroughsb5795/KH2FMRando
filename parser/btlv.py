"""BTLV battle-level table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Btlv/BtlvItem.cs).
Header: uint32 type | uint32 count. Entry size: 32 bytes.
`prog_flag` is a 2-byte bitfield (14 individual progress flags in the
reference editor); kept as a raw int here rather than exploded into properties.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 32
_ENTRY_FMT = "<iI" + "B" * 19 + "5s"


@dataclass
class BtlvEntry:
    id: int
    prog_flag: int
    battle_levels: List[int]  # 19 per-difficulty battle levels
    padding: bytes


@dataclass
class BtlvTable:
    type: int
    entries: List[BtlvEntry]


def parse_btlv(data: bytes) -> BtlvTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        id_, prog_flag, *levels_and_pad = fields
        battle_levels = list(levels_and_pad[:19])
        padding = levels_and_pad[19]
        entries.append(BtlvEntry(id=id_, prog_flag=prog_flag, battle_levels=battle_levels, padding=padding))
    return BtlvTable(type=type_val, entries=entries)


def write_btlv(table: BtlvTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(_ENTRY_FMT, e.id, e.prog_flag, *e.battle_levels, e.padding)
    return bytes(out)
