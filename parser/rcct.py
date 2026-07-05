"""RCCT reaction command table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Rcct/RcctItem.cs).
Header: uint32 type | uint32 count. Entry size: 12 bytes.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 12
_ENTRY_FMT = "<HHHHHH"


@dataclass
class RcctEntry:
    id: int
    command1: int
    command2: int
    command3: int
    command4: int
    command5: int


@dataclass
class RcctTable:
    type: int
    entries: List[RcctEntry]


def parse_rcct(data: bytes) -> RcctTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        id_, c1, c2, c3, c4, c5 = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(RcctEntry(id=id_, command1=c1, command2=c2, command3=c3, command4=c4, command5=c5))
    return RcctTable(type=type_val, entries=entries)


def write_rcct(table: RcctTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(_ENTRY_FMT, e.id, e.command1, e.command2, e.command3, e.command4, e.command5)
    return bytes(out)
