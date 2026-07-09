# PyInstaller spec for the KH2FM Item Randomizer GUI.
#
# Build (from the repo root, on the target OS -- Windows for a real release):
#     pyinstaller kh2rando.spec
#
# Produces a --onedir build at dist/KH2Rando/ -- zip that whole folder for
# release. Do NOT use --onefile: slower startup (unpacks to a temp dir on
# every launch) and single-file PyInstaller binaries get flagged by
# antivirus/SmartScreen far more often.
#
# data/*.bin is deliberately NOT bundled here -- it's extracted, copyrighted
# game data the user must supply themselves (see scripts/paths.py).

from pathlib import Path

REPO_ROOT = Path(SPECPATH)  # noqa: F821 -- SPECPATH is injected by PyInstaller

a = Analysis(  # noqa: F821
    ["scripts/gui.py"],
    pathex=[str(REPO_ROOT), str(REPO_ROOT / "scripts")],
    binaries=[],
    datas=[
        (str(REPO_ROOT / "config" / "rules.yaml"), "config"),
        (str(REPO_ROOT / "config" / "itemid.txt"), "config"),
        (str(REPO_ROOT / "presets"), "presets"),
    ],
    hiddenimports=[
        "scripts.build_pools", "scripts.shuffle_pools", "scripts.classify",
        "scripts.paths", "scripts.run", "run", "build_pools", "shuffle_pools",
        "classify", "paths",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KH2Rando",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="KH2Rando",
)
