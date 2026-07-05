"""STOP entity-stop-flag table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Stop/StopItem.cs).
Header: uint32 type | uint32 count. Entry size: 4 bytes.
`flags` bit 0 = Exist, bit 1 = DisableDamageReaction, bit 2 = Star,
bit 3 = DisableDraw (kept as a raw int rather than exploded into properties).
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 4
_ENTRY_FMT = "<HH"


@dataclass
class StopEntry:
    id: int
    flags: int


@dataclass
class StopTable:
    type: int
    entries: List[StopEntry]


def parse_stop(data: bytes) -> StopTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        id_, flags = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(StopEntry(id=id_, flags=flags))
    return StopTable(type=type_val, entries=entries)


def write_stop(table: StopTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(_ENTRY_FMT, e.id, e.flags)
    return bytes(out)
