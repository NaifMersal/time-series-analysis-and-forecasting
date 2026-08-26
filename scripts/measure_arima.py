"""Measure AutoARIMA on the spine once, so deck 6 does not refit it every render.

Every other model in this course is cheap enough to fit inside a `{python}` cell
while a deck renders. AutoARIMA is not: an order search over eight rolling folds
takes about a minute, plus another fit to read the selected order off, and
`freeze` has not proved reliable enough to spare a deck author that on every
edit. A two-and-a-half minute render for a one-word change is how a deck stops
getting screenshotted.

So this script measures it once and writes the answer to
`coursekit/data/day3_arima.json`, which deck 6 reads. The numbers stay measured
rather than typed off a screenshot, and re-measuring is one command:

    .venv/Scripts/python.exe scripts/measure_arima.py

Re-run it if the spine, the fold layout or `scoring.LEVELS` ever changes.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA

from coursekit import datasets as D
from coursekit import scoring

OUT = Path(__file__).resolve().parent.parent / "coursekit" / "data" / "day3_arima.json"


def main() -> None:
    spine = D.spine()

    print("fitting AutoARIMA on the full spine ...")
    t0 = time.perf_counter()
    fit = StatsForecast(models=[AutoARIMA(season_length=12)], freq=D.FREQ,
                        n_jobs=1)
    fit.fit(df=spine)
    # statsforecast keeps R's ordering in this tuple: (p, q, P, Q, m, d, D).
    p, q, P, Q, m, d, Dd = fit.fitted_[0, 0].model_["arma"]
    spec = f"ARIMA({p},{d},{q})({P},{Dd},{Q})[{m}]"
    fit_seconds = time.perf_counter() - t0
    print(f"  selected {spec}  ({fit_seconds:.1f}s)")

    print("cross-validating over 8 rolling folds ...")
    t0 = time.perf_counter()
    cv = StatsForecast(models=[AutoARIMA(season_length=12)], freq=D.FREQ,
                       n_jobs=1).cross_validation(
        df=spine, h=12, step_size=12, n_windows=8, level=scoring.LEVELS)
    cv_seconds = time.perf_counter() - t0

    payload = {
        "spec": spec,
        "fit_seconds": round(fit_seconds, 1),
        "cv_seconds": round(cv_seconds, 1),
        **scoring.score_cv(cv, "AutoARIMA", spine),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"\nwrote {OUT.relative_to(OUT.parent.parent.parent)}")
    for k, v in payload.items():
        print(f"  {k:14s} {v}")


if __name__ == "__main__":
    main()
