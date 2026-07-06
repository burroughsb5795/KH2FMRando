"""
Slot classification for the KH2FM randomizer.

Every shuffleable position across the four tables (trsr, bons, lvup, fmlv) is
normalized into a Slot, then classify() routes each one to exactly one
Disposition. This single gate is what the whole shuffle hangs off:

    forced   -> set to a specific item, skip the pool
    excluded -> not shuffleable (empty slot, or a stat column)
    locked   -> keep the vanilla value, skip the pool
    grouped  -> shuffle only within a named group (e.g. maps, Donald's kit)
    pool     -> the shared pool (the default for anything not called out)

The rules file only lists EXCEPTIONS; anything unmatched falls through to POOL.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Disposition(Enum):
    FORCED = "forced"
    EXCLUDED = "excluded"
    LOCKED = "locked"
    GROUPED = "grouped"
    POOL = "pool"


@dataclass(frozen=True)
class Slot:
    """One addressable position in one table.

    address holds whatever key fields that table uses. The rules match against
    these, so the field names here MUST match the field names in rules.yml:
        trsr / fmlv -> {"index": N}
        bons        -> {"id": N}
        lvup        -> {"character": name, "level": N, "column": col}
    kind is "item" for ability/loot slots (poolable) or "stat" for lvup stat
    columns (never poolable).
    """
    table: str
    address: dict
    item_id: int          # current vanilla contents; 0 / falsy == empty
    kind: str = "item"


@dataclass
class Decision:
    disposition: Disposition
    group: str | None = None
    forced_item: int | None = None
    reason: str | None = None


# ---- matching helpers -------------------------------------------------------

_NON_MATCH_KEYS = {"reason", "item"}  # payload/metadata, not address matchers


def _matches(rule: dict, slot: Slot) -> bool:
    """True if every address field the rule specifies equals the slot's.

    A rule like {"index": 376} matches trsr slot 376. A rule like
    {"character": "Sora", "level": 1} matches only that lvup slot. "reason" and
    "item" are ignored here (they're metadata / the forced payload).
    """
    for key, val in rule.items():
        if key in _NON_MATCH_KEYS:
            continue
        if slot.address.get(key) != val:
            return False
    return True


def _in_group(criteria: dict, slot: Slot) -> bool:
    """Group membership. Supports an explicit index list or field-matching."""
    if "indices" in criteria:
        return slot.address.get("index") in criteria["indices"]
    return _matches(criteria, slot)


# ---- the gate ---------------------------------------------------------------

def classify(slot: Slot, table_rules: dict | None) -> Decision:
    """Route one slot to its disposition. table_rules is rules[slot.table]."""
    rules = table_rules or {}

    # 1. FORCED first -- it must win even over null-exclusion, because
    #    "put Scan at level 1" has to override "level 1 is empty in vanilla".
    for rule in rules.get("forced", []):
        if _matches(rule, slot):
            return Decision(Disposition.FORCED,
                            forced_item=rule["item"],
                            reason=rule.get("reason"))

    # 2. Never-shuffle: stat columns, and (if enabled) empty slots.
    if slot.kind == "stat":
        return Decision(Disposition.EXCLUDED, reason="stat column")
    if rules.get("exclude_null") and not slot.item_id:
        return Decision(Disposition.EXCLUDED, reason="empty slot")

    # 3. LOCKED: keep the vanilla value in place.
    for rule in rules.get("locked", []):
        if _matches(rule, slot):
            return Decision(Disposition.LOCKED, reason=rule.get("reason"))

    # 4. GROUPED: shuffle only within a named group.
    for name, criteria in rules.get("groups", {}).items():
        if _in_group(criteria, slot):
            return Decision(Disposition.GROUPED, group=name,
                            reason=f"group:{name}")

    # 5. Default: the shared pool.
    return Decision(Disposition.POOL)


# ---- adapters: turn your parsed tables into Slots ---------------------------
# These are the ONLY parts you adapt to your real field names. The classifier
# above never changes.

def slots_from_trsr(table):
    for i, e in enumerate(table.entries):
        yield Slot("trsr", {"index": i}, item_id=e.item_id)


def slots_from_bons(table):
    for e in table.entries:
        yield Slot("bons", {"id": e.id}, item_id=e.item_id)


def slots_from_fmlv(table):
    for i, e in enumerate(table.entries):
        yield Slot("fmlv", {"index": i}, item_id=e.item_id)


def slots_from_lvup(table):
    """lvup is the gnarly one: per (character, level) there are stat columns
    (excluded) and 3 ability columns (sword/shield/staff).

    NOTE the granularity decision. To preserve weapon symmetry (everyone gets
    the same ability at a given level regardless of Dream Weapon), treat the 3
    ability columns as ONE logical slot and have your emitter write that one
    result to all three columns. That's the version below. If you instead want
    the columns to shuffle independently, yield three slots with a "column"
    field -- but know that breaks symmetry across weapon choices.
    """
    for char_name, levels in table.items():
        for lv in levels:
            # stat columns: represented so they round-trip, but kind="stat"
            # makes classify() always EXCLUDE them from the pool.
            yield Slot("lvup",
                       {"character": char_name, "level": lv.n, "part": "stats"},
                       item_id=0, kind="stat")
            # one logical ability slot per level (maps to all 3 columns on write)
            yield Slot("lvup",
                       {"character": char_name, "level": lv.n, "part": "ability"},
                       item_id=lv.ability_id)  # your representative ability value
