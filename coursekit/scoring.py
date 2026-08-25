"""The scoring half of the Day 2 harness, packaged for Day 3.

Day 2 has students build this by hand in Exercise 2.5, which is the point of
the exercise. What lives here is the same thing, named and tested, so that a
Day 3 author scoring a new model does not have to reconstruct it from the
solution notebook.

Three things are worth having in one place rather than retyped per notebook:

``LEVELS``
    The ladder of prediction intervals every forecast in this course asks for.
    80 is the band coverage is read off; the rest exist so ``scaled_crps`` has
    quantiles to integrate over.

``QCOLS`` / ``QUANTILES``
    The interval column suffixes and the quantile each one *is*, in the same
    order. These two lists have to agree or ``scaled_crps`` returns a number
    that is wrong and still positive, which nothing downstream would catch.
    Keeping them adjacent, and derived from ``LEVELS``, is the whole reason
    this module exists.

``score_cv``
    One model, one cross-validation frame, the four numbers the leaderboard
    wants. MASE and RMSSE are averaged *across folds*, each fold scored against
    its own training history, because a fold's denominator has to come from
    data that fold was allowed to see.

    >>> from coursekit import scoring, leaderboard as lb
    >>> cv = sf.cross_validation(df=spine, h=12, step_size=12, n_windows=8,
    ...                          level=scoring.LEVELS)
    >>> lb.record("AutoETS", day=3, **scoring.score_cv(cv, "AutoETS", spine))
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from utilsforecast.losses import mase, rmsse, scaled_crps

#: One ladder of levels for every forecast in the course.
LEVELS = [20, 40, 60, 80, 95]

#: Interval column suffixes, low quantile to high.
QCOLS = ([f"lo-{lvl}" for lvl in sorted(LEVELS, reverse=True)]
         + [f"hi-{lvl}" for lvl in sorted(LEVELS)])

#: The quantile each entry of QCOLS is. Derived from LEVELS so the two cannot
#: drift apart: a level L brackets the central L%, so its bounds sit at
#: (1 - L/100) / 2 and 1 - that.
QUANTILES = np.array(
    [(1 - lvl / 100) / 2 for lvl in sorted(LEVELS, reverse=True)]
    + [1 - (1 - lvl / 100) / 2 for lvl in sorted(LEVELS)])


def qcols(model: str) -> list[str]:
    """The interval columns of one model, in ``QUANTILES`` order."""
    return [f"{model}-{c}" for c in QCOLS]


def coverage(cv: pd.DataFrame, model: str, level: int = 80) -> float:
    """Share of scored points that fell inside the model's ``level``% band."""
    lo, hi = cv[f"{model}-lo-{level}"], cv[f"{model}-hi-{level}"]
    return float(((cv["y"] >= lo) & (cv["y"] <= hi)).mean())


def score_cv(cv: pd.DataFrame, model: str, train_df: pd.DataFrame,
             seasonality: int = 12, level: int = 80,
             cutoff_col: str = "cutoff") -> dict:
    """Score one model over a rolling-origin cross-validation frame.

    ``cv`` is what ``StatsForecast.cross_validation(..., level=LEVELS)``
    returns; ``train_df`` is the full series the folds were cut from. Returns
    the keyword arguments ``coursekit.leaderboard.record`` takes, plus the best
    and worst fold MASE, because a mean with no spread is the thing Day 2
    spends an hour arguing against.
    """
    fold_mase, fold_rmsse = [], []
    for cut, g in cv.groupby(cutoff_col):
        history = train_df[train_df["ds"] <= cut]
        scored = g.drop(columns=[cutoff_col])
        fold_mase.append(float(mase(scored, models=[model],
                                    seasonality=seasonality,
                                    train_df=history)[model].iloc[0]))
        fold_rmsse.append(float(rmsse(scored, models=[model],
                                      seasonality=seasonality,
                                      train_df=history)[model].iloc[0]))

    crps = scaled_crps(cv.drop(columns=[cutoff_col]),
                       models={model: qcols(model)},
                       quantiles=QUANTILES)[model].iloc[0]

    return {
        "mase": float(np.mean(fold_mase)),
        "rmsse": float(np.mean(fold_rmsse)),
        "crps": float(crps),
        f"coverage_{level}": coverage(cv, model, level=level),
        "mase_min": float(np.min(fold_mase)),
        "mase_max": float(np.max(fold_mase)),
    }
