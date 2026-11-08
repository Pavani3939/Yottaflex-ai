"""
YottaPay AI – Reproducibility Verification Script
==================================================
Runs the data generator TWICE with the fixed seed and verifies:
  - Identical row counts
  - Identical primary keys
  - Identical file checksums
  - Identical ground-truth labels

Usage:
    python scripts/reproduce_data.py
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

# Ensure scripts can import from sibling modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_data import YottaPayDataGenerator, SEED, OUTPUT_DIR, GROUND_TRUTH_PATH

RUN1_DIR = OUTPUT_DIR.parent / "run1"
RUN2_DIR = OUTPUT_DIR.parent / "run2"


def compute_checksums(directory: Path) -> dict[str, str]:
    checksums = {}
    for f in sorted(directory.glob("*.csv")):
        checksums[f.name] = hashlib.md5(f.read_bytes()).hexdigest()
    return checksums


def run_generation(output_dir: Path, gt_path: Path) -> dict:
    """Run the generator writing to a specific output dir."""
    # Monkey-patch paths temporarily
    import generate_data as gd
    orig_out = gd.OUTPUT_DIR
    orig_gt = gd.GROUND_TRUTH_PATH

    gd.OUTPUT_DIR = output_dir
    gd.GROUND_TRUTH_PATH = gt_path

    gen = YottaPayDataGenerator(seed=SEED, output_dir=output_dir)
    gen.run()

    gd.OUTPUT_DIR = orig_out
    gd.GROUND_TRUTH_PATH = orig_gt
    return compute_checksums(output_dir)


def main():
    print("\n" + "="*60)
    print("  YottaPay AI – Reproducibility Verification")
    print("="*60)

    # Clean previous runs
    for d in [RUN1_DIR, RUN2_DIR]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    print("\n[RUN 1]")
    checksums1 = run_generation(RUN1_DIR, RUN1_DIR / "ground_truth.csv")

    print("\n[RUN 2]")
    checksums2 = run_generation(RUN2_DIR, RUN2_DIR / "ground_truth.csv")

    # Compare
    print("\n" + "="*60)
    print("  COMPARISON RESULTS")
    print("="*60)

    all_pass = True
    files = sorted(set(list(checksums1.keys()) + list(checksums2.keys())))
    for fname in files:
        c1 = checksums1.get(fname, "MISSING")
        c2 = checksums2.get(fname, "MISSING")
        match = "✓ MATCH" if c1 == c2 else "✗ MISMATCH"
        if c1 != c2:
            all_pass = False
        print(f"  {fname:<40} {match}")

    print("\n" + "="*60)
    if all_pass:
        print("  ✓ REPRODUCIBILITY VERIFIED — Both runs are identical.")
    else:
        print("  ✗ REPRODUCIBILITY FAILED — Runs differ.")
        sys.exit(1)
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
