"""LVUP level-up table parser for KH2FM (found in 00battle.bin).

Layout confirmed against KH2FM_Editor (Model/Battle/Lvup/*.cs): header
(uint32 type | uint32 character-pointer count), then that many uint32 pointers
(word index, x4 for a byte offset). Pointer 0 is unused padding; each of the
rest points at one character's level table -- a uint32 entry count (always 99)
followed by that many 16-byte LvupItem records.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
POINTER_SIZE = 4
LEVEL_ENTRY_SIZE = 16
_LEVEL_FMT = "<IBBBBHHHH"

# Character order for nonzero pointers 1..13 (pointer 0 is unused padding).
CHARACTERS = [
    "Sora/Roxas", "Donald", "Goofy", "Mickey", "Auron", "Ping/Mulan",
    "Aladdin", "Sparrow", "Beast", "Jack", "Simba", "Tron", "Riku",
]


@dataclass
class LvupLevel:
    exp: int
    strength: int
    magic: int
    defense: int
    ap: int
    abi_sword: int
    abi_shield: int
    abi_staff: int
    padding: int


@dataclass
class LvupCharacter:
    name: str
    levels: List[LvupLevel]  # 99 levels


@dataclass
class LvupTable:
    type: int
    characters: List[LvupCharacter]


def parse_lvup(data: bytes) -> LvupTable:
    type_val, pointer_count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE

    pointers = [
        struct.unpack_from("<I", data, header_size + i * POINTER_SIZE)[0]
        for i in range(pointer_count)
    ]

    characters = []
    for i, pointer in enumerate(pointers):
        if i == 0:
            continue  # padding entry
        byte_offset = pointer * POINTER_SIZE
        level_count = struct.unpack_from("<I", data, byte_offset)[0]
        levels = []
        for j in range(level_count):
            base = byte_offset + 4 + j * LEVEL_ENTRY_SIZE
            fields = struct.unpack_from(_LEVEL_FMT, data, base)
            levels.append(LvupLevel(*fields))
        name = CHARACTERS[i - 1] if i - 1 < len(CHARACTERS) else f"Character{i}"
        characters.append(LvupCharacter(name=name, levels=levels))

    return LvupTable(type=type_val, characters=characters)


def write_lvup(table: LvupTable) -> bytes:
    header_size = TYPE_SIZE + COUNT_SIZE
    pointer_count = len(table.characters) + 1
    pointer_table_size = pointer_count * POINTER_SIZE

    pointers = [0]  # padding entry
    body = bytearray()
    word_offset = (header_size + pointer_table_size) // POINTER_SIZE
    for character in table.characters:
        pointers.append(word_offset)
        body += struct.pack("<I", len(character.levels))
        for lvl in character.levels:
            body += struct.pack(
                _LEVEL_FMT,
                lvl.exp, lvl.strength, lvl.magic, lvl.defense, lvl.ap,
                lvl.abi_sword, lvl.abi_shield, lvl.abi_staff, lvl.padding,
            )
        word_offset += (4 + len(character.levels) * LEVEL_ENTRY_SIZE) // POINTER_SIZE

    out = bytearray(write_header(table.type, pointer_count, TYPE_SIZE, COUNT_SIZE))
    for p in pointers:
        out += struct.pack("<I", p)
    out += body
    return bytes(out)
