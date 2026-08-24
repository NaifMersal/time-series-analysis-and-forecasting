#!/usr/bin/env python3
"""
Bootstrap an SDAIA reveal.js slide project from this skill's bundle.

The `author-verify-slides` skill carries everything needed to render a *branded*
SDAIA deck in its `bundle/` dir: the global `_quarto.yml` (theme, logo, splash
filter, title-slide background), the `slides_template/` scaffold, and the brand
assets (`sdaia.scss`, the logo/icon SVGs, `splash.lua`, `favicon.html`). This
script copies that bundle into a target project root so the driver can then
render branded decks. It is the one-time setup step when you drop the skill into
a fresh repo; in a repo that already has `_quarto.yml` + `slides_template/`
(set up by hand or by a previous run), you don't need it.

Usage (from anywhere):

    python .claude/skills/author-verify-slides/scaffold.py [target_dir] [--force]

`target_dir` defaults to the repo the skill lives in (the dir three levels above
this file, i.e. `<root>/.claude/skills/author-verify-slides/scaffold.py` ->
`<root>`), matching how driver.py resolves REPO_ROOT — so post-scaffold the
driver works unchanged.

It is **non-destructive**: an existing `_quarto.yml` or `slides_template/` at the
target is left untouched (a warning is printed) unless you pass `--force`. This
keeps a project that has intentionally customized its branding from being
clobbered.
"""
import argparse
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
BUNDLE = SKILL_DIR / "bundle"
DEFAULT_TARGET = SKILL_DIR.parents[2]  # <root>/.claude/skills/<skill> -> <root>

# (source under bundle/, dest name at target, is_dir)
ITEMS = [
    (BUNDLE / "_quarto.yml", "_quarto.yml", False),
    (BUNDLE / "slides_template", "slides_template", True),
]


def copy_item(src: Path, dest: Path, is_dir: bool, force: bool) -> bool:
    """Copy one bundle item to dest. Returns True if it was written."""
    if not src.exists():
        sys.exit(f"ERROR: bundle item missing: {src}\n(Is the skill's bundle/ intact?)")
    if dest.exists() and not force:
        print(f"[skip]  {dest}  already exists (use --force to overwrite)")
        return False
    if dest.exists():  # force
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    if is_dir:
        shutil.copytree(src, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    print(f"[write] {dest}")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Scaffold an SDAIA slide project (branding config + template) from the skill bundle."
    )
    ap.add_argument("target_dir", nargs="?", default=None,
                    help="project root to scaffold into (default: the repo this skill lives in)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing _quarto.yml / slides_template/ at the target")
    args = ap.parse_args()

    target = Path(args.target_dir).resolve() if args.target_dir else DEFAULT_TARGET
    if not target.exists():
        sys.exit(f"ERROR: target dir does not exist: {target}")

    print(f"[info]  bundle: {BUNDLE}")
    print(f"[info]  target: {target}")

    wrote_any = False
    for src, name, is_dir in ITEMS:
        wrote_any |= copy_item(src, target / name, is_dir, args.force)

    if not wrote_any:
        print("\nNothing written — the target is already set up. "
              "Author a deck and render it with the driver.")
        return

    print(
        "\nDone. Next:\n"
        "  1. Author a deck at <module>/slides/<deck>.qmd — copy "
        "slides_template/template.qmd as the starting point.\n"
        "  2. Render + screenshot it:\n"
        "     python .claude/skills/author-verify-slides/driver.py "
        "<module>/slides/<deck>.qmd --all --reveal-all\n"
        "  3. Open the PNGs and look at them."
    )


if __name__ == "__main__":
    main()
