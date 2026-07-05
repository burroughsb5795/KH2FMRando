"""VTBL voice-table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Vtbl/VtblItem.cs).
Header: uint32 type | uint32 count. Entry size: 14 bytes.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 14
_ENTRY_FMT = "<BBBB" + "B" * 10


@dataclass
class VtblEntry:
    character: int
    action: int
    priority: int
    reserved03: int
    voices: List[int]  # 5 x (voice id, chance) pairs, 10 bytes


@dataclass
class VtblTable:
    type: int
    entries: List[VtblEntry]


def parse_vtbl(data: bytes) -> VtblTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        f = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(VtblEntry(character=f[0], action=f[1], priority=f[2], reserved03=f[3], voices=list(f[4:14])))
    return VtblTable(type=type_val, entries=entries)


def write_vtbl(table: VtblTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(_ENTRY_FMT, e.character, e.action, e.priority, e.reserved03, *e.voices)
    return bytes(out)
