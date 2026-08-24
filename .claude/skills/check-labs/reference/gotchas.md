# check-labs — gotchas & battle scars

Things discovered while building and running `driver.py` against the real labs.
Each one is baked into the driver; this is the "why."

## The defining constraint: labs are starter templates

The instructor `.ipynb` files are **not** completed solutions. 16 of 23 carry
intentional `TODO` / `raise NotImplementedError` / "your code here" cells, and 8
import `check_lab_*` assertion helpers (`rag_.../labs/tests/checks.py`,
`function_calling_tools/labs/checker/lab01.py`) that only pass once the exercise
is filled in. So **"executed with zero errors" is a false success test** — a
correct starter notebook *will* error.

The driver runs with `allow_errors=True` (so every cell runs and every error is
collected, not just the first) and then **classifies** each error as EXPECTED /
AUTH / BROKEN. That classification is the whole point.

## Classifier heuristics & their limits

- A cell whose source matches a TODO marker → its error is EXPECTED.
- `AssertionError` → EXPECTED (that's the `check_lab_*` grading path).
- `NameError` → EXPECTED (it almost always cascades from a skipped TODO cell
  above). **Limit:** a genuine `NameError` typo in *scaffolding* would be
  mislabelled EXPECTED. Layer 2 (agent solves & reviews) is the backstop.
- `ModuleNotFoundError`/`ImportError`/`SyntaxError`/`FileNotFoundError` → BROKEN
  wherever they occur (these are never a valid student exercise).
- Anything matching an auth signature (`AuthenticationError`, `401`,
  `OPENROUTER_API_KEY`, …) → AUTH, surfaced as `NEEDS-KEY`.

It is heuristic and admits false labels in both directions — SKILL.md says so,
and that's why Layer 2 exists.

## Real findings from the build-session sweep (worth fixing in the labs)

- **`rag_.../labs/advanced_retrieval.ipynb` is genuinely BROKEN**:
  `import rank_bm25` with no install cell, so it dies in a clean environment.
  Either add `!uv pip install rank-bm25` or document the dep.
- **The committed `.env` API keys are dead.** `ai_agents/labs/.env` returns
  `401 User not found`; `rag_.../production_readiness` returns
  `401 No cookie auth credentials`. The driver flags these `NEEDS-KEY` (AUTH),
  **not** BROKEN — a present-but-invalid key is a credential problem, not a lab
  bug. Replace the keys to verify those labs' green path.

## Platform / toolchain traps (Windows)

- **Kernel cwd must be the lab dir.** `NotebookClient(..., resources={"metadata":
  {"path": <lab_dir>}})` — without it, local imports (`simple_observe.py`,
  `checker/`, `tests/checks.py`, `utils.py`) and relative `.env`/asset paths fail
  and you get false BROKENs.
- **Console encoding.** The Windows console is cp1252 and crashes when printing
  box-drawing/em-dash characters from tracebacks. The driver forces
  `sys.stdout`/`stderr` to UTF-8 (`errors="replace"`) at startup.
- **asyncio loop.** Under the default Windows Proactor loop, pyzmq emits a
  `RuntimeWarning`. The driver sets `WindowsSelectorEventLoopPolicy` before any
  kernel starts.
- **nbformat cell ids.** Older notebooks lack cell `id` fields →
  `MissingIDFieldWarning` spam. Suppressed via a warnings filter.

## tracks.yml separator quirk

The `labs:` map keys use **backslashes** (`ai_agents\observability_and_evaluation`)
while the `sessions:` lists use forward slashes. `_norm()` normalizes both to
`/` before any comparison. Don't remove it.

## Cost / time

- Several labs self-install deps inline via `!uv pip install …` (needs network +
  `uv` on PATH). `tokenization_cost.ipynb` pulls `torch`/`transformers` — slow.
- Default per-cell timeout is 300s; raise `--timeout` for the heavy installs.
- A full `all` sweep makes real (paid) API calls for every key-bearing lab — run
  a module or single notebook while iterating.
