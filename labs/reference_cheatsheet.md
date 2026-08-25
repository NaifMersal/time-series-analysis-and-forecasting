# Time series cheat sheet: Days 1 & 2

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

| What the correlogram shows | What it means |
|---|---|
| Slow decay, all positive | **trend** |
| Spikes at $m, 2m, 3m$ | **seasonality** of period $m$ |
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

Every real model must beat these, and you must say *by how much*.

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

For the naive method $\hat\sigma_h = \hat\sigma\sqrt h$, uncertainty grows, but
*decelerating*. That $\sqrt h$ shape is why a fan chart flares fast then widens slowly.

**Intervals are usually too narrow.** The formula covers randomness *given the model*, not
the model being wrong, the parameters being estimated, or the world changing.

Measuring coverage on $n$ points carries a standard error of $\sqrt{p(1-p)/n}$, on 24
points that is $\pm16\%$. One window cannot measure coverage.

---

## Metrics

| | Scale-free? | Safe near zero? | Use it? |
|---|---|---|---|
| MAE | no | yes | within one series |
| RMSE | no | yes | within one series; punishes big misses |
| MAPE | yes | **no** | report if asked; never select on it |
| **MASE** | **yes** | **yes** | **default** |
| **RMSSE** | **yes** | **yes** | default, squared-error flavour |

$$\text{MASE}=\frac{\text{mean}(|e_t|)}{Q},\qquad
Q=\frac{1}{T-m}\sum_{t=m+1}^{T}|y_t-y_{t-m}|$$

**MASE = 1** means as good as the in-sample seasonal naive. Below 1 is better; above 1 is
worse, and you should say so.

MAPE fails three ways: undefined at zero, explosive near it, and asymmetric, optimising
it biases your forecasts low.

```python
from utilsforecast.losses import mase, rmsse
mase(merged, models=MODELS, seasonality=12, train_df=train)
```

---

## Rolling-origin cross-validation

```python
cv = sf.cross_validation(df=series, h=12, step_size=12, n_windows=8, level=[80])
```

- `h`, the horizon **the business actually plans on**
- `step_size`, smaller gives more folds, but they overlap
- `n_windows`, more folds, less noise, less training data in the first fold

Score each fold against **its own** training data. No fold ever sees its own future.

Expect the **ranking** to be stable and the **number** not to be: on our spine the
seasonal naive scored between 0.71 and 1.90 MASE depending on the fold. Report the
ranking with confidence, the number with a spread.

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
