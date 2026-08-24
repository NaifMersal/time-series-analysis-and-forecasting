"""The specific series this course teaches on, in the book's long layout.

Every deck and every notebook pulls its data through here, so "the spine" means
exactly one thing across all three days and a chart on a slide is drawn from
the same rows the students hold.

Long layout throughout: ``unique_id`` / ``ds`` / ``y`` -- the nixtlaverse
convention fpppy uses.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import fppdata as fd

#: The course spine. Monthly, m=12, 1982-04 to 2018-12, no gaps, with variance
#: that grows with the level -- so Box-Cox earns its place on Day 1.
SPINE_STATE = "Victoria"
SPINE_INDUSTRY = "Takeaway food services"
#: Must match how retail_all() builds unique_id, so the spine can be
#: located inside the 148-series sweep on Day 1.
SPINE_ID = f"{SPINE_STATE} / {SPINE_INDUSTRY}"
SEASON_LENGTH = 12
FREQ = "MS"


def _long(df, ds, y, uid):
    return (
        df.rename(columns={ds: "ds", y: "y"})
        .assign(unique_id=uid)[["unique_id", "ds", "y"]]
        .dropna(subset=["y"])
        .sort_values("ds")
        .reset_index(drop=True)
    )


def spine() -> pd.DataFrame:
    """The course spine: Victorian takeaway-food turnover, monthly."""
    retail = fd.load("aus_retail")
    sel = retail[(retail["State"] == SPINE_STATE)
                 & (retail["Industry"] == SPINE_INDUSTRY)]
    return _long(sel, "Month", "Turnover", SPINE_ID)


def retail_all(min_obs: int = 240) -> pd.DataFrame:
    """Every aus_retail series, long. Used for the Day 1 feature sweep.

    ``min_obs`` drops the short series so trend/seasonal strength is
    comparable across what remains.
    """
    retail = fd.load("aus_retail").copy()
    retail["unique_id"] = retail["State"] + " / " + retail["Industry"]
    out = (
        retail.rename(columns={"Month": "ds", "Turnover": "y"})[
            ["unique_id", "ds", "y"]
        ]
        .dropna(subset=["y"])
        .sort_values(["unique_id", "ds"])
        .reset_index(drop=True)
    )
    keep = out.groupby("unique_id")["y"].transform("size") >= min_obs
    return out[keep].reset_index(drop=True)


def beer() -> pd.DataFrame:
    """Quarterly Australian beer production -- textbook seasonality, m=4."""
    return _long(fd.load("aus_production")[["Quarter", "Beer"]],
                 "Quarter", "Beer", "Australian beer production")


def lynx() -> pd.DataFrame:
    """Canadian lynx pelts, annual.

    The course's only honest *cycle*: big rises and falls at no fixed period.
    Retail data cannot show this, which is why this series is here.
    """
    df = fd.load("pelt")[["Year", "Lynx"]].copy()
    df["Year"] = pd.to_datetime(df["Year"].astype(int).astype(str) + "-01-01")
    return _long(df, "Year", "Lynx", "Canadian lynx pelts")


def souvenirs() -> pd.DataFrame:
    """Monthly souvenir-shop sales -- violently multiplicative seasonality."""
    return _long(fd.load("souvenirs"), "Month", "Sales", "Souvenir shop sales")


def canadian_gas() -> pd.DataFrame:
    """Monthly Canadian gas production -- seasonal shape that changes over time."""
    return _long(fd.load("canadian_gas"), "Month", "Volume",
                 "Canadian gas production")


def white_noise(n: int = 200, seed: int = 1, start: str = "1990-01-01",
                freq: str = FREQ) -> pd.DataFrame:
    """Pure white noise -- the null case for every diagnostic in the course."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "unique_id": "White noise",
        "ds": pd.date_range(start, periods=n, freq=freq),
        "y": rng.normal(size=n),
    })


def add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``year`` / ``month`` / ``quarter`` for seasonal and subseries plots."""
    out = df.copy()
    out["year"] = out["ds"].dt.year
    out["month"] = out["ds"].dt.month
    out["quarter"] = out["ds"].dt.quarter
    return out


def train_test(df: pd.DataFrame, h: int = 24):
    """Split off the final ``h`` observations. Never shuffle -- see Day 1."""
    return df.iloc[:-h].copy(), df.iloc[-h:].copy()
