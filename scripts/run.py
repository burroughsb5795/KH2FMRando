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
import zipfile
from collections import defaultdict
from pathlib import Path

import yaml

import build_pools
import shuffle_pools

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "output"

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and zip the KH2FM rando mod")
    parser.add_argument("--seed", type=int, default=None, help="Shuffle seed (random if omitted)")
    args = parser.parse_args()
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**32)

    build_pools.main()
    by_table = shuffle_pools.shuffle_and_write(seed)
    for table, filename in shuffle_pools.OUTPUT_FILENAMES.items():
        print(f"{table}: {len(by_table.get(table, []))} slots -> {OUTPUT_DIR / filename}")

    mod_yml_path = OUTPUT_DIR / "mod.yml"
    mod_yml_path.write_text(build_mod_yml(seed))

    zip_path = zip_mod(seed, mod_yml_path)

    print(f"seed: {seed}")
    print(f"built {zip_path}")


if __name__ == "__main__":
    main()
