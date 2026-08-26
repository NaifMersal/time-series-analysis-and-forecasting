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


def check_ex_1_4(dcmp: pd.DataFrame) -> None:
    _not_todo(dcmp=dcmp)
    _need_cols(dcmp, ["ds", "trend", "seasonal", "remainder"], "your decomposition")
    recon = dcmp["trend"] + dcmp["seasonal"] + dcmp["remainder"]
    err = float(np.abs(recon - dcmp["transformed"]).max()) if "transformed" in dcmp else None
    if err is not None:
        assert err < 1e-6, (
            "trend + seasonal + remainder should reconstruct the transformed "
            f"series exactly (additive STL). Largest gap: {err:.2e}"
        )
    seasonal_range = float(dcmp["seasonal"].max() - dcmp["seasonal"].min())
    assert seasonal_range > 0, "The seasonal component is flat - check the period."
    _ok("EX 1.4", "components reconstruct the series")


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


# ---------------------------------------------------------------- Day 3

def check_ex_3_1(ets) -> None:
    """The fitted AutoETS object, read for what the search actually chose.

    The lesson is in the middle letter: on this series the likelihood prefers a
    model with NO trend state, having spent Day 1 establishing that the spine
    trends. Level plus season, updated every month, is enough.
    """
    _not_todo(ets=ets)
    assert isinstance(ets, dict) and "components" in ets, (
        "Pass the fitted model itself: `sf.fitted_[0, 0].model_`, after "
        "`sf.fit(df=spine)`. That is a dict, with 'method', 'components', "
        f"'par' and 'states' in it. You passed a {type(ets).__name__}."
    )
    err, trend, season = (ets["components"][0], ets["components"][1],
                          ets["components"][2])

    assert season != "N", (
        f"AutoETS should keep a seasonal state on the spine; yours picked "
        f"{ets['method']}. Check `season_length=12` reached the model - "
        "without it the search cannot see a December."
    )
    assert trend == "N", (
        f"On the full spine the AICc search picks a model with NO trend state, "
        f"but yours is {ets['method']}. If you fitted on `train` rather than "
        "the whole `spine`, or pinned `model=` by hand, you will get a "
        "different answer - refit on all 441 months and let the search choose."
    )
    assert err == "M", (
        f"Expected a multiplicative error term; yours is {ets['method']}. That "
        "letter is what lets an additive seasonal state cope with seasonal "
        "swings that grow with the level."
    )

    par = np.asarray(ets["par"], dtype=float)
    alpha, gamma = float(par[0]), float(par[2])
    assert 0 < alpha < 1, f"alpha should be a weight in (0, 1); got {alpha:.3f}."
    assert 0 < gamma < 1, f"gamma should be a weight in (0, 1); got {gamma:.3f}."
    _ok("EX 3.1", f"AutoETS chose {ets['method']} - alpha={alpha:.3f}, "
                  f"gamma={gamma:.3f}, and no trend state")


def check_ex_3_2(cv: pd.DataFrame, scores: pd.DataFrame) -> None:
    """Eight folds, two models, and the reveal: ETS wins points, loses range.

    Every assertion here is a fact about the spine measured over these eight
    folds, not a preference. If one fails, the harness was wired differently,
    not the model.
    """
    _not_todo(cv=cv, scores=scores)
    assert "cutoff" in cv.columns, (
        "A cross_validation result has a `cutoff` column - one row per fold "
        "per horizon step. Yours does not; did you call `forecast` instead?"
    )
    n_folds = cv["cutoff"].nunique()
    assert n_folds == 8, (
        f"Use the same eight folds Day 2 used, so the numbers stay comparable: "
        f"h=12, step_size=12, n_windows=8. You have {n_folds}."
    )

    _need_cols(scores, ["mase", "crps", "coverage_80"], "scores")
    idx = {str(i).lower().replace(" ", ""): i for i in scores.index}

    def _find(*needles):
        for key, original in idx.items():
            if any(n in key for n in needles):
                return original
        return None

    ets_key, sn_key = _find("ets"), _find("seasonalnaive", "seasonal")
    assert ets_key is not None, (
        f"Expected an ETS row in `scores`, found {list(scores.index)}."
    )
    assert sn_key is not None, (
        f"Expected a seasonal-naive row in `scores`, found "
        f"{list(scores.index)}. Score BOTH models - the comparison is the "
        "exercise, not the ETS number on its own."
    )
    ets_row, sn_row = scores.loc[ets_key], scores.loc[sn_key]

    assert ets_row["mase"] < sn_row["mase"], (
        f"Over eight folds ETS should just edge the seasonal naive on MASE "
        f"(1.176 against 1.183 when measured). You have "
        f"{ets_row['mase']:.3f} against {sn_row['mase']:.3f}. If ETS is far "
        "behind, check each fold is scored against its OWN training history - "
        "which is what `scoring.score_cv` does for you."
    )
    assert ets_row["crps"] > sn_row["crps"], (
        f"The reveal of this exercise is that ETS LOSES on scaled CRPS "
        f"({ets_row['crps']:.4f} against {sn_row['crps']:.4f}) despite winning "
        "on MASE. Yours does not, which usually means the quantile columns did "
        "not line up - use `scoring.score_cv`, which derives them from LEVELS."
    )
    assert ets_row["coverage_80"] > 0.80, (
        f"ETS should OVER-cover here - a band claiming 80% that catches 87.5%. "
        f"Yours reads {ets_row['coverage_80']:.1%}. Check you passed "
        "`level=scoring.LEVELS` to cross_validation."
    )
    _ok("EX 3.2",
        f"ETS {ets_row['mase']:.3f} MASE against {sn_row['mase']:.3f}, a tie "
        f"on points; CRPS {ets_row['crps']:.4f} against {sn_row['crps']:.4f} "
        f"and {ets_row['coverage_80']:.1%} coverage on an 80% band, a loss on "
        "range")


def check_ex_3_3(fc: pd.DataFrame, undamped: str = "AAN",
                 damped: str = "AAdN") -> None:
    """Optional: damping flattens a trend the further out you go."""
    _not_todo(fc=fc)
    for col in (undamped, damped):
        assert col in fc.columns, (
            f"Expected a column `{col}` in the forecast; got "
            f"{[c for c in fc.columns if c not in ('unique_id', 'ds')]}. Give "
            "each AutoETS an `alias=` so the two can be told apart."
        )
    assert len(fc) >= 36, (
        f"Forecast far enough out for damping to show - the slide used h=60. "
        f"You have {len(fc)} rows."
    )
    gap_early = float(fc[undamped].iloc[0] - fc[damped].iloc[0])
    gap_late = float(fc[undamped].iloc[-1] - fc[damped].iloc[-1])
    assert gap_late > gap_early, (
        "The damped forecast should fall further behind the undamped one the "
        f"further out you go; here the gap goes {gap_early:.1f} to "
        f"{gap_late:.1f}. Check `damped=True` reached the second model."
    )
    _ok("EX 3.3", f"over {len(fc)} months the damped trend gives up "
                  f"{gap_late:.1f} units against the straight line")


def check_ex_3_4(ag_board: pd.DataFrame) -> None:
    """AutoGluon's own leaderboard, read on its own terms.

    Deliberately *not* compared against a course table. The exercise is about
    reading what a framework hands back -- its sign convention, its catalogue,
    and the single validation window behind its ranking -- and the room has no
    table of its own on screen at this point to set beside it.

    Skip-guarded in the notebook: without autogluon installed the cell says so
    and moves on, which is how both check-labs targets stay honest on a machine
    that has neither torch nor 2.5 GB to spare.
    """
    _not_todo(ag_board=ag_board)
    assert "model" in ag_board.columns, (
        f"An AutoGluon leaderboard has a `model` column; got "
        f"{list(ag_board.columns)}."
    )
    assert len(ag_board) >= 3, (
        f"Expected AutoGluon to fit several models, found {len(ag_board)}. "
        "Pass the local zoo through `hyperparameters=` and give it a "
        "`time_limit` long enough to get through them."
    )
    assert any("score" in str(c).lower() for c in ag_board.columns), (
        f"Expected a score column on the AutoGluon leaderboard; got "
        f"{list(ag_board.columns)}."
    )
    names = " ".join(str(m) for m in ag_board["model"])
    assert "Naive" in names, (
        "The local zoo should include the benchmarks this course built on, "
        f"SeasonalNaive above all. AutoGluon fitted: {names}"
    )
    _ok("EX 3.4", f"AutoGluon fitted {len(ag_board)} models - note its scores "
                  "are NEGATED, so higher is better there while every metric "
                  "this course taught is lower-is-better")


def check_ex_3_5(results: pd.DataFrame, model: str) -> None:
    """The capstone: one more model, the same four lines, the same numbers.

    ``results`` is the frame Exercise 3.2 built -- one row per model, indexed by
    name, carrying what ``scoring.score_cv`` returns. The point of the exercise
    is that adding a row to it costs four lines whatever the model is.
    """
    _not_todo(results=results, model=model)
    _need_cols(results, ["mase", "rmsse", "crps", "coverage_80"], "RESULTS")
    assert model in set(results.index), (
        f"'{model}' is not in RESULTS. `RESULTS.loc[name] = "
        "scoring.score_cv(cv, column, spine)` - and the name you use there has "
        f"to be the name you pass here. Present: {sorted(results.index)}"
    )
    row = results.loc[model]
    assert pd.notna(row["crps"]) and row["crps"] > 0, (
        "Your model needs a scaled CRPS, which means cross-validating with "
        "`level=scoring.LEVELS`. A model with no closed-form interval raises "
        "'You must pass prediction_intervals' the moment you ask for a level - "
        "give it `prediction_intervals=ConformalIntervals(n_windows=..., "
        "h=...)`, from Day 2's segment E."
    )
    floor = next((i for i in results.index
                  if "seasonal" in str(i).lower().replace(" ", "")), None)
    assert floor is not None, (
        "Keep the seasonal naive in RESULTS - it is the floor every other row "
        f"is read against. Present: {sorted(results.index)}"
    )
    verdict = ("beats" if row["crps"] < results.loc[floor, "crps"]
               else "does not beat")
    _ok("EX 3.5", f"{len(results)} models scored; {model} {verdict} the floor "
                  f"on scaled CRPS ({row['crps']:.4f} against "
                  f"{results.loc[floor, 'crps']:.4f})")
