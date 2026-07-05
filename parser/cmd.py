"""CMD battle command table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Cmd/CmdItem.cs).
Header: uint32 type | uint32 count. Entry size: 48 bytes.

`flag` is a 4-byte bitfield (32 individual flags in the reference editor);
kept as a raw int here rather than exploded into properties.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 48
_ENTRY_FMT = "<HHHbBiIfffBBBBHHBBHHHHBB"


@dataclass
class CmdEntry:
    id: int
    exec: int
    argument: int
    submenu: int
    icon: int
    text: int
    flag: int
    range: float
    dir: float
    dir_range: float
    mp_dr_cost: int
    camera: int
    priority: int
    receiver: int
    time: int
    require: int
    mark: int
    action: int
    rc_count: int
    distance_range: int
    score: int
    disable_form: int
    group: int
    reserve: int


@dataclass
class CmdTable:
    type: int
    entries: List[CmdEntry]


def parse_cmd(data: bytes) -> CmdTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(CmdEntry(*fields))
    return CmdTable(type=type_val, entries=entries)


def write_cmd(table: CmdTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.id, e.exec, e.argument, e.submenu, e.icon, e.text, e.flag,
            e.range, e.dir, e.dir_range, e.mp_dr_cost, e.camera, e.priority,
            e.receiver, e.time, e.require, e.mark, e.action, e.rc_count,
            e.distance_range, e.score, e.disable_form, e.group, e.reserve,
        )
    return bytes(out)
