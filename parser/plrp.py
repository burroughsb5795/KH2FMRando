"""PLRP player-preset table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Plrp/PlrpItem.cs).
Header: uint32 type | uint32 count. Entry size: 128 bytes (stats + a fixed
loadout of 50 item slots; 16 trailing bytes are unused padding).
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 128
_ENTRY_FMT = "<H" + "B" * 10 + "H" * 50 + "16s"


@dataclass
class PlrpEntry:
    version: int
    character: int
    hp: int
    mp: int
    ap: int
    strength: int
    magic: int
    defense: int
    armor: int
    acc: int
    item: int
    items: List[int]  # 50 item slots
    padding: bytes


@dataclass
class PlrpTable:
    type: int
    entries: List[PlrpEntry]


def parse_plrp(data: bytes) -> PlrpTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        f = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(PlrpEntry(
            version=f[0], character=f[1], hp=f[2], mp=f[3], ap=f[4],
            strength=f[5], magic=f[6], defense=f[7], armor=f[8], acc=f[9],
            item=f[10], items=list(f[11:61]), padding=f[61],
        ))
    return PlrpTable(type=type_val, entries=entries)


def write_plrp(table: PlrpTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.version, e.character, e.hp, e.mp, e.ap, e.strength, e.magic,
            e.defense, e.armor, e.acc, e.item, *e.items, e.padding,
        )
    return bytes(out)
