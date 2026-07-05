"""WENT weapon-entity table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Went/*.cs):
70 uint32 pointers (each holds a *word* index, i.e. multiply by 4 for a byte
offset) into a following run of weapon sets, one set per distinct pointer
value (sorted). Each set starts with a uint32 word count (including itself)
followed by (count - 1) uint32 entity ids.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

POINTER_COUNT = 70
WORD_SIZE = 4


@dataclass
class WentSet:
    entries: List[int]  # entity ids


@dataclass
class WentTable:
    pointers: List[int]  # 70 raw word-index pointers (0 = unused)
    sets: List[WentSet]  # one set per distinct nonzero pointer, in ascending order


def parse_went(data: bytes) -> WentTable:
    pointers = [struct.unpack_from("<I", data, i * WORD_SIZE)[0] for i in range(POINTER_COUNT)]
    distinct = sorted(set(p for p in pointers if p != 0))

    sets = []
    for word_offset in distinct:
        byte_offset = word_offset * WORD_SIZE
        total_size = struct.unpack_from("<I", data, byte_offset)[0]
        entries = []
        for i in range(1, total_size):
            entity_id = struct.unpack_from("<I", data, byte_offset + i * WORD_SIZE)[0]
            entries.append(entity_id)
        sets.append(WentSet(entries=entries))

    return WentTable(pointers=pointers, sets=sets)


def write_went(table: WentTable) -> bytes:
    out = bytearray()
    for p in table.pointers:
        out += struct.pack("<I", p)
    for s in table.sets:
        out += struct.pack("<I", len(s.entries) + 1)
        for entity_id in s.entries:
            out += struct.pack("<I", entity_id)
    return bytes(out)
