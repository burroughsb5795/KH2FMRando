"""SKLT skeleton-bone table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Sklt/SkltItem.cs).
Header: uint32 type | uint32 count. Entry size: 8 bytes.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 8
_ENTRY_FMT = "<Ihh"


@dataclass
class SkltEntry:
    character: int
    bone1: int
    bone2: int


@dataclass
class SkltTable:
    type: int
    entries: List[SkltEntry]


def parse_sklt(data: bytes) -> SkltTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        character, bone1, bone2 = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(SkltEntry(character=character, bone1=bone1, bone2=bone2))
    return SkltTable(type=type_val, entries=entries)


def write_sklt(table: SkltTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(_ENTRY_FMT, e.character, e.bone1, e.bone2)
    return bytes(out)
