# Time series cheat sheet: Days 1, 2 & 3

One page. Print it. It covers everything you need to diagnose a series and prove whether
a forecast is any good.

---

## The rule everything rests on

**The order is the data.** No shuffling, no random train/test split, no k-fold. The
replacement is rolling-origin cross-validation (bottom of this page).

---

## Patterns

| | Period | Example |
|---|---|---|
| **Trend** | none | long-term rise or fall; need not be linear |
| **Seasonality** | **fixed and known** | month of year, day of week, hour of day |
| **Cycle** | **not fixed** | business cycles, predator–prey populations |

If you know the period in advance it is seasonality. If the gaps between peaks vary, it
is a cycle, and cycles are the thing nobody forecasts well.

**Components:** $y_t = S_t + T_t + R_t$ (additive), or $y_t = S_t \times T_t \times R_t$
when the seasonal swing grows with the level. $T_t$ is trend **and** cycle together.

---

## The four plots

| Plot | Question it answers |
|---|---|
| Time plot | What is going on at all? Outliers, level shifts, gaps. **Always first.** |
| Seasonal plot | What is the seasonal shape, and is it changing? |
| Subseries plot | How does each season behave across years? |
| Lag plot | Is $y_t$ related to $y_{t-k}$? |

`D.add_calendar(df)` adds `year`, `month` and `quarter` columns, which is what the
seasonal and subseries plots group on.

```python
sp = D.add_calendar(df)

P.plot_series(df, title="...")                              # time plot
P.seasonal_plot(sp, "year", "month",                        # one line per year
                season_labels=P.MONTH_LABELS, colorbar=True)
P.subseries_plot(sp, "month",                               # one panel per month
                 season_labels=P.MONTH_LABELS)              # returns (fig, axes)
P.lag_plot_grid(df["y"], lags=(1, 6, 12))                   # y_t against y_{t-k}
```

**Before any of them:** check the timestamps.

```python
pd.infer_freq(df["ds"])            # what frequency does pandas see?
df["ds"].duplicated().sum()        # duplicates
len(pd.date_range(df["ds"].min(), df["ds"].max(), freq="MS")) == len(df)   # gaps
```

A missing row does **not** raise an error, it silently shifts every seasonal lag after
it. Repair with `.asfreq()` or `.reindex()` so the gap becomes a visible `NaN`.

---

## ACF: the central diagnostic

$$r_k = \frac{\sum_{t=k+1}^{T}(y_t-\bar y)(y_{t-k}-\bar y)}{\sum_{t=1}^{T}(y_t-\bar y)^2}
\qquad\text{bounds } \pm\frac{1.96}{\sqrt{T}}$$

```python
P.acf_plot(df["y"], nlags=36, highlight_every=12)   # draw the correlogram
r, bound = P.acf_values(df["y"], nlags=36)          # the numbers behind it:
                                                    # r[k-1] is r_k, bound is 1.96/sqrt(T)
```

| What the correlogram shows | What it means |
|---|---|
| Slow decay, all positive | **trend** |
| Spikes at $m, 2m, 3m$ | **seasonality** of period $m$ |
| Slow decay with peaks riding on it | **trend + seasonality** |
| Slow oscillating wave | **cycle** |
| Everything inside the bounds | **white noise**: nothing left to model |

The bounds are a null hypothesis about *one* lag. Plot 36 lags and expect 1–2 outside by
chance. A *pattern* matters; a lone spike does not.

```python
from coursekit.plotting import acf_values, acf_plot
r, bound = acf_values(y, nlags=36)
acf_plot(y, nlags=36, highlight_every=12)
```

---

## Transform, then decompose

**Box-Cox** stabilises a growing seasonal swing:

$$w_t = \begin{cases}\log(y_t) & \lambda = 0\\ (y_t^{\lambda}-1)/\lambda & \text{otherwise}\end{cases}$$

```python
from coreforecast.scalers import boxcox, boxcox_lambda
lam = boxcox_lambda(y, method="loglik")
w = boxcox(y, lam)
```

$\lambda$ near 0 means a log will do, and a log is easier to explain.

**STL** splits the result. You must supply `period`; it will not guess.

```python
from statsmodels.tsa.seasonal import STL
res = STL(w, period=12, robust=True).fit()
res.trend, res.seasonal, res.resid
```

Seasonally adjusted = `w - res.seasonal`.

**Decomposition is also a forecasting method** (Ch 5.7): forecast the seasonally
adjusted part with something that handles trend, re-seasonalise with a seasonal naive.
`MSTL` is that whole recipe in one model.

```python
from statsforecast.models import MSTL, RandomWalkWithDrift
MSTL(season_length=12, trend_forecaster=RandomWalkWithDrift())
```

Forecasting on a transformed scale? Back-transforming returns the **median** of the
forecast distribution, not the mean (Ch 5.6). Medians do not add up, so a regional
total summed from back-transformed store forecasts is biased low until you apply the
bias adjustment.

STL over classical decomposition: it estimates the trend all the way to both ends (which
is the end you forecast from), and it lets the seasonal shape change over time.

---

## Features: one row per series

$$F_T = \max\left(0,\ 1-\frac{\mathrm{Var}(R_t)}{\mathrm{Var}(T_t+R_t)}\right)
\qquad
F_S = \max\left(0,\ 1-\frac{\mathrm{Var}(R_t)}{\mathrm{Var}(S_t+R_t)}\right)$$

Both in $[0,1]$. Near 1 = strong. Use them to triage a portfolio, route models, and find
data problems, then **plot the series** that look odd.

---

## The benchmark floor

| Method | statsforecast | Forecasts |
|---|---|---|
| Mean | `HistoricAverage()` | the average of all history |
| Naive | `Naive()` | the last value |
| **Seasonal naive** | `SeasonalNaive(season_length=m)` | same season last year |
| Drift | `RandomWalkWithDrift()` | last value + average slope |
| STL + drift | `MSTL(season_length=m, trend_forecaster=RandomWalkWithDrift())` | decompose, forecast, re-seasonalise |

Every real model must beat the first four, and you must say *by how much*. The STL
route is not a benchmark - it is the cheapest thing that is actually trying.

---

## Residuals

`residual = actual − fitted`, one step ahead, **on training data**. Not the same as a
forecast error (which is out of sample and often many steps ahead).

Good residuals are:

1. **uncorrelated**: else there is signal left
2. **zero mean**: else the forecast is biased
3. constant variance ← intervals need this
4. roughly normal ← intervals need this

```python
from statsmodels.stats.diagnostic import acorr_ljungbox
acorr_ljungbox(resid.dropna(), lags=[2 * m], return_df=True)
```

Small $p$ → autocorrelated → not finished. Large $p$ → *no evidence of* structure, which
is not proof there is none. Read the ACF plot too.

---

## Prediction intervals

$$\hat y_{T+h|T} \pm c\,\hat\sigma_h \qquad c = 1.28\ (80\%),\ 1.96\ (95\%)$$

$\hat\sigma_h$ is **not** $\hat\sigma\sqrt h$ for every method. That is the naive method's:

| Method | $\hat\sigma_h$ |
|---|---|
| Mean | $\hat\sigma\sqrt{1 + 1/T}$ |
| Naive | $\hat\sigma\sqrt h$ |
| Seasonal naive | $\hat\sigma\sqrt{k+1}$, $k = \lfloor (h-1)/m \rfloor$: a **staircase**, flat inside a year |
| Drift | $\hat\sigma\sqrt{h\,(1 + h/(T-1))}$ |

**Intervals are usually too narrow.** The formula covers randomness *given the model*, not
the model being wrong, the parameters being estimated, or the world changing.

Measuring coverage on $n$ points carries a standard error of $\sqrt{p(1-p)/n}$, on 24
points that is $\pm16\%$. One window cannot measure coverage.

### Three methods, three assumptions

| Method | Assumes | Interval is |
|---|---|---|
| Gaussian | residuals uncorrelated, constant variance, **normal** | $\hat y \pm c\,\hat\sigma_h$ |
| Bootstrap | residuals uncorrelated and **i.i.d. from $\hat F$**: one distribution whose characteristics do not change over time | percentiles of simulated paths |
| Split conformal | past $h$-step errors **exchangeable** with future ones (weaker than i.i.d.: order carries no information) | $\hat y_{T+h\vert T} \pm Q_{1-\alpha}(\lvert e_{t+h\vert t}\rvert)$ |

**Bootstrap.** Resample past residuals into the model's own recursion, then take
percentiles down each column. Nothing forces the result to be symmetric.

```python
resid = (fv["y"] - fv["SeasonalNaive"]).dropna()
paths = P.bootstrap_paths(train["y"], resid, h=24, season_length=12,
                          n_paths=5000, seed=7)      # -> (5000, 24)
fan = P.paths_to_fan(fc["ds"], paths, levels=(80, 95))
P.sim_paths_plot(train, fc["ds"], paths, n_show=8)   # the paths, not the band
```

`resid_tail=N` draws only from the last `N` residuals. On a series whose error spread
grows with its level, a shorter and more recent pool is the more honest one: coverage on
the spine goes 61% (all 405 residuals) → about 87% (last 120), against a nominal 80%.

**Conformal.** The calibration set is $h$-step forecast errors, collected by rolling the
origin:

$$e_{t+h|t} = y_{t+h} - \hat y_{t+h|t}$$

$t$ is when the forecast was made, $t+h$ what it predicted. At $h=1$ these are the
residuals; for $h>1$ they must be collected, not fitted. One quantile per horizon, so the
widening with $h$ is measured rather than assumed.

```python
from statsforecast.utils import ConformalIntervals

sf = StatsForecast(
    models=[SeasonalNaive(season_length=12,
                          prediction_intervals=ConformalIntervals(n_windows=8, h=24))],
    freq="MS",
)
```

Needs $2h+1$ observations minimum. With 8 windows only 16 scores sit behind each horizon,
so the band comes out visibly jittery.

On the spine, 80% coverage over 8 rolling origins: Gaussian 77%, bootstrap 61%,
conformal 83%. None of the three assumptions actually holds here: pick knowing which one
you are spending.

---

## Metrics

$e_t = y_t - \hat{y}_t$ is the forecast error. **MAE** is the mean of $|e_t|$,
**RMSE** the root of the mean of $e_t^2$, **MAPE** the mean of $|e_t / y_t|$.
**MASE** and **RMSSE** divide those by the seasonal naive's in-sample values of
the same; **scaled CRPS** divides CRPS the same way.

| | Scale-free? | Safe near zero? | Use it? |
|---|---|---|---|
| MAE | no | yes | within one series |
| RMSE | no | yes | within one series; punishes big misses |
| MAPE | yes | **no** | report if asked; never select on it |
| **MASE** | **yes** | **yes** | **default** |
| **RMSSE** | **yes** | **yes** | default, squared-error flavour |
| **scaled CRPS** | **yes** | **yes** | **default for the whole distribution** |

Scale each error by the in-sample one-step seasonal naive error,
$q_j = e_j / Q$, then average:

$$\text{MASE}=\text{mean}(|q_j|)=\frac{\text{mean}(|e_t|)}{Q},\qquad
Q=\frac{1}{T-m}\sum_{t=m+1}^{T}|y_t-y_{t-m}|$$

$$\text{RMSSE}=\sqrt{\text{mean}(q_j^2)},\qquad
q_j^2=\frac{e_j^2}{\frac{1}{T-m}\sum_{t=m+1}^{T}(y_t-y_{t-m})^2}$$

Nothing here is seasonal by nature: set $m=1$ and the denominator becomes the
plain naive's error, which is the non-seasonal version of both metrics.

**Why scale-free is not a slogan.** Re-measure the series in another unit,
$y'_t = k y_t$ and $\hat{y}'_t = k \hat{y}_t$ with $k>0$. Then
$\text{MAE}' = k\,\text{MAE}$, so MAE moves. But $Q' = kQ$ as well, so
$\text{MASE}' = k\,\text{MAE}/kQ = \text{MASE}$, and the percentage error cancels
$k$ the same way: $(k y_t - k \hat y_t)/k y_t = (y_t - \hat y_t)/y_t$.

Cancelling $k$ is necessary, not sufficient, and MAPE is the proof: it passes
that test and still cannot select a model. Add an offset, $y'_t = k y_t + c$,
which is what °C to °F is. Every term in MASE is a difference so $c$ vanishes,
while MAPE's denominator keeps it. That is the "needs a true zero" rule,
derived rather than asserted.

**MASE = 1** means as good as the in-sample seasonal naive. Below 1 is better; above 1 is
worse, and you should say so.

MAPE fails three ways: undefined at zero, explosive near it, and asymmetric, optimising
it biases your forecasts low.

```python
from utilsforecast.losses import mase, rmsse, scaled_crps
mase(merged, models=MODELS, seasonality=12, train_df=train)
```

Coverage checks whether the 80% band is honest. It cannot **rank**: an interval of
plus-or-minus infinity covers everything and is worth nothing. **Scaled CRPS** averages
the quantile (pinball) loss over a ladder of levels, so width and misses are priced
together in one scale-free number. Lower is better.

```python
from coursekit import scoring          # QCOLS and QUANTILES, derived from LEVELS
scaled_crps(cv, models={m: scoring.qcols(m)}, quantiles=scoring.QUANTILES)

# what they are, if you want to see them:
#   QCOLS     lo-95 lo-80 lo-60 lo-40 lo-20 hi-20 hi-40 hi-60 hi-80 hi-95
#   QUANTILES .025  .10   .20   .30   .40   .60   .70   .80   .90   .975
# The two lists MUST stay in step. Out of step, scaled_crps returns a number
# that is wrong and still positive, and nothing downstream catches it.
```

---

## Rolling-origin cross-validation

```python
cv = sf.cross_validation(df=series, h=12, step_size=12, n_windows=8,
                         level=[20, 40, 60, 80, 95])   # a ladder, so CRPS has quantiles
```

- `h`, the horizon **the business actually plans on**
- `step_size`, smaller gives more folds, but they overlap
- `n_windows`, more folds, less noise, less training data in the first fold

Score each fold against **its own** training data. No fold ever sees its own future:

```python
per_fold = pd.DataFrame([
    mase(g.drop(columns=['cutoff']), models=MODELS, seasonality=12,
         train_df=series[series['ds'] <= cut])[MODELS].iloc[0]
    for cut, g in cv.groupby('cutoff')
])
per_fold.mean()          # the number to report
per_fold.min(), per_fold.max()   # with its spread
```

`coursekit.scoring.score_cv(cv, model, series)` is that loop packaged, and it
returns `mase` / `rmsse` / `crps` / `coverage_80` ready for `lb.record(...)`.

Expect the **ranking** to be broadly stable and the **number** not to be: on our spine the
seasonal naive scored between 0.71 and 1.90 MASE depending on the fold. Report the
ranking with confidence, the number with a spread - and check the top two yourself.

The top of the table is exactly where one window lies to you. STL + drift beat the
seasonal naive 0.70 to 1.11 on a single 24-month holdout and lost 1.22 to 1.18 over
eight origins.

---

## Leakage: three ways the future gets in

1. Scaling or imputing using the **whole** series before splitting
2. A feature built from a **centred** window (it peeks forward)
3. Choosing the model, or the horizon, by **looking at the test set**: including
   re-tuning on the same holdout more than once

Also watch for: regime change making old folds irrelevant, too few scored points to
separate two models, and silent calendar gaps.

---

## The spine, for reference

`coursekit.datasets.spine()`, Victorian takeaway-food turnover, monthly, 441 obs,
1982-04 to 2018-12, $m = 12$, no gaps, $\lambda \approx 0.07$.
