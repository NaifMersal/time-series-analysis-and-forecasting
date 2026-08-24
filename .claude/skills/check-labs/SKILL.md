---
name: check-labs
description: Check that the course Jupyter labs work, are logical, and are correct. Use when asked to run, check, verify, test, validate, or smoke-test the labs/notebooks, confirm a lab works in a clean environment, find broken labs, or audit a lab against its slides. Drives the notebooks with .claude/skills/check-labs/driver.py (nbclient) plus an agent-driven solve-and-verify pass.
---

# check-labs

The course's lab notebooks are **starter templates**, not solutions: they carry
intentional `TODO` cells (written as the literal `...`) and `checks.check_ex_*` assertions
that fail until a student fills them in. So "ran with zero errors" is **not** a valid
check — a student notebook that reports `OK` means the TODOs leaked into the student copy.
This skill works in two layers:

- **Layer 1 — `driver.py`:** executes every cell (`allow_errors=True`) and *classifies*
  each failure as genuine breakage vs. an expected-incomplete exercise. Fast, automated.
- **Layer 2 — agent solve-and-verify:** for a chosen lab, complete the exercises and
  re-run until every `check_ex_*` passes, then review it against its slide deck.

All paths below are relative to the repo root. The driver lives at
`.claude/skills/check-labs/driver.py`.

## This repo's layout

Flat: every student notebook is `labs/*.ipynb`; the instructor answer keys are
`labs/solutions/*.ipynb` (the same notebooks with every TODO filled in and every
discussion question answered). There is **no `tracks.yml` and no `scripts/utils.py`** —
the driver discovers notebooks by globbing `labs/`, skipping `solutions/`.

Both copies are generated from one source, so they cannot drift. If you change a lab,
change the generator and regenerate both — do not hand-edit one copy.

## Prerequisites

In the project venv (`uv sync --extra dev`): `nbclient`, `nbformat`, `nbconvert`,
`ipykernel`. Run the driver with `.venv/Scripts/python.exe` so it sees `coursekit`.

No API keys and no GPU notebooks exist in this course. (When Day 3 lands it may add
optional `[neural]` / `[foundation]` extras; a notebook that needs one should *skip*
rather than fail.)

## Run — Layer 1 (mechanical sweep)

```bash
# What a target selects, without running anything:
.venv/Scripts/python.exe .claude/skills/check-labs/driver.py all --list
```

`TARGET` is `all` (default, the student copies) · `solutions` (the answer keys) · a
notebook stem or substring (e.g. `day1`) · or a `<path/to/notebook.ipynb>`.

```bash
.venv/Scripts/python.exe .claude/skills/check-labs/driver.py all
.venv/Scripts/python.exe .claude/skills/check-labs/driver.py solutions
.venv/Scripts/python.exe .claude/skills/check-labs/driver.py day2 --json report.json
```

`--timeout` is per-cell seconds (default 300). Exit code is **1 iff any lab is
`BROKEN`**.

**The two targets have opposite healthy states:**

| Target | Healthy result | Why |
|---|---|---|
| `all` (student copies) | `EXERCISES-INCOMPLETE` | The TODOs are unfilled, as shipped. `OK` here is a **bug** — an answer leaked into the student copy. |
| `solutions` | `OK` | Every TODO filled, every `check_ex_*` passing. Anything else means the answer key is broken. |

**Reading the statuses** (worst-first):

| Status | Meaning | What you do |
|---|---|---|
| `BROKEN` | Real failure — `ImportError`, `SyntaxError`, missing file, or an error in a non-exercise cell. | **Fix the lab.** The cell + traceback are printed. |
| `EXERCISES-INCOMPLETE` | Only expected `TODO` / `check_ex_*` errors. | Nothing — this is the healthy state for a student copy. |
| `OK` | Ran clean. | Healthy for `solutions`; investigate for `all`. |

The classifier treats any error mentioning `ellipsis` as an unfilled TODO, because that
is exactly how this repo writes them. It is otherwise heuristic (see
`reference/gotchas.md`) — Layer 2 is the backstop.

## Run — Layer 2 (solve & verify one lab, then judge it)

1. **Pair it with its deck.** `labs/01_day1_*` follows `slides/01_*` and `slides/02_*`;
   `labs/02_day2_*` follows `slides/03_*` and `slides/04_*`. Each exercise's markdown
   header names the segment it follows.
2. **Complete the exercises** in the student copy (use `labs/solutions/` as the spec),
   editing cells with `NotebookEdit`.
3. **Re-run that notebook** until it reports `OK` — every `check_ex_*` passing proves the
   lab is solvable end to end.
4. **Judge logic & correctness** against the paired deck:
   - Does the lab teach what the slides claim, in the same order?
   - Are exercises well-posed; do the `check_ex_*` messages point at the real mistake?
   - Do the numbers in the deck's prose still match what the lab computes? (Both run the
     same `coursekit` helpers, so a drift here is a real finding.)
   - No deprecated APIs or contradictory instructions?

   The `curriculum-reviewer` skill complements this: it reviews pedagogy, check-labs
   reviews execution.

## Gotchas

See `reference/gotchas.md`. The load-bearing ones here:

- **Starter templates fail by design.** `EXERCISES-INCOMPLETE` is success for a student
  copy; `OK` is the thing to investigate.
- **`labs/leaderboard.csv` is written by exercise 2.5** and is generated output, not
  source. Running the Day 2 solution overwrites it.
- The driver sets the kernel cwd to the **notebook's own directory** (`labs/`), not the
  repo root. `from coursekit import ...` still resolves because `uv sync` installs the
  project itself as an editable install — so edits to `coursekit/` take effect with no
  reinstall, but a bare `python` outside the venv will not see it.
- The driver also forces UTF-8 console output and fixes the Windows asyncio loop. Both
  are load-bearing on this machine; don't undo them.

## Troubleshooting

- `NoSuchKernel: python3` → `.venv/Scripts/python.exe -m ipykernel install --user`.
- `ModuleNotFoundError: coursekit` → you ran the system Python; use `.venv/Scripts/python.exe`.
- A lab hangs → a cell exceeds `--timeout`; raise it or run that notebook alone.
