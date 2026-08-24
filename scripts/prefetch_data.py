#!/usr/bin/env python3
"""Download and cache every dataset Days 1-2 touch.

Run once, with internet. After that neither the labs nor `quarto render` needs
the network -- which matters twice over: a lab must not stall on conference
wifi, and the decks execute their {python} cells at render time.

    python scripts/prefetch_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coursekit import fppdata as fd  # noqa: E402

# Why each one is here, so this list can be pruned when the syllabus changes.
DATASETS = {
    "aus_retail": "the course spine (VIC / Takeaway food services) + the E1.5 feature sweep",
    "aus_production": "quarterly Beer -- clean seasonality for the patterns panel",
    "canadian_gas": "E1.4 stretch: a series where STL behaves differently",
    "pelt": "Canadian lynx -- the only honest *cycle* example (S1)",
    "souvenirs": "strong multiplicative seasonality for the additive-vs-multiplicative slide",
}


def main() -> int:
    failed = []
    for name, why in DATASETS.items():
        try:
            df = fd.load(name)
        except Exception as exc:  # noqa: BLE001 - report and keep going
            failed.append((name, exc))
            print(f"[FAIL] {name:<16} {exc}")
        else:
            print(f"[ok]   {name:<16} {df.shape[0]:>6} rows   {why}")

    if failed:
        print("\nSome datasets could not be fetched:")
        for name, exc in failed:
            print(f"  {name}: {exc}")
        print("\nCheck your connection and re-run; the cache is incremental.")
        return 1

    print(f"\nAll {len(DATASETS)} datasets cached in coursekit/data/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
