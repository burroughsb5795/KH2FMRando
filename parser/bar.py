"""BAR container format parser for KH2 binary files."""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import List, Optional

BAR_MAGIC = b"BAR\x01"
HEADER_SIZE = 16       # 4 magic + 4 count + 8 padding
ENTRY_RECORD_SIZE = 16 # per-entry header in the table


@dataclass
class BarEntry:
    type: int
    name: str
    offset: int
    size: int


@dataclass
class Bar:
    entries: List[BarEntry]
    _data: bytes

    def find(self, name: str) -> Optional[BarEntry]:
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None

    def read(self, entry: BarEntry) -> bytes:
        return self._data[entry.offset : entry.offset + entry.size]


def parse_bar(data: bytes) -> Bar:
    if data[:4] != BAR_MAGIC:
        raise ValueError(f"Not a BAR file (magic={data[:4]!r})")

    count = struct.unpack_from("<I", data, 4)[0]
    entries: List[BarEntry] = []
    for i in range(count):
        base = HEADER_SIZE + i * ENTRY_RECORD_SIZE
        etype = struct.unpack_from("<H", data, base)[0]
        name = data[base + 4 : base + 8].rstrip(b"\x00").decode("ascii")
        offset = struct.unpack_from("<I", data, base + 8)[0]
        size = struct.unpack_from("<I", data, base + 12)[0]
        entries.append(BarEntry(type=etype, name=name, offset=offset, size=size))

    return Bar(entries=entries, _data=data)
