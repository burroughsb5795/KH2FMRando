"""ATKP attack-parameter table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Atkp/AtkpItem.cs).
Header: uint32 type | uint32 count. Entry size: 48 bytes, followed by a
trailing opaque footer of whatever bytes remain (AtkpFileEnd in the reference
editor -- unparsed there too).
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
ENTRY_SIZE = 48
_ENTRY_FMT = "<HHBBHBBBBhhHBBBBhiiHBbBBHBBBBBBBB"


@dataclass
class AtkpEntry:
    sub_id: int
    id: int
    type: int
    crit_adjust: int
    power: int
    team: int
    element: int
    reaction: int
    hit_effect: int
    knockback_str1: int
    knockback_str2: int
    unk16: int
    flags: int
    refact_self: int
    refact_other: int
    reflect_motion: int
    reflect_hit_back: int
    reflect_action: int
    sound_effect: int
    reflect_rc: int
    reflect_range: int
    reflect_angle: int
    damage_effect: int
    switch: int
    frames_per_hit: int
    floor_check: int
    drive_drain: int
    revenge: int
    tr_reaction: int
    combo_group: int
    random_effect: int
    kind: int
    hp_drain: int


@dataclass
class AtkpTable:
    type: int
    entries: List[AtkpEntry]
    footer: bytes


def parse_atkp(data: bytes) -> AtkpTable:
    type_val, count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE
    entries = []
    for i in range(count):
        base = header_size + i * ENTRY_SIZE
        fields = struct.unpack_from(_ENTRY_FMT, data, base)
        entries.append(AtkpEntry(*fields))
    footer_start = header_size + count * ENTRY_SIZE
    footer = data[footer_start:]
    return AtkpTable(type=type_val, entries=entries, footer=footer)


def write_atkp(table: AtkpTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.sub_id, e.id, e.type, e.crit_adjust, e.power, e.team, e.element,
            e.reaction, e.hit_effect, e.knockback_str1, e.knockback_str2, e.unk16,
            e.flags, e.refact_self, e.refact_other, e.reflect_motion, e.reflect_hit_back,
            e.reflect_action, e.sound_effect, e.reflect_rc, e.reflect_range,
            e.reflect_angle, e.damage_effect, e.switch, e.frames_per_hit,
            e.floor_check, e.drive_drain, e.revenge, e.tr_reaction, e.combo_group,
            e.random_effect, e.kind, e.hp_drain,
        )
    out += table.footer
    return bytes(out)
