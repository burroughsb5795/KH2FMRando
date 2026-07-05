"""LIMT limit-command table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Limt/LimtItem.cs).
Header: uint32 type | uint32 count. Entry size: 64 bytes. Note: the reference
editor's declared padding offset (48) doesn't actually reach entrySize (64);
the real trailing gap starts right after `world` at byte 45 (19 bytes).
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 64
_ENTRY_FMT = "<BBBB32sIHHB19s"


@dataclass
class LimtEntry:
    id: int
    character: int
    summon: int
    group: int
    file: bytes  # 32-byte null-padded ASCII filename
    spawn: int
    command: int
    limit: int
    world: int
    padding: bytes


@dataclass
class LimtTable:
    type: int
    entries: List[LimtEntry]


def parse_limt(data: bytes) -> LimtTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(LimtEntry(*fields))
    return LimtTable(type=type_val, entries=entries)


def write_limt(table: LimtTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.id, e.character, e.summon, e.group, e.file, e.spawn,
            e.command, e.limit, e.world, e.padding,
        )
    return bytes(out)
