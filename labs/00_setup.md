# Setup — do this before Day 1

Twenty minutes, once. Day 1 opens with content, not an install clinic.

## What you need

- **Python 3.11 or 3.12** (3.13+ is not supported by every dependency yet)
- **[uv](https://docs.astral.sh/uv/)** — the installer this project uses
- Internet access **once**, to download packages and datasets. After that the whole
  course runs offline.

Installing uv:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Install

From the repository root:

```bash
uv sync --extra dev
```

That creates `.venv/` and installs everything, including `coursekit` — the course's own
helper package — as an **editable** install, so the labs can `from coursekit import ...`
from anywhere.

## Verify

```bash
# Windows
.venv\Scripts\python.exe scripts\check_env.py
.venv\Scripts\python.exe scripts\prefetch_data.py

# macOS / Linux
.venv/bin/python scripts/check_env.py
.venv/bin/python scripts/prefetch_data.py
```

`check_env.py` must end with **"Ready. See you on Day 1."** If it does not, it names
exactly what is missing and how to fix it.

`prefetch_data.py` downloads the five datasets the labs use and caches them under
`coursekit/data/`. This is the step that needs internet; run it at home, not on the
conference wifi.

## Open the notebooks

```bash
uv run jupyter lab
```

Then open `labs/00_pre_work.ipynb` and work through it — about 20 minutes.

If you prefer VS Code: open the folder, then pick the `.venv` interpreter
(Ctrl+Shift+P → *Python: Select Interpreter*) before opening a notebook.

## Troubleshooting

**`ModuleNotFoundError: coursekit`**
You are running a different Python than the one `uv sync` set up. Use
`.venv/Scripts/python.exe` (Windows) or `.venv/bin/python`, or select the `.venv`
interpreter in your editor.

**`check_env.py` says datasets are missing**
Run `scripts/prefetch_data.py`. If it fails, you are probably behind a proxy that blocks
`raw.githubusercontent.com` — try from a different network, or ask the instructor for the
`coursekit/data/` folder on a USB stick.

**`pyreadr` fails to install**
It ships as a wheel for common platforms. If yours is unusual, tell the instructor before
Day 1 — the datasets can be supplied as CSV instead.

**A plot does not appear in Jupyter**
Make sure the cell ends with `plt.show()` and that you selected the `.venv` kernel.

**Still stuck?** Bring the laptop to the room ten minutes early. Do not spend an hour on
this alone.
