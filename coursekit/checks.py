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


def check_ex_2_3b(paths, boot_fan, fc: pd.DataFrame) -> None:
    """The residual bootstrap: many simulated futures, then percentiles."""
    _not_todo(boot_paths=paths, boot_fan=boot_fan)
    paths = np.asarray(paths, dtype=float)
    assert paths.ndim == 2, (
        f"bootstrap_paths returns one row per simulated future and one column "
        f"per horizon, so a 2-D array. Yours has shape {paths.shape}."
    )
    n_paths, h = paths.shape
    assert h == 24, f"Expected 24 horizons, got {h}"
    assert n_paths >= 1000, (
        f"{n_paths} paths is too few for a stable 95% percentile - the tails are "
        f"estimated from the outer 2.5%. Use at least 1000; the deck uses 5000."
    )
    _need_cols(boot_fan, ["ds", "lo-80", "hi-80", "lo-95", "hi-95"], "boot_fan")

    w80 = (boot_fan["hi-80"] - boot_fan["lo-80"]).to_numpy()
    assert w80[-1] > w80[0], (
        "The bootstrap interval must still widen with the horizon. Yours does "
        "not - check that the recursion feeds simulated values back in "
        "(season_length=12), rather than resampling around a fixed forecast."
    )
    gauss80 = float((fc["SeasonalNaive-hi-80"] - fc["SeasonalNaive-lo-80"]).mean())
    assert float(w80.mean()) < gauss80, (
        f"On this series the bootstrap's 80% interval should come out NARROWER "
        f"than the Gaussian one ({gauss80:.1f}), because the residuals have a "
        f"sharper peak than a normal. Yours averages {w80.mean():.1f}."
    )
    lo_gap = (boot_fan["mean"] - boot_fan["lo-95"]).to_numpy()
    hi_gap = (boot_fan["hi-95"] - boot_fan["mean"]).to_numpy()
    assert not np.allclose(lo_gap, hi_gap, rtol=0.01), (
        "A bootstrap interval is a pair of empirical percentiles, so it has no "
        "reason to be symmetric about the mean - and on this series it is not. "
        "Yours is exactly symmetric, which suggests a +/- c * sd was used."
    )
    _ok("EX 2.3b", f"{n_paths} paths, mean 80% width {w80.mean():.1f} "
                   f"vs {gauss80:.1f} Gaussian")


def check_ex_2_3c(cmp: pd.DataFrame) -> None:
    """Three intervals on one model, compared on the same holdout."""
    _not_todo(cmp=cmp)
    _need_cols(cmp, ["method", "width_80", "coverage_80"], "cmp")
    names = " ".join(cmp["method"].astype(str)).lower()
    for want in ("gauss", "bootstrap", "conformal"):
        assert want in names, f"cmp is missing the {want} row; got {list(cmp['method'])}"
    assert cmp["coverage_80"].between(0, 1).all(), (
        "coverage_80 is a proportion in [0, 1], not a percentage."
    )

    def _row(key, col):
        return float(cmp.loc[cmp["method"].str.lower().str.contains(key), col].iloc[0])

    assert _row("bootstrap", "width_80") < _row("gauss", "width_80"), (
        "The bootstrap should be the narrowest of the three at 80% here."
    )
    conf_w = _row("conformal", "width_80")
    assert 30 < conf_w < 120, (
        f"A conformal 80% width of {conf_w:.1f} is off the scale for this series "
        f"(expect roughly 60). Check ConformalIntervals(n_windows=8, h=H) was "
        f"passed to the MODEL, not to forecast()."
    )
    _ok("EX 2.3c", "  ".join(f"{r.method} {r.width_80:.0f}/{r.coverage_80:.0%}"
                             for r in cmp.itertuples()))


def check_ex_2_4(scores: pd.DataFrame) -> None:
    _not_todo(scores=scores)
    needed = {"MASE", "RMSSE"}
    missing = needed - set(scores.columns)
    assert not missing, f"scores is missing {sorted(missing)}"
    best = scores["MASE"].idxmin()
    assert "STL" in str(best), (
        f"On THIS 24-month window the STL route should win on MASE; you have "
        f"{best}. Check the model column names line up with the metric call, and "
        "that MSTL made it into MODELS."
    )
    assert scores["MASE"].max() > 5, (
        "The mean method should score terribly here (MASE ~ 12). Yours does not "
        "- is HistoricAverage included?"
    )
    _ok("EX 2.4", f"best by MASE on this window: {best} "
                  f"({scores['MASE'].min():.3f}) - hold that result loosely "
                  f"until Exercise 2.5")


def check_ex_2_5(cv: pd.DataFrame, summary: pd.DataFrame) -> None:
    _not_todo(cv=cv, summary=summary)
    assert "cutoff" in cv.columns, (
        "A cross_validation result has a `cutoff` column - one per fold."
    )
    n_folds = cv["cutoff"].nunique()
    assert n_folds >= 5, f"Use at least 5 folds; you have {n_folds}."
    _need_cols(summary, ["model", "mase", "rmsse", "crps", "coverage_80"], "summary")
    assert len(summary) >= 5, "Score all four benchmarks plus the STL route."
    assert summary["coverage_80"].between(0, 1).all(), "coverage_80 is a proportion."
    assert (summary["crps"] > 0).all(), (
        "Every scaled CRPS should be positive. A column of zeros or NaNs usually "
        "means the quantile column names did not line up with QUANTILES."
    )

    sn = summary.loc[summary["model"].str.contains("easonal"), "mase"]
    assert len(sn) == 1, "Expected exactly one seasonal-naive row."
    assert sn.iloc[0] == summary["mase"].min(), (
        "Across folds the seasonal naive should have the lowest MASE - including "
        "beating the STL route that won the single window in Exercise 2.4. If "
        "something else wins here, check each fold is scored against its OWN "
        "training data."
    )
    _ok("EX 2.5", f"{n_folds} folds, {len(summary)} models scored")


def check_leaderboard(table: pd.DataFrame) -> None:
    _not_todo(table=table)
    _need_cols(table, ["model", "mase", "rmsse", "crps", "coverage_80"],
               "the leaderboard")
    assert len(table) >= 5, (
        f"Expected the four benchmarks plus the STL route on the leaderboard, "
        f"found {len(table)}."
    )
    assert table["model"].duplicated().sum() == 0, (
        "A model appears twice. `leaderboard.record()` replaces by model name - "
        "check for a typo in one of them."
    )
    assert table["mase"].notna().all(), "Every row needs a MASE."
    _ok("leaderboard", f"{len(table)} models recorded; "
                       f"best = {table.loc[table['mase'].idxmin(), 'model']}")
