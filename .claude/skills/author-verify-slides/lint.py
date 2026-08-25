#!/usr/bin/env python
"""Lint a Quarto reveal.js deck for the defects a screenshot cannot show you.

Screenshots catch overflow, illegible figures and broken diagrams. They do not
catch an em dash, a banned word, a title that names its topic instead of its
point, or a chart hand-rolled inside the deck instead of drawn by the project's
shared plotting module. Those are all textual, all mechanical, and all of them
have shipped in this repo at least once.

    python .claude/skills/author-verify-slides/lint.py slides/03_deck.qmd
    python .claude/skills/author-verify-slides/lint.py slides/*.qmd --strict

Exit status is 0 when nothing above the failure threshold fired, 1 otherwise.
With no --strict, only ERROR fails the run; with --strict, WARN fails too.

Every rule is one function in RULES, so adding a project's own house rule is a
few lines. Rules that are project-specific rather than universal read their
configuration from the constants at the top of the file.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Configuration. These are the house rules; change them here, not in the rules.
# --------------------------------------------------------------------------

#: Words that make a slide sound like marketing rather than teaching.
BANNED_WORDS = [
    "crucial", "robust", "leverage", "seamless", "cutting-edge", "delve",
    "unlock", "harness the power", "game-changing", "revolutionise",
    "revolutionize", "best-in-class", "world-class", "paradigm shift",
]

#: Spellings the deck must not mix. Each entry is (bad_pattern, preferred).
SPELLING = [
    (r"\b(visuali|organi|recogni|normali|summari|emphasi|analy)s(e|es|ed|ing|ation)\b",
     "use the -z- spelling consistently across the course"),
]

#: A title this short is fine; longer than this and it wraps on the projector.
MAX_TITLE_CHARS = 62

#: A bullet longer than this is a paragraph wearing a dash.
MAX_BULLET_CHARS = 110

#: More than this many bullets in one list and nobody reads the last ones.
MAX_BULLETS_PER_LIST = 6

#: Titles that name a topic rather than state a conclusion, as a heuristic:
#: a title with no verb in it is usually a label.
_VERBLESS_HINTS = re.compile(
    r"^(the |a |an )?[\w$\\{}^+*/()\-]+([ :.,\-]+[\w$\\{}^+*/()\-]+){0,5}$", re.I)
_HAS_VERB = re.compile(
    r"\b(is|are|was|were|has|have|do|does|can|cannot|must|will|would|should|"
    r"makes?|breaks?|shows?|hides?|gives?|takes?|buys?|costs?|beats?|wins?|"
    r"loses?|fails?|passes?|needs?|requires?|explodes?|widens?|separates?|"
    r"turns?|keeps?|moves?|sets?|clears?|tests?|checks?|ranks?|scores?|"
    r"assumes?|rests?|comes?|exist|exists|reveal|reveals|expose|exposes|"
    r"isolate|isolates|obscure|obscures|verify|verifies|split|splits|"
    r"flatter|flatters|license|licenses|name|names|resample|resamples|"
    r"pick|picks|choose|chooses|avoid|avoids|start|starts|go|going|"
    r"dividing|choosing|rolling|seeing|widen)\b", re.I)


class Finding:
    __slots__ = ("level", "path", "line", "rule", "message", "fix")

    def __init__(self, level, path, line, rule, message, fix):
        self.level, self.path, self.line = level, path, line
        self.rule, self.message, self.fix = rule, message, fix

    def __str__(self):
        loc = f"{self.path}:{self.line}"
        return (f"[{self.level}] {loc}  {self.rule}\n"
                f"        {self.message}\n"
                f"        fix: {self.fix}")


def _blocks(lines):
    """Yield (index, line, in_code_fence, in_yaml) for every line."""
    fence = False
    yaml = False
    for i, ln in enumerate(lines, start=1):
        st = ln.strip()
        if i == 1 and st == "---":
            yaml = True
            yield i, ln, False, True
            continue
        if yaml:
            yield i, ln, False, True
            if st == "---":
                yaml = False
            continue
        if st.startswith("```"):
            fence = not fence
            yield i, ln, True, False
            continue
        yield i, ln, fence, False


def _slide_titles(lines):
    """(line_number, title_text) for real slide headings only.

    A `##` inside a ::: div is a callout title, not a slide, and a `#` inside a
    fenced block is a comment.
    """
    out, fence, depth = [], False, 0
    for i, ln in enumerate(lines, start=1):
        st = ln.strip()
        if st.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if st.startswith(":::"):
            depth = depth + 1 if st.lstrip(":").strip() else max(0, depth - 1)
            continue
        if depth == 0 and (ln.startswith("# ") or ln.startswith("## ")):
            title = re.sub(r"\{.*", "", ln.lstrip("#")).strip()
            out.append((i, title))
    return out


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------

def rule_em_dash(path, text, lines):
    for i, ln, in_code, in_yaml in _blocks(lines):
        if in_code or in_yaml:
            continue
        if "—" in ln:
            yield Finding("ERROR", path, i, "em-dash",
                          "an em dash on a slide reads as an aside nobody has "
                          "time for at projector size",
                          "recast as two sentences, a colon, or a semicolon")


def rule_banned_words(path, text, lines):
    for i, ln, in_code, in_yaml in _blocks(lines):
        if in_code or in_yaml:
            continue
        low = ln.lower()
        for w in BANNED_WORDS:
            if re.search(rf"\b{re.escape(w)}\b", low):
                yield Finding("ERROR", path, i, "banned-word",
                              f"{w!r} is marketing language, not teaching "
                              "language",
                              "say the specific thing the word is standing in for")


def rule_spelling(path, text, lines):
    for i, ln, in_code, in_yaml in _blocks(lines):
        if in_code or in_yaml:
            continue
        for pattern, advice in SPELLING:
            m = re.search(pattern, ln)
            if m:
                yield Finding("WARN", path, i, "spelling",
                              f"{m.group(0)!r} mixes spelling conventions",
                              advice)


def rule_inline_matplotlib(path, text, lines):
    """The rule this repo has broken most often: a chart built inside a deck.

    A figure drawn inline in a `.qmd` can drift from the one the lab draws, and
    then a slide claims something the students' own code does not show.
    """
    patterns = [
        (r"plt\.subplots\s*\(", "plt.subplots inside a deck"),
        (r"^\s*ax\.(plot|bar|barh|scatter|hist|fill_between)\s*\(", "a bare ax.* call"),
        (r"^\s*axes\[\d\]\.(plot|bar|barh|scatter|hist|fill_between)\s*\(",
         "a bare axes[...] call"),
    ]
    fence_lang = None
    for i, ln in enumerate(lines, start=1):
        st = ln.strip()
        if st.startswith("```"):
            fence_lang = None if fence_lang is not None else st.strip("`").strip()
            continue
        if fence_lang is None:
            continue
        # only executable python cells matter; ```python is highlight-only, but
        # a highlight block showing hand-rolled matplotlib is just as much a
        # duplicate of the plotting module, so both are flagged.
        if not (fence_lang.startswith("{python}") or fence_lang.startswith("python")):
            continue
        for pattern, what in patterns:
            if re.search(pattern, ln):
                yield Finding("ERROR", path, i, "inline-chart",
                              f"{what}: this figure is not coming from the "
                              "project's shared plotting module",
                              "move it into coursekit/plotting.py with a "
                              "signature the lab can call, then call it here")
                break


def rule_python_fence_confusion(path, text, lines):
    """`{python}` executes; `{.python}` only highlights. Confusing them is the
    most common render failure in this repo."""
    for i, ln in enumerate(lines, start=1):
        if re.match(r"^\s*```\s*\{\s*\.python", ln):
            yield Finding("WARN", path, i, "fence",
                          "```{.python} is not a Quarto engine block; it "
                          "highlights but never runs",
                          "use ```{python} to execute, or ```python to "
                          "highlight only")


def rule_title_length(path, text, lines):
    for i, title in _slide_titles(lines):
        plain = re.sub(r"\$[^$]*\$", "x", title)
        plain = re.sub(r"\\\w+|[{}]", "", plain)
        if len(plain) > MAX_TITLE_CHARS:
            yield Finding("WARN", path, i, "title-length",
                          f"title is {len(plain)} characters and will wrap to "
                          "two lines on the projector",
                          f"cut to {MAX_TITLE_CHARS} or fewer, or move the "
                          "qualifier into the body")


def rule_title_states_a_point(path, text, lines):
    """A title should carry the slide's conclusion, not name its topic.

    This one is a heuristic (a title with no verb is usually a label) and it
    has false positives, so it reports at INFO: it is a prompt to look at the
    title, not a verdict on it. "5000 possible futures" trips it and is right.
    """
    skip = re.compile(r"(recap|summary|^[A-E]\.|rightarrow|→|lab [a-d]|"
                      r"exercise \d|the goal|where we are going|plan$)", re.I)
    for i, title in _slide_titles(lines):
        if skip.search(title):
            continue
        plain = re.sub(r"\$[^$]*\$", "x", title).strip()
        if not plain:
            continue
        if _HAS_VERB.search(plain):
            continue
        if plain.endswith("?"):
            continue
        if _VERBLESS_HINTS.match(plain):
            yield Finding("INFO", path, i, "title-names-topic",
                          f"{title!r} may name the topic rather than state the "
                          "point the slide makes",
                          "rewrite as the sentence you would say out loud when "
                          "the slide appears, or confirm this one is a "
                          "deliberate hook")


def rule_bullet_length(path, text, lines):
    for i, ln, in_code, in_yaml in _blocks(lines):
        if in_code or in_yaml:
            continue
        m = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)$", ln)
        if not m:
            continue
        body = re.sub(r"\*\*|\*|`|\$[^$]*\$", "", m.group(2)).strip()
        if len(body) > MAX_BULLET_CHARS:
            yield Finding("WARN", path, i, "bullet-length",
                          f"bullet is {len(body)} characters; at that length it "
                          "is a paragraph and the room reads instead of listening",
                          f"cut to {MAX_BULLET_CHARS} or fewer, or move the "
                          "detail into ::: {.notes}")


def rule_bullet_count(path, text, lines):
    run_start, run = None, 0
    for i, ln, in_code, in_yaml in _blocks(lines):
        if in_code or in_yaml:
            continue
        if re.match(r"^\s*([-*+]|\d+\.)\s+\S", ln):
            if run == 0:
                run_start = i
            run += 1
            continue
        if ln.strip() == "":
            continue
        if run > MAX_BULLETS_PER_LIST:
            yield Finding("WARN", path, run_start, "bullet-count",
                          f"{run} bullets in one list",
                          f"cut to {MAX_BULLETS_PER_LIST} or split across two "
                          "slides; nobody reads past the sixth")
        run = 0
    if run > MAX_BULLETS_PER_LIST:
        yield Finding("WARN", path, run_start, "bullet-count",
                      f"{run} bullets in one list",
                      f"cut to {MAX_BULLETS_PER_LIST} or split across two slides")


def rule_speaker_notes(path, text, lines):
    """A content slide with no notes is a slide the instructor has to improvise."""
    titles = _slide_titles(lines)
    if not titles:
        return
    bounds = [t[0] for t in titles] + [len(lines) + 1]
    skip = re.compile(r"(recap|summary|rightarrow|→|lab [a-d]|^[A-E]\.)", re.I)
    for (start, title), end in zip(titles, bounds[1:]):
        if skip.search(title) or lines[start - 1].startswith("# "):
            continue
        body = "\n".join(lines[start:end - 1])
        if "::: {.notes}" not in body:
            yield Finding("INFO", path, start, "no-speaker-notes",
                          f"{title!r} carries no ::: {{.notes}} block",
                          "add the sentence you would say that is not printed "
                          "on the slide, or confirm the slide truly needs none")


def rule_static_image_of_data(path, text, lines):
    for i, ln, in_code, in_yaml in _blocks(lines):
        if in_code or in_yaml:
            continue
        m = re.search(r"!\[[^\]]*\]\(([^)]+\.(png|jpg|jpeg|gif))\)", ln, re.I)
        if m:
            yield Finding("INFO", path, i, "static-image",
                          f"static image {m.group(1)!r}",
                          "if this shows data, draw it with a {python} cell "
                          "instead so it cannot go stale")


RULES = [
    rule_em_dash,
    rule_banned_words,
    rule_spelling,
    rule_inline_matplotlib,
    rule_python_fence_confusion,
    rule_title_length,
    rule_title_states_a_point,
    rule_bullet_length,
    rule_bullet_count,
    rule_speaker_notes,
    rule_static_image_of_data,
]

LEVEL_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}


def lint(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    out = []
    for rule in RULES:
        out.extend(rule(str(path).replace("\\", "/"), text, lines))
    out.sort(key=lambda f: (LEVEL_ORDER[f.level], f.line))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("decks", nargs="+", help="one or more .qmd decks")
    ap.add_argument("--strict", action="store_true",
                    help="fail on WARN as well as ERROR")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress INFO findings")
    args = ap.parse_args(argv)

    paths = []
    for d in args.decks:
        p = Path(d)
        paths.extend(sorted(Path().glob(d)) if any(c in d for c in "*?[") else [p])

    total = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for p in paths:
        if not p.exists():
            print(f"lint: no such deck: {p}", file=sys.stderr)
            return 2
        findings = [f for f in lint(p)
                    if not (args.quiet and f.level == "INFO")]
        print(f"\n=== {p} ===")
        if not findings:
            print("  clean")
        for f in findings:
            total[f.level] += 1
            print(f)

    print(f"\n{total['ERROR']} error(s), {total['WARN']} warning(s), "
          f"{total['INFO']} note(s)")
    fail = total["ERROR"] or (args.strict and total["WARN"])
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
