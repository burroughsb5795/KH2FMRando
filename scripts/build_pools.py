#!/usr/bin/env python3
"""Classify every preset in presets/ and bucket its slots for the shuffle.

Reads presets/*.yml, runs each entry through classify() against
config/rules.yaml, and writes output/pools.yml with five buckets:

    pool      -> one shared list; item_ids here get shuffled together
    grouped   -> one list per named group; item_ids shuffle within their group
    locked    -> kept at their vanilla item_id, never touched
    forced    -> item_id overridden to the rule's forced value
    excluded  -> not shuffleable (stat columns, empty slots); listed for
                 visibility only, not part of any pool
"""

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.classify import classify, Slot, Disposition
from scripts.paths import resource_root, output_root

PRESETS_DIR = resource_root() / "presets"
RULES_PATH = resource_root() / "config" / "rules.yaml"
OUTPUT_PATH = output_root() / "output" / "pools.yml"


# Final Form (item 29) has no vanilla trsr slot -- unlike Valor/Wisdom/
# Master/Limit Form, which are already ordinary chest items and have been
# poolable all along, Final Form is normally granted by a post-Roxas story
# event in The World That Never Was that this project doesn't touch. Row 2
# (trsr id 498, vanilla "Mythril Shard", one of 37 in the game) is
# repurposed to supply it instead, making it a genuinely obtainable,
# randomly-placed pool item like the other forms -- the normal late-game
# unlock still works independently if a seed doesn't hand it out early.
FINAL_FORM_ITEM_ID = 29
FINAL_FORM_HOST_INDEX = 2


def slots_from_trsr(data: dict):
    """trsrList.yml is keyed by TrsrEntry.id, in table row order; the row
    order (not the id) is what rules.yaml's trsr `index` rules address."""
    for i, fields in enumerate(data.values()):
        item_id = FINAL_FORM_ITEM_ID if i == FINAL_FORM_HOST_INDEX else fields["ItemId"]
        yield Slot("trsr", {"index": i}, item_id=item_id)


def slots_from_fmlv(data: dict):
    """formsList.yml is keyed by row index; each row carries the raw packed
    fields (Type/Level/AntiRate/AbilityLevel) needed to rebuild the OpenKH
    FmlvList entry. Type 6 (the anti-form meter, 3 rows, Reward always 0)
    isn't a real ability slot -- it's excluded via exclude_null in rules.yaml
    and the writer drops it entirely (no "Anti" form in the OpenKH schema)."""
    for fields in data.values():
        yield Slot("fmlv", {
            "type": fields["Type"], "level": fields["Level"],
            "anti_rate": fields["AntiRate"], "ability_level": fields["AbilityLevel"],
            "exp": fields["Exp"],
        }, item_id=fields["Reward"])


def slots_from_bons(data: dict):
    """eventList.yml nests id -> character -> fields, with two independent
    item slots (Item1/Item2) per character row -- each becomes its own
    poolable slot, carrying the rest of that row's fields so the writer can
    rebuild the full record without re-reading the preset."""
    for entry_id, chars in data.items():
        for char_name, fields in chars.items():
            base = {
                "id": entry_id, "character": char_name,
                "character_id": fields["CharacterId"], "hp": fields["Hp"],
                "mp": fields["Mp"], "drive": fields["Drive"],
                "item_slot": fields["ItemSlot"], "acc_slot": fields["AccSlot"],
                "armor_slot": fields["ArmorSlot"],
            }
            yield Slot("bons", {**base, "part": "item1"}, item_id=fields["Item1"])
            yield Slot("bons", {**base, "part": "item2"}, item_id=fields["Item2"])


# lvup.yml carries a "Mickey" table, but he's not a real playable character slot in
# the mod output (his abilities are all-zero vanilla anyway, so dropping him
# changes nothing about the shuffle); Sora's table is keyed "Sora/Roxas" since
# Roxas shares it, but the output just calls it "Sora".
LVUP_EXCLUDED_CHARACTERS = {"Mickey"}
# Renamed to match OpenKH.Patcher's characterMap exactly (PatcherProcessor.cs) --
# a name that isn't an exact key match throws a lookup error when the mod is applied.
LVUP_CHARACTER_RENAME = {"Sora/Roxas": "Sora", "Ping/Mulan": "PingMulan"}


def slots_from_lvup(data: dict):
    """Stat columns are excluded outright (kind="stat"), but carry their
    growth values in the address so the lvup writer can rebuild the entry
    without re-reading the preset.

    The 3 ability columns (sword/shield/staff) teach the exact same 23
    abilities in vanilla, just at different levels per weapon (confirmed:
    the three columns are the identical multiset, just permuted). One
    "ability" slot per level anchors the shuffle -- item_id is whichever
    column is nonzero (always AbiSword when present) -- but all 3 raw
    values are carried in the address so the writer can remap each column
    independently by ability *identity* rather than by level, preserving
    vanilla's per-weapon ordering shape instead of forcing every weapon
    into lockstep. See write_lvup in shuffle_pools.py."""
    for character, levels in data.items():
        if character in LVUP_EXCLUDED_CHARACTERS:
            continue
        character = LVUP_CHARACTER_RENAME.get(character, character)
        for lv in levels:
            level = lv["Level"]
            yield Slot("lvup", {
                "character": character, "level": level, "part": "stats",
                "exp": lv["Exp"], "strength": lv["Strength"], "magic": lv["Magic"],
                "defense": lv["Defense"], "ap": lv["Ap"],
            }, item_id=0, kind="stat")
            raw_sword, raw_shield, raw_staff = lv["AbiSword"], lv["AbiShield"], lv["AbiStaff"]
            ability = raw_sword or raw_shield or raw_staff
            yield Slot("lvup", {
                "character": character, "level": level, "part": "ability",
                "raw_sword": raw_sword, "raw_shield": raw_shield, "raw_staff": raw_staff,
            }, item_id=ability)


# preset filename -> (table name as used in config/rules.yaml, slot adapter)
PRESETS = {
    "trsrList.yml": ("trsr", slots_from_trsr),
    "formsList.yml": ("fmlv", slots_from_fmlv),
    "eventList.yml": ("bons", slots_from_bons),
    "lvup.yml": ("lvup", slots_from_lvup),
}


def record(slot: Slot, **overrides) -> dict:
    entry = {"table": slot.table, "address": slot.address, "item_id": slot.item_id}
    entry.update(overrides)
    return entry


def all_group_names(rules: dict) -> set:
    names = set()
    for table_rules in rules.values():
        if isinstance(table_rules, dict):
            names.update(table_rules.get("groups", {}))
    return names


def build_buckets(rules: dict, disabled_tables: frozenset = frozenset()) -> dict:
    """disabled_tables lets a caller (e.g. the GUI) opt a whole table out of
    randomization -- every one of its slots is routed to "locked" (kept at
    its vanilla item_id) instead of being classified normally."""
    pool = []
    # pre-seeded so groups with no poolable members (e.g. a character with no
    # nonzero abilities in the vanilla data) still show up as empty, not missing
    grouped = {name: [] for name in all_group_names(rules)}
    locked = []
    forced = []
    excluded = []

    for filename, (table_name, adapter) in PRESETS.items():
        data = yaml.safe_load((PRESETS_DIR / filename).read_text())
        table_rules = rules.get(table_name)
        for slot in adapter(data):
            if table_name in disabled_tables:
                locked.append(record(slot, reason="table disabled by user"))
                continue
            decision = classify(slot, table_rules)
            if decision.disposition is Disposition.POOL:
                pool.append(record(slot))
            elif decision.disposition is Disposition.GROUPED:
                grouped[decision.group].append(record(slot))
            elif decision.disposition is Disposition.LOCKED:
                locked.append(record(slot, reason=decision.reason))
            elif decision.disposition is Disposition.FORCED:
                forced.append(record(slot, item_id=decision.forced_item, reason=decision.reason))
            elif decision.disposition is Disposition.EXCLUDED:
                excluded.append(record(slot, reason=decision.reason))

    return {
        "pool": pool,
        "grouped": grouped,
        "locked": locked,
        "forced": forced,
        "excluded": excluded,
    }


def main():
    ap = argparse.ArgumentParser(description="Classify presets/ slots into output/pools.yml")
    ap.add_argument(
        "--disable", nargs="*", default=[], choices=sorted(t for t, _ in PRESETS.values()),
        help="Table(s) to keep 100%% vanilla (excluded from randomization entirely)",
    )
    args = ap.parse_args()

    rules = yaml.safe_load(RULES_PATH.read_text()) or {}
    buckets = build_buckets(rules, disabled_tables=frozenset(args.disable))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w") as f:
        yaml.safe_dump(buckets, f, sort_keys=False, default_flow_style=False)

    print(f"pool: {len(buckets['pool'])}")
    for group, entries in buckets["grouped"].items():
        print(f"grouped[{group}]: {len(entries)}")
    print(f"locked: {len(buckets['locked'])}")
    print(f"forced: {len(buckets['forced'])}")
    print(f"excluded: {len(buckets['excluded'])}")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
