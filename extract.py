from pathlib import Path
import sys
import argparse

from parser.bar import parse_bar

parser = argparse.ArgumentParser(description="Specify which bin to extract")
parser.add_argument(
    "bin_file", 
    type=str, 
    help="Entry name to extract")

args = parser.parse_args()




TARGET = Path(args.bin_file)
OUT_DIR = Path("data") / TARGET.stem


bar = parse_bar(TARGET.read_bytes())

OUT_DIR.mkdir(parents=True, exist_ok=True)
for entry in bar.entries:
    (OUT_DIR / f"{entry.name}.bin").write_bytes(bar.read(entry))

