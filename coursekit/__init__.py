"""Shared helpers for the SDAIA Time Series Analysis & Forecasting course.

Both the Quarto decks (`slides/*.qmd`) and the lab notebooks (`labs/*.ipynb`)
import from here, so a chart on a slide is drawn by exactly the same code the
students run. That is the point: the slides cannot drift from the labs.

    from coursekit import fppdata as fd
    from coursekit.plotting import use_course_style, acf_plot
"""

from . import datasets, fppdata, leaderboard, plotting

__all__ = ["datasets", "fppdata", "leaderboard", "plotting"]
