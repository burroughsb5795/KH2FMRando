"""Shared helpers for the Str_EntryFile-style tables used across 03system.bin.

Mirrors the layout used by KH2FM_Editor (osdanova/KH2FM_Editor, Model/COMMON/Str_EntryFile.cs):
a header of `type_size` + `count_size` bytes (little-endian, either field may be 0),
followed by `count` fixed-size entries, followed by optional trailing padding.
"""

from __future__ import annotations


def read_header(data: bytes, type_size: int, count_size: int) -> tuple[int, int]:
    type_val = int.from_bytes(data[0:type_size], "little") if type_size else 0
    count = int.from_bytes(data[type_size:type_size + count_size], "little") if count_size else 0
    return type_val, count


def write_header(type_val: int, count: int, type_size: int, count_size: int) -> bytes:
    out = b""
    if type_size:
        out += type_val.to_bytes(type_size, "little")
    if count_size:
        out += count.to_bytes(count_size, "little")
    return out
