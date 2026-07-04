"""TRSR treasure table parser for KH2FM (found in 03system.bin).

Field layout confirmed against KH2FM_Editor (osdanova/KH2FM_Editor TrsrItem.cs):
  offset 0  size 2: id           uint16  unique chest identifier
  offset 2  size 2: item         uint16  item reward — the value randomizers swap
  offset 4  size 1: type         uint8   0=Chest, 1=Event
  offset 5  size 1: world        uint8   world id
  offset 6  size 1: room         uint8   room number within world
  offset 7  size 1: room_index   uint8   chest index within room
  offset 8  size 2: event        uint16  event identifier
  offset 10 size 2: global_index uint16  global index
"""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List

TRSR_HEADER_SIZE = 4   # uint16 version + uint16 count
TRSR_ENTRY_SIZE = 12
_ENTRY_FMT = "<HHBBBBHH"


@dataclass
class TrsrEntry:
    id: int           # unique chest identifier
    item: int         # item reward (this is what randomizers swap)
    type: int         # 0=Chest, 1=Event
    world: int        # world id
    room: int         # room number within world
    room_index: int   # chest index within room
    event: int        # event identifier
    global_index: int # global index

    @property
    def entry_type(self) -> str:
        return "Event" if self.type == 1 else "Chest"


@dataclass
class TrsrTable:
    version: int
    entries: List[TrsrEntry]

    def chests(self) -> List[TrsrEntry]:
        return [e for e in self.entries if e.entry_type == "Chest"]

    def events(self) -> List[TrsrEntry]:
        return [e for e in self.entries if e.entry_type == "Event"]

    def by_world(self, world: int) -> List[TrsrEntry]:
        return [e for e in self.entries if e.world == world]


def parse_trsr(data: bytes) -> TrsrTable:
    if len(data) < TRSR_HEADER_SIZE:
        raise ValueError("Data too short for TRSR header")

    version, count = struct.unpack_from("<HH", data, 0)
    expected = TRSR_HEADER_SIZE + count * TRSR_ENTRY_SIZE
    if len(data) < expected:
        raise ValueError(
            f"Data too short: need {expected} bytes for {count} entries, got {len(data)}"
        )

    entries: List[TrsrEntry] = []
    for i in range(count):
        base = TRSR_HEADER_SIZE + i * TRSR_ENTRY_SIZE
        id_, item, type_, world, room, room_index, event, global_index = struct.unpack_from(
            _ENTRY_FMT, data, base
        )
        entries.append(TrsrEntry(
            id=id_,
            item=item,
            type=type_,
            world=world,
            room=room,
            room_index=room_index,
            event=event,
            global_index=global_index,
        ))

    return TrsrTable(version=version, entries=entries)


def write_trsr(table: TrsrTable) -> bytes:
    count = len(table.entries)
    out = bytearray(struct.pack("<HH", table.version, count))
    for e in table.entries:
        out += struct.pack(
            _ENTRY_FMT,
            e.id, e.item, e.type, e.world, e.room, e.room_index, e.event, e.global_index,
        )
    return bytes(out)
