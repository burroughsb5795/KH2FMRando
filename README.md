# KH2FMRando

A randomizer toolchain for Kingdom Hearts II Final Mix, built around parsing
and repacking the game's `BAR`/`03system.bin`/`00battle.bin` binary tables.

## Layout

- `parser/` — binary format parsers/writers for each sub-table (trsr, item, shop, ...)
- `rando/` — randomizer logic (slot classification, shuffle rules)
- `scripts/` — CLI entry points: `extract.py`, `parse.py`, `pack.py`
- `config/` — `rules.yaml`, the shuffle exception rules (locked/forced/grouped slots)
- `presets/` — default data presets (event/forms/lvup/trsr lists)
- `tests/` — pytest suite
- `data/` — extracted game files (gitignored; not committed)
- `mod/` — OpenKH mod-manifest examples (gitignored except sample files)
- `notused/` — reference data not currently wired into the tool

## Usage

Run scripts from the repo root, e.g.:

```
python3 scripts/parse.py data/03system/trsr.bin --entry trsr
python3 scripts/extract.py data/03system.bin
```

## Tests

```
python3 -m pytest
```
