"""FMLV form-level table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Fmlv/FmlvItem.cs).
Header: uint32 type | uint32 count. Entry size: 8 bytes.
`fields_a` packs type (high nibble) and level (low nibble); `fields_b` packs
anti_rate (high nibble) and ability_level (low nibble) -- kept as raw bytes.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 8
_ENTRY_FMT = "<BBHI"


@dataclass
class FmlvEntry:
    fields_a: int  # type = fields_a // 16, level = fields_a % 16
    fields_b: int  # anti_rate = fields_b // 16, ability_level = fields_b % 16
    reward: int
    exp: int


@dataclass
class FmlvTable:
    type: int
    entries: List[FmlvEntry]


def parse_fmlv(data: bytes) -> FmlvTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields_a, fields_b, reward, exp = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(FmlvEntry(fields_a=fields_a, fields_b=fields_b, reward=reward, exp=exp))
    return FmlvTable(type=type_val, entries=entries)


def write_fmlv(table: FmlvTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(_ENTRY_FMT, e.fields_a, e.fields_b, e.reward, e.exp)
    return bytes(out)
