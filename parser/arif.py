"""ARIF audio/room-info table parser for KH2FM (found in 03system.bin).

Layout confirmed against KH2FM_Editor (Model/System03/Arif/*.cs):
header (uint32 type | uint32 pointer count), then that many 4-byte pointers
(uint16 entry count | uint16 absolute byte offset into the file), each
pointing at a block of that many 64-byte ArifItem records. One block per
world; the pointer's offset is an absolute offset from the start of the file.
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

from .common import read_header, write_header

TYPE_SIZE = 4
COUNT_SIZE = 4
POINTER_SIZE = 4
ITEM_SIZE = 64
_ITEM_FMT = "<IiiiHHHHHHHHHHHHHHHHHHB11s"


@dataclass
class ArifItem:
    flag: int
    reverb: int
    bg_set1: int
    bg_set2: int
    bgm1a: int
    bgm1b: int
    bgm2a: int
    bgm2b: int
    bgm3a: int
    bgm3b: int
    bgm4a: int
    bgm4b: int
    bgm5a: int
    bgm5b: int
    bgm6a: int
    bgm6b: int
    bgm7a: int
    bgm7b: int
    bgm8a: int
    bgm8b: int
    voice: int
    navimap: int
    command: int
    reserve: bytes


@dataclass
class ArifBlock:
    entries: List[ArifItem]


@dataclass
class ArifTable:
    type: int
    blocks: List[ArifBlock]


def parse_arif(data: bytes) -> ArifTable:
    type_val, pointer_count = read_header(data, TYPE_SIZE, COUNT_SIZE)
    header_size = TYPE_SIZE + COUNT_SIZE

    pointers = []
    for i in range(pointer_count):
        base = header_size + i * POINTER_SIZE
        entry_count, offset = struct.unpack_from("<HH", data, base)
        pointers.append((entry_count, offset))

    blocks = []
    for entry_count, offset in pointers:
        entries = []
        for i in range(entry_count):
            base = offset + i * ITEM_SIZE
            fields = struct.unpack_from(_ITEM_FMT, data, base)
            entries.append(ArifItem(*fields))
        blocks.append(ArifBlock(entries=entries))

    return ArifTable(type=type_val, blocks=blocks)


def write_arif(table: ArifTable) -> bytes:
    header_size = TYPE_SIZE + COUNT_SIZE
    pointer_table_size = len(table.blocks) * POINTER_SIZE

    pointers = []
    offset = header_size + pointer_table_size
    body = bytearray()
    for block in table.blocks:
        pointers.append((len(block.entries), offset))
        for e in block.entries:
            body += struct.pack(
                _ITEM_FMT,
                e.flag, e.reverb, e.bg_set1, e.bg_set2,
                e.bgm1a, e.bgm1b, e.bgm2a, e.bgm2b, e.bgm3a, e.bgm3b,
                e.bgm4a, e.bgm4b, e.bgm5a, e.bgm5b, e.bgm6a, e.bgm6b,
                e.bgm7a, e.bgm7b, e.bgm8a, e.bgm8b,
                e.voice, e.navimap, e.command, e.reserve,
            )
        offset += len(block.entries) * ITEM_SIZE

    out = bytearray(write_header(table.type, len(table.blocks), TYPE_SIZE, COUNT_SIZE))
    for entry_count, ptr_offset in pointers:
        out += struct.pack("<HH", entry_count, ptr_offset)
    out += body
    return bytes(out)
