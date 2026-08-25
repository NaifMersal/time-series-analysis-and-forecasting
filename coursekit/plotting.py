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

# Data colours are Okabe-Ito, not the SDAIA chrome palette, and that is deliberate:
# these are the colours students read *data* off, and Okabe-Ito stays separable
# under all three common forms of colour blindness. SDAIA teal and coral are close
# in luminance and converge for deuteranopes, which is fine for a border on a card
# and not fine for two series on one axis. The SDAIA palette still owns everything
# around the plot (dividers, cardboxes, rules); the plot interior is Okabe-Ito.
#
# Day 1 colour meanings, kept fixed across both decks:
#   BLACK  the spine, and "trend" wherever the taxonomy is being taught
#   BLUE   the seasonal component / a second series being contrasted
#   ORANGE the derived or highlighted thing (transform, MA, seasonal lags)
#   GREY   noise, and the raw observed series when something derived sits on top
#   PINK   a third category when one is genuinely needed
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
    year labels into an unreadable smear at projector size.

    On a date axis a plain MaxNLocator picks arbitrary interior positions and
    prints them in full, which is where labels like ``1997-05-19`` came from on
    monthly data. Date axes get a date locator and a concise formatter instead,
    so the ticks land on years.
    """
    import matplotlib.dates as mdates

    for ax in np.atleast_1d(axes).ravel():
        if isinstance(ax.xaxis.get_major_locator(), mdates.DateLocator):
            lo, hi = (mdates.num2date(v) for v in ax.get_xlim())
            years = max(1, hi.year - lo.year)
            # AutoDateLocator jumps straight from 10 to 20 years, and a 20-year
            # step on a 37-year span leaves one lonely label mid-axis. Pick the
            # coarsest of 1/2/5/10 years that still yields at least two labels.
            for step in (1, 2, 5, 10, 20):
                if years / step <= max(2, n):
                    break
            loc = mdates.YearLocator(step)
            ax.xaxis.set_major_locator(loc)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        else:
            ax.xaxis.set_major_locator(plt.MaxNLocator(n))
    return axes


def year_xticks(axes, step=10, minor=1, fmt="%Y", rotation=0):
    """Put a date axis on a plain calendar-year scale.

    A label every ``step`` years, and an unlabelled tick plus a faint gridline
    on every ``minor``-th year. That minor grid is the point of this helper:
    on annual data like ``D.lynx()`` the question students are asked is how
    many years apart the peaks fall, and they cannot count that off an axis
    whose only marks are 20 years apart.

    Set ``minor=0`` to drop the yearly grid, and ``rotation=90`` when the
    labels are dense enough to collide.

    Unlike :func:`thin_xticks`, which picks a step to keep small panels
    readable, this one is told the step -- so call it *after* ``thin_xticks``
    if both touch the same axes.
    """
    import matplotlib.dates as mdates

    for ax in np.atleast_1d(axes).ravel():
        ax.xaxis.set_major_locator(mdates.YearLocator(step))
        ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
        if minor:
            ax.xaxis.set_minor_locator(mdates.YearLocator(minor))
            ax.grid(True, which="minor", axis="x", lw=0.4, alpha=0.3)
        if rotation:
            plt.setp(ax.get_xticklabels(), rotation=rotation,
                     ha="right" if rotation % 180 else "center")
    return axes


def plot_series(df, x="ds", y="y", ax=None, title="", xlabel="", ylabel="",
                color=BLACK, **kw):
    """Plot one series. Stand-in for the book's `plot_series` helper."""
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(df[x], df[y], color=color, **kw)
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
    ax.margins(x=0.01)
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
            ax.annotate("no MA trend", (lo + (hi - lo) / 2, 0.90),
                        xycoords=("data", "axes fraction"),
                        ha="center", size=10, weight="bold", color=ORANGE)
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
        _, ax = plt.subplots(figsize=(7.5, 4.2))
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
    inner, end = float(w[k]), float(w[0])
    ticks = [end, inner] if m % 2 == 0 else [inner]
    ax.set(title=title if title is not None else f"{label} weights",
           xlabel="offset from t", ylabel="weight",
           xticks=off[::2], yticks=ticks,
           ylim=(0, inner * 1.45))
    ax.set_yticklabels([f"1/{round(1 / t)}" for t in ticks])
    if m % 2 == 0:
        ax.annotate(f"1/{round(1 / end)} each", (off[0], end),
                    textcoords="offset points", xytext=(0, 8),
                    ha="center", size=9, color=ORANGE)
        ax.annotate(f"1/{round(1 / inner)} each", (0, inner),
                    textcoords="offset points", xytext=(0, 8),
                    ha="center", size=9, color=BLUE)
    return ax


def decomposition_plot(dcmp, cols, title, ylabel="", x="ds", panel_height=1.0):
    """Stack the components of a decomposition, one panel each.

    ``panel_height`` is deliberately small: four panels at the old 1.4 inches
    each made a figure taller than a 16:9 slide, so the remainder panel fell off
    the bottom of the deck.
    """
    fig, axes = plt.subplots(len(cols), 1, sharex=True,
                             figsize=(9, 0.8 + panel_height * len(cols)))
    axes = np.atleast_1d(axes)
    for ax, col in zip(axes, cols):
        ax.plot(dcmp[x], dcmp[col], color=BLACK, lw=0.9)
        ax.set_ylabel(col)
    axes[0].set_title(title, size="medium", loc="left")
    fig.supylabel(ylabel)
    return fig, axes


MONTH_LABELS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
QUARTER_LABELS = ["Q1", "Q2", "Q3", "Q4"]


def seasonal_plot(df, period_col, season_col, y="y", ax=None, title="",
                  cmap="viridis", season_labels=None, ylabel=None,
                  colorbar=False, xlabel=None):
    """Seasonal plot: one line per period (e.g. per year), x = season index.

    ``period_col`` is the grouping (year); ``season_col`` is the position
    within the period (month 1-12, quarter 1-4, ...).

    ``season_labels`` replaces the numeric season ticks with names, and
    ``colorbar`` adds a key for which line is which period. Without one, the
    colour gradient is decoration rather than information.
    """
    if ax is None:
        _, ax = plt.subplots()
    periods = sorted(df[period_col].unique())
    colors = plt.get_cmap(cmap)(np.linspace(0.05, 0.95, len(periods)))
    for p, c in zip(periods, colors):
        g = df[df[period_col] == p].sort_values(season_col)
        ax.plot(g[season_col], g[y], color=c, lw=1.1)
    ax.set(title=title, xlabel=season_col if xlabel is None else xlabel,
           ylabel=y if ylabel is None else ylabel)
    if season_labels is not None:
        ax.set_xticks(range(1, len(season_labels) + 1))
        ax.set_xticklabels(list(season_labels))
    if colorbar and len(periods) > 1:
        import matplotlib as mpl

        norm = mpl.colors.Normalize(vmin=min(periods), vmax=max(periods))
        sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
        cb = ax.figure.colorbar(sm, ax=ax, fraction=0.035, pad=0.02)
        cb.set_label(period_col, size=9)
        cb.ax.tick_params(labelsize=9)
    return ax


def subseries_plot(df, season_col, y="y", x="ds", title="", ylabel=None,
                   season_labels=None, height=3.4):
    """Subseries plot: one small panel per season, with that season's mean."""
    seasons = sorted(df[season_col].unique())
    labels = list(season_labels) if season_labels is not None else [str(s) for s in seasons]
    fig, axes = plt.subplots(1, len(seasons), sharey=True,
                             figsize=(max(7.5, 1.0 + 0.7 * len(seasons)), height))
    axes = np.atleast_1d(axes)
    for ax, s, lab in zip(axes, seasons, labels):
        g = df[df[season_col] == s].sort_values(x)
        ax.plot(g[x], g[y], color=BLACK, lw=0.9)
        ax.axhline(g[y].mean(), color=ORANGE, lw=1.6)
        ax.set_title(lab, size=9)
        ax.set_xticks([])
    axes[0].set_ylabel(y if ylabel is None else ylabel)
    fig.suptitle(title, size=12, x=0.02, ha="left")
    return fig, axes


def adjusted_plot(df, observed, adjusted, ax=None, title="", ylabel=""):
    """Observed series in grey with a derived version drawn over it.

    Used for seasonal adjustment, where the point is that the derived line is
    the same series with one component subtracted, not a different series.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 3.4))
    ax.plot(df["ds"], observed, color=GREY, lw=0.8, label="Observed")
    ax.plot(df["ds"], adjusted, color=ORANGE, lw=1.0, label="Seasonally adjusted")
    ax.set(title=title, ylabel=ylabel)
    ax.margins(x=0.01)
    ax.legend(frameon=False)
    return ax


def feature_scatter(feat, x="trend_strength", y="seasonal_strength", ax=None,
                    title="", marks=(), xlabel=None, ylabel=None):
    """One point per series in feature space, on the full [0, 1] square.

    Both axes are pinned to the full range on purpose. Autoscaling makes a
    feature that does not vary across the portfolio look like it separates the
    portfolio, which is the opposite of what these plots are used to show.

    ``marks`` is a sequence of ``(row, colour, label)``; each is drawn larger and
    labelled with a leader line into empty space, so no label sits on the cloud.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(9.5, 4.3))
    ax.scatter(feat[x], feat[y], s=26, color=BLUE, alpha=0.55)
    for off, (row, col, note) in zip(((-160, 26), (-160, -4), (-160, -34)), marks):
        ax.scatter([row[x]], [row[y]], s=130, color=col, zorder=3)
        ax.annotate(f"{note}\n{row['unique_id']}", (row[x], row[y]),
                    textcoords="offset points", xytext=off, size=9, color=col,
                    ha="left", va="center", zorder=4,
                    arrowprops=dict(arrowstyle="-", color=col, lw=1.0,
                                    shrinkA=2, shrinkB=7))
    ax.set(xlabel=xlabel or "Trend strength ($F_T$)",
           ylabel=ylabel or "Seasonal strength ($F_S$)",
           title=title, xlim=(0, 1.05), ylim=(0, 1.05))
    return ax


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
             color=BLACK, show_bounds=True, ylim=(-1.05, 1.05)):
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
    ax.set(title=title, xlabel="lag", ylabel="ACF", ylim=ylim)
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
              actual=None, history_tail=None, color=BLUE, mean_col="mean",
              figsize=(9, 4)):
    """Point forecast with nested prediction intervals.

    ``forecast`` needs columns ``ds``, ``mean_col`` and, per level L, ``lo-L``
    and ``hi-L``. ``actual`` (optional) overlays the truth so that whether the
    interval actually covered it is visible rather than asserted.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)
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


# --------------------------------------------------------------------------
# Prediction intervals: bootstrap and conformal
#
# The three ways this course draws an interval differ only in what they assume:
#   Gaussian    residuals uncorrelated, constant variance, AND normal
#   bootstrap   residuals uncorrelated and identically distributed (drop normal)
#   conformal   past h-step errors exchangeable with future ones (weaker still)
# The helpers below exist so a deck and a lab demonstrate that with the same code.
# --------------------------------------------------------------------------

def bootstrap_paths(y, resid, h, season_length=None, n_paths=1000, seed=0,
                    resid_tail=None, centre=True):
    """Simulate future sample paths by resampling past residuals.

    This is the residual bootstrap of fpppy 5.5. It assumes the residuals are
    uncorrelated and *identically distributed* -- one common distribution
    :math:`\hat{F}` whose characteristics do not change over time -- so that a
    future error can be drawn from the pool of past ones.

    ``season_length=None`` uses the naive recursion
    :math:`y^*_{T+i} = y^*_{T+i-1} + e^*`; an integer ``m`` uses the seasonal
    naive recursion :math:`y^*_{T+i} = y^*_{T+i-m} + e^*`, where the lag reaches
    into the observed history until the simulated path is long enough.

    ``resid_tail`` keeps only the last N residuals. That is the knob for the
    identically-distributed assumption: on a series whose error spread grows
    with its level, a shorter, more recent pool is the more honest one.

    Returns an ``(n_paths, h)`` array -- one simulated future per row.
    """
    y = np.asarray(y, dtype=float)
    e = np.asarray(pd.Series(resid).dropna(), dtype=float)
    if resid_tail:
        e = e[-resid_tail:]
    if centre:
        e = e - e.mean()
    rng = np.random.default_rng(seed)
    draws = rng.choice(e, size=(n_paths, h))

    paths = np.empty((n_paths, h), dtype=float)
    m = 1 if season_length is None else int(season_length)
    for i in range(h):
        base = y[len(y) - m + i] if i < m else paths[:, i - m]
        paths[:, i] = base + draws[:, i]
    return paths


def paths_to_fan(future_ds, paths, levels=(80, 95), mean_col="mean"):
    """Collapse simulated paths into the frame :func:`fan_chart` expects.

    The interval is the empirical percentile of the paths at each horizon, so --
    unlike a Gaussian interval -- it is free to be asymmetric.
    """
    paths = np.asarray(paths, dtype=float)
    out = {"ds": pd.Series(future_ds).to_numpy(), mean_col: paths.mean(axis=0)}
    for lvl in levels:
        alpha = (100 - lvl) / 200
        out[f"lo-{lvl}"] = np.quantile(paths, alpha, axis=0)
        out[f"hi-{lvl}"] = np.quantile(paths, 1 - alpha, axis=0)
    return pd.DataFrame(out)


def sim_paths_plot(history, future_ds, paths, ax=None, n_show=8, history_tail=48,
                   title="", actual=None, seed=0, figsize=(9, 4)):
    """Show a handful of individual simulated futures, not their envelope.

    Students meet the bootstrap as a shaded band and assume the band *is* the
    method. It is not: the method is these paths, and the band is a percentile
    taken down each column. Drawing a few of them makes that order of operations
    visible.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)
    paths = np.asarray(paths, dtype=float)
    hist = history.tail(history_tail) if history_tail else history
    future_ds = pd.Series(future_ds).to_numpy()

    ax.plot(hist["ds"], hist["y"], color=BLACK, lw=1.2, label="observed")
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(paths), size=min(n_show, len(paths)), replace=False)
    for j, idx in enumerate(pick):
        ax.plot(future_ds, paths[idx], lw=1.0, alpha=0.75, color=BLUE,
                label="simulated futures" if j == 0 else None)
    if actual is not None:
        ax.plot(actual["ds"], actual["y"], color=ORANGE, lw=1.4, ls="--",
                label="actual")
    ax.set(title=title, ylabel="y")
    ax.legend(loc="upper left", frameon=False, ncols=3)
    return ax


def h_step_error_diagram(history, errors, ax=None, title="", history_tail=None,
                         ylabel="y", annotate=True, figsize=(9, 4), xticks=None):
    """Draw the h-step errors :math:`e_{t+h|t} = y_{t+h} - \hat{y}_{t+h|t}`.

    ``errors`` needs one row per scored point with columns ``cutoff`` (the
    origin *t* the forecast was made from), ``ds`` (the target *t+h*), ``y`` and
    ``yhat``. Each error is drawn as the vertical gap between the two, so the
    calibration set conformal prediction quantifies is a thing on screen rather
    than a definition on a slide.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)
    hist = history.tail(history_tail) if history_tail else history
    ax.plot(hist["ds"], hist["y"], color=BLACK, lw=1.2, zorder=2, label="observed")

    for j, (_, row) in enumerate(errors.iterrows()):
        ax.axvline(row["cutoff"], color=GREY, lw=1.0, ls=":", zorder=1,
                   label="forecast origin $t$" if j == 0 else None)
        ax.plot([row["ds"], row["ds"]], [row["yhat"], row["y"]], color=ORANGE,
                lw=2.0, zorder=3,
                label=r"$e_{t+h|t}$" if j == 0 else None)
        ax.scatter([row["ds"]], [row["yhat"]], s=42, color=BLUE, zorder=4,
                   label=r"$\hat{y}_{t+h|t}$" if j == 0 else None)
        ax.scatter([row["ds"]], [row["y"]], s=42, color=BLACK, zorder=4,
                   label=r"$y_{t+h}$" if j == 0 else None)
        if annotate:
            ax.annotate(f"{row['y'] - row['yhat']:+.0f}",
                        (row["ds"], max(row["y"], row["yhat"])),
                        textcoords="offset points", xytext=(4, 4),
                        size=9, color=ORANGE)
    if xticks is not None:
        ax.set_xticks(list(xticks))
    ax.set(title=title, ylabel=ylabel)
    ax.legend(loc="upper left", frameon=False, ncols=3)
    return ax


def cv_staircase(n_obs=60, initial=36, horizon=6, step=6, ax=None,
                 n_folds=None, title="Rolling-origin cross-validation",
                 figsize=(9, 4)):
    """Draw the rolling-origin diagram: train block, scored block, unseen tail.

    Deliberately hand-drawn rather than shipped as a static image, so it can be
    revealed fold-by-fold (pass ``n_folds`` and emit one figure per fragment)
    and so the parameters on the slide are the ones used in the lab.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)
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
                lower_is_better=True, figsize=(6.2, 3.2), fmt="{:.3f}"):
    """Horizontal bars of one metric across models, best one highlighted."""
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)
    names = list(scores)
    vals = [scores[n] for n in names]
    best = (min if lower_is_better else max)(vals)
    colors = [ORANGE if (highlight_best and v == best) else BLUE for v in vals]
    ax.barh(names, vals, color=colors, height=0.62)
    for i, v in enumerate(vals):
        ax.text(v, i, " " + fmt.format(v), va="center", size=9)
    ax.set(title=title)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    return ax


# --------------------------------------------------------------------------
# Day 2: benchmarks, intervals and evaluation
#
# Every chart in decks 3 and 4 comes from below, and each one takes the objects
# the lab already has in hand -- a statsforecast forecast frame, a residual
# series, a dict of scores -- so a student can redraw any slide with one call.
# --------------------------------------------------------------------------

#: Two-sided normal multipliers, so a deck and a lab quote the same c.
NORMAL_Z = {50: 0.6745, 80: 1.2816, 90: 1.6449, 95: 1.9600, 99: 2.5758}

#: Colour order when several *models* share one pair of axes. Distinct from
#: SERIES_COLORS: black is reserved for the observed series underneath.
MODEL_COLORS = [PINK, GREEN, ORANGE, BLUE]


def forecast_overlay(history, forecast, models, labels=None, colors=None,
                     actual=None, history_tail=72, ax=None, figsize=(10, 4.6),
                     title="", ylabel="y", ncols=3, lw=1.7,
                     history_label="observed", actual_label="actual holdout"):
    """Several point forecasts drawn over the history that produced them.

    ``forecast`` is a statsforecast-shaped frame: ``ds`` plus one column per
    model in ``models``. ``labels`` renames them for the legend, which is where
    a score belongs when the point of the slide is which forecast won.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)
    labels = dict(labels or {})
    palette = list(colors) if colors is not None else MODEL_COLORS
    hist = history.tail(history_tail) if history_tail else history
    ax.plot(hist["ds"], hist["y"], color=BLACK, lw=1.1, label=history_label)
    if actual is not None:
        ax.plot(actual["ds"], actual["y"], color=GREY, lw=1.4, ls="--",
                label=actual_label)
    for i, m in enumerate(models):
        ax.plot(forecast["ds"], forecast[m], lw=lw,
                color=palette[i % len(palette)], label=labels.get(m, m))
    ax.set(title=title, ylabel=ylabel)
    ax.legend(frameon=False, ncols=ncols)
    return ax


def interval_width_plot(forecast, model="SeasonalNaive", models=(), labels=None,
                        season_length=12, level=80, colors=None,
                        figsize=(9.5, 3.7), titles=None):
    r"""Interval width against horizon, against both candidate growth laws.

    Left: one model's width with the :math:`\sqrt{k+1}` staircase it should
    follow and the :math:`\sqrt{h}` curve it should not, so a reader can see
    which one the data tracks instead of being told. Right: the same width for
    several models, where the shapes separate.
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    width = (forecast[f"{model}-hi-{level}"]
             - forecast[f"{model}-lo-{level}"]).to_numpy()
    h = np.arange(1, len(width) + 1)
    k = (h - 1) // season_length
    t = tuple(titles) if titles else (
        f"{model}: a staircase, not a curve", "Width growth by benchmark")

    axes[0].plot(h, width, color=BLUE, lw=4.5, alpha=0.55, label="actual width")
    axes[0].plot(h, width[0] * np.sqrt(k + 1), color=GREEN, lw=2.0,
                 dashes=(6, 4), label=r"$\sqrt{k+1}$ (correct)")
    axes[0].plot(h, width[0] * np.sqrt(h), color=ORANGE, lw=1.4, ls=":",
                 label=r"$\sqrt{h}$ (wrong method)")
    axes[0].set(xlabel="horizon h", ylabel=f"{level}% interval width", title=t[0])
    axes[0].legend(frameon=False)

    labels = dict(labels or {})
    palette = list(colors) if colors is not None else [GREEN, BLUE, PINK, ORANGE]
    for i, m in enumerate(models):
        w = forecast[f"{m}-hi-{level}"] - forecast[f"{m}-lo-{level}"]
        axes[1].plot(h, w, color=palette[i % len(palette)], lw=1.8,
                     label=labels.get(m, m))
    axes[1].set(xlabel="horizon h", title=t[1])
    axes[1].legend(frameon=False)
    fig.tight_layout()
    return fig, axes


def residual_assumption_plot(resid, ds=None, window=36, level=80, bins=45,
                             figsize=(9.5, 3.1), titles=None):
    r"""Two of the Gaussian interval's three assumptions, tested on one figure.

    Left: a rolling SD against the pooled :math:`\hat{\sigma}` -- constant
    variance? Right: the residual histogram against a normal of the *same* SD,
    with the empirical and the normal central-``level``% cut points drawn on
    top -- normal? Where the two pairs of lines disagree is the error the
    closed-form interval makes.
    """
    r = np.asarray(pd.Series(resid).dropna(), dtype=float)
    sd = float(r.std(ddof=1))
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    t = tuple(titles) if titles else (
        f"Rolling {window}-month residual SD",
        f"Central {level}%: empirical (blue) vs normal (orange)")

    x = pd.Series(ds).to_numpy()[-len(r):] if ds is not None else np.arange(len(r))
    axes[0].plot(x, pd.Series(r).rolling(window).std().to_numpy(),
                 color=ORANGE, lw=2)
    axes[0].axhline(sd, color=BLACK, ls="--", lw=1.3,
                    label=f"pooled sigma-hat = {sd:.1f}")
    axes[0].set(title=t[0], ylabel="SD")
    axes[0].legend(frameon=False)

    axes[1].hist(r, bins=bins, density=True, color=GREY, alpha=0.7)
    grid = np.linspace(r.min(), r.max(), 300)
    axes[1].plot(grid, np.exp(-0.5 * (grid / sd) ** 2) / (sd * np.sqrt(2 * np.pi)),
                 color=BLACK, lw=1.6, label="normal, same SD")
    tail = (1 - level / 100) / 2
    for v in np.quantile(r, [tail, 1 - tail]):
        axes[1].axvline(v, color=BLUE, lw=1.6)
    for v in NORMAL_Z[level] * sd * np.array([-1.0, 1.0]):
        axes[1].axvline(v, color=ORANGE, ls="--", lw=1.6)
    axes[1].set(title=t[1], xlabel="residual")
    axes[1].legend(frameon=False)
    fig.tight_layout()
    return fig, axes


def fan_chart_panels(history, fans, titles=(), levels=(80, 95), actual=None,
                     history_tail=36, figsize=(10, 3.3), colors=None,
                     mean_col="mean", sharey=True):
    """The same history and horizon under two or more interval methods.

    ``fans`` is a list of fan-shaped frames (``ds`` / ``mean_col`` / ``lo-L`` /
    ``hi-L``). Panels share a y axis by default, because the comparison the
    slide is making is of *width* and that only reads if the scales match.
    """
    fans = list(fans)
    fig, axes = plt.subplots(1, len(fans), figsize=figsize, sharey=sharey)
    axes = np.atleast_1d(axes)
    titles = list(titles) + [""] * (len(fans) - len(titles))
    palette = list(colors) if colors is not None else [BLUE] * len(fans)
    for ax, fan, title, color in zip(axes, fans, titles, palette):
        fan_chart(history, fan, levels=levels, ax=ax, actual=actual,
                  history_tail=history_tail, title=title, color=color,
                  mean_col=mean_col)
    fig.tight_layout()
    return fig, axes


def interval_bounds_plot(history, forecast_ds, bands, actual=None,
                         history_tail=24, level=80, colors=None,
                         figsize=(10, 3.6), titles=None, year_step=1):
    """Several interval methods as bare bounds, plus their widths by horizon.

    ``bands`` maps a method name to ``(lo, hi)``. The left panel puts the bounds
    on one time axis; the right turns each pair into width against horizon,
    which is where a staircase, a narrow band and a jittery one separate.
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    palette = list(colors) if colors is not None else [ORANGE, GREEN, BLUE, PINK]
    hist = history.tail(history_tail) if history_tail else history
    axes[0].plot(hist["ds"], hist["y"], color=BLACK, lw=1.2, label="observed")
    if actual is not None:
        axes[0].plot(actual["ds"], actual["y"], color=GREY, lw=1.4, ls="--",
                     label="actual")
    for i, (name, (lo, hi)) in enumerate(bands.items()):
        color = palette[i % len(palette)]
        lo, hi = np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
        axes[0].plot(forecast_ds, lo, color=color, lw=1.6, label=f"{name} {level}%")
        axes[0].plot(forecast_ds, hi, color=color, lw=1.6)
        axes[1].plot(np.arange(1, len(lo) + 1), hi - lo, color=color, lw=2,
                     label=name)
    t = tuple(titles) if titles else (
        f"{level}% bounds, same point forecast",
        "Staircase, narrow, and jittery")
    axes[0].set(title=t[0])
    axes[0].legend(frameon=False, ncols=2, fontsize=8)
    year_xticks([axes[0]], step=year_step)
    axes[1].set(xlabel="horizon h", ylabel=f"{level}% width", title=t[1])
    axes[1].legend(frameon=False)
    fig.tight_layout()
    return fig, axes


def single_vs_cv_plot(single, folds, labels=None, figsize=(10, 3.5),
                      ylabel="MASE", ylim=None, titles=None, log_right=True):
    """One holdout's scores against the mean of many folds, and the spread.

    ``single`` maps model -> score on one window; ``folds`` is a frame with one
    column per model and one row per fold. The left panel is the ranking
    question, the right is why one window could not have answered it.
    """
    models = list(folds.columns)
    labels = dict(labels or {})
    names = [labels.get(m, m) for m in models]
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    t = tuple(titles) if titles else (
        "Stable ranking, except at the top", "Score distribution across folds")

    x = np.arange(len(models))
    one = np.array([float(single[m]) for m in models])
    many = np.array([float(folds[m].mean()) for m in models])
    axes[0].bar(x - 0.2, one, width=0.4, color=GREY, label="single split")
    axes[0].bar(x + 0.2, many, width=0.4, color=BLUE,
                label=f"mean of {len(folds)} folds")
    axes[0].set_xticks(x, names, rotation=20, ha="right")
    axes[0].set(ylabel=ylabel, title=t[0], **({"ylim": ylim} if ylim else {}))
    axes[0].legend(frameon=False, loc="upper center")
    span = max(one.max(), many.max())
    for xi, (a, b) in enumerate(zip(one, many)):
        axes[0].text(xi - 0.2, a + span * 0.02, f"{a:.2f}", ha="center", size=8,
                     color=BLACK)
        axes[0].text(xi + 0.2, b + span * 0.02, f"{b:.2f}", ha="center", size=8,
                     color=BLUE)

    for i, m in enumerate(models):
        axes[1].scatter(np.full(len(folds), i), folds[m], s=40, color=ORANGE,
                        alpha=0.75, zorder=3)
    axes[1].set_xticks(range(len(models)), names, rotation=20, ha="right")
    axes[1].set(ylabel=ylabel, title=t[1])
    if log_right:
        axes[1].set_yscale("log")
    fig.tight_layout()
    return fig, axes


def coverage_bars(coverage, nominal=0.8, labels=None, ax=None, figsize=(9, 3.4),
                  title="", tolerance=0.1):
    """Measured coverage per model against the nominal rate it claims.

    Bars within ``tolerance`` of ``nominal`` are blue, the rest orange: the
    slide's claim is honest-or-not, so the colour carries it and the reader does
    not have to compare bar ends to a dashed line by eye.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)
    labels = dict(labels or {})
    names = [labels.get(m, m) for m in coverage]
    vals = [float(v) for v in coverage.values()]
    colors = [BLUE if abs(v - nominal) < tolerance else ORANGE for v in vals]
    ax.barh(names, vals, color=colors, height=0.6)
    ax.axvline(nominal, color=BLACK, ls="--", lw=1.4)
    ax.text(nominal, -0.75, f" nominal {nominal:.0%}", size=10)
    for i, v in enumerate(vals):
        ax.text(v, i, f" {v:.0%}", va="center", size=10)
    ax.set(xlim=(0, 1.05), title=title)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    return ax


def width_vs_crps_plot(width, crps, coverage=None, labels=None,
                       figsize=(10, 3.4), titles=None, level=80):
    """Sharpness beside a proper score, so narrow-but-wrong is visible.

    Left: mean interval width per model, annotated with the coverage it bought.
    Right: scaled CRPS, best highlighted. A model can win the left panel and
    lose the right, which is the whole reason a proper score exists.
    """
    models = list(crps)
    labels = dict(labels or {})
    names = [labels.get(m, m) for m in models]
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    t = tuple(titles) if titles else (
        f"Mean {level}% interval width", "Scaled CRPS (lower is better)")

    widths = [float(width[m]) for m in models]
    axes[0].barh(names, widths, color=GREY, height=0.6)
    if coverage is not None:
        for i, m in enumerate(models):
            axes[0].text(widths[i], i, f"  {coverage[m]:.0%} cov", va="center",
                         size=9)
    axes[0].set(title=t[0], xlim=(0, max(widths) * 1.35))
    axes[0].invert_yaxis()
    axes[0].grid(axis="y", visible=False)

    metric_bars({n: float(crps[m]) for n, m in zip(names, models)}, ax=axes[1],
                title=t[1])
    axes[1].set(xlim=(0, max(float(crps[m]) for m in models) * 1.35))
    fig.tight_layout()
    return fig, axes
