"""PTYA party-action table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Ptya/*.cs): header
(uint32 type | uint32 pointer count), then that many uint32 pointers holding
*absolute byte offsets* (unlike WENT's word-index pointers) into a following
run of action sets, one set per distinct nonzero pointer value (sorted). Each
set starts with a uint32 entry count followed by that many 68-byte PtyaItem
records.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
POINTER_SIZE = 4
ITEM_SIZE = 68
_ITEM_FMT = "<BBbbIHH" + "f" * 13 + "HH"


@dataclass
class PtyaItem:
    id: int
    type: int
    sub: int
    combo_offset: int
    flag: int
    motion: int
    next_motion: int
    jump: float
    jump_max: float
    jump_min: float
    speed_min: float
    speed_max: float
    near: float
    far: float
    low: float
    high: float
    inner_min: float
    inner_max: float
    blend_time: float
    distance_adjust: float
    ability: int
    score: int


@dataclass
class PtyaSet:
    entries: List[PtyaItem]


@dataclass
class PtyaTable:
    type: int
    pointers: List[int]  # raw absolute-byte-offset pointers (0 = unused)
    sets: List[PtyaSet]  # one set per distinct nonzero pointer, in ascending order


def parse_ptya(data: bytes) -> PtyaTable:
    type_val, pointer_count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE

    pointers = [
        struct.unpack_from("<I", data, header_size + i * POINTER_SIZE)[0]
        for i in range(pointer_count)
    ]
    distinct = sorted(set(p for p in pointers if p != 0))

    sets = []
    for offset in distinct:
        entry_count = struct.unpack_from("<I", data, offset)[0]
        entries = []
        for i in range(entry_count):
            base = offset + 4 + i * ITEM_SIZE
            fields = struct.unpack_from(_ITEM_FMT, data, base)
            entries.append(PtyaItem(*fields))
        sets.append(PtyaSet(entries=entries))

    return PtyaTable(type=type_val, pointers=pointers, sets=sets)


def write_ptya(table: PtyaTable) -> bytes:
    header_size = TYPE_SIZE + COUNT_SIZE
    pointer_table_size = len(table.pointers) * POINTER_SIZE

    body = bytearray()
    offset = header_size + pointer_table_size
    offset_by_index = []
    for s in table.sets:
        offset_by_index.append(offset)
        body += struct.pack("<I", len(s.entries))
        for e in s.entries:
            body += struct.pack(
                _ITEM_FMT,
                e.id, e.type, e.sub, e.combo_offset, e.flag, e.motion, e.next_motion,
                e.jump, e.jump_max, e.jump_min, e.speed_min, e.speed_max,
                e.near, e.far, e.low, e.high, e.inner_min, e.inner_max,
                e.blend_time, e.distance_adjust, e.ability, e.score,
            )
        offset += 4 + len(s.entries) * ITEM_SIZE

    distinct_old = sorted(set(p for p in table.pointers if p != 0))
    remap = dict(zip(distinct_old, offset_by_index))
    new_pointers = [remap.get(p, 0) for p in table.pointers]

    out = bytearray(write_header(table.type, len(new_pointers), TYPE_SIZE, COUNT_SIZE))
    for p in new_pointers:
        out += struct.pack("<I", p)
    out += body
    return bytes(out)
