#!/usr/bin/env python3
"""
Render a course .qmd deck and screenshot slides with headless Chrome.

This is the agent harness for SDAIA Quarto slide decks: it turns a `.qmd`
source into a rendered reveal.js deck and then captures PNGs of chosen
slides so you can VISUALLY verify branding, overflow, dark sections,
diagrams, etc. — things you cannot see from the markdown alone.

Usage (run from the repo root):

    python .claude/skills/author-verify-slides/driver.py <deck.qmd> [options]

Options:
    --slides 0,4,8     Comma-separated slide selectors, in DOCUMENT order. Each
                       selector is either an integer index (0 == title slide,
                       counts vertical sub-slides — see "vertical decks" below)
                       OR a case-insensitive title/id substring, which may match
                       several slides. Mix freely, e.g.
                         --slides 0,reasoning,"Key API"
                       Prefer substrings over indices: a `## Foo` inside a
                       `::: {.callout}`/column div is a callout title, NOT a
                       slide, so counting headings to guess an index misleads.
                       Default: 0.
    --all              Shoot every slide (auto-detected, vertical-aware).
    --changed          Shoot only slides whose source changed vs git HEAD — the
                       fast path when verifying a few edits instead of a whole
                       deck. An untracked (brand-new) deck counts as all-changed.
                       Composes with --reveal-all.
    --reveal-all       Reveal ALL fragments before shooting. Renders a
                       throwaway copy with every fragment source neutralized
                       (`. . .` pauses, `.fragment`/`.incremental` classes, and
                       a global `incremental: true`), so each slide shows its
                       FINAL state. This is how you catch overflow — a
                       deep-linked slide otherwise sits at fragment 0 and late
                       content (tables/callouts/footers after a pause, or inside
                       a `.fragment` div) stays hidden. Implies a render.
    --no-render        Skip `quarto render`; screenshot the existing HTML.
    --outdir DIR       Where PNGs go. Default: output/_screenshots/<deck>/
    --width,--height   Viewport. Default 1600x900 (16:9).
    --wait MS          Chrome virtual-time budget per shot. Default 8000.
    --jobs N           Concurrent Chrome screenshots. Multi-slide runs (--all,
                       --changed, multi --slides) shoot in parallel. Default:
                       auto (~physical cores). Lower it if shots start FAILING
                       (too many Chromes); it won't speed past your core count.

Vertical decks: if a deck uses `#` section dividers, Quarto nests its `##`
slides as VERTICAL children of each divider. Flat `#/N` index navigation only
reaches the horizontal dividers, so this driver enumerates and navigates by
each slide's reveal.js **id** (`#/<id>`) instead — which addresses flat and
vertical decks identically. `--slides N` indexes into that full document-order
list (title = 0).

Examples:
    python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --slides 0,4,8
    python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --slides reasoning,"Key API"
    python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --changed --reveal-all
    python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --all --reveal-all
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = REPO_ROOT / "output"

CHROME_CANDIDATES = [
    os.environ.get("SLIDES_CHROME"),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    for name in ("chrome", "chromium", "chromium-browser", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit(
        "ERROR: No Chrome/Edge found. Set SLIDES_CHROME=<path-to-chrome.exe> "
        "or install Google Chrome."
    )


def qmd_to_html(qmd: Path) -> Path:
    """Map a source .qmd to its rendered HTML under output/ (output-dir in _quarto.yml)."""
    rel = qmd.resolve().relative_to(REPO_ROOT)
    return (OUTPUT_DIR / rel).with_suffix(".html")


def render(qmd: Path) -> None:
    print(f"[render] quarto render {qmd}")
    # Windows file-watchers occasionally lock the intermediate _files dir
    # (os error 32). One retry clears the transient case.
    for attempt in (1, 2):
        proc = subprocess.run(
            ["quarto", "render", str(qmd)],
            cwd=REPO_ROOT,
            shell=(os.name == "nt"),  # quarto is a .cmd shim on Windows
        )
        if proc.returncode == 0:
            return
        if attempt == 1:
            print("[render] non-zero exit (possible file lock); retrying once...")
    sys.exit(f"ERROR: quarto render failed for {qmd}")


def list_slides(html: Path) -> list[tuple[str, str]]:
    """Ordered `(hash_target, title)` per slide, in document order.

    Element 0 is the title slide (`("0", "title slide")`, always reliable).
    The rest are `(section id, heading text)` for every `slide level1`/
    `slide level2` section — the id (`#/<id>`) is what makes navigation work
    for vertical decks (where `##` slides are vertical children that flat
    `#/N` indices skip), and the title is what lets `--slides` match by name.
    """
    text = html.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<div class="slides">(.*)', text, re.S)
    body = m.group(1) if m else text
    slides: list[tuple[str, str]] = [("0", "title slide")]
    opens = list(re.finditer(r'<section id="([^"]+)"\s+class="([^"]*)"', body))
    for i, sm in enumerate(opens):
        if not re.search(r"slide level[12]", sm.group(2)):
            continue
        sid = sm.group(1)
        end = opens[i + 1].start() if i + 1 < len(opens) else len(body)
        hm = re.search(r"<h[12][^>]*>(.*?)</h[12]>", body[sm.end():end], re.S)
        title = re.sub(r"<[^>]+>", "", hm.group(1)).strip() if hm else sid
        slides.append((sid, title))
    return slides


def source_slides(qmd: Path) -> list[tuple[int, str]]:
    """Ordered `(1-based source line, title)` per slide, mirroring `list_slides`.

    A `#`/`##` line starts a slide only at top level — headings inside fenced
    divs (`::: {.callout}`, `::: {.column}`) are callout/column titles, and `#`
    lines inside ``` code fences are comments; both are skipped. Element 0 is
    the title slide. Used to map changed source lines back to slides.
    """
    slides: list[tuple[int, str]] = [(1, "title slide")]
    in_code = False
    fence_depth = 0
    for lineno, line in enumerate(qmd.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if re.match(r"^(```|~~~)", stripped):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^:::+", stripped):
            rest = re.sub(r"^:::+", "", stripped).strip()
            fence_depth = fence_depth + 1 if rest else max(0, fence_depth - 1)
            continue
        if fence_depth == 0:
            hm = re.match(r"^(#{1,2})\s+(.*)$", line)
            if hm:
                title = re.sub(r"\s*\{[^}]*\}\s*$", "", hm.group(2)).strip()
                slides.append((lineno, title))
    return slides


def changed_source_lines(qmd: Path) -> tuple[set[int], bool]:
    """New-file line numbers changed in `qmd` vs git HEAD.

    Returns `(line_numbers, whole_file)`. `whole_file` is True when the deck is
    untracked (brand-new) — there's no baseline, so every slide is "changed".
    """
    rel = qmd.resolve().relative_to(REPO_ROOT).as_posix()
    tracked = subprocess.run(
        ["git", "ls-files", "--", rel], cwd=REPO_ROOT,
        capture_output=True, text=True,
    )
    if tracked.returncode != 0:
        sys.exit("ERROR: --changed needs a git repo (git not available or not a repo).")
    if not tracked.stdout.strip():
        return set(), True  # untracked → treat as all-changed
    diff = subprocess.run(
        ["git", "diff", "-U0", "--no-color", "HEAD", "--", rel],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    changed: set[int] = set()
    for line in diff.stdout.splitlines():
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if not m:
            continue
        start = int(m.group(1))
        count = int(m.group(2)) if m.group(2) is not None else 1
        changed.update(range(start, start + max(count, 1)))  # count 0 = deletion point
    return changed, False


def slide_index_for_line(src: list[tuple[int, str]], line: int) -> int:
    """Index of the source slide that owns `line` (largest heading line <= line)."""
    idx = 0
    for i, (ln, _) in enumerate(src):
        if ln <= line:
            idx = i
        else:
            break
    return idx


def resolve_slide_tokens(tokens: list[str], slides: list[tuple[str, str]]) -> list[int]:
    """Turn `--slides` tokens into indices. A token is either an integer index
    or a case-insensitive substring matched against each slide's title and id
    (a substring may expand to several slides)."""
    resolved: list[int] = []
    for tok in tokens:
        tok = tok.strip()
        if tok == "":
            continue
        if re.fullmatch(r"-?\d+", tok):
            resolved.append(int(tok))
            continue
        low = tok.lower()
        hits = [i for i, (h, t) in enumerate(slides)
                if low in t.lower() or low in h.lower()]
        if hits:
            resolved.extend(hits)
        else:
            print(f"[warn]  no slide title/id matches '{tok}' — skipped")
    # de-dupe, preserve order
    return list(dict.fromkeys(resolved))


def changed_indices(qmd: Path, slides: list[tuple[str, str]]) -> list[int]:
    """Rendered-slide indices whose source changed vs HEAD (for --changed)."""
    lines, whole_file = changed_source_lines(qmd)
    if whole_file:
        print("[info]  deck is untracked — every slide counts as changed.")
        return list(range(len(slides)))
    if not lines:
        return []
    src = source_slides(qmd)
    src_idx = sorted({slide_index_for_line(src, n) for n in lines})
    if len(src) == len(slides):
        return src_idx  # 1:1 source↔rendered order — direct mapping
    # Counts diverged (fence/heading parse drift): fall back to title matching.
    print(f"[warn]  source slides ({len(src)}) != rendered slides ({len(slides)}); "
          "matching changed slides by title.")
    rendered = [t for _, t in slides]
    indices: list[int] = []
    for i in src_idx:
        title = src[i][1]
        if title in rendered:
            indices.append(rendered.index(title))
        else:
            print(f"[warn]  changed slide '{title}' not found in render — re-run with --all.")
    return list(dict.fromkeys(indices))


def file_url(html: Path, hash_target: str) -> str:
    p = str(html.resolve()).replace("\\", "/")
    return f"file:///{p}#/{hash_target}"


# Each worker thread gets its OWN Chrome profile dir, created once and reused
# across all of that worker's shots. Two reasons: (1) concurrent `chrome
# --headless` runs sharing a profile contend on its singleton lock and
# serialize; a per-worker dir isolates them. (2) Doing it per-worker (not
# per-shot) avoids paying cold profile-init + dir cleanup on every single
# screenshot. We never touch the user's real default Chrome profile.
_tls = threading.local()
_profiles_lock = threading.Lock()
_profile_dirs: list[Path] = []


def _worker_profile() -> Path:
    p = getattr(_tls, "profile", None)
    if p is None:
        p = Path(tempfile.mkdtemp(prefix="slideshot_"))
        _tls.profile = p
        with _profiles_lock:
            _profile_dirs.append(p)
    return p


def cleanup_profiles() -> None:
    """Remove all per-worker Chrome profile dirs created during the run."""
    with _profiles_lock:
        for p in _profile_dirs:
            shutil.rmtree(p, ignore_errors=True)
        _profile_dirs.clear()


def shoot(chrome: str, html: Path, hash_target: str, out: Path, w: int, h: int,
          wait: int, label: str = "") -> str:
    """Capture one slide PNG. Returns the `[shot]` log line for ordered printing
    by the caller (so parallel workers don't interleave output)."""
    out = out.resolve()  # Chrome --screenshot needs an absolute path or it writes nothing
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={_worker_profile()}",
        f"--window-size={w},{h}",
        f"--virtual-time-budget={wait}",
        f"--screenshot={out}",
        file_url(html, hash_target),
    ]
    subprocess.run(cmd, capture_output=True)
    status = out.name if out.exists() else "FAILED (no file written)"
    return f"[shot]  {label} -> {status}"


# reveal.js fragment sources, ordered by how they hide content:
#   `. . .`            — a pause; content after it becomes a fragment (line dropped)
#   `{.fragment}`      — explicit fragment class on a div/span/heading
#   `{.incremental}`   — makes a list's items fragments
#   `incremental: true`— front-matter flag that fragments every list globally
# The class forms are neutralized by RENAMING `.fragment`/`.incremental` to an
# inert class (not deleting them): a fenced-div opener `::: {.fragment}` must
# keep a non-empty `{...}` or Pandoc can't tell it from a closing `:::`. Once the
# class is gone reveal.js never hides the element, so it shows in its final state.
_FRAG_CLASS_RE = re.compile(r"\.(?:fragment|incremental)(?![-\w])")
_ATTR_BLOCK_RE = re.compile(r"\{([^{}]*)\}")


def reveal_fragments_in_line(line: str) -> str:
    """Neutralize fragment/incremental fragments on one (non-code) source line.

    `::: {.fragment .fade-in}` -> `::: {.reveal-shown .fade-in}`,
    `[x]{.fragment}` -> `[x]{.reveal-shown}`, and a global `incremental: true`
    front-matter line -> `incremental: false`. Leftover animation classes
    (`.fade-in`, …) are inert without `.fragment`, so the element stays visible.
    """
    if re.match(r"^\s*incremental:\s*true\s*$", line):
        return re.sub(r"\btrue\b", "false", line, count=1)
    return _ATTR_BLOCK_RE.sub(
        lambda m: "{" + _FRAG_CLASS_RE.sub(".reveal-shown", m.group(1)) + "}", line
    )


def make_revealall_copy(qmd: Path) -> Path:
    """Write a sibling copy of the deck with every fragment fully revealed, so
    each slide renders in its final state (the only way to catch overflow that
    lives in late/fragmented content).

    Drops `. . .` pause lines and neutralizes `.fragment`/`.incremental` classes
    plus a global `incremental: true` (see `reveal_fragments_in_line`). Code
    fences are left untouched so example snippets containing braces or `. . .`
    survive verbatim.

    The name must NOT start with `_` — Quarto treats underscore-prefixed files
    as non-project and renders them without the global theme/output-dir.
    """
    out_lines: list[str] = []
    in_code = False
    for ln in qmd.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\s*(```|~~~)", ln):
            in_code = not in_code
            out_lines.append(ln)
            continue
        if not in_code:
            if ln.strip() == ". . .":
                continue
            ln = reveal_fragments_in_line(ln)
        out_lines.append(ln)
    tmp = qmd.with_name(f"tmp_revealall_{qmd.stem}.qmd")
    tmp.write_text("\n".join(out_lines), encoding="utf-8")
    return tmp


def cleanup_revealall(tmp_qmd: Path) -> None:
    """Remove the throwaway reveal-all deck and its render artifacts."""
    tmp_html = qmd_to_html(tmp_qmd)
    targets = [tmp_qmd, tmp_html]
    dirs = [
        tmp_html.with_name(tmp_qmd.stem + "_files"),
        tmp_qmd.with_name(tmp_qmd.stem + "_files"),
    ]
    for t in targets:
        if t.exists():
            t.unlink()
    for d in dirs:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)


def main() -> None:
    # Slide titles may contain non-cp1252 chars (e.g. "→"); keep the log from
    # dying on a Windows console / piped stdout whose default codec can't encode.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description="Render + screenshot a course slide deck.")
    ap.add_argument("deck", help="path to the .qmd deck (relative to repo root)")
    ap.add_argument("--slides", default="0",
                    help="comma-separated slide selectors: integer indices (0=title) "
                         "and/or title/id substrings, e.g. --slides 0,reasoning,\"Key API\"")
    ap.add_argument("--all", action="store_true", help="screenshot every slide (vertical-aware)")
    ap.add_argument("--changed", action="store_true",
                    help="screenshot only slides whose source changed vs git HEAD "
                         "(untracked deck = all slides)")
    ap.add_argument("--reveal-all", action="store_true",
                    help="reveal all fragments (`. . .`, .fragment/.incremental, "
                         "incremental: true) — needed to see overflow")
    ap.add_argument("--no-render", action="store_true", help="skip quarto render")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--wait", type=int, default=8000)
    ap.add_argument("--jobs", type=int, default=None,
                    help="concurrent Chrome screenshots (default: auto, capped at 8)")
    args = ap.parse_args()

    qmd = (REPO_ROOT / args.deck).resolve() if not Path(args.deck).is_absolute() else Path(args.deck)
    if not qmd.exists():
        sys.exit(f"ERROR: deck not found: {qmd}")

    tmp_qmd = None
    try:
        if args.reveal_all:
            # A fully-revealed copy always needs a fresh render; --no-render
            # would point at the original (fragment-0) HTML, defeating the flag.
            tmp_qmd = make_revealall_copy(qmd)
            print(f"[reveal-all] rendering fully-revealed copy: {tmp_qmd.name}")
            render(tmp_qmd)
            render_qmd = tmp_qmd
        else:
            if not args.no_render:
                render(qmd)
            render_qmd = qmd

        html = qmd_to_html(render_qmd)
        if not html.exists():
            sys.exit(f"ERROR: rendered HTML not found: {html}\n(Render it first; drop --no-render.)")

        chrome = find_chrome()
        stem = qmd.stem
        outdir = Path(args.outdir) if args.outdir else OUTPUT_DIR / "_screenshots" / stem
        tag = "_full" if args.reveal_all else ""

        slides = list_slides(html)
        total = len(slides)
        if args.all:
            indices = list(range(total))
            print(f"[info]  detected {total} slides (vertical-aware)")
        elif args.changed:
            indices = changed_indices(qmd, slides)
            if not indices:
                print("[info]  no source changes vs HEAD — nothing to shoot.")
        else:
            indices = resolve_slide_tokens(args.slides.split(","), slides)

        print(f"[info]  chrome: {chrome}")
        print(f"[info]  html:   {html}")

        # Build the valid job list first (keeping the out-of-range skip message),
        # then capture in parallel — the shots are independent (distinct PNGs,
        # separate Chrome processes, read-only HTML).
        jobs = []  # (idx, sid, out, label)
        for idx in indices:
            if idx < 0 or idx >= total:
                print(f"[shot]  index {idx} out of range (deck has {total} slides) — skipped")
                continue
            sid, title = slides[idx]
            out = outdir / f"{stem}{tag}_s{idx:02d}.png"
            # filename uses the 0-based index; the on-slide counter is 1-based (idx+1).
            label = f's{idx:02d} (slide {idx + 1}/{total})  "{title}"'
            jobs.append((idx, sid, out, label))

        if jobs:
            # Headless Chrome rendering is CPU-bound — ~1-2 cores per shot — so
            # speedup saturates around (physical cores). os.cpu_count() reports
            # logical CPUs; halving it approximates physical cores and avoids the
            # oversubscription that makes more workers *slower*. Override: --jobs.
            workers = args.jobs or min(len(jobs), max(2, (os.cpu_count() or 4) // 2))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                # Map preserves submission (slide) order, so log lines stay ordered.
                lines = pool.map(
                    lambda j: shoot(chrome, html, j[1], j[2],
                                    args.width, args.height, args.wait, j[3]),
                    jobs,
                )
                for line in lines:
                    print(line)

        print(f"\nDone. Open the PNGs in {outdir} and LOOK at them.")
    finally:
        cleanup_profiles()
        if tmp_qmd is not None:
            cleanup_revealall(tmp_qmd)


if __name__ == "__main__":
    main()
