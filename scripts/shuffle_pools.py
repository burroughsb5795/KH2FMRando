#!/usr/bin/env python3
"""Shuffle output/pools.yml with a seeded RNG and write the result back out
as per-table preset ymls for the mod pipeline.

pool[] is shuffled as one shared deck; each groups{} entry is shuffled as its
own private deck (dealt independently, same seeded RNG). locked[], forced[],
and excluded[] pass through unchanged. Everything is then recombined, grouped
by table, merged back into the original preset records (to recover the
non-item fields pools.yml doesn't carry), and written out.
"""

import argparse
import random
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.paths import resource_root, output_root

PRESETS_DIR = resource_root() / "presets"
OUTPUT_DIR = output_root() / "output"
POOLS_PATH = OUTPUT_DIR / "pools.yml"
ITEM_LIST_PATH = PRESETS_DIR / "itemList.yml"

# table name -> output filename
OUTPUT_FILENAMES = {
    "trsr": "TrsrList.yml",
    "lvup": "lvlList.yml",
    "fmlv": "formsList.yml",
    "bons": "eventList.yml",
}

# Item categories aren't interchangeable everywhere: vanilla trsr chests
# never contain an ability (category 19), and vanilla fmlv/lvup-ability/bons
# never contain anything outside {magic=18, ability=19} -- confirmed by
# scanning every vanilla reward in each table. Handing a chest an ability,
# or a level-up slot a weapon, isn't something the game expects and crashes
# on (same failure class as the bons RewardId bug, different cause).
ABILITY_CATEGORY = 19
MAGIC_CATEGORY = 18


def load_pools():
    if not POOLS_PATH.exists():
        sys.exit(f"{POOLS_PATH} not found -- run scripts/build_pools.py first")
    data = yaml.safe_load(POOLS_PATH.read_text())
    return data["pool"], data["grouped"], data["locked"], data["forced"], data["excluded"]


def load_item_categories() -> dict:
    data = yaml.safe_load(ITEM_LIST_PATH.read_text())
    return {item_id: fields["Category"] for item_id, fields in data.items()}


def deal(entries: list, rng: random.Random) -> None:
    """Shuffle the item_ids across entries in place -- same slots, new items."""
    item_ids = [e["item_id"] for e in entries]
    rng.shuffle(item_ids)
    for entry, item_id in zip(entries, item_ids):
        entry["item_id"] = item_id


def is_ability_slot(entry: dict) -> bool:
    if entry["table"] == "fmlv":
        return True
    return entry["table"] == "lvup" and entry["address"].get("part") == "ability"


def shuffle_pool(pool: list, rng: random.Random, categories: dict) -> None:
    """Category-safe replacement for a flat deal() over the shared pool.

    Splits the pool into three decks by what vanilla actually shows is safe:
    general (trsr only), magic (trsr + bons), ability (fmlv + lvup-ability +
    bons). trsr's demand is filled by all of general plus however much magic
    it needs; ability-only slots draw straight from the ability deck; bons
    (the one table that accepts either magic or ability) absorbs whatever's
    left of both -- which always divides evenly, since every pool entry is
    counted on exactly one side of both partitions (by table, and by its own
    vanilla category).
    """
    trsr_entries = [e for e in pool if e["table"] == "trsr"]
    ability_entries = [e for e in pool if is_ability_slot(e)]
    bons_entries = [e for e in pool if e["table"] == "bons"]
    assert len(trsr_entries) + len(ability_entries) + len(bons_entries) == len(pool)

    general = [e["item_id"] for e in trsr_entries if categories.get(e["item_id"]) != MAGIC_CATEGORY]
    magic = [e["item_id"] for e in trsr_entries if categories.get(e["item_id"]) == MAGIC_CATEGORY]
    magic += [e["item_id"] for e in bons_entries if categories.get(e["item_id"]) == MAGIC_CATEGORY]
    ability = [e["item_id"] for e in ability_entries]
    ability += [e["item_id"] for e in bons_entries if categories.get(e["item_id"]) == ABILITY_CATEGORY]

    rng.shuffle(magic)
    rng.shuffle(ability)

    trsr_need = len(trsr_entries) - len(general)
    trsr_deck = general + magic[:trsr_need]
    leftover_magic = magic[trsr_need:]

    ability_need = len(ability_entries)
    ability_deck = ability[:ability_need]
    leftover_ability = ability[ability_need:]

    bons_deck = leftover_magic + leftover_ability
    assert len(bons_deck) == len(bons_entries)

    rng.shuffle(trsr_deck)
    rng.shuffle(ability_deck)
    rng.shuffle(bons_deck)

    for entry, item_id in zip(trsr_entries, trsr_deck):
        entry["item_id"] = item_id
    for entry, item_id in zip(ability_entries, ability_deck):
        entry["item_id"] = item_id
    for entry, item_id in zip(bons_entries, bons_deck):
        entry["item_id"] = item_id


def shuffle_all(pool: list, grouped: dict, rng: random.Random, categories: dict) -> None:
    shuffle_pool(pool, rng, categories)
    for group_entries in grouped.values():
        deal(group_entries, rng)


def combine(pool, grouped, locked, forced, excluded) -> list:
    combined = list(pool)
    for group_entries in grouped.values():
        combined.extend(group_entries)
    combined.extend(locked)
    combined.extend(forced)
    combined.extend(excluded)
    return combined


def group_by_table(combined: list) -> dict:
    by_table = {}
    for entry in combined:
        by_table.setdefault(entry["table"], []).append(entry)
    return by_table


# ---- per-table reconstruction: merge shuffled item_ids into full preset
# records and dump to yaml text. Each writer controls its own dump options.

def build_trsr_yml(slots: list) -> str:
    original = yaml.safe_load((PRESETS_DIR / "trsrList.yml").read_text())
    keys_in_order = list(original.keys())
    by_index = {s["address"]["index"]: s["item_id"] for s in slots}
    out = {key: {"ItemId": by_index[i]} for i, key in enumerate(keys_in_order)}
    return yaml.safe_dump(out, sort_keys=False, default_flow_style=False)


# FormId -> OpenKH form name. Type 6 (anti-form meter) has no Ability slot in
# vanilla (Reward is always 0) and isn't part of the OpenKH FmlvList schema --
# it's dropped here rather than emitted as a bogus 7th form.
FMLV_FORM_NAMES = {0: "Summon", 1: "Valor", 2: "Wisdom", 3: "Limit", 4: "Master", 5: "Final"}


def build_fmlv_yml(slots: list) -> str:
    out = {}   # {form_name: [ {FormId, FormLevel, Experience, Ability, GrowthAbilityLevel}, ... ]}
    for s in slots:
        addr = s["address"]
        form = FMLV_FORM_NAMES.get(addr["type"])
        if form is None:
            continue
        out.setdefault(form, []).append({
            "FormId": addr["type"],
            "FormLevel": addr["level"],
            "Experience": addr["exp"],
            "Ability": s["item_id"],          # the shuffled ability
            "GrowthAbilityLevel": addr["ability_level"],
        })
    for levels in out.values():
        levels.sort(key=lambda e: e["FormLevel"])
    return yaml.safe_dump(out, sort_keys=False, default_flow_style=False)


def build_bons_yml(slots: list) -> str:
    out = {}   # {id: {char_name: {fields...}}}
    for s in slots:
        addr = s["address"]
        bid, char = addr["id"], addr["character"]      # "Donald", "Sora", etc.
        block = out.setdefault(bid, {}).setdefault(char, {
            # OpenKH deserializes this record directly into its Bons class,
            # which is a flat list keyed by RewardId -- omitting it here
            # means every row comes back RewardId=0 after listpatch, which
            # corrupts the id/event mapping for the whole table regardless
            # of what item ends up in it.
            "RewardId": bid,
            "AccessorySlotUpgrade": addr["acc_slot"],
            "ArmorSlotUpgrade": addr["armor_slot"],
            "BonusItem1": 0,
            "BonusItem2": 0,
            "CharacterId": addr["character_id"],
            "DriveGaugeUpgrade": addr["drive"],
            "HpIncrease": addr["hp"],
            "ItemSlotUpgrade": addr["item_slot"],
            "MpIncrease": addr["mp"],
            "Padding": 0,
        })
        key = "BonusItem1" if addr["part"] == "item1" else "BonusItem2"
        block[key] = s["item_id"]
    return yaml.safe_dump(out, sort_keys=True, default_flow_style=False)


def write_lvup(slots: list) -> str:
    """Build {character: {level: {full field dict}}} matching OpenKH's schema.

    Rebuilt entirely from the slots themselves (stats + ability), not by
    re-reading presets/lvup.yml -- the "stats" slot carries the growth
    values in its address for exactly this reason (see slots_from_lvup).

    Sword/Shield/Staff teach the same 23 abilities in vanilla, just at
    different levels per weapon. Rather than forcing every weapon into
    lockstep (one shuffled value written to all 3 columns at the same
    level), build a per-character old-ability -> new-ability mapping from
    the shuffle result, then remap each of the 3 raw columns independently
    by ability *identity*. This preserves vanilla's per-weapon ordering
    shape (which levels diverge, which already coincide) while still
    randomizing which abilities you actually get."""
    ability_map: dict = {}  # character -> {vanilla_ability_id: new_ability_id}
    for s in slots:
        if s["address"]["part"] != "ability":
            continue
        addr = s["address"]
        vanilla_ability = addr["raw_sword"] or addr["raw_shield"] or addr["raw_staff"]
        if vanilla_ability:
            ability_map.setdefault(addr["character"], {})[vanilla_ability] = s["item_id"]

    out = {}  # character -> level -> fields

    for s in slots:
        char = s["address"]["character"]
        lvl = s["address"]["level"]
        entry = out.setdefault(char, {}).setdefault(lvl, {})

        # every level needs these identity fields present
        entry["Character"] = char
        entry["Level"] = lvl
        entry.setdefault("Padding", 0)

        if s["address"]["part"] == "stats":
            # stat slot carries the growth numbers
            entry["Exp"] = s["address"]["exp"]
            entry["Strength"] = s["address"]["strength"]
            entry["Magic"] = s["address"]["magic"]
            entry["Defense"] = s["address"]["defense"]
            entry["Ap"] = s["address"]["ap"]

        elif s["address"]["part"] == "ability":
            mapping = ability_map.get(char, {})
            addr = s["address"]
            entry["SwordAbility"] = mapping.get(addr["raw_sword"], addr["raw_sword"])
            entry["ShieldAbility"] = mapping.get(addr["raw_shield"], addr["raw_shield"])
            entry["StaffAbility"] = mapping.get(addr["raw_staff"], addr["raw_staff"])

    return yaml.safe_dump(out, sort_keys=True, default_flow_style=False)


BUILDERS = {
    "trsr": build_trsr_yml,
    "fmlv": build_fmlv_yml,
    "bons": build_bons_yml,
    "lvup": write_lvup,
}


def shuffle_and_write(seed: int) -> dict:
    """Run the full shuffle for `seed` and write the per-table ymls to
    OUTPUT_DIR. Returns {table: slots} for the caller to report on."""
    rng = random.Random(seed)
    categories = load_item_categories()

    pool, grouped, locked, forced, excluded = load_pools()
    shuffle_all(pool, grouped, rng, categories)
    by_table = group_by_table(combine(pool, grouped, locked, forced, excluded))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for table, filename in OUTPUT_FILENAMES.items():
        slots = by_table.get(table, [])
        (OUTPUT_DIR / filename).write_text(BUILDERS[table](slots))

    return by_table


def main():
    parser = argparse.ArgumentParser(description="Shuffle pools.yml and write per-table preset ymls")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed (random if omitted)")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**32)
    by_table = shuffle_and_write(seed)

    for table, filename in OUTPUT_FILENAMES.items():
        print(f"{table}: {len(by_table.get(table, []))} slots -> {OUTPUT_DIR / filename}")

    print(f"seed: {seed}")


if __name__ == "__main__":
    main()
