"""Path resolution that works both for `python scripts/x.py` (dev) and a
PyInstaller-frozen build.

Two different roots are needed once frozen, because they behave differently
under PyInstaller:

- resource_root(): where bundled *read-only* data lives (config/, presets/).
  In a frozen build this is PyInstaller's extraction dir (sys._MEIPASS) --
  temporary and cleaned up for --onefile, a folder next to the exe for
  --onedir, but either way not a place to write persistent output.
- output_root(): where the app should read/write user-facing files (the
  output/ mod zips, and an optional user-supplied data/ for the spoiler
  viewer). Must resolve next to the actual .exe, not the temp extraction
  dir, or a built mod would vanish the moment the app closes.

In dev (not frozen), both resolve to the repo root, matching every script's
previous `Path(__file__).resolve().parent.parent` -- this module is a drop-in
replacement for that pattern, not a behavior change for source runs.
"""

from __future__ import annotations

import sys
from pathlib import Path


def resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def output_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
