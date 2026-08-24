"""Loader for the FPP3 / fpppy example datasets.

The book (https://otexts.com/fpppy/) reads its data from a local ``data/``
folder that is not distributed with the online text.  The same series live in
the R packages ``tsibbledata``, ``tsibble`` and ``fpp3``, so this module
downloads the ``.rda`` files once, caches them under ``exercises/data/`` and
converts the R date/time indices into pandas datetimes.

Usage
-----
>>> from fppdata import load
>>> aus_production = load("aus_production")

Requires ``pyreadr`` (``pip install pyreadr``).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

_TSIBBLEDATA = "https://raw.githubusercontent.com/tidyverts/tsibbledata/master/data/{}.rda"
_TSIBBLE = "https://raw.githubusercontent.com/tidyverts/tsibble/main/data/{}.rda"
_FPP3 = "https://raw.githubusercontent.com/robjhyndman/fpp3-package/master/data/{}.rda"
_FMA = "https://raw.githubusercontent.com/robjhyndman/fma/master/data/{}.rda"

SOURCES = {
    "ansett": _TSIBBLEDATA,
    "aus_livestock": _TSIBBLEDATA,
    "aus_production": _TSIBBLEDATA,
    "aus_retail": _TSIBBLEDATA,
    "gafa_stock": _TSIBBLEDATA,
    "global_economy": _TSIBBLEDATA,
    "hh_budget": _TSIBBLEDATA,
    "nyc_bikes": _TSIBBLEDATA,
    "olympic_running": _TSIBBLEDATA,
    "pelt": _TSIBBLEDATA,
    "PBS": _TSIBBLEDATA,
    "vic_elec": _TSIBBLEDATA,
    "pedestrian": _TSIBBLE,
    "tourism": _TSIBBLE,
    "canadian_gas": _FPP3,
    "us_employment": _FPP3,
    "us_change": _FPP3,
    "us_gasoline": _FPP3,
    "aus_airpassengers": _FPP3,
    "aus_arrivals": _FPP3,
    "souvenirs": _FPP3,
    "insurance": _FPP3,
    "prices": _FPP3,
    "boston_marathon": _FPP3,
    "bank_calls": _FPP3,
    # Australian civilian labour force, monthly Feb 1978 - Aug 1995 (Fig. 3.15/3.16).
    "labour": _FMA,
}

# Columns holding an R ``yearquarter``/``yearmonth``/``yearweek``/``Date``
# index, which pyreadr hands back as "days since 1970-01-01".
_DAY_INDEX_COLS = {
    "ansett": ["Week"],
    "aus_livestock": ["Month"],
    "aus_production": ["Quarter"],
    "aus_retail": ["Month"],
    "canadian_gas": ["Month"],
    "us_employment": ["Month"],
    "us_gasoline": ["Week"],
    "souvenirs": ["Month"],
    "aus_airpassengers": ["Year"],
    "pedestrian": ["Date"],
    "vic_elec": ["Date"],
    "gafa_stock": ["Date"],
    "nyc_bikes": ["start_time", "stop_time"],
}

# Columns holding a POSIXct stamp that R stored in a local timezone.
_TZ_COLS = {
    "vic_elec": ("Time", "Australia/Melbourne"),
    "pedestrian": ("Date_Time", "Australia/Melbourne"),
}

_EPOCH = pd.Timestamp("1970-01-01")


def _download(name: str) -> Path:
    if name not in SOURCES:
        raise KeyError(f"unknown dataset {name!r}; known: {sorted(SOURCES)}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.rda"
    if not path.exists():
        url = SOURCES[name].format(name)
        print(f"downloading {name} from {url}")
        urllib.request.urlretrieve(url, path)
    return path


def load(name: str) -> pd.DataFrame:
    """Return dataset ``name`` as a tidy pandas DataFrame."""
    import pyreadr  # imported lazily so the module can be inspected without it

    path = _download(name)
    result = pyreadr.read_r(path)
    df = next(iter(result.values())).copy()

    for col in _DAY_INDEX_COLS.get(name, []):
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            df[col] = _EPOCH + pd.to_timedelta(df[col], unit="D")

    if name in _TZ_COLS:
        col, tz = _TZ_COLS[name]
        df[col] = df[col].dt.tz_localize("UTC").dt.tz_convert(tz).dt.tz_localize(None)

    for col in df.columns:
        if isinstance(df[col].dtype, pd.CategoricalDtype):
            df[col] = df[col].astype("object")

    if name == "aus_airpassengers":
        df["Year"] = df["Year"].dt.year

    if name == "global_economy":
        df["Year"] = df["Year"].astype(int)

    if name == "labour":
        # An R ``ts`` object: pyreadr drops the index, so rebuild it.
        df.insert(0, "Month", pd.date_range("1978-02-01", periods=len(df), freq="MS"))
        df = df.rename(columns={"labour": "Persons"})

    return df.reset_index(drop=True)


def to_nixtla(
    df: pd.DataFrame,
    time_col: str,
    value_col: str,
    id_cols: str | list[str] | None = None,
    id_name: str | None = None,
) -> pd.DataFrame:
    """Reshape to the ``unique_id`` / ``ds`` / ``y`` layout used by the book.

    ``id_cols`` are joined with ``" / "`` to build ``unique_id``; pass
    ``id_name`` instead to label a single-series frame.
    """
    out = df.copy()
    if id_cols is None:
        out["unique_id"] = id_name if id_name is not None else value_col
    else:
        if isinstance(id_cols, str):
            id_cols = [id_cols]
        out["unique_id"] = (
            out[id_cols].astype(str).agg(" / ".join, axis=1) if len(id_cols) > 1
            else out[id_cols[0]].astype(str)
        )
    out = out.rename(columns={time_col: "ds", value_col: "y"})
    return (
        out[["unique_id", "ds", "y"]]
        .sort_values(["unique_id", "ds"])
        .reset_index(drop=True)
    )


def wide_to_nixtla(df: pd.DataFrame, time_col: str) -> pd.DataFrame:
    """Melt a wide frame (one column per series) into ``unique_id``/``ds``/``y``."""
    return (
        df.melt(id_vars=time_col, var_name="unique_id", value_name="y")
        .rename(columns={time_col: "ds"})
        .sort_values(["unique_id", "ds"])
        .reset_index(drop=True)
    )
