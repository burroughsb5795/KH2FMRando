# test_pools.py
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
POOLS_PATH = REPO_ROOT / "output" / "pools.yml"
PRESETS_DIR = REPO_ROOT / "presets"


@pytest.fixture
def pools():
    if not POOLS_PATH.exists():
        pytest.skip(f"{POOLS_PATH} not present -- run scripts/build_pools.py first")
    return yaml.safe_load(POOLS_PATH.read_text())


def bucket_total(pools: dict) -> int:
    return (len(pools.get("pool", []))
            + len(pools.get("locked", []))
            + len(pools.get("forced", []))
            + len(pools.get("excluded", []))
            + sum(len(s) for s in pools.get("grouped", {}).values()))


def test_bucket_total_matches_vanilla_slot_count(pools):
    trsr = yaml.safe_load((PRESETS_DIR / "trsrList.yml").read_text())
    fmlv = yaml.safe_load((PRESETS_DIR / "formsList.yml").read_text())
    bons = yaml.safe_load((PRESETS_DIR / "eventList.yml").read_text())
    lvup = yaml.safe_load((PRESETS_DIR / "lvup.yml").read_text())

    # Mickey's table is dropped from the mod output -- see
    # LVUP_EXCLUDED_CHARACTERS in scripts/build_pools.py
    lvup_levels = sum(len(levels) for char, levels in lvup.items() if char != "Mickey")

    # bons nests id -> character -> fields; count character rows, not ids
    bons_char_rows = sum(len(chars) for chars in bons.values())

    vanilla_total = (
        len(trsr)
        + len(fmlv)
        + bons_char_rows * 2  # item1 + item2 slot per character row
        + lvup_levels * 2  # stats + ability slot per level
    )
    assert bucket_total(pools) == vanilla_total


def test_every_disposition_bucket_is_present(pools):
    for section in ("pool", "grouped", "locked", "forced", "excluded"):
        assert section in pools
