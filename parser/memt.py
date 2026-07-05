"""MEMT party-member table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Memt/MemtItem.cs, MemtConf.cs).
Header: uint32 type | uint32 count. Entry size: 52 bytes, followed by a
fixed footer of 7 x 4-byte MemtConf records (player/party1/party2/party3 bytes).
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 52
_ENTRY_FMT = "<BBHH10sHHHHHHHHHHHHHHHHHH"

CONF_COUNT = 7
CONF_SIZE = 4
_CONF_FMT = "<BBBB"


@dataclass
class MemtEntry:
    world_id: int
    pad1: int
    world_story: int
    world_story_neg: int
    unk06: bytes
    player: int
    party1: int
    party2: int
    party3: int
    player_valor: int
    player_wisdom: int
    player_limit: int
    player_master: int
    player_final: int
    player_anti: int
    player_mickey: int
    player_hp: int
    player_valor_hp: int
    player_wisdom_hp: int
    player_limit_hp: int
    player_master_hp: int
    player_final_hp: int
    player_hp2: int


@dataclass
class MemtConf:
    player: int
    party1: int
    party2: int
    party3: int


@dataclass
class MemtTable:
    type: int
    entries: List[MemtEntry]
    confs: List[MemtConf]


def parse_memt(data: bytes) -> MemtTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(MemtEntry(*fields))

    conf_start = header_size + count * ENTRY_SIZE
    confs = []
    for i in range(CONF_COUNT):
        base = conf_start + i * CONF_SIZE
        player, party1, party2, party3 = struct.unpack_from(_CONF_FMT, data, base)
        confs.append(MemtConf(player=player, party1=party1, party2=party2, party3=party3))

    return MemtTable(type=type_val, entries=entries, confs=confs)


def write_memt(table: MemtTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.world_id, e.pad1, e.world_story, e.world_story_neg, e.unk06,
            e.player, e.party1, e.party2, e.party3,
            e.player_valor, e.player_wisdom, e.player_limit, e.player_master,
            e.player_final, e.player_anti, e.player_mickey, e.player_hp,
            e.player_valor_hp, e.player_wisdom_hp, e.player_limit_hp,
            e.player_master_hp, e.player_final_hp, e.player_hp2,
        )
    for c in table.confs:
        out += struct.pack(_CONF_FMT, c.player, c.party1, c.party2, c.party3)
    return bytes(out)
