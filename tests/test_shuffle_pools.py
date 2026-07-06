# test_shuffle_pools.py
import random

from scripts.build_pools import slots_from_lvup
from scripts.shuffle_pools import combine, deal, group_by_table


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
