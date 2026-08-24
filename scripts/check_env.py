#!/usr/bin/env python3
"""Pre-work gate: confirm this machine can run the course labs and slides.

Students run this *before* Day 1. Day 1 opens with content, not an install
clinic, and this script is what makes that true.

    python scripts/check_env.py

Exits 0 if everything a Day 1-2 lab touches imports cleanly, non-zero with an
actionable message otherwise.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (import name, pip/distribution name, what the course uses it for)
REQUIRED = [
    ("numpy", "numpy", "arrays and the random-number generator"),
    ("pandas", "pandas", "every dataset in the course"),
    ("matplotlib", "matplotlib", "all plots"),
    ("seaborn", "seaborn", "plot styling"),
    ("statsmodels", "statsmodels", "STL, ACF, Ljung-Box"),
    ("statsforecast", "statsforecast", "benchmark models and cross-validation"),
    ("utilsforecast", "utilsforecast", "accuracy metrics (MASE, RMSSE)"),
    ("coreforecast", "coreforecast", "Box-Cox transform and lambda selection"),
    ("sklearn", "scikit-learn", "assorted utilities"),
    ("pyreadr", "pyreadr", "reads the .rda datasets from the book"),
    ("ipykernel", "ipykernel", "runs the notebooks, and the slides' code cells"),
]

OPTIONAL = [
    ("nbclient", "nbclient", "instructor-side lab checking"),
    ("nbformat", "nbformat", "instructor-side lab checking"),
]

MIN_PYTHON = (3, 11)


def _version(dist: str) -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(dist)
    except PackageNotFoundError:
        return "?"


def check_group(group, label, fatal):
    missing = []
    print(f"\n{label}")
    for module, dist, purpose in group:
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - report anything that stops an import
            missing.append((dist, purpose, exc))
            print(f"  [MISSING] {dist:<16} {purpose}")
        else:
            print(f"  [ok]      {dist:<16} {_version(dist)}")
    return missing if fatal else []


def main() -> int:
    print("Time Series course - environment check")
    print(f"  python     {sys.version.split()[0]}  ({sys.executable})")

    problems = []
    if sys.version_info[:2] < MIN_PYTHON:
        problems.append(
            f"Python {'.'.join(map(str, MIN_PYTHON))}+ is required; this is "
            f"{sys.version.split()[0]}."
        )

    missing = check_group(REQUIRED, "Required packages:", fatal=True)
    check_group(OPTIONAL, "Optional (instructor only):", fatal=False)

    # The data cache matters as much as the packages: labs must not need the
    # network mid-class.
    data_dir = REPO_ROOT / "coursekit" / "data"
    cached = sorted(p.stem for p in data_dir.glob("*.rda")) if data_dir.exists() else []
    needed = ["aus_retail", "aus_production", "canadian_gas", "pelt", "souvenirs"]
    absent = [n for n in needed if n not in cached]
    print(f"\nCached datasets ({len(cached)} found in coursekit/data):")
    for name in needed:
        print(f"  [{'ok' if name in cached else 'MISSING'}]      {name}")

    print()
    if missing:
        problems.append(
            "Missing packages: " + ", ".join(d for d, _, _ in missing) + "\n"
            "  Fix:  uv sync            (or: pip install -e .)"
        )
    if absent:
        problems.append(
            "Missing cached datasets: " + ", ".join(absent) + "\n"
            "  Fix:  python scripts/prefetch_data.py     (needs internet, once)"
        )

    if problems:
        print("NOT READY:\n")
        for p in problems:
            print(f"  - {p}\n")
        return 1

    print("Ready. See you on Day 1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
