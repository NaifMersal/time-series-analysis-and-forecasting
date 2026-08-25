"""The running scoreboard the whole course builds toward.

One CSV, appended to across the three days. Day 2 writes the benchmark rows
from the evaluation harness the students build; Day 3 adds every model it
covers to the same table, and the closing decision record is written off it.

That makes this module an *interface*, not a convenience: adding a model on
Day 3 must stay a few lines.

    from coursekit import leaderboard as lb

    lb.record("SeasonalNaive", mase=1.00, rmsse=1.00, coverage_80=0.71,
              crps=0.031)
    lb.show()

Columns beyond the standard ones are allowed and are carried through, so a
later day can add e.g. ``fit_seconds`` without a migration.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

#: Written next to the labs so students can see and inspect it.
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "labs" / "leaderboard.csv"

#: Columns every row carries. ``day`` keeps the table readable once Day 3 lands.
CORE_COLUMNS = ["model", "day", "mase", "rmsse", "crps", "coverage_80",
                "mase_min", "mase_max", "notes"]


def record(model: str, *, day: int | None = None, mase: float | None = None,
           rmsse: float | None = None, crps: float | None = None,
           coverage_80: float | None = None, mase_min: float | None = None,
           mase_max: float | None = None,
           notes: str = "", path: Path | str | None = None,
           **extra) -> pd.DataFrame:
    """Append (or replace) one model's row and return the whole table.

    Re-recording a model overwrites its existing row rather than duplicating
    it, so re-running a lab cell is idempotent -- students *will* re-run cells.

    ``mase_min`` / ``mase_max`` are the best and worst fold, and they are core
    columns rather than extras because Day 2 spends an hour arguing that a mean
    with no spread is not evidence. ``coursekit.scoring.score_cv`` returns them,
    so ``lb.record(name, **score_cv(...))`` fills them in.
    """
    path = Path(path) if path is not None else DEFAULT_PATH
    row = {
        "model": model,
        "day": day,
        "mase": mase,
        "rmsse": rmsse,
        "crps": crps,
        "coverage_80": coverage_80,
        "mase_min": mase_min,
        "mase_max": mase_max,
        "notes": notes,
        **extra,
    }

    table = load(path)
    table = table[table["model"] != model] if not table.empty else table
    table = pd.concat([table, pd.DataFrame([row])], ignore_index=True)

    ordered = CORE_COLUMNS + [c for c in table.columns if c not in CORE_COLUMNS]
    table = table.reindex(columns=ordered)

    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False)
    return table


def load(path: Path | str | None = None) -> pd.DataFrame:
    """Read the leaderboard, or an empty frame with the core columns."""
    path = Path(path) if path is not None else DEFAULT_PATH
    if not path.exists():
        return pd.DataFrame(columns=CORE_COLUMNS)
    return pd.read_csv(path)


def show(path: Path | str | None = None, sort_by: str = "mase") -> pd.DataFrame:
    """Return the leaderboard sorted best-first, ready to display."""
    table = load(path)
    if table.empty or sort_by not in table.columns:
        return table
    return table.sort_values(sort_by, na_position="last").reset_index(drop=True)


def reset(path: Path | str | None = None) -> None:
    """Delete the leaderboard. Useful when re-running a lab from scratch."""
    path = Path(path) if path is not None else DEFAULT_PATH
    path.unlink(missing_ok=True)
