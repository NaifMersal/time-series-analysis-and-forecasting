"""Generate the lab notebooks -- student and solution copies -- from one source.

Each exercise is defined once here, with the student version (TODOs) and the
solution version side by side, so the two copies cannot drift apart. **Edit this
file, not the notebooks**, then re-run:

    .venv/Scripts/python.exe scripts/build_labs.py

Writes labs/*.ipynb and labs/solutions/*.ipynb. Regenerating discards any
hand-edits to the notebooks, which is the point.
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
LABS = ROOT / "labs"
SOLS = LABS / "solutions"


def md(text):
    return ("md", text.strip("\n"), None)


def code(student, solution=None):
    """A code cell. If `solution` is None the cell is identical in both copies."""
    return ("code", student.strip("\n"), (solution or student).strip("\n"))


def build(cells, path_student, path_solution, title_note):
    for solution_mode, out in ((False, path_student), (True, path_solution)):
        nb = nbf.v4.new_notebook()
        nb.cells = []
        for kind, student, sol in cells:
            if kind == "md":
                body = student
                if solution_mode:
                    body = body.replace("<!--STUDENT-->", "").replace(
                        "<!--SOLUTION-->", "")
                nb.cells.append(nbf.v4.new_markdown_cell(body))
            else:
                nb.cells.append(nbf.v4.new_code_cell(sol if solution_mode else student))
        banner = nbf.v4.new_markdown_cell(title_note(solution_mode))
        nb.cells.insert(0, banner)
        nb.metadata["kernelspec"] = {
            "display_name": "Python 3", "language": "python", "name": "python3"}
        nb.metadata["language_info"] = {"name": "python", "version": "3.11"}
        out.parent.mkdir(parents=True, exist_ok=True)
        nbf.write(nb, str(out))
        print(f"wrote {out.relative_to(ROOT)}  ({len(nb.cells)} cells)")


SETUP = code("""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from coursekit import checks
from coursekit import datasets as D
from coursekit import plotting as P

P.use_course_style()
print("ready")
""")

# =====================================================================
# LAB 1 - Day 1
# =====================================================================

LAB1 = [
    md("""
## Setup

Everything the labs need lives in `coursekit`. If the next cell fails, run
`python scripts/check_env.py` from the repo root and fix what it reports.
"""),
    SETUP,

    # ---------------------------------------------------------------- 1.1
    md("""
---
# Exercise 1.1 - Name the pattern

*Follows segment 1. 10 minutes. No modelling - look and argue.*

Six series are plotted below. For each one decide:

- Is there a **trend**?
- Is there **seasonality** (a *fixed, known* period)?
- Is there a **cycle** (rises and falls at *no* fixed period)?
- Is the seasonal swing **additive** (constant size) or **multiplicative**
  (grows with the level)?
"""),
    code("""
series = {
    "spine": D.spine(),
    "beer": D.beer(),
    "lynx": D.lynx(),
    "noise": D.white_noise(n=300, seed=7),
    "souvenirs": D.souvenirs(),
    "canadian_gas": D.canadian_gas(),
}

fig, axes = plt.subplots(2, 3, figsize=(12, 6))
for ax, (name, df) in zip(axes.ravel(), series.items()):
    P.plot_series(df, ax=ax, title=name)
P.thin_xticks(axes, n=3)
plt.show()
"""),
    md("""
Fill in your calls below. Use any of: `"trend"`, `"seasonality"`, `"cycle"`,
`"none"`, `"additive"`, `"multiplicative"`.
"""),
    code("""
answers = {
    "spine":        [],   # TODO
    "beer":         [],   # TODO
    "lynx":         [],   # TODO
    "noise":        [],   # TODO
    "souvenirs":    [],   # TODO
    "canadian_gas": [],   # TODO
}

checks.check_ex_1_1(answers)
""", """
answers = {
    "spine":        ["trend", "seasonality", "multiplicative"],
    "beer":         ["trend", "seasonality", "additive"],
    "lynx":         ["cycle"],
    "noise":        ["none"],
    "souvenirs":    ["trend", "seasonality", "multiplicative"],
    "canadian_gas": ["trend", "seasonality", "multiplicative"],
}

checks.check_ex_1_1(answers)
"""),
    md("""
> **Discussion.** `lynx` is the one that catches people. Its peaks are 8-11
> years apart - never the same gap twice - so it is a *cycle*, not seasonality.
> Nothing in the calendar produces it.
>
> `canadian_gas` is worth a second look too: its seasonal *shape* changes over
> the decades, not just its size. STL will show you that in exercise 1.4.
"""),

    # ---------------------------------------------------------------- 1.2
    md("""
---
# Exercise 1.2 - Load, verify, and look

*Follows segment 2. 15 minutes.*

The spine for this whole course is Victorian takeaway-food turnover: monthly,
1982-2018.

**Before plotting anything, verify the timestamps.** A silent gap shifts every
seasonal lag after it, and nothing downstream will warn you.
"""),
    code("""
spine = ...   # TODO: load the spine (see coursekit/datasets.py)
spine.head()
""", """
spine = D.spine()
spine.head()
"""),
    code("""
# TODO: fill in the four checks below.
inferred_freq = ...          # what frequency does pandas infer?
n_duplicates  = ...          # duplicated timestamps
n_expected    = ...          # how many months SHOULD lie between first and last?
n_actual      = ...          # how many rows do we have?

print(f"inferred frequency : {inferred_freq}")
print(f"duplicate stamps   : {n_duplicates}")
print(f"expected / actual  : {n_expected} / {n_actual}")

checks.check_ex_1_2(spine)
""", """
inferred_freq = pd.infer_freq(spine["ds"])
n_duplicates  = int(spine["ds"].duplicated().sum())
n_expected    = len(pd.date_range(spine["ds"].min(), spine["ds"].max(), freq="MS"))
n_actual      = len(spine)

print(f"inferred frequency : {inferred_freq}")
print(f"duplicate stamps   : {n_duplicates}")
print(f"expected / actual  : {n_expected} / {n_actual}")

checks.check_ex_1_2(spine)
"""),
    md("""
This series is clean. Most are not - so here is what a gap actually costs.
Run this and compare the two seasonal lags.
"""),
    code("""
# Drop three months at random and see what happens to the seasonal structure.
rng = np.random.default_rng(0)
holes = rng.choice(np.arange(100, 300), size=3, replace=False)
broken = spine.drop(index=holes).reset_index(drop=True)

r_full, _ = P.acf_values(spine["y"], nlags=24)
r_broken, _ = P.acf_values(broken["y"], nlags=24)
print(f"r_12 with a complete calendar : {r_full[11]:.3f}")
print(f"r_12 after dropping 3 months  : {r_broken[11]:.3f}")
print("\\nThe rows still line up. The CALENDAR does not.")
"""),
    md("""
**Repairing a gap.** Reindex onto the full date range, then decide what the
missing values mean - interpolate, carry forward, or leave `NaN` and use a
model that tolerates them. Never let the gap stay *invisible*.
"""),
    code("""
full_index = pd.date_range(broken["ds"].min(), broken["ds"].max(), freq="MS")
repaired = (broken.set_index("ds")
                  .reindex(full_index)
                  .rename_axis("ds")
                  .reset_index())
repaired["unique_id"] = repaired["unique_id"].ffill()
print(f"rows: {len(broken)} -> {len(repaired)},  NaNs now visible: {repaired['y'].isna().sum()}")
repaired["y"] = repaired["y"].interpolate()
print(f"after interpolation, NaNs: {repaired['y'].isna().sum()}")
"""),
    md("""
Now the three plots. Each answers a different question.
"""),
    code("""
sp = D.add_calendar(spine)

# TODO: 1. a time plot of the whole series
# TODO: 2. a seasonal plot (one line per year, month on the x axis)
# TODO: 3. a subseries plot (one panel per month)
""", """
sp = D.add_calendar(spine)

# 1. time plot
ax = P.plot_series(spine, title="Spine - monthly turnover")
plt.show()

# 2. seasonal plot
fig, ax = plt.subplots(figsize=(9, 4.2))
P.seasonal_plot(sp, "year", "month", ax=ax, title="One line per year")
ax.set_xticks(range(1, 13))
plt.show()

# 3. subseries plot
fig, axes = P.subseries_plot(sp, "month", title="One panel per month")
plt.show()
"""),
    md("""
**Write your answer here.** In two or three sentences: what is going on in this
series? Mention the trend, the seasonal shape, whether the swing is growing, and
anything unusual around 2009.

<!--STUDENT-->
*Your answer:*

<!--SOLUTION-->
*Answer.* Turnover rises roughly eight-fold from 1982 to 2018, with a clear
December peak and February trough every year. The seasonal swing grows with the
level, so the series is multiplicative - that is what the Box-Cox transform in
1.4 will fix. Growth flattens noticeably around 2009-2010 (the financial
crisis), which is a level effect rather than a seasonal one; the seasonal plot
shows the *shape* stays put while the level stalls.
"""),
    md("""
### Stretch

Pick a second retail series with `D.retail_all()` and contrast it with the
spine. Is its seasonal shape the same? Does it peak in December too?
"""),
    code("""
# Stretch - your code here.
""", """
allr = D.retail_all()
other = allr[allr["unique_id"] == "New South Wales / Newspaper and book retailing"]
fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
P.plot_series(spine, ax=axes[0], title="Spine - takeaway food")
P.plot_series(other, ax=axes[1], title="Newspapers and books", color=P.ORANGE)
P.thin_xticks(axes, n=4)
plt.show()
print("Both peak in December, but the book series declines after 2005 while "
      "takeaway keeps growing - opposite trends, same seasonal calendar.")
"""),

    # ---------------------------------------------------------------- 1.3
    md("""
---
# Exercise 1.3 - Read the correlogram

*Follows segment 3. 15 minutes.*

First, the matching game. Four correlograms below, in a scrambled order.
Match each to its series.
"""),
    code("""
mystery = {
    "A": D.white_noise(n=400, seed=11),
    "B": D.spine(),
    "C": D.beer(),
    "D": D.lynx(),
}
order = ["C", "A", "D", "B"]      # the plots are drawn in THIS order

fig, axes = plt.subplots(1, 4, figsize=(13, 3.2))
for ax, key in zip(axes, order):
    P.acf_plot(mystery[key]["y"], nlags=30, ax=ax, title=f"correlogram {order.index(key) + 1}")
plt.show()
"""),
    md("""
Which correlogram belongs to which series? Say *why* - name the feature you
used (slow decay, spikes at a period, everything inside the bounds).

<!--STUDENT-->
*Your answer:*

<!--SOLUTION-->
*Answer.*

1. **beer** - spikes at lags 4, 8, 12 (quarterly data, m = 4) with little decay.
2. **white noise** - every spike inside the bounds.
3. **lynx** - a slow *wave*: positive at short lags, negative around lag 5,
   positive again near lag 10. A cycle shows as an oscillating ACF, not as
   spikes at a fixed multiple.
4. **spine** - slow decay from near 1.0, the signature of a strong trend, with
   a seasonal ripple riding on top.
"""),
    code("""
noise = D.white_noise(n=len(spine), seed=7)

# TODO: compute the ACF of the spine and of the noise series, to 36 lags,
#       plus the significance bound.
acf_spine, bound = ...
acf_noise, _ = ...

print(f"bound = {bound:.4f}")
print(f"spine  r_1 = {acf_spine[0]:.3f}   r_12 = {acf_spine[11]:.3f}")
print(f"noise: fraction of lags outside the bounds = "
      f"{(np.abs(acf_noise) > bound).mean():.1%}")

checks.check_ex_1_3(acf_spine, acf_noise, bound)
""", """
noise = D.white_noise(n=len(spine), seed=7)

acf_spine, bound = P.acf_values(spine["y"], nlags=36)
acf_noise, _ = P.acf_values(noise["y"], nlags=36)

print(f"bound = {bound:.4f}")
print(f"spine  r_1 = {acf_spine[0]:.3f}   r_12 = {acf_spine[11]:.3f}")
print(f"noise: fraction of lags outside the bounds = "
      f"{(np.abs(acf_noise) > bound).mean():.1%}")

checks.check_ex_1_3(acf_spine, acf_noise, bound)
"""),
    md("""
**Question.** Roughly 5% of white-noise autocorrelations land outside the
bounds *by construction*. If you plot 36 lags, how many spikes outside the band
should stop worrying you?

<!--STUDENT-->
*Your answer:*

<!--SOLUTION-->
*Answer.* About 36 x 0.05 = 1.8, so one or two stray spikes are exactly what
white noise looks like. Treat the bounds as a null hypothesis about a *single*
lag, not as a per-plot decision rule. What matters is a pattern - a run of
spikes, or a spike at a meaningful lag like 12.
"""),

    # ---------------------------------------------------------------- 1.4
    md("""
---
# Exercise 1.4 - Transform and decompose

*Follows segment 4. 15 minutes.*

The spine's seasonal swing grows with its level. Stabilise it first, then split
it into trend, seasonal and remainder.
"""),
    code("""
from coreforecast.scalers import boxcox, boxcox_lambda
from statsmodels.tsa.seasonal import STL

# TODO: choose lambda by the log-likelihood method, then transform.
lam = ...
yt = ...

fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
P.plot_series(spine, ax=axes[0], title="original")
axes[1].plot(spine["ds"], yt, color=P.ORANGE, lw=0.9)
axes[1].set_title(f"Box-Cox, lambda = {lam:.3f}")
plt.show()
""", """
from coreforecast.scalers import boxcox, boxcox_lambda
from statsmodels.tsa.seasonal import STL

lam = boxcox_lambda(spine["y"].to_numpy(), method="loglik")
yt = boxcox(spine["y"].to_numpy(), lam)

fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
P.plot_series(spine, ax=axes[0], title="original")
axes[1].plot(spine["ds"], yt, color=P.ORANGE, lw=0.9)
axes[1].set_title(f"Box-Cox, lambda = {lam:.3f}")
plt.show()
"""),
    code("""
# TODO: run STL on the transformed series (remember: you must supply `period`)
#       and assemble a frame with columns ds / transformed / trend / seasonal / remainder.
res = ...
dcmp = ...

fig, axes = P.decomposition_plot(
    dcmp, ["transformed", "trend", "seasonal", "remainder"], "STL")
plt.show()

checks.check_ex_1_4(dcmp, lam)
""", """
res = STL(yt, period=12, robust=True).fit()
dcmp = spine.assign(
    transformed=yt,
    trend=np.asarray(res.trend),
    seasonal=np.asarray(res.seasonal),
    remainder=np.asarray(res.resid),
)

fig, axes = P.decomposition_plot(
    dcmp, ["transformed", "trend", "seasonal", "remainder"], "STL")
plt.show()

checks.check_ex_1_4(dcmp, lam)
"""),
    code("""
# TODO: plot the seasonally adjusted series against the transformed series.
""", """
fig, ax = plt.subplots(figsize=(9.5, 4))
ax.plot(spine["ds"], dcmp["transformed"], color=P.GREY, lw=0.8, label="observed")
ax.plot(spine["ds"], dcmp["transformed"] - dcmp["seasonal"], color=P.ORANGE,
        lw=1.2, label="seasonally adjusted")
ax.set(title="Seasonally adjusted")
ax.legend(frameon=False)
plt.show()
"""),
    md("""
### Stretch

Run a **classical** decomposition (`seasonal_decompose`) on the same series and
compare it with STL. Look hard at the first and last six months.
"""),
    code("""
# Stretch - your code here.
""", """
from statsmodels.tsa.seasonal import seasonal_decompose

cl = seasonal_decompose(yt, period=12, model="additive")
fig, axes = plt.subplots(2, 1, figsize=(9.5, 5), sharex=True)
axes[0].plot(spine["ds"], np.asarray(res.trend), color=P.BLUE, lw=1.2)
axes[0].set_title("STL trend - defined everywhere")
axes[1].plot(spine["ds"], np.asarray(cl.trend), color=P.ORANGE, lw=1.2)
axes[1].set_title("Classical trend - six months missing at each end")
plt.show()

print("Classical decomposition uses a centred moving average, so it cannot "
      "estimate the trend for the first and last m/2 observations - exactly "
      "the end you care about when forecasting. It also forces ONE seasonal "
      "shape for all 37 years; STL lets the shape evolve.")
"""),

    # ---------------------------------------------------------------- 1.5
    md("""
---
# Exercise 1.5 - Features across a portfolio

*Follows segment 5. 16 minutes.*

One series is a plot. A hundred and forty-eight series need **numbers**.

Compute strength of trend and strength of seasonality for every Australian
retail series, then use them to find the interesting ones.
"""),
    code("""
def stl_features(g):
    \"\"\"Return trend and seasonal strength for one series (long format).\"\"\"
    y = np.log(np.clip(g["y"].to_numpy(), 1e-6, None))
    r = STL(y, period=12, robust=True).fit()
    R, T_, S = np.asarray(r.resid), np.asarray(r.trend), np.asarray(r.seasonal)
    var_r = np.var(R)
    # TODO: implement the two formulas from the slides.
    trend_strength = ...
    seasonal_strength = ...
    return pd.Series({"trend_strength": trend_strength,
                      "seasonal_strength": seasonal_strength})


allr = D.retail_all()
feat = (allr.groupby("unique_id")[["y"]]
            .apply(stl_features, include_groups=False)
            .reset_index())

checks.check_ex_1_5(feat)
feat.head()
""", """
def stl_features(g):
    \"\"\"Return trend and seasonal strength for one series (long format).\"\"\"
    y = np.log(np.clip(g["y"].to_numpy(), 1e-6, None))
    r = STL(y, period=12, robust=True).fit()
    R, T_, S = np.asarray(r.resid), np.asarray(r.trend), np.asarray(r.seasonal)
    var_r = np.var(R)
    trend_strength = max(0.0, 1 - var_r / np.var(T_ + R))
    seasonal_strength = max(0.0, 1 - var_r / np.var(S + R))
    return pd.Series({"trend_strength": trend_strength,
                      "seasonal_strength": seasonal_strength})


allr = D.retail_all()
feat = (allr.groupby("unique_id")[["y"]]
            .apply(stl_features, include_groups=False)
            .reset_index())

checks.check_ex_1_5(feat)
feat.head()
"""),
    code("""
# TODO: which series are the most and least seasonal? Print the top 5 and bottom 5.
""", """
print("MOST seasonal")
print(feat.nlargest(5, "seasonal_strength").to_string(index=False))
print("\\nLEAST seasonal")
print(feat.nsmallest(5, "seasonal_strength").to_string(index=False))
"""),
    md("""
**Now check the numbers meant what you think.** Plot the most and the least
seasonal series side by side. If the feature is doing its job, the difference
should be obvious to the eye.
"""),
    code("""
# TODO: plot the most and least seasonal series.
""", """
most = feat.nlargest(1, "seasonal_strength")["unique_id"].iloc[0]
least = feat.nsmallest(1, "seasonal_strength")["unique_id"].iloc[0]

fig, axes = plt.subplots(2, 1, figsize=(10, 5.5))
for ax, uid, col in [(axes[0], most, P.ORANGE), (axes[1], least, P.BLUE)]:
    g = allr[allr["unique_id"] == uid]
    P.plot_series(g, ax=ax, color=col,
                  title=f"{uid}  (F_S = {feat.loc[feat['unique_id'] == uid, 'seasonal_strength'].iloc[0]:.2f})")
plt.show()
"""),
    code("""
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.scatter(feat["trend_strength"], feat["seasonal_strength"], s=26,
           color=P.BLUE, alpha=0.6)
mine = feat[feat["unique_id"] == D.SPINE_ID].iloc[0]
ax.scatter([mine["trend_strength"]], [mine["seasonal_strength"]], s=120,
           color=P.GREEN, zorder=3, label="our spine")
ax.set(xlabel="strength of trend", ylabel="strength of seasonality",
       title="148 retail series in feature space")
ax.legend(frameon=False)
plt.show()
"""),
    md("""
**Question.** Trend strength is above 0.96 for nearly every series. Is that
feature useless here?

<!--STUDENT-->
*Your answer:*

<!--SOLUTION-->
*Answer.* Useless for *discriminating between these series* - yes. But it is
still a finding: it says "everything in Australian retail trends", which tells
you that any model you pick must handle a trend, and that seasonality is the
axis worth routing on. A feature that does not vary across your portfolio is a
feature you can stop computing - after you have looked at it once.
"""),

    md("""
---
## End of Day 1

You can now diagnose a series: see its patterns, measure them with the ACF,
split it into components, and summarise a whole portfolio.

Tomorrow you forecast - and, more importantly, learn how to tell whether the
forecast was any good.
"""),
]

# =====================================================================
# LAB 2 - Day 2
# =====================================================================

LAB2 = [
    md("""
## Setup

Same `coursekit` imports, plus `statsforecast` for the models and
`utilsforecast` for the metrics.
"""),
    code("""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import (HistoricAverage, Naive, RandomWalkWithDrift,
                                  SeasonalNaive)
from statsmodels.stats.diagnostic import acorr_ljungbox
from utilsforecast.losses import mae, mape, mase, rmse, rmsse

from coursekit import checks
from coursekit import datasets as D
from coursekit import leaderboard as lb
from coursekit import plotting as P

P.use_course_style()

spine = D.spine()
H = 24
train, test = D.train_test(spine, h=H)
print(f"train: {len(train)} months to {train['ds'].max().date()}")
print(f"test : {len(test)} months from {test['ds'].min().date()}")
"""),

    # ---------------------------------------------------------------- 2.1
    md("""
---
# Exercise 2.1 - The benchmark floor

*Follows segment 1. 13 minutes.*

Fit all four benchmarks and look at them. Everything for the rest of the course
is measured against these.
"""),
    code("""
MODELS = ["HistoricAverage", "Naive", "SeasonalNaive", "RWD"]
LABELS = {"HistoricAverage": "Mean", "Naive": "Naive",
          "SeasonalNaive": "Seasonal naive", "RWD": "Drift"}

# TODO: build a StatsForecast object with all four benchmarks and forecast H
#       months ahead from `train`, with 80% and 95% intervals, keeping fitted values.
sf = ...
fc = ...

checks.check_ex_2_1(fc, MODELS)
fc.head()
""", """
MODELS = ["HistoricAverage", "Naive", "SeasonalNaive", "RWD"]
LABELS = {"HistoricAverage": "Mean", "Naive": "Naive",
          "SeasonalNaive": "Seasonal naive", "RWD": "Drift"}

sf = StatsForecast(
    models=[HistoricAverage(), Naive(), SeasonalNaive(season_length=12),
            RandomWalkWithDrift()],
    freq=D.FREQ, n_jobs=1,
)
fc = sf.forecast(df=train, h=H, level=[80, 95], fitted=True)

checks.check_ex_2_1(fc, MODELS)
fc.head()
"""),
    code("""
# TODO: plot the last 6 years of training data, the four forecasts, and the
#       held-out actuals on one chart.
""", """
fig, ax = plt.subplots(figsize=(10, 4.6))
hist = train.tail(72)
ax.plot(hist["ds"], hist["y"], color=P.BLACK, lw=1.1, label="observed")
ax.plot(test["ds"], test["y"], color=P.GREY, lw=1.4, ls="--", label="actual")
for m, c in zip(MODELS, [P.PINK, P.GREEN, P.ORANGE, P.BLUE]):
    ax.plot(fc["ds"], fc[m], lw=1.7, color=c, label=LABELS[m])
ax.set(title="Four benchmarks, 24 months ahead")
ax.legend(frameon=False, ncols=3)
plt.show()
"""),
    md("""
**Question.** Two of these are obviously wrong before you compute a single
metric. Which, and why?

<!--STUDENT-->
*Your answer:*

<!--SOLUTION-->
*Answer.* The **mean** method forecasts a flat line at roughly 160 for a series
currently sitting near 370 - it averages over 37 years of growth, so it is
hopeless on any trending series. The **naive** method forecasts a flat line at
the last value, which throws away the seasonality we spent all of Day 1
establishing. **Drift** at least captures the trend but still ignores season.
Only the **seasonal naive** reproduces the annual shape.
"""),
    md("""
### Stretch - forecasting on a transformed scale

The spine is multiplicative. Forecast the Box-Cox transformed series, then
back-transform. Note that the naive back-transform gives you the **median**, not
the mean.
"""),
    code("""
# Stretch - your code here.
""", """
from coreforecast.scalers import boxcox, boxcox_lambda, inv_boxcox

lam = boxcox_lambda(train["y"].to_numpy(), method="loglik")
train_t = train.assign(y=boxcox(train["y"].to_numpy(), lam))

sf_t = StatsForecast(models=[SeasonalNaive(season_length=12)], freq=D.FREQ, n_jobs=1)
fc_t = sf_t.forecast(df=train_t, h=H, level=[80])
back = inv_boxcox(fc_t["SeasonalNaive"].to_numpy(), lam)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(train.tail(48)["ds"], train.tail(48)["y"], color=P.BLACK, lw=1.1, label="observed")
ax.plot(test["ds"], test["y"], color=P.GREY, ls="--", lw=1.4, label="actual")
ax.plot(fc["ds"], fc["SeasonalNaive"], color=P.ORANGE, lw=1.6, label="SNaive, raw scale")
ax.plot(fc_t["ds"], back, color=P.BLUE, lw=1.6, label="SNaive, via Box-Cox")
ax.legend(frameon=False, ncols=2)
ax.set(title=f"Forecasting on the transformed scale (lambda = {lam:.3f})")
plt.show()

print("Back-transforming a forecast gives the MEDIAN of the forecast "
      "distribution, not the mean. For a skewed distribution those differ, and "
      "if you are adding forecasts up (across stores, across months) you need "
      "means. That correction is the 'bias adjustment' in Ch 5.6.")
"""),

    # ---------------------------------------------------------------- 2.2
    md("""
---
# Exercise 2.2 - Are the residuals white noise?

*Follows segment 2. 13 minutes.*

If a model's residuals still carry structure, the model has not finished.
"""),
    code("""
fv = sf.forecast_fitted_values()

# TODO: compute the seasonal naive's residuals, plot the three-panel
#       diagnostic, and run a Ljung-Box test at lag 24.
resid = ...
lb_pvalue = ...

print(f"mean residual : {pd.Series(resid).mean():.3f}")
print(f"Ljung-Box p   : {lb_pvalue:.3e}")

checks.check_ex_2_2(resid, lb_pvalue)
""", """
fv = sf.forecast_fitted_values()

resid = fv["y"] - fv["SeasonalNaive"]
fig, axes = P.residual_diagnostics(resid, ds=fv["ds"],
                                   title="Seasonal naive residuals")
plt.show()

lb_pvalue = float(acorr_ljungbox(resid.dropna(), lags=[24],
                                 return_df=True)["lb_pvalue"].iloc[0])

print(f"mean residual : {pd.Series(resid).mean():.3f}")
print(f"Ljung-Box p   : {lb_pvalue:.3e}")

checks.check_ex_2_2(resid, lb_pvalue)
"""),
    code("""
# TODO: do the same for the drift method. Which of the four properties
#       (uncorrelated / zero mean / constant variance / normal) does each satisfy?
""", """
resid_d = fv["y"] - fv["RWD"]
fig, axes = P.residual_diagnostics(resid_d, ds=fv["ds"], title="Drift residuals")
plt.show()

for name, r in [("SeasonalNaive", resid), ("RWD", resid_d)]:
    r = r.dropna()
    p = float(acorr_ljungbox(r, lags=[24], return_df=True)["lb_pvalue"].iloc[0])
    first_half, second_half = r.iloc[:len(r) // 2], r.iloc[len(r) // 2:]
    print(f"{name:<14} mean={r.mean():8.3f}  LB p={p:.2e}  "
          f"sd early={first_half.std():6.2f}  sd late={second_half.std():6.2f}")
"""),
    md("""
**Write your verdict.** For each method, which of the four residual properties
hold, and what does that imply?

<!--STUDENT-->
*Your answer:*

<!--SOLUTION-->
*Answer.* Neither is close to white noise.

- **Uncorrelated:** fails badly for both - Ljung-Box p is effectively zero and
  the residual ACF has large spikes. There is a great deal of signal left.
- **Zero mean:** the seasonal naive's mean residual is clearly positive, because
  the series trends upward and last year's value is systematically too low. That
  is a *bias*: the forecast will be low every time.
- **Constant variance:** fails - the late-period standard deviation is several
  times the early one, because the series grew eightfold. This is exactly what
  the Box-Cox transform in 1.4 addresses.
- **Normal:** roughly, but with heavy tails.

Implication: the benchmark floor is a floor, not a model. The failures are
informative - the bias says "add a trend", the seasonal spikes say "the seasonal
shape has changed", the variance says "transform first".
"""),

    # ---------------------------------------------------------------- 2.3
    md("""
---
# Exercise 2.3 - Intervals, and how much to believe them

*Follows segment 3. 15 minutes.*
"""),
    code("""
# TODO: plot the seasonal naive's forecast with 80% and 95% intervals against
#       the held-out actuals. (P.fan_chart wants columns mean / lo-80 / hi-80 / ...)
""", """
fan = fc.rename(columns={
    "SeasonalNaive": "mean",
    "SeasonalNaive-lo-80": "lo-80", "SeasonalNaive-hi-80": "hi-80",
    "SeasonalNaive-lo-95": "lo-95", "SeasonalNaive-hi-95": "hi-95",
})
fig, ax = plt.subplots(figsize=(10, 4.6))
P.fan_chart(train, fan, levels=(80, 95), ax=ax, actual=test, history_tail=72,
            title="Seasonal naive with prediction intervals")
plt.show()
"""),
    code("""
# TODO: the 80% interval width at each horizon, and how it compares with
#       width_1 * sqrt(h).
width = ...

h = np.arange(1, len(width) + 1)
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(h, width, color=P.BLUE, lw=2, label="actual width")
ax.plot(h, width.iloc[0] * np.sqrt(h), color=P.ORANGE, ls="--", lw=1.4,
        label="width_1 * sqrt(h)")
ax.set(xlabel="horizon h", ylabel="80% interval width", title="Widening with h")
ax.legend(frameon=False)
plt.show()
""", """
width = fc["SeasonalNaive-hi-80"] - fc["SeasonalNaive-lo-80"]

h = np.arange(1, len(width) + 1)
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(h, width, color=P.BLUE, lw=2, label="actual width")
ax.plot(h, width.iloc[0] * np.sqrt(h), color=P.ORANGE, ls="--", lw=1.4,
        label="width_1 * sqrt(h)")
ax.set(xlabel="horizon h", ylabel="80% interval width", title="Widening with h")
ax.legend(frameon=False)
plt.show()
"""),
    code("""
merged = test.merge(fc, on=["unique_id", "ds"])

# TODO: what fraction of the held-out actuals fall inside the 80% interval?
#       And what is the standard error of that estimate?
coverage = ...
se = ...

print(f"nominal 80%,  measured {coverage:.1%}  +/- {1.96 * se:.1%} (95% CI)")
checks.check_ex_2_3(width, coverage, se)
""", """
merged = test.merge(fc, on=["unique_id", "ds"])

coverage = float(((merged["y"] >= merged["SeasonalNaive-lo-80"])
                  & (merged["y"] <= merged["SeasonalNaive-hi-80"])).mean())
se = float(np.sqrt(0.8 * 0.2 / len(merged)))

print(f"nominal 80%,  measured {coverage:.1%}  +/- {1.96 * se:.1%} (95% CI)")
checks.check_ex_2_3(width, coverage, se)
"""),
    md("""
**Question.** Your measured coverage came with an error bar roughly 16 points
wide. What would you have to change to measure coverage properly - and is that
what exercise 2.5 does?

<!--STUDENT-->
*Your answer:*

<!--SOLUTION-->
*Answer.* You need more scored points, and they must come from *different
origins* rather than from extending one test window (extending it just forecasts
further ahead, where the model is worse). Rolling-origin cross-validation gives
exactly that: 8 folds x 12 months = 96 scored points instead of 24, cutting the
standard error in half. That is exercise 2.5.

Note it does not fix the *other* problem - the interval formula ignores model
uncertainty - so even a well-measured coverage tends to come in under nominal.
"""),

    # ---------------------------------------------------------------- 2.4
    md("""
---
# Exercise 2.4 - Scoring, and the metric that lies

*Follows segment 4. 12 minutes.*
"""),
    code("""
# TODO: build a table of MAE, RMSE, MAPE, MASE and RMSSE for all four models
#       on the holdout. MASE and RMSSE need seasonality=12 and train_df=train.
scores = ...

checks.check_ex_2_4(scores)
scores.round(3)
""", """
scores = pd.DataFrame({
    "MAE": mae(merged, models=MODELS)[MODELS].iloc[0],
    "RMSE": rmse(merged, models=MODELS)[MODELS].iloc[0],
    "MAPE_pct": mape(merged, models=MODELS)[MODELS].iloc[0] * 100,
    "MASE": mase(merged, models=MODELS, seasonality=12, train_df=train)[MODELS].iloc[0],
    "RMSSE": rmsse(merged, models=MODELS, seasonality=12, train_df=train)[MODELS].iloc[0],
})
scores.index = [LABELS[m] for m in scores.index]

checks.check_ex_2_4(scores)
scores.round(3)
"""),
    md("""
Now build the case where MAPE misleads. Construct a near-zero series and two
forecasts: one that is a little too **low**, one that is much too **high**.
"""),
    code("""
rng = np.random.default_rng(3)
n = 48
low = pd.DataFrame({
    "ds": pd.date_range("2020-01-01", periods=n, freq="MS"),
    "y": np.clip(rng.poisson(1.4, n).astype(float), 0.2, None),
})

# TODO: forecast A is always 2.0 units too HIGH; forecast B is always 0.15 too LOW.
#       Compute MAE and MAPE for each. Which does MAE prefer? Which does MAPE prefer?
""", """
rng = np.random.default_rng(3)
n = 48
low = pd.DataFrame({
    "ds": pd.date_range("2020-01-01", periods=n, freq="MS"),
    "y": np.clip(rng.poisson(1.4, n).astype(float), 0.2, None),
})

pred_hi = low["y"] + 2.0
pred_lo = low["y"] - 0.15
for name, pred in [("A: +2.00 units", pred_hi), ("B: -0.15 units", pred_lo)]:
    err = low["y"] - pred
    print(f"{name:<18} MAE = {err.abs().mean():5.2f}   "
          f"MAPE = {(err / low['y']).abs().mean() * 100:8.1f}%")

print("\\nMAE says B is 13x better, which matches the picture. MAPE agrees on "
      "direction here but wildly exaggerates: dividing a 2-unit error by an "
      "actual of 0.2 gives 1000%. On a series that ever touches zero, MAPE is "
      "undefined outright.")
"""),
    md("""
**Rank the four benchmarks and defend the ranking.** Which metric did you use,
and why not the others?

<!--STUDENT-->
*Your answer:*

<!--SOLUTION-->
*Answer.* Seasonal naive > Naive > Drift > Mean, on MASE.

MASE, because it is scale-free (so this ranking can be compared against other
series later), it is defined even when the series touches zero, and the
benchmark is built into it - a MASE of 1.11 immediately tells you the winner is
still slightly worse than a one-step seasonal naive.

Not MAE or RMSE: correct here, but their units are millions of dollars, so they
cannot be pooled across series. Not MAPE: this series never approaches zero so
it happens to behave, but selecting on MAPE builds a habit that breaks the first
time you meet slow-moving demand.
"""),

    # ---------------------------------------------------------------- 2.5
    md("""
---
# Exercise 2.5 - The harness

*Follows segment 5. 17 minutes.*

This is the exercise the rest of the course rests on. You are building the
evaluation harness that every Day 3 model gets plugged into.
"""),
    code("""
# TODO: rolling-origin cross-validation over the WHOLE spine:
#       8 origins, 12 months forecast each, 80% intervals.
cv = ...

print(f"folds : {cv['cutoff'].nunique()}")
print(f"scored points : {len(cv)}")
cv.head()
""", """
cv = sf.cross_validation(df=spine, h=12, step_size=12, n_windows=8, level=[80])

print(f"folds : {cv['cutoff'].nunique()}")
print(f"scored points : {len(cv)}")
cv.head()
"""),
    code("""
# TODO: for each model compute, ACROSS FOLDS:
#         - mean MASE   (score each fold against its own training data)
#         - mean RMSSE
#         - empirical 80% coverage
#       Return a tidy frame with columns: model / mase / rmsse / coverage_80
summary = ...

checks.check_ex_2_5(cv, summary)
summary.round(3)
""", """
rows = []
for m in MODELS:
    fold_mase, fold_rmsse = [], []
    for cut, g in cv.groupby("cutoff"):
        tr = spine[spine["ds"] <= cut]
        g1 = g.drop(columns=["cutoff"])
        fold_mase.append(mase(g1, models=[m], seasonality=12, train_df=tr)[m].iloc[0])
        fold_rmsse.append(rmsse(g1, models=[m], seasonality=12, train_df=tr)[m].iloc[0])
    inside = ((cv["y"] >= cv[f"{m}-lo-80"]) & (cv["y"] <= cv[f"{m}-hi-80"])).mean()
    rows.append({"model": LABELS[m], "mase": np.mean(fold_mase),
                 "rmsse": np.mean(fold_rmsse), "coverage_80": float(inside),
                 "mase_min": np.min(fold_mase), "mase_max": np.max(fold_mase)})

summary = pd.DataFrame(rows)

checks.check_ex_2_5(cv, summary)
summary.round(3)
"""),
    md("""
Write the results to the leaderboard. **This file is the course's running
scoreboard** - Day 3 appends to the same table.
"""),
    code("""
lb.reset()   # start clean; re-running this cell is safe

for _, row in summary.iterrows():
    lb.record(
        row["model"], day=2,
        mase=float(row["mase"]), rmsse=float(row["rmsse"]),
        coverage_80=float(row["coverage_80"]),
        notes="benchmark, 8-fold rolling origin",
    )

table = lb.show()
checks.check_leaderboard(table)
table.round(3)
"""),
    md("""
### Stretch - how much does one window matter?

Score each fold separately and look at the spread.
"""),
    code("""
# Stretch - your code here.
""", """
per_fold = pd.DataFrame([
    mase(g.drop(columns=["cutoff"]), models=MODELS, seasonality=12,
         train_df=spine[spine["ds"] <= cut])[MODELS].iloc[0]
    for cut, g in cv.groupby("cutoff")
]).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(8, 3.8))
for i, m in enumerate(MODELS):
    ax.scatter(np.full(len(per_fold), i), per_fold[m], s=45, color=P.ORANGE,
               alpha=0.75, zorder=3)
ax.set_xticks(range(len(MODELS)), [LABELS[m] for m in MODELS], rotation=20, ha="right")
ax.set(ylabel="MASE", title="One dot per fold")
ax.set_yscale("log")
plt.show()

sn = per_fold["SeasonalNaive"]
print(f"Seasonal naive MASE by fold: {'  '.join(f'{v:.2f}' for v in sn)}")
print(f"best {sn.min():.2f}, worst {sn.max():.2f} - a {sn.max() / sn.min():.1f}x spread")
print("\\nThe RANKING was identical in every fold. The NUMBER was not. Report "
      "the ranking with confidence and the number with a spread.")
"""),

    md("""
---
## End of Day 2

You have an evaluation harness: benchmarks, residual diagnostics, intervals with
an honest error bar, scale-free metrics, and rolling-origin cross-validation.

`labs/leaderboard.csv` now holds the benchmark floor. Every model on Day 3 has
to get past it.
"""),
]


# =====================================================================
# PRE-WORK - sent before Day 1
# =====================================================================

PREWORK = [
    md("""
Twenty minutes, before Day 1. Two jobs:

1. **Prove your environment works** - so Day 1 opens with content, not an install clinic.
2. **Refresh the pandas and regression bits** the course leans on.

Nothing here is assessed. If a section is already obvious to you, skim it.
"""),
    md("""
---
## 1. Does the environment work?

From the repo root, in a terminal:

```bash
uv sync --extra dev
.venv/Scripts/python.exe scripts/check_env.py
.venv/Scripts/python.exe scripts/prefetch_data.py
```

`check_env.py` must print **"Ready. See you on Day 1."** If it does not, it tells you
exactly what to fix. `prefetch_data.py` needs internet **once**; after that the course
runs offline.

Then run the cell below.
"""),
    code("""
from coursekit import datasets as D
from coursekit import plotting as P

P.use_course_style()
spine = D.spine()
print(f"Loaded {len(spine)} months, "
      f"{spine['ds'].min():%b %Y} to {spine['ds'].max():%b %Y}")
P.plot_series(spine, title="If you can see this chart, you are ready.")
"""),
    md("""
---
## 2. Dates in pandas

A time series is a value **plus a timestamp**, and almost every real-world bug in
forecasting is a timestamp bug. Three things to be fluent in.
"""),
    code("""
import numpy as np
import pandas as pd

# A DatetimeIndex is not a list of strings.
dates = pd.date_range("2024-01-01", periods=6, freq="MS")   # MS = month START
print(dates)
print("\\nyear:", dates.year.tolist())
print("month:", dates.month.tolist())
"""),
    md("""
`freq="MS"` is month-start, `"ME"` is month-end, `"D"` daily, `"h"` hourly,
`"QS"` quarter-start. Getting this wrong shifts your whole series by a month.
"""),
    code("""
# resample: change the frequency. asfreq: assert one, exposing gaps as NaN.
daily = pd.Series(np.arange(60.0), index=pd.date_range("2024-01-01", periods=60, freq="D"))
print("daily -> monthly totals:")
print(daily.resample("MS").sum())

# Now punch a hole in the calendar and make it visible.
holed = daily.drop(daily.index[10:14])
print(f"\\nrows after dropping 4 days: {len(holed)}")
print(f"rows after asfreq('D'):     {len(holed.asfreq('D'))}  "
      f"<- the gap is now VISIBLE as NaN")
"""),
    md("""
**Why this matters.** Dropping four rows does not shift the index - but it *does* mean
row `t-7` is no longer "one week ago". Every seasonal lag after the gap is wrong, and
nothing raises an error. Day 1 opens with this.
"""),
    code("""
# TODO: `s` below is missing two months. Reindex it onto a complete monthly
#       calendar so the gaps become visible NaNs, then count them.
s = pd.Series(
    [10.0, 11, 13, 12, 15, 16],
    index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-05-01",
                          "2024-06-01", "2024-07-01", "2024-08-01"]),
)

repaired = ...

assert repaired is not Ellipsis, "Fill in `repaired` above."
print(repaired)
print(f"missing months: {int(repaired.isna().sum())}")
""", """
s = pd.Series(
    [10.0, 11, 13, 12, 15, 16],
    index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-05-01",
                          "2024-06-01", "2024-07-01", "2024-08-01"]),
)

repaired = s.asfreq("MS")

assert repaired is not Ellipsis, "Fill in `repaired` above."
print(repaired)
print(f"missing months: {int(repaired.isna().sum())}  (March and April)")
"""),
    md("""
---
## 3. Long format, and groupby

The whole course uses the layout fpppy uses: one row per series per timestamp, with
columns **`unique_id` / `ds` / `y`**. It looks redundant for one series and pays off the
moment you have 148.
"""),
    code("""
allr = D.retail_all()
print(allr.head())
print(f"\\n{allr['unique_id'].nunique()} series, {len(allr):,} rows")

# One number per series - the pattern used constantly on Day 1.
summary = (allr.groupby("unique_id")["y"]
               .agg(n="size", mean="mean", last="last")
               .sort_values("mean", ascending=False))
print("\\nBiggest five by average turnover:")
print(summary.head())
"""),
    md("""
---
## 4. A ten-minute regression refresher

You do not need to *derive* anything in this course, but two ideas from ordinary least
squares come back on Day 2.
"""),
    code("""
rng = np.random.default_rng(0)
x = np.linspace(0, 10, 60)
y = 3 + 1.8 * x + rng.normal(scale=2.0, size=60)

# Fit a straight line and look at what is left over.
slope, intercept = np.polyfit(x, y, 1)
fitted = intercept + slope * x
residuals = y - fitted

print(f"true slope 1.80,  estimated {slope:.3f}")
print(f"residual mean {residuals.mean():.3f} (should be ~0)")
print(f"residual sd   {residuals.std():.3f} (we generated with 2.0)")
"""),
    md("""
Two things to carry into Day 2:

- **A residual is what the model failed to explain.** `residual = actual - fitted`. If
  the residuals still contain a pattern, the model is not finished.
- **Least squares assumes the residuals are independent.** Time series residuals usually
  are *not* - this month's error looks like last month's. That single fact is why
  forecasting needs its own toolkit, and it is the thread running through Day 2.
"""),
    code("""
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
axes[0].scatter(x, y, s=18, color=P.BLUE)
axes[0].plot(x, fitted, color=P.ORANGE, lw=2)
axes[0].set_title("fit")
axes[1].scatter(x, residuals, s=18, color=P.GREY)
axes[1].axhline(0, color=P.ORANGE, lw=1.5)
axes[1].set_title("residuals - no pattern left here")
plt.show()
"""),
    md("""
---
## You are ready

If the chart in section 1 rendered and `check_env.py` printed "Ready", you are set.

Bring: a laptop that can run the cells above, and one time series from your own work if
you have one - the last exercise on Day 1 is easy to point at your own data.
"""),
]


def note(kind):
    def _n(solution_mode):
        head = f"# {kind}"
        if solution_mode:
            return (head + " - SOLUTIONS\n\n"
                    "> Instructor copy. Every TODO is filled in and every question answered.\n"
                    "> The student copy is the same notebook with these cells blanked.")
        return (head + "\n\n"
                "> Work through the exercises in order - each follows a segment of the\n"
                "> session. Cells marked `TODO` are yours to fill in; a `checks.check_ex_*`\n"
                "> call tells you whether it worked. Stretch sections are optional.")
    return _n


def prework_note(kind):
    def _n(solution_mode):
        if solution_mode:
            return ("# Pre-work - WORKED\n\n"
                    "> Instructor copy: the one TODO is filled in.")
        return ("# Pre-work - before Day 1\n\n"
                "> Twenty minutes. Confirms your environment works"
                " and refreshes the pandas and regression bits"
                " the course leans on.")
    return _n

if __name__ == "__main__":
    build(PREWORK,
          LABS / "00_pre_work.ipynb",
          SOLS / "00_pre_work.ipynb",
          prework_note("Pre-work"))
    build(LAB1,
          LABS / "01_day1_structure_and_diagnostics.ipynb",
          SOLS / "01_day1_structure_and_diagnostics.ipynb",
          note("Day 1 - Structure & Diagnostics"))
    build(LAB2,
          LABS / "02_day2_toolbox_and_evaluation.ipynb",
          SOLS / "02_day2_toolbox_and_evaluation.ipynb",
          note("Day 2 - Toolbox & Evaluation"))
