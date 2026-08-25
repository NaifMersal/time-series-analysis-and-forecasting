# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this repo is

Instructor repo for the SDAIA **Time Series Analysis & Forecasting** course — three days,
three hours a day. It holds Quarto reveal.js slide sources (`.qmd`), Jupyter lab
notebooks, and `coursekit`, the shared helper package both of those import from.

The main reference is [*Forecasting: Principles and Practice, the Pythonic Way*](https://otexts.com/fpppy/)
(fpppy). The stack is the nixtlaverse — `statsforecast`, `utilsforecast`, `coreforecast` —
plus `statsmodels` for STL, ACF and Ljung-Box.

**Days 1 and 2 are built. Day 3 is an open decision** — see the bottom of this file.

`notes/day1_readiness.md` is the brief for the Day 1 delivery-readiness pass: the goal,
the pass/fail criteria, the review protocol, and the definition of done. Read it before
editing Day 1 slides or labs. `notes/` is gitignored on purpose, so working documents
there stay out of the diff.

## Common commands

```bash
uv sync --extra dev                                   # install; coursekit goes in editable
.venv/Scripts/python.exe scripts/check_env.py         # the pre-work gate students run
.venv/Scripts/python.exe scripts/prefetch_data.py     # cache datasets (needs network once)

quarto render                                         # all decks + index -> output/
quarto preview slides/02_acf_decomposition_and_features.qmd

.venv/Scripts/python.exe scripts/build_labs.py        # regenerate ALL notebooks

# render a deck and screenshot slides so you can look at them
.venv/Scripts/python.exe .claude/skills/author-verify-slides/driver.py \
    slides/03_benchmarks_residuals_and_intervals.qmd --slides 0,4,8

.venv/Scripts/python.exe .claude/skills/check-labs/driver.py all         # student copies
.venv/Scripts/python.exe .claude/skills/check-labs/driver.py solutions   # answer keys
```

Always use `.venv/Scripts/python.exe` (Windows) — a bare `python` will not see `coursekit`.
Quarto is pinned to it by the project-root `_environment` file (`QUARTO_PYTHON=.venv/Scripts/python.exe`);
without that pin Quarto grabs the first python on PATH and its decks die on missing deps.

There are no tests beyond the two skill drivers. `check-labs` is the test suite.

## Layout

```
slides/          01..04_*.qmd -- flat, numeric prefixes carry the order
  assets/        image_prompts.md (manifest; no images yet, by design)
labs/            00_setup.md, 00_pre_work.ipynb, 01_day1_*.ipynb, 02_day2_*.ipynb
                 reference_cheatsheet.md, leaderboard.csv (generated)
  solutions/     answer keys -- same notebooks, TODOs filled
coursekit/       the shared package (installed editable)
  fppdata.py     downloads + caches the FPP3 .rda datasets
  datasets.py    the specific series this course teaches on
  plotting.py    every chart in the decks AND the labs
  leaderboard.py the running scoreboard
  checks.py      the check_ex_* assertions the labs call
  data/          cached .rda files -- COMMITTED so the course runs offline
scripts/         check_env.py, prefetch_data.py, build_labs.py
slides_template/ SDAIA branding, from the author-verify-slides skill bundle
exercises/       03-decomposition.ipynb -- pre-existing Ch-3 worked exercises, kept as
                 instructor reference; not part of the taught course
```

No `tracks.yml`, no module directories, no index generator, no student-dist pipeline.
`index.qmd` is hand-written; update it when you add a deck.

## Conventions that matter

**Long format everywhere.** `unique_id` / `ds` / `y`, the layout fpppy and the nixtlaverse
use. `coursekit.datasets` returns it; do not invent a wide variant.

**One spine.** `D.spine()` — Victorian takeaway-food turnover, monthly, 441 obs, m=12, no
gaps. Days 1 and 2 both teach on it, and Day 3 will. `D.SPINE_ID` matches how
`D.retail_all()` builds `unique_id`, so the spine can be found inside the 148-series
sweep; keep that true.

**Slides and labs share their plotting code.** Every chart in a deck comes from
`coursekit.plotting`, which the labs import too. That is deliberate: a slide cannot drift
from what students run. Add a chart helper there, not inline in a deck.

**Notebooks are generated, never hand-edited.** `scripts/build_labs.py` defines each
exercise once, with the student body and the solution body side by side, and emits both
copies. Edit the generator and re-run it. Hand-edits are lost on the next build.

Two traps in that generator: cell bodies are triple-quoted strings, so an escape meant for
the *notebook* needs doubling (`\\n`), and a TODO is written as the literal `...`, which
`coursekit.checks._not_todo` turns into a readable message.

**The two check-labs targets have opposite healthy states.** Student copies should report
`EXERCISES-INCOMPLETE`; `solutions` should report `OK`. A student copy reporting `OK` means
an answer leaked.

**Every concept is followed by an exercise.** Each day is five concept → exercise cycles,
not two lectures and a lab. Deck slides titled `→ Exercise N.M` are the pacing markers;
keep them in step with the notebook's section headers.

### Slides

Branding is global in `_quarto.yml`. Deck front matter is only
`title` / `subtitle` / `date` / `format: revealjs` — never re-declare `theme` or `logo`.
Section dividers cycle **teal → coral → purple**, starting teal; content dark slides are
always navy→purple. See `.claude/skills/author-verify-slides/reference/patterns.md`.

`_quarto.yml` sets `execute-dir: project` (so `{python}` cells can import `coursekit`) and
`freeze: auto` (so untouched decks do not re-execute). Both are load-bearing.

**Visual policy.** Data-driven visuals are executable `{python}` cells; conceptual flows
are `{dot}` or `{mermaid}` with literal hex colours; illustrative imagery is recorded in
`slides/assets/image_prompts.md` first. Never use a static image for something a `{python}`
cell could draw.

**`{python}` executes; `{.python}` only highlights.** Confusing them is the most common
render failure. Code is hidden by default — add `#| echo: true` to show it.

**Screenshot before believing a slide.** An executed cell can render a chart that is
correct and still illegible at projector size. Several slides in this repo were rewritten
because their prose claimed something the rendered figure did not show.

## Facts about the data worth not rediscovering

- Spine: 441 months, 1982-04 to 2018-12, no gaps, Box-Cox λ ≈ 0.074.
- `retail_all()` gives 148 series after the `min_obs` filter. Nearly all have trend
  strength > 0.96 — trend does not discriminate in retail; seasonality does.
- Seasonal naive is the clear winner among the benchmarks: MASE ≈ 1.18 over 8 rolling
  folds, versus 2.80 (naive), 3.10 (drift), 12.25 (mean).
- Day 2 also teaches **Ch 5.7's decomposition route** as a fifth model:
  `MSTL(season_length=12, trend_forecaster=RandomWalkWithDrift())`. The default
  `trend_forecaster` is `AutoETS` — the course pins drift on purpose, so no Day 3 model
  leaks into Day 2.
- **That fifth model reverses between one window and eight, and the reversal is the
  lesson.** On the single 24-month holdout it beats the seasonal naive on MASE, 0.70 to
  1.11; over 8 rolling folds it loses, 1.22 to 1.18. Exercises 2.1 and 2.4 set the trap
  and 2.5 springs it, `check_ex_2_4` asserts the STL route wins the window and
  `check_ex_2_5` asserts the seasonal naive wins the folds. Do not "fix" either.
- 8-fold scaled CRPS: 0.031 (seasonal naive), 0.034 (STL + drift), 0.081 (naive),
  0.090 (drift), 0.348 (mean). The STL route earns its worse CRPS with the *narrowest*
  intervals (40 units against 49) and worse coverage (61% against 77%) — that contrast
  is the whole Ch 5.9 point, coverage checks a band but cannot rank.
- Day 2 forecasts and cross-validation ask for `LEVELS = [20, 40, 60, 80, 95]`, so
  `scaled_crps` has a quantile ladder to integrate over. Coverage is still read off
  `lo-80` / `hi-80`.
- The seasonal naive's residuals are emphatically not white noise (Ljung-Box p ≈ 1e-240) — the floor leaves
  a lot on the table, which is the opening for Day 3.
- 80% interval coverage: 77% for seasonal naive over 8 folds, but **96% on a single
  24-month window**. That gap is taught deliberately — one window cannot measure a rate.
- `RandomWalkWithDrift` appears in statsforecast output as the column `RWD`.
- `STL` needs `period=` explicitly on a plain array, and returns numpy arrays (not Series)
  when fed one.

## Day 3 — open decision

Which of ETS (Ch 8), ARIMA (Ch 9), dynamic regression (Ch 7 + 10), and neural / foundation
models (Ch 14, 15) get class time, and at what depth. Three hours holds roughly five
concept → exercise cycles, which is not enough for all four taught properly.

Constraints to carry into that decision:

- fpppy has **no** chapter on lag-feature ML (LightGBM / `mlforecast`); Ch 14 is neural
  networks only.
- Ch 15's examples need a **TimeGPT API key** or a **HuggingFace weights download**
  (Moirai). Never run either live on a room full of laptops — pre-compute forecasts to CSV
  and demo from the instructor machine.
- `neuralforecast` pulls ~2.5 GB of torch, which is why no `[neural]` / `[foundation]`
  extras exist in `pyproject.toml` yet.
- Ch 10 *is* Ch 7 + Ch 9, so if dynamic regression is in, Ch 7 travels with it.

Whatever is chosen plugs into the Day 2 harness and appends to `labs/leaderboard.csv` via
`coursekit.leaderboard.record(...)` — `mase`, `rmsse`, `crps`, `coverage_80`. Adding a
model should stay a few lines.
