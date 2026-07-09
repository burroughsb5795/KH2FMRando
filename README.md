# KH2FMRando

A story-preserving item randomizer for Kingdom Hearts II Final Mix. Unlike
the Garden of Assemblage-based community randomizer, this one keeps the
normal world order intact — it only shuffles reward tables (treasure chests,
level-up rewards, drive form abilities, event bonuses), never warps, spawns,
or event scripts. See `CLAUDE.md` for the full design rationale.

## For players

1. Download the latest `KH2Rando-windows.zip` from
   [Releases](../../releases), and unzip it anywhere.
2. Copy your own OpenKH-extracted `03system.bin` and `00battle.bin` into a
   `data/` folder next to `KH2Rando.exe` (only needed if you want to use the
   chest spoiler viewer — the randomizer itself doesn't need them).
3. Run `KH2Rando.exe`, pick a seed and which tables to randomize, and click
   **Generate Mod**. It builds a zip in `output/` next to the exe.
4. Load that zip in OpenKH Mods Manager the same way as any other mod.

No Python install required — everything needed is bundled in the zip.

## For developers

```
KH2FMRando/
├── parser/            # binary format parsers/writers for each sub-table (trsr, item, bons, fmlv, lvup, ...)
├── scripts/
│   ├── build_pools.py     # presets/ + config/rules.yaml -> output/pools.yml (slot classification)
│   ├── shuffle_pools.py   # pools.yml -> shuffled per-table OpenKH listpatch YAML
│   ├── run.py              # build_pools -> shuffle_pools -> mod.yml -> zip, shared by CLI and GUI
│   ├── gui.py               # desktop GUI wrapping run.py (the packaged app's entry point)
│   ├── spoiler_viewer.py  # browse a built TrsrList.yml by world/chest/item name
│   ├── classify.py          # slot -> disposition (pool/grouped/locked/forced/excluded)
│   ├── paths.py             # path resolution that works both from source and PyInstaller-frozen
│   ├── parse.py, pack.py, extract.py  # dev tools for working with the raw .bin files
├── config/
│   ├── rules.yaml       # shuffle exception rules (locked/forced/grouped slots)
│   └── itemid.txt        # item id -> name lookup, used by spoiler_viewer.py
├── presets/              # vanilla tables as YAML, exported from the game's bins (committed)
├── data/                 # extracted game files (gitignored -- copyrighted, never committed)
├── tests/                # pytest suite
└── kh2rando.spec         # PyInstaller build recipe for the packaged app
```

### Running from source

```
python3 -m pip install -r requirements.txt
python3 scripts/gui.py                          # desktop GUI
python3 scripts/run.py --seed 1234              # CLI: shuffle + build a mod zip
python3 scripts/spoiler_viewer.py                # browse output/TrsrList.yml by world
python3 scripts/parse.py data/03system.bin --entry trsr   # dump a raw table
```

### Tests

```
python3 -m pip install pytest
python3 -m pytest
```

### Building the packaged release

The packaged app is a PyInstaller `--onedir` build (a folder, not a single
`.exe` — faster startup and far less likely to be flagged by antivirus than
`--onefile`). It bundles `config/` and `presets/`; it deliberately does
**not** bundle `data/*.bin` (extracted, copyrighted game data players must
supply themselves).

Build on the target OS (PyInstaller doesn't cross-compile) — for a real
release that means Windows:

```
python3 -m pip install -r requirements-build.txt
pyinstaller kh2rando.spec --noconfirm
```

Output lands in `dist/KH2Rando/` — zip that folder for release. Pushing a
tag like `v1.0.0` also triggers `.github/workflows/release.yml`, which does
this on a Windows runner and attaches the zip to a new GitHub Release
automatically.
