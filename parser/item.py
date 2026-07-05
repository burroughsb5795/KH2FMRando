"""ITEM item/equipment table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Item/*.cs). The file is
two back-to-back Str_EntryFile tables: an item table, then an equipment
(stat) table for the equippable subset, immediately following it.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4

ITEM_ENTRY_SIZE = 24
_ITEM_FMT = "<HBBBBHHHHHHHHBB"

EQUIP_ENTRY_SIZE = 16
_EQUIP_FMT = "<HHBBBBBBBBBBBB"


@dataclass
class ItemEntry:
    id: int
    category: int
    visibility: int
    sub_id: int
    rank: int
    status: int
    name: int
    description: int
    buy: int
    sell: int
    command: int
    slot: int
    image: int
    prize_box: int
    icon: int


@dataclass
class EquipmentEntry:
    id: int
    ability: int
    strength: int
    magic: int
    defense: int
    ap: int
    phys_res: int
    fire_res: int
    bliz_res: int
    thun_res: int
    dark_res: int
    neutral_res: int
    general_res: int
    padding: int


@dataclass
class ItemTable:
    type: int
    entries: List[ItemEntry]
    equip_type: int
    equipment: List[EquipmentEntry]


def parse_item(data: bytes) -> ItemTable:
    header_size = TYPE_SIZE + COUNT_SIZE
    type_val, item_count = read_header(data, TYPE_SIZE, COUNT_SIZE)

    entries = []
    for i in range(item_count):
        base = header_size + i * ITEM_ENTRY_SIZE
        fields = struct.unpack_from(_ITEM_FMT, data, base)
        entries.append(ItemEntry(*fields))

    equip_start = header_size + item_count * ITEM_ENTRY_SIZE
    equip_type, equip_count = read_header(data[equip_start:], TYPE_SIZE, COUNT_SIZE)

    equipment = []
    for i in range(equip_count):
        base = equip_start + header_size + i * EQUIP_ENTRY_SIZE
        fields = struct.unpack_from(_EQUIP_FMT, data, base)
        equipment.append(EquipmentEntry(*fields))

    return ItemTable(type=type_val, entries=entries, equip_type=equip_type, equipment=equipment)


def write_item(table: ItemTable) -> bytes:
    out = bytearray(write_header(table.type, len(table.entries), TYPE_SIZE, COUNT_SIZE))
    for e in table.entries:
        out += struct.pack(
            _ITEM_FMT,
            e.id, e.category, e.visibility, e.sub_id, e.rank, e.status, e.name,
            e.description, e.buy, e.sell, e.command, e.slot, e.image, e.prize_box, e.icon,
        )

    out += write_header(table.equip_type, len(table.equipment), TYPE_SIZE, COUNT_SIZE)
    for e in table.equipment:
        out += struct.pack(
            _EQUIP_FMT,
            e.id, e.ability, e.strength, e.magic, e.defense, e.ap, e.phys_res,
            e.fire_res, e.bliz_res, e.thun_res, e.dark_res, e.neutral_res,
            e.general_res, e.padding,
        )
    return bytes(out)
