# test_trsr.py
from pathlib import Path
import pytest

from parser.trsr import parse_trsr, write_trsr

TRSR = Path(__file__).parent.parent / "data" / "trsr.bin"

@pytest.fixture
def raw():
    if not TRSR.exists():
        pytest.skip(f"{TRSR} not present (game data, not committed)")
    return TRSR.read_bytes()

def test_trsr_roundtrip(raw):
    table = parse_trsr(raw)
    repacked = write_trsr(table)
    assert repacked == raw
    