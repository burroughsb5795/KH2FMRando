# test_shuffle_pools.py
import random

import yaml

from scripts.build_pools import slots_from_lvup
from scripts.shuffle_pools import (
    ABILITY_CATEGORY, MAGIC_CATEGORY, combine, deal, group_by_table, shuffle_pool, write_lvup,
)


def _lvup_level(**overrides):
    level = {"Level": 1, "Exp": 0, "Strength": 0, "Magic": 0, "Defense": 0, "Ap": 0,
             "AbiSword": 0, "AbiShield": 0, "AbiStaff": 0}
    level.update(overrides)
    return level


def test_slots_from_lvup_drops_mickey_and_renames_sora():
    data = {
        "Sora/Roxas": [_lvup_level()],
        "Mickey": [_lvup_level()],
        "Donald": [_lvup_level()],
    }
    characters = {s.address["character"] for s in slots_from_lvup(data)}
    assert characters == {"Sora", "Donald"}


def test_write_lvup_remaps_by_ability_identity_not_level():
    """Sword/Shield/Staff teach the same abilities at different levels in
    vanilla (a rotation of the same 3 values here). The writer should remap
    each column by what ability it originally held, not overwrite every
    column with one shuffled-per-level value -- so a rotation in stays a
    rotation out, just with new ability ids, and a level where all three
    already coincide (100 here) stays coincident after remapping."""
    data = {
        "Sora/Roxas": [
            _lvup_level(Level=1, AbiSword=100, AbiShield=200, AbiStaff=300),
            _lvup_level(Level=2, AbiSword=200, AbiShield=300, AbiStaff=100),
            _lvup_level(Level=3, AbiSword=300, AbiShield=100, AbiStaff=200),
            _lvup_level(Level=4, AbiSword=400, AbiShield=400, AbiStaff=400),
        ],
    }
    slots = list(slots_from_lvup(data))
    records = [{"table": s.table, "address": s.address, "item_id": s.item_id} for s in slots]

    # simulate the pool shuffle's result for the 4 unique vanilla abilities
    mapping = {100: 7, 200: 8, 300: 9, 400: 40}
    for r in records:
        if r["address"]["part"] == "ability":
            addr = r["address"]
            old = addr["raw_sword"] or addr["raw_shield"] or addr["raw_staff"]
            r["item_id"] = mapping[old]

    out = yaml.safe_load(write_lvup(records))
    sora = out["Sora"]

    assert (sora[1]["SwordAbility"], sora[1]["ShieldAbility"], sora[1]["StaffAbility"]) == (7, 8, 9)
    assert (sora[2]["SwordAbility"], sora[2]["ShieldAbility"], sora[2]["StaffAbility"]) == (8, 9, 7)
    assert (sora[3]["SwordAbility"], sora[3]["ShieldAbility"], sora[3]["StaffAbility"]) == (9, 7, 8)
    assert (sora[4]["SwordAbility"], sora[4]["ShieldAbility"], sora[4]["StaffAbility"]) == (40, 40, 40)


def test_deal_permutes_without_changing_the_multiset():
    entries = [{"item_id": i} for i in range(20)]
    before = sorted(e["item_id"] for e in entries)
    deal(entries, random.Random(1))
    after = sorted(e["item_id"] for e in entries)
    assert before == after
    assert [e["item_id"] for e in entries] != list(range(20))


def test_deal_is_deterministic_for_a_given_seed():
    a = [{"item_id": i} for i in range(10)]
    b = [{"item_id": i} for i in range(10)]
    deal(a, random.Random(42))
    deal(b, random.Random(42))
    assert a == b


def test_combine_concatenates_every_bucket():
    pool = [{"item_id": 1}]
    grouped = {"g1": [{"item_id": 2}], "g2": [{"item_id": 3}]}
    locked = [{"item_id": 4}]
    forced = [{"item_id": 5}]
    excluded = [{"item_id": 6}]
    combined = combine(pool, grouped, locked, forced, excluded)
    assert sorted(e["item_id"] for e in combined) == [1, 2, 3, 4, 5, 6]


def test_group_by_table_buckets_by_table_key():
    combined = [
        {"table": "trsr", "item_id": 1},
        {"table": "lvup", "item_id": 2},
        {"table": "trsr", "item_id": 3},
    ]
    by_table = group_by_table(combined)
    assert [e["item_id"] for e in by_table["trsr"]] == [1, 3]
    assert [e["item_id"] for e in by_table["lvup"]] == [2]


def _pool_entry(table, item_id, part=None):
    address = {"part": part} if part else {}
    return {"table": table, "address": address, "item_id": item_id}


def _category_pool():
    # 1,2 = general (no category); 3,4 = magic (18); 5,6,7 = ability (19)
    categories = {1: 0, 2: 0, 3: 18, 4: 18, 5: 19, 6: 19, 7: 19}
    pool = [
        _pool_entry("trsr", 1),
        _pool_entry("trsr", 2),
        _pool_entry("trsr", 3),          # trsr's own magic-sourced slot
        _pool_entry("fmlv", 5),
        _pool_entry("lvup", 6, part="ability"),
        _pool_entry("bons", 4, part="item1"),   # bons' magic-sourced slot
        _pool_entry("bons", 7, part="item2"),   # bons' ability-sourced slot
    ]
    return pool, categories


def test_shuffle_pool_never_crosses_incompatible_categories():
    pool, categories = _category_pool()
    shuffle_pool(pool, random.Random(7), categories)

    trsr_items = [e["item_id"] for e in pool if e["table"] == "trsr"]
    ability_items = [e["item_id"] for e in pool if e["table"] in ("fmlv", "lvup")]
    bons_items = [e["item_id"] for e in pool if e["table"] == "bons"]

    assert all(categories[i] != ABILITY_CATEGORY for i in trsr_items)
    assert all(categories[i] == ABILITY_CATEGORY for i in ability_items)
    assert all(categories[i] in (MAGIC_CATEGORY, ABILITY_CATEGORY) for i in bons_items)


def test_shuffle_pool_preserves_the_multiset():
    pool, categories = _category_pool()
    before = sorted(e["item_id"] for e in pool)
    shuffle_pool(pool, random.Random(7), categories)
    after = sorted(e["item_id"] for e in pool)
    assert before == after


def test_shuffle_pool_is_deterministic_for_a_given_seed():
    pool_a, categories = _category_pool()
    pool_b, _ = _category_pool()
    shuffle_pool(pool_a, random.Random(99), categories)
    shuffle_pool(pool_b, random.Random(99), categories)
    assert pool_a == pool_b
