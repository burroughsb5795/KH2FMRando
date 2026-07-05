"""EVTP event-type table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Evtp/EvtpItem.cs).
Header: uint32 type | uint32 count. Entry size: 8 bytes.
Fields beyond `id` are unidentified bit-packed data (kept as raw ints
so round-tripping is exact); see EvtpItem.cs if you need to decode them.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 8


@dataclass
class EvtpEntry:
    id: int      # 1 byte
    unk1: int    # 2 bytes
    unk3: int    # 3 bytes
    unk6: int    # 2 bytes


@dataclass
class EvtpTable:
    type: int
    entries: List[EvtpEntry]


def parse_evtp(data: bytes) -> EvtpTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        id_ = data[base]
        unk1 = int.from_bytes(data[base + 1:base + 3], "little")
        unk3 = int.from_bytes(data[base + 3:base + 6], "little")
        unk6 = int.from_bytes(data[base + 6:base + 8], "little")
        entries.append(EvtpEntry(id=id_, unk1=unk1, unk3=unk3, unk6=unk6))
    return EvtpTable(type=type_val, entries=entries)


def write_evtp(table: EvtpTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out.append(e.id)
        out += e.unk1.to_bytes(2, "little")
        out += e.unk3.to_bytes(3, "little")
        out += e.unk6.to_bytes(2, "little")
    return bytes(out)
