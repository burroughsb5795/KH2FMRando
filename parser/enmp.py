"""ENMP enemy-parameter table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Enmp/EnmpItem.cs).
Header: uint32 type | uint32 count. Entry size: 92 bytes (46 x uint16 fields,
most of them still unidentified in the reference editor -- kept as `unk`).
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 92
_ENTRY_FMT = "<" + "H" * 46


@dataclass
class EnmpEntry:
    id: int
    level: int
    hp: int
    hp1: int
    hp2: int
    hp3: int
    hp4: int
    hp5: int
    hp6: int
    unk: List[int]  # 25 unidentified uint16 fields (offsets 18-66)
    max_dmg: int
    min_dmg: int
    phys_res: int
    fire_res: int
    bliz_res: int
    thun_res: int
    dark_res: int
    neutral_res: int
    general_res: int
    exp: int
    prize: int
    bonus_level: int


@dataclass
class EnmpTable:
    type: int
    entries: List[EnmpEntry]


def parse_enmp(data: bytes) -> EnmpTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        f = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(EnmpEntry(
            id=f[0], level=f[1], hp=f[2], hp1=f[3], hp2=f[4], hp3=f[5], hp4=f[6],
            hp5=f[7], hp6=f[8], unk=list(f[9:34]),
            max_dmg=f[34], min_dmg=f[35], phys_res=f[36], fire_res=f[37],
            bliz_res=f[38], thun_res=f[39], dark_res=f[40], neutral_res=f[41],
            general_res=f[42], exp=f[43], prize=f[44], bonus_level=f[45],
        ))
    return EnmpTable(type=type_val, entries=entries)


def write_enmp(table: EnmpTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.id, e.level, e.hp, e.hp1, e.hp2, e.hp3, e.hp4, e.hp5, e.hp6,
            *e.unk,
            e.max_dmg, e.min_dmg, e.phys_res, e.fire_res, e.bliz_res, e.thun_res,
            e.dark_res, e.neutral_res, e.general_res, e.exp, e.prize, e.bonus_level,
        )
    return bytes(out)
