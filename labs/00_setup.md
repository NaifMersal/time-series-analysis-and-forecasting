# Setup: do this before Day 1

The course runs on **Google Colab**. There is nothing to install on your own
machine.

## What you need

- A Google account (Colab runs in the browser)
- Internet access on the day — the notebooks clone the course repository
  when they start

## Day 1, before class: the pre-work lab

1. Read [**A Statistics Refresher**](../slides/00_statistics_refresher.html)
   (~40 minutes). It builds the five ideas the course assumes — a forecast is
   a range, an 80% interval is a pair of cuts, i.i.d. and how each half
   breaks, a test of a claim, and the p-value. **Required.**
2. Open `labs/00_pre_work.ipynb` in Colab (download it from the course
   repository, then **File → Open → Upload** in Colab).
3. Run the **Setup** cell. It clones the course and installs `coursekit`.
   When it prints the spine chart, the environment works.
4. Work through the rest of the notebook, about 20 minutes. Section 5 runs
   four short checks on the refresher's ideas. Nothing is assessed.

## Each day

1. Open that day's notebook in Colab and run the **Setup** cell first.
   It prints a line for the spine (441 months, Apr 1982 to Dec 2018) —
   if you see it, you are ready.
2. Work down in order. Cells marked `TODO` are yours to fill in; a
   `checks.check_ex_*` call tells you whether it worked.

**If your runtime resets, every install is gone.** Re-run the Setup cell
of the notebook you are in. A reset can happen any time Colab is idle;
this is the single most common way to lose ten minutes in the room.

## Day 3, Exercise 3.4

AutoGluon is not installed by the Setup cell (it is large). When you reach
Exercise 3.4, run the install cell it points to — it takes a few minutes.
Everything else on Day 3 needs nothing extra.

## Troubleshooting

**The Setup cell fails part-way**
Run it again. If it fails twice, check your connection and try again;
the clone is the only step that needs the network.

**`ModuleNotFoundError: coursekit`**
You are in a fresh runtime. Run the Setup cell of the notebook you are in.

**A plot does not appear**
Re-run the cell above it. Colab notebooks do not keep state across
runtime resets.

**Still stuck?** Raise your hand in the room. Do not spend an hour on
this alone.

## If you want to work on your own machine

Optional. The course is built for Colab; this is for people who prefer
their own environment.

```bash
uv sync --extra dev
.venv/Scripts/python.exe scripts/check_env.py     # Windows
.venv/bin/python scripts/check_env.py             # macOS / Linux
.venv/Scripts/python.exe scripts/prefetch_data.py # downloads the datasets
uv run jupyter lab
```

`check_env.py` must end with **"Ready. See you on Day 1."** Then open
`labs/00_pre_work.ipynb` in Jupyter and work through it.