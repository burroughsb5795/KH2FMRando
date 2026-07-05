"""SUMN summon table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Sumn/SumnItem.cs).
Header: uint32 type | uint32 count. Entry size: 64 bytes.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 64
_ENTRY_FMT = "<HHIIH50s"


@dataclass
class SumnEntry:
    command: int
    item: int
    entity: int
    entity2: int
    limit: int
    padding: bytes


@dataclass
class SumnTable:
    type: int
    entries: List[SumnEntry]


def parse_sumn(data: bytes) -> SumnTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(SumnEntry(*fields))
    return SumnTable(type=type_val, entries=entries)


def write_sumn(table: SumnTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(_ENTRY_FMT, e.command, e.item, e.entity, e.entity2, e.limit, e.padding)
    return bytes(out)
