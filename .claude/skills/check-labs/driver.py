#!/usr/bin/env python
"""check-labs driver — Layer 1: mechanically execute the course labs and
classify what fails.

The instructor notebooks are STARTER TEMPLATES, not solutions: most carry
intentional `TODO` exercise cells and `check_lab_*` assertions that only pass
once a student fills them in. So "ran with zero errors" is NOT the success
test. This driver executes each notebook with `allow_errors=True` (so every
cell runs and every error is collected), then classifies each error as:

  - EXPECTED   incomplete exercise (TODO cell / check_lab_* assertion /
               NameError cascading from a skipped TODO cell)
  - AUTH       missing-or-bad API key
  - BROKEN     genuine breakage (ImportError, SyntaxError, FileNotFoundError,
               an error raised in a non-exercise/infrastructure cell, ...)

Notebook status (worst-first): BROKEN > NEEDS-KEY > GPU-FLAGGED >
EXERCISES-INCOMPLETE > OK.

Discovery reuses scripts/utils.py (the same labs map / module / track logic the
index build uses) so this stays in lockstep with tracks.yml.

Usage:
    python .claude/skills/check-labs/driver.py [TARGET] [--json OUT] [--timeout S]

TARGET (default "all"):
    all                       every lab in the tracks.yml labs map
    core | extended | full    labs whose session is in that track
    <module_slug>             e.g. ai_agents  — that module's labs
    all                       every student notebook under labs/
    solutions                 the instructor answer keys under labs/solutions/
    <stem or substring>       e.g. "day1" or "02_day2_toolbox_and_evaluation"
    <path/to/notebook.ipynb>  a single notebook
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path

# On Windows the default Proactor loop warns under pyzmq; the selector loop is
# what jupyter_client expects. Set it before any kernel starts.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# The Windows console defaults to cp1252 and chokes on box-drawing / em-dash
# characters in tracebacks. Force UTF-8 so the report never crashes on output.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# This course uses a flat layout: every notebook lives under labs/. There is no
# tracks.yml and no scripts/utils.py to consult, so discovery is a glob.
REPO_ROOT = Path(__file__).resolve().parents[3]
LABS_DIR = REPO_ROOT / "labs"

import warnings  # noqa: E402

import nbformat  # noqa: E402
from nbclient import NotebookClient  # noqa: E402

# Many course notebooks predate nbformat's cell-id requirement; the warning is
# cosmetic and would otherwise spam the report.
warnings.filterwarnings("ignore", category=nbformat.warnings.MissingIDFieldWarning)

# Notebooks that require a GPU — flagged, never executed (per skill design).
GPU_LABS: set[str] = set()   # no GPU notebooks in this course

# Env vars that signal a notebook makes real API calls.
API_KEY_NAMES = ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")

# Markers that identify an intentionally-incomplete student exercise cell.
TODO_MARKERS = (
    "todo",
    "your code here",
    "raise notimplementederror",
    "fill in",
    "complete the",
    "# ___",
    "# your turn",
)

# ename values that are always genuine breakage, wherever they occur.
GENUINE_ENAMES = {
    "ModuleNotFoundError",
    "ImportError",
    "SyntaxError",
    "IndentationError",
    "FileNotFoundError",
    "TabError",
}

# Substrings that mark an auth / missing-key failure.
AUTH_SIGNS = (
    "authenticationerror",
    "api key",
    "api_key",
    "incorrect api key",
    "no api key",
    "401",
    "unauthorized",
    "openrouter_api_key",
    "openai_api_key",
    "anthropic_api_key",
)

STATUS_ORDER = ["BROKEN", "NEEDS-KEY", "GPU-FLAGGED", "EXERCISES-INCOMPLETE", "OK"]


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #
def _norm(ref: str) -> str:
    """Normalize a session ref to forward slashes (the labs map uses '\\')."""
    return "/".join(re.split(r"[\\/]", ref))


def all_labs() -> list[tuple[str, Path]]:
    """Every student notebook under labs/, in filename order.

    `labs/solutions/` holds the instructor copies -- same notebooks with the
    TODOs filled in -- so they are excluded here. Check them with an explicit
    path when you want to confirm the answer key still runs.
    """
    out: list[tuple[str, Path]] = []
    for nb in sorted(LABS_DIR.rglob("*.ipynb")):
        if "solutions" in nb.relative_to(LABS_DIR).parts:
            continue
        if ".ipynb_checkpoints" in nb.parts:
            continue
        out.append((nb.stem, nb))
    return out


def select(target: str) -> list[tuple[str, Path]]:
    """Resolve a TARGET to a list of (ref, notebook_path)."""
    if target.endswith(".ipynb"):
        nb = Path(target)
        if not nb.is_absolute():
            nb = (Path.cwd() / nb).resolve()
        # Recover the ref if this notebook is in the map (for slide pairing).
        ref = next((r for r, p in all_labs() if p.resolve() == nb.resolve()), nb.stem)
        return [(ref, nb)]

    labs = all_labs()
    if target == "all":
        return labs
    if target == "solutions":
        return [(p.stem, p) for p in sorted((LABS_DIR / "solutions").glob("*.ipynb"))]
    # Otherwise: a notebook stem, or any substring of one (e.g. "day1").
    hits = [(r, p) for r, p in labs if target == r or target in r]
    if not hits:
        known = ", ".join(r for r, _ in labs) or "(none found under labs/)"
        sys.exit(f"error: target {target!r} matches no notebook. Known: {known}")
    return hits


# --------------------------------------------------------------------------- #
# Environment (.env) handling
# --------------------------------------------------------------------------- #
def read_env_file(env_path: Path) -> dict[str, str]:
    """Minimal KEY=VALUE .env parser (no python-dotenv dependency)."""
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


@contextmanager
def temp_env(extra: dict[str, str]):
    """Temporarily overlay `extra` onto os.environ (kernels inherit it)."""
    saved = {k: os.environ.get(k) for k in extra}
    os.environ.update({k: v for k, v in extra.items() if v})
    try:
        yield
    finally:
        for k, old in saved.items():
            if old is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = old


def required_keys(nb) -> list[str]:
    """API key names a notebook references in its source."""
    src = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
    return [k for k in API_KEY_NAMES if k in src]


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #
def is_exercise_cell(source: str) -> bool:
    low = source.lower()
    return any(m in low for m in TODO_MARKERS)


def classify_error(ename: str, evalue: str, source: str) -> str:
    """Return 'EXPECTED', 'AUTH', or 'BROKEN' for one cell error."""
    blob = f"{ename} {evalue}".lower()

    # Auth / key problems first — these aren't lab bugs.
    if any(s in blob for s in AUTH_SIGNS):
        return "AUTH"

    # This course's student notebooks leave TODOs as the literal `...`, so any
    # error naming an ellipsis is an unfilled exercise, not breakage — whatever
    # the exception type, and wherever it cascaded to.
    if "ellipsis" in blob:
        return "EXPECTED"

    # An incomplete exercise cell, by marker.
    if is_exercise_cell(source):
        return "EXPECTED"

    # check_lab_* / check_ex_* assertions and bare asserts are the
    # exercise-grading path.
    if ename == "AssertionError":
        return "EXPECTED"

    # NameError almost always cascades from a skipped/unfilled TODO cell above.
    if ename == "NameError":
        return "EXPECTED"

    # Anything in the genuine set is real breakage wherever it appears.
    if ename in GENUINE_ENAMES:
        return "BROKEN"

    # Otherwise: an error in a non-exercise cell is breakage.
    return "BROKEN"


# --------------------------------------------------------------------------- #
# Execution
# --------------------------------------------------------------------------- #
def run_notebook(ref: str, nb_path: Path, timeout: int) -> dict:
    """Execute one notebook and classify it. Returns a result record."""
    rec = {
        "ref": ref,
        "path": nb_path.relative_to(REPO_ROOT).as_posix()
        if nb_path.is_relative_to(REPO_ROOT)
        else str(nb_path),
        "status": None,
        "errors": [],          # genuine + auth errors (for the report)
        "expected_count": 0,
        "needs_keys": [],
        "seconds": 0.0,
        "note": "",
    }

    if not nb_path.exists():
        rec["status"] = "BROKEN"
        rec["note"] = "notebook file not found"
        return rec

    # GPU labs: flag, never execute.
    if nb_path.stem in GPU_LABS:
        rec["status"] = "GPU-FLAGGED"
        rec["note"] = "requires a GPU — not executed (review manually)"
        return rec

    nb = nbformat.read(nb_path, as_version=4)

    # Decide whether we have the keys this notebook needs.
    module_env = read_env_file(nb_path.parent / ".env")
    needed = required_keys(nb)
    have = {k for k in needed if module_env.get(k) or os.environ.get(k)}
    missing = [k for k in needed if k not in have]
    if missing:
        rec["status"] = "NEEDS-KEY"
        rec["needs_keys"] = missing
        rec["note"] = f"missing {', '.join(missing)} in {nb_path.parent.as_posix()}/.env"
        return rec

    start = time.time()
    client = NotebookClient(
        nb,
        timeout=timeout,
        allow_errors=True,           # run every cell; collect all errors
        kernel_name="python3",
        resources={"metadata": {"path": str(nb_path.parent)}},  # kernel cwd = lab dir
    )
    try:
        with temp_env(module_env):
            client.execute()
    except Exception as exc:  # kernel start failure, fatal timeout, etc.
        rec["status"] = "BROKEN"
        rec["note"] = f"execution aborted: {type(exc).__name__}: {exc}"
        rec["seconds"] = round(time.time() - start, 1)
        return rec
    rec["seconds"] = round(time.time() - start, 1)

    # Walk cell outputs and classify every error.
    has_broken = has_auth = has_expected = False
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        for out in cell.get("outputs", []):
            if out.get("output_type") != "error":
                continue
            ename = out.get("ename", "")
            evalue = out.get("evalue", "")
            kind = classify_error(ename, evalue, cell.source)
            if kind == "EXPECTED":
                has_expected = True
            elif kind == "AUTH":
                has_auth = True
                rec["errors"].append(
                    {"cell": i, "kind": kind, "ename": ename, "evalue": evalue[:300]}
                )
            else:  # BROKEN
                has_broken = True
                rec["errors"].append(
                    {"cell": i, "kind": kind, "ename": ename, "evalue": evalue[:300]}
                )
    rec["expected_count"] = sum(
        1
        for cell in nb.cells
        if cell.cell_type == "code"
        for out in cell.get("outputs", [])
        if out.get("output_type") == "error"
    ) - len(rec["errors"])

    if has_broken:
        rec["status"] = "BROKEN"
    elif has_auth:
        rec["status"] = "NEEDS-KEY"
    elif has_expected:
        rec["status"] = "EXERCISES-INCOMPLETE"
    else:
        rec["status"] = "OK"
    return rec


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
ICON = {
    "OK": "[ OK ]",
    "EXERCISES-INCOMPLETE": "[EXER]",
    "NEEDS-KEY": "[KEY ]",
    "GPU-FLAGGED": "[GPU ]",
    "BROKEN": "[FAIL]",
}


def print_report(results: list[dict]) -> None:
    width = max((len(r["path"]) for r in results), default=20)
    print()
    for r in results:
        line = f"{ICON[r['status']]}  {r['path']:<{width}}  {r['status']}"
        extra = []
        if r["seconds"]:
            extra.append(f"{r['seconds']}s")
        if r["status"] == "EXERCISES-INCOMPLETE":
            extra.append(f"{r['expected_count']} expected exercise error(s)")
        if r["note"]:
            extra.append(r["note"])
        if extra:
            line += "   (" + "; ".join(extra) + ")"
        print(line)
        for e in r["errors"]:
            print(f"         └─ cell {e['cell']}: {e['ename']}: {e['evalue'].splitlines()[0][:160]}")
    print()
    counts = {s: sum(1 for r in results if r["status"] == s) for s in STATUS_ORDER}
    summary = "  ".join(f"{s}={counts[s]}" for s in STATUS_ORDER if counts[s])
    print(f"summary: {len(results)} lab(s)  |  {summary}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Execute and classify the course labs.")
    ap.add_argument("target", nargs="?", default="all",
                    help="all | core/extended/full | <module_slug> | path/to/notebook.ipynb")
    ap.add_argument("--json", metavar="OUT", help="write a JSON report to OUT")
    ap.add_argument("--timeout", type=int, default=300, help="per-cell timeout seconds (default 300)")
    ap.add_argument("--list", action="store_true",
                    help="list the notebooks a target selects, without running them")
    args = ap.parse_args()

    labs = select(args.target)

    if args.list:
        print(f"check-labs: target {args.target!r} selects {len(labs)} notebook(s):")
        for ref, nb in labs:
            rel = nb.relative_to(REPO_ROOT).as_posix() if nb.is_relative_to(REPO_ROOT) else str(nb)
            print(f"  {ref:<60} {rel}")
        return 0

    print(f"check-labs: {len(labs)} notebook(s) for target {args.target!r} "
          f"(per-cell timeout {args.timeout}s)")

    results = []
    for ref, nb in labs:
        print(f"  running {nb.relative_to(REPO_ROOT).as_posix() if nb.is_relative_to(REPO_ROOT) else nb} ...",
              flush=True)
        results.append(run_notebook(ref, nb, args.timeout))

    print_report(results)

    if args.json:
        import json
        Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"wrote JSON report to {args.json}")

    # Exit non-zero only on genuine breakage (CI-friendly).
    return 1 if any(r["status"] == "BROKEN" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
