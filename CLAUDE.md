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

# lint the decks for what a screenshot cannot show (em dashes, banned words,
# over-long bullets, inline matplotlib). ERROR fails; --strict fails WARN too.
.venv/Scripts/python.exe .claude/skills/author-verify-slides/lint.py slides/*.qmd

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

**Each deck is taught straight through, then its lab block.** A day is two
lecture → lab cycles, one per deck — not five interleaved ones. The four blocks are
Lab A (Ex 1.1–1.2, 25 min), Lab B (1.3–1.5, 45), Lab C (2.1–2.3, 46), Lab D (2.4–2.5, 29).

The single slide titled `→ Lab X · <name>` at the end of each deck, just before its
Recap/Summary slide, is the pacing marker. It lists exercise number, title and minutes in
a table and says nothing else — **do not re-bullet the concepts there.** That restatement
is what the interleaved `→ Exercise N.M` slides used to do, and removing it is the point:
a concept should be taught once on the slides and once in the notebook, not three times.
Keep the table in step with the notebook's `# Lab X` banner and its exercise headers.

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

## Day 3 — settled: ETS, then AutoGluon

Day 3 is taught on **Google Colab** (torch preinstalled, network always available).
The arc is *transparent → orchestrated → the map*, ~70/30 basics-to-black-box:
when students build with a black-box tool, the mental model they bring is the one
this course built. Two decks, two lab blocks, ~5 exercises — fits three hours.

**Deck 3 — ETS (Ch 8), the deep one.** State-space intuition, Box-Cox (spine
λ ≈ 0.074), framed as the Day 2 STL+drift route with the weights learned instead of
pinned. statsforecast ETS emits native quantiles, so it lands on the Day 2
CRPS/coverage leaderboard with no extra plumbing. Lab: fit, 8 rolling folds,
CRPS/coverage, add to the leaderboard.

**AutoARIMA** (optional exercise, ~3 lines in statsforecast) closes the Day 2
white-noise hook (seasonal naive residuals, Ljung-Box p ≈ 1e-240).

**Deck 4 — AutoGluon TimeSeries, hands-on.** `autogluon[timeseries]` goes into
`labs/00_pre_work.ipynb` (light install on Colab; warn students a runtime reset
wipes installs — re-run setup). Pin it to the local zoo only (Naive / SeasonalNaive
/ Drift / ETS / AutoARIMA / Theta) with `time_limit` ≈ 120 s, and set its
`leaderboard()` next to the course's. Punchline: "You've now seen every line this
library runs — in industry you hand this step to a framework."

**Capstone.** A student adds a model of their choosing to the leaderboard — a few
lines, the same path as every other model. This is the "you can now build" beat.

**The rest of the field is listed, not taught** — one line each on a closing slide:
Theta (simple, strong, already in AutoGluon's zoo); dynamic regression (Ch 7+10,
for when exogenous data exists); lag-feature ML (LightGBM / `mlforecast`, tabular
framing — fpppy has no chapter for it); neural nets (DeepAR / Transformer, global,
data-hungry); foundation models (Chronos / Moirai / TimeGPT, zero-shot — on Colab
use the small models, Chronos-Bolt-small / Moirai-small, on CPU; TimeGPT needs an
API key, Moirai needs HF weights); ensembles (AutoGluon's WeightedEnsemble is the
example).

Constraints that survive this decision:

- Whatever is chosen plugs into the Day 2 harness and appends to
  `labs/leaderboard.csv` via `coursekit.leaderboard.record(...)` — `mase`, `rmsse`,
  `crps`, `coverage_80`. Adding a model should stay a few lines.
- Ch 10 *is* Ch 7 + Ch 9, so if dynamic regression gets class time, Ch 7 travels
  with it.
- The pin-drift rule stands: no Day 3 model may leak into Day 2 content.
- `coursekit/data/` stays committed (offline insurance) even though Colab has
  network.

Why AutoGluon is not the centerpiece: it is a parallel API universe (own data
format, own fit loop, own leaderboard with sign-flipped metrics) whose local-model
zoo is a subset of what statsforecast already teaches. On a laptop it also costs a
~2.5 GB torch install — on Colab that cost is sunk, which is what lets it earn the
"orchestrated layer" slot after ETS without replacing the harness.
