"""MAGC magic-command table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Magc/MagcItem.cs).
Header: uint32 type | uint32 count. Entry size: 56 bytes.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 56
_ENTRY_FMT = "<BBBB32sHHHHHHHHBBBB"


@dataclass
class MagcEntry:
    type_id: int
    level_id: int
    world: int
    padding1: int
    filename: bytes  # 32-byte null-padded ASCII filename
    item: int
    command: int
    ground_anim: int
    ground_blend: int
    air_anim: int
    air_blend: int
    finish_anim: int
    finish_blend: int
    voice: int
    voice_finish: int
    voice_self: int
    padding: int


@dataclass
class MagcTable:
    type: int
    entries: List[MagcEntry]


def parse_magc(data: bytes) -> MagcTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(MagcEntry(*fields))
    return MagcTable(type=type_val, entries=entries)


def write_magc(table: MagcTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.type_id, e.level_id, e.world, e.padding1, e.filename, e.item, e.command,
            e.ground_anim, e.ground_blend, e.air_anim, e.air_blend, e.finish_anim,
            e.finish_blend, e.voice, e.voice_finish, e.voice_self, e.padding,
        )
    return bytes(out)
