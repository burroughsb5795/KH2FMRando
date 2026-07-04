import struct
from pathlib import Path

def extract_bar(data: bytes) -> dict[str, bytes]:
    magic, num_files = struct.unpack_from("<4si", data, 0)
    if magic != b"BAR\x01":
        raise ValueError(f"not a BAR archive: {magic!r}")
    out = {}
    pos = 16  # skip 4 magic + 4 count + 8 padding
    for _ in range(num_files):
        _type, _dup, name, offset, size = struct.unpack_from("<HH4sii", data, pos)
        name = name.rstrip(b"\x00").decode("ascii", "replace")
        out[name] = data[offset:offset + size]
        pos += 16
    return out

sub = extract_bar(Path("data/03system.bin").read_bytes())
#print("sub-files:", list(sub))          # trsr, item, shop, ...
Path("data/trsr.bin").write_bytes(sub["trsr"])