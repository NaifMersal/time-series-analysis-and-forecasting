"""Plot helpers shared by the course slides and labs.

Every chart in the decks comes from here so that what students see projected is
drawn by the same code they run in the notebooks.

Conventions: series live in the book's long layout -- ``unique_id`` / ``ds`` /
``y`` -- but most functions here also accept a bare ``ds``/``y`` frame or a
plain array, because the labs build up to the long layout gradually.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Colour-blind friendly palette, carried over from the Ch-3 exercise notebook.
BLACK = "#000000"
ORANGE = "#D55E00"
BLUE = "#0072B2"
GREEN = "#009E73"
PINK = "#CC79A7"
GREY = "#9aa3ad"

#: Cycle used when several series share one pair of axes.
SERIES_COLORS = [BLACK, ORANGE, BLUE, GREEN, PINK]


def use_course_style(figsize=(9, 5), dpi=110) -> None:
    """Apply the course's matplotlib defaults.

    Call once at the top of a deck or notebook. Type sizes are deliberately
    large: these charts get read from the back of a room.
    """
    import seaborn as sns

    sns.set_style("whitegrid")
    plt.rcParams.update(
        {
            "figure.figsize": figsize,
            "figure.dpi": dpi,
            "figure.constrained_layout.use": True,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "axes.titlelocation": "left",
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "lines.linewidth": 1.3,
        }
    )


# --------------------------------------------------------------------------
# basic series plots
# --------------------------------------------------------------------------

def thin_xticks(axes, n=4):
    """Cap the number of x ticks. Small multi-panel figures otherwise collide
    year labels into an unreadable smear at projector size."""
    for ax in np.atleast_1d(axes).ravel():
        ax.xaxis.set_major_locator(plt.MaxNLocator(n))
    return axes


def plot_series(df, x="ds", y="y", ax=None, title="", xlabel="", ylabel="",
                color=BLACK, **kw):
    """Plot one series. Stand-in for the book's `plot_series` helper."""
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(df[x], df[y], color=color, **kw)
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
    return ax


# --------------------------------------------------------------------------
# moving averages -- the trend-cycle estimator behind classical decomposition
# --------------------------------------------------------------------------

def ma_weights(m: int) -> np.ndarray:
    """Weights of the centred moving average of order ``m``.

    Odd ``m``: ``m`` equal weights of ``1/m``, symmetric about t.
    Even ``m``: the **2xm-MA** (spoken "two-by-m") -- ``m + 1`` weights ``(1/2m, 1/m, ..., 1/m,
    1/2m)``. That is the average of the two adjacent m-term averages, and it is
    what puts an even-order average back on an integer t while still giving
    every season a total weight of exactly ``1/m``.
    """
    m = int(m)
    if m < 2:
        raise ValueError("m must be at least 2")
    if m % 2:
        return np.full(m, 1.0 / m)
    w = np.full(m + 1, 1.0 / m)
    w[0] = w[-1] = 1.0 / (2 * m)
    return w


def centred_ma(y, m: int) -> np.ndarray:
    """Centred moving average of order ``m`` (a 2xm-MA when ``m`` is even).

    Same length as ``y``, with NaN in the first and last ``len(weights) // 2``
    positions -- the ends a centred window cannot reach. Those gaps are not a
    bug to hide: they are the reason classical decomposition cannot estimate
    the trend at the edge you forecast from.
    """
    y = np.asarray(pd.Series(y), dtype=float)
    w = ma_weights(m)
    k = len(w) // 2
    out = np.full(len(y), np.nan)
    if len(y) > len(w):
        out[k:len(y) - k] = np.convolve(y, w, mode="valid")
    return out


def trend_overlay_plot(df, trends, ax=None, title="", x="ds", y="y",
                       tail=None, colors=None, base_color=GREY, legend=True,
                       shade_gap=None, ylabel=""):
    """Series in grey with one or more trend estimates drawn over it.

    ``trends`` maps a label to an array the same length as ``df``. NaNs are
    simply not drawn -- which is the whole point for a centred moving average.
    ``shade_gap`` names one of those labels: the stretch after its last defined
    value is shaded, so "the moving average cannot reach the end" is something
    the room sees rather than something the slide asserts.
    """
    if ax is None:
        _, ax = plt.subplots()
    d = df.tail(tail) if tail else df
    n = len(df)
    ax.plot(d[x], d[y], color=base_color, lw=0.9, label="observed")
    colors = colors or SERIES_COLORS[1:]
    drawn = {}
    for (label, values), c in zip(trends.items(), colors):
        v = np.asarray(values, dtype=float)
        v = v[-len(d):] if len(v) == n else v
        drawn[label] = v
        ax.plot(d[x], v, color=c, lw=2.0, label=label)
    if shade_gap is not None:
        v = drawn[shade_gap]
        last = np.flatnonzero(~np.isnan(v))
        if len(last):
            xs = np.asarray(d[x])
            lo, hi = xs[last[-1]], xs[-1]
            ax.axvspan(lo, hi, color=ORANGE, alpha=0.14, lw=0)
            ax.annotate("no MA trend", (lo + (hi - lo) / 2, 0.05),
                        xycoords=("data", "axes fraction"),
                        ha="center", size=9, color=ORANGE)
    ax.set(title=title, xlabel="", ylabel=ylabel)
    if legend:
        ax.legend(frameon=False, ncols=len(trends) + 1, loc="upper left")
    return ax


def ma_weight_plot(m: int = 12, ax=None, title=None):
    """Stem plot of the centred-MA weights, offsets -k..k.

    For even ``m`` the two half-weight end points are the thing to look at:
    they land on the *same* season (they are ``m`` apart), so between them that
    season still gets ``1/m`` -- which is why the seasonal term still cancels.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(6.5, 2.8))
    w = ma_weights(m)
    k = len(w) // 2
    off = np.arange(-k, k + 1)
    ends = np.zeros(len(w), dtype=bool)
    if m % 2 == 0:
        ends[[0, -1]] = True
    ax.vlines(off[~ends], 0, w[~ends], color=BLUE, lw=6)
    if ends.any():
        ax.vlines(off[ends], 0, w[ends], color=ORANGE, lw=6)
    ax.axhline(0, color=GREY, lw=1)
    label = f"2×{m}-MA" if m % 2 == 0 else f"{m}-MA"
    ax.set(title=title if title is not None else f"{label} weights",
           xlabel="offset from t", ylabel="weight",
           xticks=off[::2], ylim=(0, float(w.max()) * 1.35))
    return ax


def decomposition_plot(dcmp, cols, title, ylabel="", x="ds"):
    """Stack the components of a decomposition, one panel each."""
    fig, axes = plt.subplots(len(cols), 1, sharex=True,
                             figsize=(9, 2 + 1.4 * len(cols)))
    axes = np.atleast_1d(axes)
    for ax, col in zip(axes, cols):
        ax.plot(dcmp[x], dcmp[col], color=BLACK, lw=0.9)
        ax.set_ylabel(col)
    axes[0].set_title(title, size="medium", loc="left")
    fig.supylabel(ylabel)
    return fig, axes


def seasonal_plot(df, period_col, season_col, y="y", ax=None, title="",
                  cmap="viridis"):
    """Seasonal plot: one line per period (e.g. per year), x = season index.

    ``period_col`` is the grouping (year); ``season_col`` is the position
    within the period (month 1-12, quarter 1-4, ...).
    """
    if ax is None:
        _, ax = plt.subplots()
    periods = sorted(df[period_col].unique())
    colors = plt.get_cmap(cmap)(np.linspace(0.05, 0.95, len(periods)))
    for p, c in zip(periods, colors):
        g = df[df[period_col] == p].sort_values(season_col)
        ax.plot(g[season_col], g[y], color=c, lw=1.1)
    ax.set(title=title, xlabel=season_col, ylabel=y)
    return ax


def subseries_plot(df, season_col, y="y", x="ds", title=""):
    """Subseries plot: one small panel per season, with that season's mean."""
    seasons = sorted(df[season_col].unique())
    fig, axes = plt.subplots(1, len(seasons), sharey=True,
                             figsize=(max(7.5, 1.0 + 0.7 * len(seasons)), 3.4))
    axes = np.atleast_1d(axes)
    for ax, s in zip(axes, seasons):
        g = df[df[season_col] == s].sort_values(x)
        ax.plot(g[x], g[y], color=BLACK, lw=0.9)
        ax.axhline(g[y].mean(), color=ORANGE, lw=1.6)
        ax.set_title(str(s), size=9)
        ax.set_xticks([])
    axes[0].set_ylabel(y)
    fig.suptitle(title, size=12, x=0.02, ha="left")
    return fig, axes


def lag_plot_grid(y, lags=(1, 2, 3, 4, 6, 12), color_by=None, title="",
                  axes=None, show_corr=True, cmap="twilight", ncol=3):
    """Grid of y_t against y_{t-k}. ``color_by`` colours points by season.

    ``show_corr`` puts the actual correlation in each panel title, so a claim
    like "lag 12 is the tight one" can be checked against a number instead of
    an impression. Pass ``axes`` to draw into an existing row of a larger
    figure (used to show raw vs trend-removed side by side).
    """
    y = np.asarray(pd.Series(y).dropna(), dtype=float)
    if axes is None:
        nrow = int(np.ceil(len(lags) / ncol))
        fig, axes = plt.subplots(nrow, ncol, figsize=(8.5, 2.9 * nrow),
                                 sharex=True, sharey=True)
    else:
        fig = np.atleast_1d(axes).ravel()[0].figure
    axes = np.atleast_1d(axes)
    for ax, k in zip(axes.ravel(), lags):
        c = BLUE if color_by is None else np.asarray(color_by)[k:]
        ax.scatter(y[:-k], y[k:], s=9, c=c, cmap=cmap, alpha=0.85)
        lo, hi = float(np.nanmin(y)), float(np.nanmax(y))
        ax.plot([lo, hi], [lo, hi], color=GREY, lw=0.8, ls="--")
        label = f"lag {k}"
        if show_corr:
            label += f"   r = {np.corrcoef(y[:-k], y[k:])[0, 1]:.2f}"
        ax.set_title(label, size=10)
    for ax in axes.ravel()[len(lags):]:
        ax.set_visible(False)
    if title:
        fig.suptitle(title, size=12, x=0.02, ha="left")
    return fig, axes


def season_colorbar(fig, axes, n_seasons=12, cmap="twilight", label="month",
                    ticks=(1, 4, 7, 10), ticklabels=("Jan", "Apr", "Jul", "Oct")):
    """Shared colour key for a season-coloured scatter grid.

    Without it "coloured by month" is a claim the audience cannot use.
    """
    import matplotlib as mpl

    norm = mpl.colors.Normalize(vmin=1, vmax=n_seasons)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=np.atleast_1d(axes).ravel().tolist(),
                      orientation="horizontal", fraction=0.05, pad=0.06,
                      aspect=45, ticks=list(ticks))
    cb.ax.set_xticklabels(list(ticklabels), size=9)
    cb.set_label(label, size=9)
    return cb


# --------------------------------------------------------------------------
# ACF -- the central diagnostic of the course
# --------------------------------------------------------------------------

def acf_values(y, nlags=24):
    """Sample autocorrelations r_1..r_nlags plus the 2/sqrt(T) bound."""
    from statsmodels.tsa.stattools import acf

    y = np.asarray(pd.Series(y).dropna(), dtype=float)
    r = acf(y, nlags=nlags, fft=False)[1:]
    bound = 1.96 / np.sqrt(len(y))
    return r, bound


def acf_plot(y, nlags=24, ax=None, title="", highlight_every=None,
             color=BLACK, show_bounds=True):
    """Correlogram with the 1.96/sqrt(T) significance band.

    ``highlight_every=m`` paints the seasonal lags (m, 2m, ...) in ORANGE --
    which is how students learn to *see* seasonality in an ACF instead of
    being told it is there.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(5.2, 3.2))
    r, bound = acf_values(y, nlags=nlags)
    lags = np.arange(1, len(r) + 1)
    colors = [color] * len(r)
    if highlight_every:
        for i, k in enumerate(lags):
            if k % highlight_every == 0:
                colors[i] = ORANGE
    ax.vlines(lags, 0, r, colors=colors, lw=2.2)
    ax.axhline(0, color=GREY, lw=1)
    if show_bounds:
        ax.axhline(bound, color=BLUE, ls="--", lw=1)
        ax.axhline(-bound, color=BLUE, ls="--", lw=1)
    ax.set(title=title, xlabel="lag", ylabel="ACF", ylim=(-1.05, 1.05))
    return ax


def residual_diagnostics(resid, ds=None, nlags=24, title="", bins=25):
    """The standard three-panel residual check: series, ACF, histogram."""
    resid = pd.Series(resid).dropna()
    fig = plt.figure(figsize=(9, 5))
    gs = fig.add_gridspec(2, 2)
    ax_top = fig.add_subplot(gs[0, :])
    ax_acf = fig.add_subplot(gs[1, 0])
    ax_hist = fig.add_subplot(gs[1, 1])

    x = np.asarray(ds)[-len(resid):] if ds is not None else np.arange(len(resid))
    ax_top.plot(x, resid.to_numpy(), color=BLACK, lw=0.9)
    ax_top.axhline(0, color=ORANGE, lw=1.2)
    ax_top.set_title(title or "Innovation residuals", size=11)

    acf_plot(resid.to_numpy(), nlags=nlags, ax=ax_acf, title="Residual ACF")
    ax_hist.hist(resid.to_numpy(), bins=bins, color=BLUE, alpha=0.85)
    ax_hist.set_title("Distribution", size=11)
    return fig, (ax_top, ax_acf, ax_hist)


# --------------------------------------------------------------------------
# forecasts and uncertainty
# --------------------------------------------------------------------------

def fan_chart(history, forecast, levels=(80, 95), ax=None, title="",
              actual=None, history_tail=None, color=BLUE, mean_col="mean"):
    """Point forecast with nested prediction intervals.

    ``forecast`` needs columns ``ds``, ``mean_col`` and, per level L, ``lo-L``
    and ``hi-L``. ``actual`` (optional) overlays the truth so that whether the
    interval actually covered it is visible rather than asserted.
    """
    if ax is None:
        _, ax = plt.subplots()
    hist = history.tail(history_tail) if history_tail else history
    ax.plot(hist["ds"], hist["y"], color=BLACK, lw=1.1, label="observed")

    shades = np.linspace(0.30, 0.13, len(levels))
    for lvl, alpha in zip(sorted(levels), shades):
        ax.fill_between(forecast["ds"], forecast[f"lo-{lvl}"],
                        forecast[f"hi-{lvl}"], color=color, alpha=float(alpha),
                        lw=0, label=f"{lvl}%")
    ax.plot(forecast["ds"], forecast[mean_col], color=color, lw=1.8,
            label="forecast")
    if actual is not None:
        ax.plot(actual["ds"], actual["y"], color=ORANGE, lw=1.3, ls="--",
                label="actual")
    ax.set(title=title, xlabel="", ylabel="y")
    ax.legend(loc="upper left", frameon=False, ncols=2)
    return ax


def cv_staircase(n_obs=60, initial=36, horizon=6, step=6, ax=None,
                 n_folds=None, title="Rolling-origin cross-validation"):
    """Draw the rolling-origin diagram: train block, scored block, unseen tail.

    Deliberately hand-drawn rather than shipped as a static image, so it can be
    revealed fold-by-fold (pass ``n_folds`` and emit one figure per fragment)
    and so the parameters on the slide are the ones used in the lab.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4))
    origins = list(range(initial, n_obs - horizon + 1, step))
    total = len(origins)
    if n_folds is not None:
        origins = origins[:n_folds]
    for row, origin in enumerate(origins):
        y = total - row - 1
        ax.barh(y, origin, height=0.62, color=BLUE, alpha=0.85)
        ax.barh(y, horizon, left=origin, height=0.62, color=ORANGE)
        ax.barh(y, n_obs - origin - horizon, left=origin + horizon,
                height=0.62, color=GREY, alpha=0.30)
        ax.text(-1.5, y, f"fold {row + 1}", ha="right", va="center", size=9)
    ax.set(title=title, xlim=(0, n_obs), ylim=(-0.7, total - 0.3),
           xlabel="time index")
    ax.set_yticks([])
    ax.grid(False)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=BLUE, alpha=0.85),
        plt.Rectangle((0, 0), 1, 1, color=ORANGE),
        plt.Rectangle((0, 0), 1, 1, color=GREY, alpha=0.30),
    ]
    ax.legend(handles, ["train", "forecast (scored)", "not yet seen"],
              loc="lower right", frameon=False, ncols=3)
    return ax


def metric_bars(scores, ax=None, title="", highlight_best=True,
                lower_is_better=True):
    """Horizontal bars of one metric across models, best one highlighted."""
    if ax is None:
        _, ax = plt.subplots(figsize=(6.2, 3.2))
    names = list(scores)
    vals = [scores[n] for n in names]
    best = (min if lower_is_better else max)(vals)
    colors = [ORANGE if (highlight_best and v == best) else BLUE for v in vals]
    ax.barh(names, vals, color=colors, height=0.62)
    for i, v in enumerate(vals):
        ax.text(v, i, f" {v:.3f}", va="center", size=9)
    ax.set(title=title)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    return ax
