"""Self-checks the lab exercises call.

Each ``check_ex_*`` raises AssertionError with a message that says what is wrong
and, where useful, what the right shape looks like. They are written to be
*read* by students, not just run -- so they check meaning, not just types.

    from coursekit import checks
    checks.check_ex_1_2(spine)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import datasets as D


def _not_todo(**named) -> None:
    """Turn the cryptic `'ellipsis' object has no attribute ...` into English.

    An unfilled TODO in a lab is literally the value `...`, so catch it here and
    say so rather than letting pandas complain three frames deeper.
    """
    todo = [k for k, v in named.items() if v is Ellipsis or v is None]
    assert not todo, (
        f"Still a TODO: {', '.join(todo)} "
        f"{'is' if len(todo) == 1 else 'are'} not filled in yet."
    )


def _ok(label: str, detail: str = "") -> None:
    print(f"[PASS] {label}" + (f" - {detail}" if detail else ""))


def _need_cols(df, cols, what):
    missing = [c for c in cols if c not in df.columns]
    assert not missing, (
        f"{what} is missing column(s) {missing}. "
        f"Expected the long layout: {cols}. Got: {list(df.columns)}"
    )


# ---------------------------------------------------------------- Day 1

def check_ex_1_1(answers: dict) -> None:
    """Six series classified. We check completeness and vocabulary, not taste."""
    _not_todo(answers=answers)
    expected = {"spine", "beer", "lynx", "noise", "souvenirs", "canadian_gas"}
    assert isinstance(answers, dict), "answers should be a dict, series name -> your call"
    missing = expected - set(answers)
    assert not missing, f"No answer yet for: {sorted(missing)}"

    allowed = {"trend", "seasonality", "cycle", "none",
               "additive", "multiplicative"}
    for name, call in answers.items():
        assert isinstance(call, (list, tuple, set)), (
            f"{name!r}: give a list of labels, e.g. ['trend', 'seasonality', 'multiplicative']"
        )
        bad = {str(c).lower() for c in call} - allowed
        assert not bad, f"{name!r}: unrecognised label(s) {sorted(bad)}. Allowed: {sorted(allowed)}"

    # The one that is genuinely a matter of fact, not opinion.
    lynx = {str(c).lower() for c in answers["lynx"]}
    assert "cycle" in lynx, (
        "The lynx series rises and falls at no fixed period - that is a cycle, "
        "not seasonality. Look again at the gaps between peaks."
    )
    assert "seasonality" not in lynx, (
        "Lynx is annual data with peaks 8-11 years apart. Seasonality needs a "
        "FIXED, KNOWN period; this has neither."
    )
    _ok("EX 1.1", f"{len(answers)} series classified")


def check_ex_1_2(spine: pd.DataFrame) -> None:
    _not_todo(spine=spine)
    _need_cols(spine, ["unique_id", "ds", "y"], "spine")
    assert len(spine) == 441, f"Expected 441 monthly observations, got {len(spine)}"
    assert spine["ds"].is_monotonic_increasing, "Sort by ds - order is the data."
    assert not spine["ds"].duplicated().any(), "Duplicate timestamps found."
    expected = pd.date_range(spine["ds"].min(), spine["ds"].max(), freq="MS")
    assert len(expected) == len(spine), (
        f"Calendar gap: {spine['ds'].min().date()} to {spine['ds'].max().date()} "
        f"spans {len(expected)} months but you have {len(spine)} rows."
    )
    assert spine["y"].notna().all(), "Missing values in y."
    _ok("EX 1.2", "441 rows, no gaps, no duplicates")


def check_ex_1_3(acf_spine, acf_noise, bound) -> None:
    _not_todo(acf_spine=acf_spine, acf_noise=acf_noise, bound=bound)
    acf_spine = np.asarray(acf_spine)
    acf_noise = np.asarray(acf_noise)
    assert len(acf_spine) >= 24, "Compute at least 24 lags so the seasonal spikes are visible."
    assert abs(bound - 1.96 / np.sqrt(441)) < 1e-3, (
        f"The bound should be 1.96/sqrt(T) with T = 441, i.e. {1.96 / np.sqrt(441):.4f}"
    )
    assert acf_spine[0] > 0.9, (
        "r_1 for the spine should be very large (> 0.9) - a trending series is "
        f"almost perfectly correlated with last month. You have {acf_spine[0]:.3f}"
    )
    outside = (np.abs(acf_noise) > bound).mean()
    assert outside < 0.2, (
        f"{outside:.0%} of the white-noise autocorrelations are outside the "
        "bounds. Expect roughly 5%. Did you pass the noise series?"
    )
    _ok("EX 1.3", f"r_1 = {acf_spine[0]:.3f}, noise outside bounds = {outside:.0%}")


def check_ex_1_4(dcmp: pd.DataFrame, lam: float) -> None:
    _not_todo(dcmp=dcmp, lam=lam)
    _need_cols(dcmp, ["ds", "trend", "seasonal", "remainder"], "your decomposition")
    assert 0.0 <= lam <= 0.4, (
        f"lambda = {lam:.3f} looks off. For this series the log-likelihood "
        "method gives about 0.07 - close to a log transform."
    )
    recon = dcmp["trend"] + dcmp["seasonal"] + dcmp["remainder"]
    err = float(np.abs(recon - dcmp["transformed"]).max()) if "transformed" in dcmp else None
    if err is not None:
        assert err < 1e-6, (
            "trend + seasonal + remainder should reconstruct the transformed "
            f"series exactly (additive STL). Largest gap: {err:.2e}"
        )
    seasonal_range = float(dcmp["seasonal"].max() - dcmp["seasonal"].min())
    assert seasonal_range > 0, "The seasonal component is flat - check the period."
    _ok("EX 1.4", f"lambda = {lam:.3f}, components reconstruct the series")


def check_ex_1_5(feat: pd.DataFrame) -> None:
    _not_todo(feat=feat)
    _need_cols(feat, ["unique_id", "trend_strength", "seasonal_strength"], "feat")
    assert len(feat) > 100, f"Expected ~148 series, got {len(feat)}"
    for col in ["trend_strength", "seasonal_strength"]:
        assert feat[col].between(0, 1).all(), f"{col} must lie in [0, 1] by construction."
    assert D.SPINE_ID in set(feat["unique_id"]), (
        f"Our spine ({D.SPINE_ID!r}) should be in the sweep. Check how you built unique_id."
    )
    row = feat.loc[feat["unique_id"] == D.SPINE_ID].iloc[0]
    assert row["trend_strength"] > 0.9, (
        f"The spine trends hard; expected trend strength > 0.9, got {row['trend_strength']:.3f}"
    )
    _ok("EX 1.5", f"{len(feat)} series; spine F_T = {row['trend_strength']:.3f}, "
                  f"F_S = {row['seasonal_strength']:.3f}")


# ---------------------------------------------------------------- Day 2

def check_ex_2_1(fc: pd.DataFrame, models: list[str]) -> None:
    _not_todo(fc=fc, models=models)
    _need_cols(fc, ["unique_id", "ds"] + list(models), "fc")
    assert len(fc) == 24, f"Expected a 24-month forecast, got {len(fc)} rows"
    sn = fc["SeasonalNaive"] if "SeasonalNaive" in fc else None
    assert sn is not None, "Include SeasonalNaive - it is the benchmark floor."
    assert sn.nunique() > 6, (
        "The seasonal naive should repeat last year's SHAPE, so a 24-month "
        "forecast has ~12 distinct values. Yours looks flat - did you use Naive?"
    )
    assert fc["HistoricAverage"].nunique() == 1, (
        "The mean method forecasts one constant. Yours varies."
    )
    _ok("EX 2.1", f"{len(models)} benchmarks forecast 24 months ahead")


def check_ex_2_2(resid, lb_pvalue: float) -> None:
    _not_todo(resid=resid, lb_pvalue=lb_pvalue)
    r = pd.Series(resid).dropna()
    assert len(r) > 300, f"Expected residuals over most of the training set, got {len(r)}"
    assert 0.0 <= lb_pvalue <= 1.0, "A p-value must lie in [0, 1]."
    assert lb_pvalue < 0.05, (
        "The seasonal naive's residuals on this series are strongly "
        f"autocorrelated, so Ljung-Box should reject decisively. You got "
        f"p = {lb_pvalue:.3g}. Check you passed residuals, not the series."
    )
    _ok("EX 2.2", f"n = {len(r)}, Ljung-Box p = {lb_pvalue:.2e} - not white noise")


def check_ex_2_3(width: pd.Series | np.ndarray, coverage: float, se: float) -> None:
    _not_todo(width=width, coverage=coverage, se=se)
    width = np.asarray(width, dtype=float)
    assert len(width) == 24, f"Expected 24 horizons, got {len(width)}"
    assert width[-1] > width[0], (
        "Interval width must grow with the horizon. Yours does not - check "
        "you subtracted lo from hi at the same level."
    )
    assert 0.0 <= coverage <= 1.0, "Coverage is a proportion, in [0, 1]."
    expected_se = np.sqrt(0.8 * 0.2 / 24)
    assert abs(se - expected_se) < 0.01, (
        f"The standard error of an 80% rate on 24 points is "
        f"sqrt(0.8*0.2/24) = {expected_se:.3f}; you have {se:.3f}"
    )
    _ok("EX 2.3", f"width {width[0]:.1f} -> {width[-1]:.1f}, "
                  f"coverage {coverage:.1%} +/- {1.96 * se:.1%}")


def check_ex_2_4(scores: pd.DataFrame) -> None:
    _not_todo(scores=scores)
    needed = {"MASE", "RMSSE"}
    missing = needed - set(scores.columns)
    assert not missing, f"scores is missing {sorted(missing)}"
    best = scores["MASE"].idxmin()
    assert "easonal" in str(best), (
        f"On this series the seasonal naive should win on MASE; you have {best}. "
        "Check the model column names line up with the metric call."
    )
    assert scores["MASE"].max() > 5, (
        "The mean method should score terribly here (MASE ~ 12). Yours does not "
        "- is HistoricAverage included?"
    )
    _ok("EX 2.4", f"best by MASE: {best} ({scores['MASE'].min():.3f})")


def check_ex_2_5(cv: pd.DataFrame, summary: pd.DataFrame) -> None:
    _not_todo(cv=cv, summary=summary)
    assert "cutoff" in cv.columns, (
        "A cross_validation result has a `cutoff` column - one per fold."
    )
    n_folds = cv["cutoff"].nunique()
    assert n_folds >= 5, f"Use at least 5 folds; you have {n_folds}."
    _need_cols(summary, ["model", "mase", "rmsse", "coverage_80"], "summary")
    assert len(summary) >= 4, "Score all four benchmarks."
    assert summary["coverage_80"].between(0, 1).all(), "coverage_80 is a proportion."

    sn = summary.loc[summary["model"].str.contains("easonal"), "mase"]
    assert len(sn) == 1, "Expected exactly one seasonal-naive row."
    assert sn.iloc[0] == summary["mase"].min(), (
        "The seasonal naive should have the lowest MASE across folds."
    )
    _ok("EX 2.5", f"{n_folds} folds, {len(summary)} models scored")


def check_leaderboard(table: pd.DataFrame) -> None:
    _not_todo(table=table)
    _need_cols(table, ["model", "mase", "rmsse", "coverage_80"], "the leaderboard")
    assert len(table) >= 4, (
        f"Expected at least the four benchmarks on the leaderboard, found {len(table)}."
    )
    assert table["model"].duplicated().sum() == 0, (
        "A model appears twice. `leaderboard.record()` replaces by model name - "
        "check for a typo in one of them."
    )
    assert table["mase"].notna().all(), "Every row needs a MASE."
    _ok("leaderboard", f"{len(table)} models recorded; "
                       f"best = {table.loc[table['mase'].idxmin(), 'model']}")
