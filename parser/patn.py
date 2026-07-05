"""PATN pattern table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Patn/PatnItem.cs).
Header: uint32 type | uint32 count. Entry size: 32 bytes. Fields 1-19 are
still unidentified in the reference editor (magnet/magnet_burst live at
indices 4/5 of `unk`); kept as a raw 19-byte blob.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 32
_ENTRY_FMT = "<B19s12s"


@dataclass
class PatnEntry:
    id: int
    unk: bytes  # 19 unidentified bytes (unk1..unk19; magnet_burst/magnet at index 4/5)
    padding: bytes


@dataclass
class PatnTable:
    type: int
    entries: List[PatnEntry]


def parse_patn(data: bytes) -> PatnTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(PatnEntry(*fields))
    return PatnTable(type=type_val, entries=entries)


def write_patn(table: PatnTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(_ENTRY_FMT, e.id, e.unk, e.padding)
    return bytes(out)
