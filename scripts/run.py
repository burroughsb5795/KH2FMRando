#!/usr/bin/env python3
"""Run the full KH2FM randomizer pipeline end to end: build the disposition
pools from presets/ + config/rules.yaml, shuffle them with a seed, and zip
the result into an OpenKH Mods Manager-ready archive.

Usage:
    python scripts/run.py --seed 1234
    python scripts/run.py                 # random seed, printed for you
"""

import argparse
import random
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import yaml

import build_pools
import shuffle_pools

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.paths import output_root

OUTPUT_DIR = output_root() / "output"

# which bin file each table's listpatch lives under (see parser/registry.py)
BIN_FOR_TABLE = {
    "trsr": "03system.bin",
    "lvup": "00battle.bin",
    "fmlv": "00battle.bin",
    "bons": "00battle.bin",
}


def build_mod_yml(seed: int) -> str:
    by_bin = defaultdict(list)
    for table, filename in shuffle_pools.OUTPUT_FILENAMES.items():
        by_bin[BIN_FOR_TABLE[table]].append((table, filename))

    mod = {
        "title": "KH2FM Item Rando",
        "description": f"Story-preserving item/ability/magic/form/level-up randomizer (seed {seed}).",
        "assets": [
            {
                "name": bin_name,
                "method": "binarc",
                "source": [
                    {
                        "name": table,
                        "method": "listpatch",
                        "type": "List",
                        "source": [{"name": filename, "type": table}],
                    }
                    for table, filename in tables
                ],
            }
            for bin_name, tables in by_bin.items()
        ],
    }
    return yaml.safe_dump(mod, sort_keys=False, default_flow_style=False)


def zip_mod(seed: int, mod_yml_path: Path) -> Path:
    """Zip mod.yml + the four listpatch ymls (only those -- output/ also
    holds pools.yml, which isn't part of the mod) at the archive root."""
    zip_path = OUTPUT_DIR / f"kh2fm-rando-{seed}.zip"
    files = [mod_yml_path] + [OUTPUT_DIR / f for f in shuffle_pools.OUTPUT_FILENAMES.values()]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, arcname=f.name)
    return zip_path


def build(seed: int, disabled_tables: frozenset = frozenset(), log=print) -> Path:
    """Run build_pools -> shuffle_pools -> mod.yml -> zip for one seed.

    Shared by the CLI (main, below) and the GUI (scripts/gui.py) so both
    stay on exactly one code path. `log` receives each progress line --
    the CLI prints them, the GUI routes them into its log pane."""
    rules = yaml.safe_load(build_pools.RULES_PATH.read_text()) or {}
    buckets = build_pools.build_buckets(rules, disabled_tables=disabled_tables)
    build_pools.OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with build_pools.OUTPUT_PATH.open("w") as f:
        yaml.safe_dump(buckets, f, sort_keys=False, default_flow_style=False)
    log(f"pool: {len(buckets['pool'])}")
    for group, entries in buckets["grouped"].items():
        log(f"grouped[{group}]: {len(entries)}")
    log(f"locked: {len(buckets['locked'])}")
    log(f"forced: {len(buckets['forced'])}")
    log(f"excluded: {len(buckets['excluded'])}")
    log(f"wrote {build_pools.OUTPUT_PATH}")

    by_table = shuffle_pools.shuffle_and_write(seed)
    for table, filename in shuffle_pools.OUTPUT_FILENAMES.items():
        log(f"{table}: {len(by_table.get(table, []))} slots -> {OUTPUT_DIR / filename}")

    mod_yml_path = OUTPUT_DIR / "mod.yml"
    mod_yml_path.write_text(build_mod_yml(seed))
    zip_path = zip_mod(seed, mod_yml_path)

    log(f"seed: {seed}")
    log(f"built {zip_path}")
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and zip the KH2FM rando mod")
    parser.add_argument("--seed", type=int, default=None, help="Shuffle seed (random if omitted)")
    parser.add_argument(
        "--disable", nargs="*", default=[], choices=sorted(BIN_FOR_TABLE),
        help="Table(s) to keep 100%% vanilla (excluded from randomization entirely)",
    )
    args = parser.parse_args()
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**32)
    build(seed, disabled_tables=frozenset(args.disable))


if __name__ == "__main__":
    main()
