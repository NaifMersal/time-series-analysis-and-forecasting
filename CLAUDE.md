# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this repo is

Instructor repo for the SDAIA **Time Series Analysis & Forecasting** course — three days,
three hours a day. It holds Quarto reveal.js slide sources (`.qmd`), Jupyter lab
notebooks, and `coursekit`, the shared helper package both of those import from.

The main reference is [*Forecasting: Principles and Practice, the Pythonic Way*](https://otexts.com/fpppy/)
(fpppy). The stack is the nixtlaverse — `statsforecast`, `utilsforecast`, `coreforecast` —
plus `statsmodels` for STL, ACF and Ljung-Box.

**All three days are built.** See the bottom of this file for Day 3's shape, and
`notes/day3_plan.md` for the rationale and the measured numbers.

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
slides/          01..06_*.qmd -- flat, numeric prefixes carry the order
  assets/        image_prompts.md (manifest; no images yet, by design)
labs/            00_setup.md, 00_pre_work.ipynb, 01_day1_*.ipynb, 02_day2_*.ipynb,
                 03_day3_*.ipynb
                 reference_cheatsheet.md, leaderboard.csv (generated)
  solutions/     answer keys -- same notebooks, TODOs filled
coursekit/       the shared package (installed editable)
  fppdata.py     downloads + caches the FPP3 .rda datasets
  datasets.py    the specific series this course teaches on
  plotting.py    every chart in the decks AND the labs
  leaderboard.py the running scoreboard
  scoring.py     LEVELS/QCOLS/QUANTILES and score_cv -- the harness Day 3 plugs into
  checks.py      the check_ex_* assertions the labs call
  data/          cached .rda files -- COMMITTED so the course runs offline
scripts/         check_env.py, prefetch_data.py, build_labs.py, measure_arima.py
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
lecture → lab cycles, one per deck — not five interleaved ones. The six blocks are
Lab A (Ex 1.1–1.2, 25 min), Lab B (1.3–1.5, 45), Lab C (2.1–2.3, 46), Lab D (2.4–2.5, 29),
Lab E (3.1–3.3, 40), Lab F (3.4–3.5, 35).

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
are the theme's `.flowrow` / `.flowconv` HTML classes (see the skill's `patterns.md`);
illustrative imagery is recorded in `slides/assets/image_prompts.md` first. Never use a
static image for something a `{python}` cell could draw, and no Graphviz: `{dot}` output
ignores the deck's fonts and palette and reads as a foreign object on the slide. Mermaid
is still fine for a genuinely graph-shaped diagram a flow row cannot express.

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

## Day 3 — built: ETS, then AutoGluon

Day 3 is taught on **Google Colab** (torch preinstalled, network always available).
The arc is *transparent → orchestrated → the map*, ~70/30 basics-to-black-box:
when students build with a black-box tool, the mental model they bring is the one
this course built. Two decks, two lab blocks, five exercises. `notes/day3_plan.md`
holds the rationale; the measured numbers are reproduced by `notes/day3_probe.py`.

**Deck 5 (`05_exponential_smoothing_and_ets.qmd`) — ETS (Ch 8), the deep one, and
the only model taught properly.** 34 slides. Three steps, one component added each
time: SES → Holt → Holt-Winters. The 30-variant (E,T,S) taxonomy is a single
lookup-table slide, not a segment. Framed as the Day 2 STL+drift route with the
weights learned instead of pinned. Lab E: fit, read the components, 8 rolling
folds, CRPS/coverage, add to the leaderboard.

**Deck 6 (`06_orchestration_and_the_field.qmd`) — AutoARIMA, AutoGluon, the map.**
22 slides. Segment A closes Day 2's white-noise hook by name (Ljung-Box
p ≈ 2e-245) and names the selected `ARIMA(1,0,1)(1,1,1)[12]`. Segment B is
AutoGluon, hands-on in the lab. Segment C is the field, listed not taught.

### The results, and why they are the lesson

Measured over 8 rolling folds on the spine:

| model | MASE | CRPS | cov-80 |
|---|---|---|---|
| **Theta** (the capstone plant) | **1.025** | **0.0288** | 70% |
| Seasonal naive (the Day 2 floor) | 1.183 | 0.0306 | 77% |
| ARIMA | 1.149 | 0.0311 | 62.5% |
| ETS | 1.176 | 0.0329 | 87.5% |
| STL + drift | 1.225 | 0.0339 | 61% |

- **ETS ties the floor on MASE and loses the distribution** by over-covering at
  87.5% — bands too wide. That is deck 5's payoff and it is a better lesson than
  a win. Do not go looking for a model that wins outright instead.
- **ARIMA fails in the opposite direction**, under-covering at 62.5%. Two models,
  two opposite interval failures, one Day 2 lesson confirmed from both sides.
- **AutoTheta is the capstone plant**: three lines, no lecture, and it is the only
  model all day that beats the seasonal naive on CRPS. The floor surviving
  everything else is the closing beat. `check_ex_3_2` asserts ETS wins MASE and
  loses CRPS; do not "fix" it.

**ARIMA is deliberately not taught** — it costs a chapter (differencing,
stationarity, AR vs MA, PACF for order selection, then seasonal orders) and three
hours buys either a rushed half-version or a black box, and the black-box beat
already belongs to AutoGluon. It gets one slide plus its result.

### Two things that bite

**AutoARIMA is measured once, not fitted on every render.** An order search plus
eight folds is ~100 s, `freeze` was not reliably reusing it, and a 2.5-minute
render for a one-word edit is how a deck stops getting screenshotted. So
`scripts/measure_arima.py` writes `coursekit/data/day3_arima.json` and deck 6
reads it. The numbers stay measured rather than typed. **Re-run that script if the
spine, the fold layout or `scoring.LEVELS` changes.** Every other model in deck 6
is still fitted live (the whole cell is ~5 s).

**`check-labs` cannot verify the AutoGluon cells here** — no torch, no autogluon
locally, ~2.5 GB to install. Every AutoGluon cell is skip-guarded on
`importlib.util.find_spec("autogluon")`, so both targets stay honest; without it
they print the install line and move on. **Exercise 3.4 has therefore never
executed** — it needs one real run on Colab, after which the resulting leaderboard
should be committed to `coursekit/data/`. Two details to confirm on that run: the
zoo key names (`AutoETS` vs `ETS`, `Theta` vs `AutoTheta`) and that AutoGluon has
no Drift model, so the zoo is five models rather than the six the plan named.

### The harness is the interface

Every Day 3 model plugs into the Day 2 harness and appends to
`labs/leaderboard.csv`:

```python
from coursekit import scoring, leaderboard as lb
cv = sf.cross_validation(df=spine, h=12, step_size=12, n_windows=8,
                         level=scoring.LEVELS)
lb.record("ETS", day=3, **scoring.score_cv(cv, "AutoETS", spine))
```

`scoring.QCOLS` and `scoring.QUANTILES` are derived from `LEVELS` rather than
typed out, because out of step they make `scaled_crps` return a number that is
wrong and still positive. A model with no closed-form interval (`WindowAverage`,
and most ML models) raises *"You must pass `prediction_intervals`"* the moment
`cross_validation` is asked for a level; give it
`prediction_intervals=ConformalIntervals(...)`, which deck 03's segment E teaches.

The AutoGluon data conversion stays **visible in the notebook**. A `coursekit`
adapter would shorten it, but "a parallel API universe with its own frame, its own
fit loop and a sign-flipped leaderboard" is deck 6's thesis; a helper deletes the
lesson.

The pin-drift rule stands: no Day 3 model may leak into Day 2 content. And
`coursekit/data/` stays committed (offline insurance) even though Colab has
network.
