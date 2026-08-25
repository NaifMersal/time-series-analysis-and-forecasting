---
name: author-verify-slides
description: Author, render, preview, and screenshot SDAIA-branded Quarto reveal.js slide decks (.qmd). Use when asked to build, render, preview, screenshot, or visually verify a deck, check SDAIA branding/overflow, or author a new slide deck. Branding and Quarto patterns are constant across SDAIA slide projects; project-specific facts (course name, module layout, indexing/distribution) live in the project's CLAUDE.md.
---

# Author & Verify SDAIA Course Slides

SDAIA course decks are Quarto reveal.js presentations: `.qmd` source →
`quarto render` → self-contained HTML under `output/`. You cannot tell from
the markdown whether branding applied, text overflowed, a diagram rendered,
or a dark section is readable — **you have to look at the rendered slide.**

The driver does that: `python .claude/skills/author-verify-slides/driver.py <deck.qmd>`
renders the deck and screenshots chosen slides with headless Chrome so you
can open the PNGs and inspect them.

This skill is shared across SDAIA Quarto-slide projects, so it covers only
what's constant: **SDAIA branding + Quarto authoring patterns + render/verify
tooling**. It is **self-contained**: `bundle/` carries the branding config and
assets, so the skill can stand up a branded slide project in a fresh repo on its
own (see "Bootstrapping into a fresh project" below).

> **Project-specific facts live in the project's `CLAUDE.md`** — the
> project/course name, module/directory layout, how decks are indexed
> (e.g. `tracks.yml`, `gen_index.py`), and how a student distribution is
> built. Consult `CLAUDE.md` for those; don't hard-code them here.

References (load on demand):
- `reference/patterns.md` — the full SDAIA pattern library: branding rules,
  color palette + CSS vars, dark-slide rules, gradients, callouts, cardbox,
  DOT/mermaid theming, code, layout, the annotated template, common mistakes.
- `reference/advanced.md` — rarely-needed Quarto features (absolute
  positioning, custom size, advanced auto-animate, plugins, etc.).
- `bundle/` — the portable SDAIA slide scaffold the skill carries: a generic
  `_quarto.yml` (global branding) and `slides_template/` (the `template.qmd`
  starter + `assets/` brand files: `sdaia.scss`, the logo/icon SVGs,
  `splash.lua`, `favicon.html`). `scaffold.py` copies it into a project.

All paths below are **relative to the repo root**. Run commands from there.

## Prerequisites

- **Quarto** `>= 1.8.26` (`_quarto.yml` pins this). Check: `quarto --version`.
  Not a pip package — if missing, install from https://quarto.org/docs/get-started.
- **Python 3.11+** (for the driver) — already used by the repo.
- **Google Chrome or Edge** for screenshots. The driver auto-finds
  `C:\Program Files\Google\Chrome\Application\chrome.exe` (or Edge).
  Override with env var `SLIDES_CHROME=<path-to-chrome.exe>`.

No `npm`/`node` needed — screenshots use the installed Chrome directly.

## Run (agent path) — render + screenshot

This is the path you want almost every time.

```bash
# Render the deck and screenshot the title + two interior slides:
python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --slides 0,4,8
```

Then **open the PNGs and actually look at them** — they land in
`output/_screenshots/<deck-stem>/<deck-stem>_sNN.png`. Slide index `0` is the
title slide; the rest are every `#`/`##` heading in **document order**
(vertical sub-slides included — see below). The `sNN` in the filename is the
**0-based** index; the counter printed on the slide itself ("17 / 26") is
**1-based** (`NN + 1`), and each `[shot]` line prints both plus the title so you
never have to guess the mapping.

**Selecting slides by name.** `--slides` takes integer indices *or*
case-insensitive title/id substrings (mix them), so you don't have to count:

```bash
python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --slides reasoning,"Key API"
```

Useful options:

```bash
# Shoot only slides whose source changed vs git HEAD — the fast edit/verify loop:
python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --changed --reveal-all

# Skip rendering — screenshot an already-rendered deck (fast iteration):
python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --slides 0,4,8 --no-render

# Screenshot every slide (auto-detected count, vertical-aware):
python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --all

# Reveal ALL fragments first — REQUIRED to catch overflow (see below):
python .claude/skills/author-verify-slides/driver.py <module>/slides/<deck>.qmd --all --reveal-all
```

`--changed` is the one to reach for after editing a few slides: it diffs the
deck against HEAD, maps the changed source lines back to slides, and shoots
only those (an untracked/brand-new deck counts as all-changed). Combine with
`--reveal-all` to catch overflow on exactly the slides you touched.

Defaults: viewport `1600x900` (16:9, matches the deck aspect), `--wait 8000`
(ms Chrome waits for reveal.js + fragments to settle), output to
`output/_screenshots/`. See `--help` for `--width/--height/--outdir/--wait`.

The driver is `.claude/skills/author-verify-slides/driver.py` — edit it if you need a
new capability (e.g. shoot a specific fragment step).

### Things that bite on real decks

**Don't count headings to guess an index.** A `## Foo` inside a `::: {.callout}`
or `::: {.column}` fenced div is a callout/column *title*, not a slide — so
eyeballing the source and counting `#`/`##` lines gives the wrong `--slides N`.
Either select by title substring (`--slides "Reasoning Parameters"`) or read the
`[shot]` lines, which print `sNN (slide N/total) "Title"` for every slide.

**Vertical decks.** If a deck uses `#` section dividers (the SDAIA
`{.sdaia-dark}` divider pattern), Quarto nests each `##` slide as a *vertical*
child of its divider. Flat `#/N` index navigation only reaches the horizontal
dividers — so the *content* slides never get shot. The driver avoids this by
enumerating and navigating by each slide's reveal.js **id** (`#/<id>`), which
addresses flat and vertical decks identically. `--slides N` indexes into the
full document-order list; you don't have to know whether the deck is nested.

**Fragments hide overflow.** A deep-linked slide loads at *fragment 0*, so
anything after a `. . .` pause (later bullets, a table, a callout, a `.footer`)
or inside a `::: {.fragment}` div is **not shown**. That late content is exactly
what overflows the frame. If you shoot without revealing fragments you'll see
whitespace and wrongly call the slide clean. Use **`--reveal-all`**: it renders
a throwaway copy with every fragment source neutralized — `. . .` pauses
dropped, `.fragment`/`.incremental` classes renamed to an inert class, and a
global `incremental: true` flipped to false — so every slide is in its final
state, writes `<stem>_full_sNN.png`, then cleans up. Always pass `--reveal-all`
for an overflow/branding pass on a finished deck. (Code fences are left
untouched, so `. . .`/`{.fragment}` shown *inside* a code sample survive.)

## Lint — the defects a screenshot cannot show you

A screenshot proves the slide *renders*. It says nothing about an em dash, a
banned word, a nine-bullet list, a title that names its topic instead of its
point, or a chart hand-rolled inside the deck instead of drawn by the project's
shared plotting module. Those are textual and mechanical, so a linter catches
them for free and catches them before you spend a render cycle.

```bash
python .claude/skills/author-verify-slides/lint.py slides/03_deck.qmd
python .claude/skills/author-verify-slides/lint.py slides/*.qmd --strict --quiet
```

Three levels. **ERROR** is mechanical and always wrong: an em dash in prose, a
banned word, `plt.subplots` or a bare `ax.plot` inside a deck. **WARN** is a
threshold someone chose: title over 62 characters, bullet over 110, more than
six bullets in one list, mixed -ise/-ize spelling. **INFO** is a prompt to look,
not a verdict: a content slide with no `::: {.notes}`, a static image that might
be showing data, a title with no verb in it.

Exit status is 0 unless an ERROR fired; `--strict` fails on WARN too, which is
what you want in a pre-delivery gate. `--quiet` drops the INFO findings.

The `inline-chart` rule is the one worth keeping. A figure built inside a `.qmd`
can drift from the one the lab draws, and then a slide claims something the
students' own code does not show. Run against this repo's deck 3 as it stood
before the Day 2 pass, the rule fires 41 times.

House rules live in the constants at the top of `lint.py` — `BANNED_WORDS`,
`SPELLING`, the three numeric thresholds. Each rule is one generator function in
`RULES`, so a project-specific rule is a few lines.

## Bootstrapping into a fresh project

Branding only applies if the project has a root `_quarto.yml` and a
`slides_template/assets/` dir (the driver renders via `quarto render`, which
reads them). A repo already set up this way — like the course repo — needs
nothing; **skip this step**. In a fresh repo where they're missing, scaffold
them from the skill's bundle once:

```bash
# Copy bundle/_quarto.yml + bundle/slides_template/ into the repo root.
# Non-destructive: skips anything that already exists (use --force to overwrite).
python .claude/skills/author-verify-slides/scaffold.py
```

> **Sync caveat.** `bundle/` is the skill's **own copy** of the SDAIA branding.
> If `sdaia.scss`, the brand assets, or the `_quarto.yml` config change, update
> **both** the host project's `slides_template/` + `_quarto.yml` **and** the
> skill's `bundle/` — they don't auto-sync, and a host repo may intentionally
> diverge from the bundle.

## Authoring a new deck

1. Copy `slides_template/template.qmd` as the starting point (or, if the project
   has none, `bundle/slides_template/template.qmd`) — it carries the expected
   sectioning conventions (`.sdaia-dark` sections, columns, cardbox, callouts).
   Don't hand-write the YAML.
2. Branding is applied **globally** by `_quarto.yml` (theme
   `slides_template/assets/sdaia.scss`, the SDAIA logo, the `splash.lua`
   filter, the title-slide background). A deck's own front-matter only
   needs `title:` / `subtitle:` / `date:` and `format: revealjs` — do
   **not** re-declare theme/logo per deck.
3. Follow `reference/patterns.md` for the full SDAIA pattern library: color
   palette + CSS vars, dark-slide rules, gradients for section dividers,
   callouts, cardbox, DOT/mermaid diagram theming.
4. Register / index the new deck per the project's `CLAUDE.md`.
5. Render + screenshot with the driver and inspect every new slide.

The single most important branding rule: **every dark-background slide
must carry the `.sdaia-dark` class**, or text stays dark-on-dark and is
unreadable. Verify dark slides by screenshot, not by eye on the source.

## Run (human path) — live preview

For interactive authoring a human can use the live-reloading server. It is
useless for headless verification (it just opens a browser tab) and boots
slowly (it does a full render first, ~30s):

```bash
quarto preview <module>/slides/<deck>.qmd --port 7811
```

Serves at `http://localhost:<port>/<deck-path>.html`; Ctrl-C to stop.

## Gotchas

- **`os error 32` on render** ("process cannot access the file ...
  `<deck>_files/libs`"). A file-watcher (VS Code / Antigravity / a stray
  `quarto preview`) is holding the intermediate `_files` dir on Windows.
  It's transient — the driver **retries once automatically**; manually,
  just re-run `quarto render`. The HTML is often written even on the
  failing run.
- **Render must happen from the repo root**, not from inside the module
  dir. `_quarto.yml` sets `output-dir: output`, `execute-dir`, and the
  global theme/filter paths resolve relative to root. The driver always
  `cd`s to root for you.
- **Deep-linking uses `file:///…#/<id>`** — the driver navigates by each
  slide's reveal.js id, not a flat `#/N` index, so it reaches vertical
  sub-slides too (see "Two things that bite on real decks" above). reveal.js
  honors the initial hash even with `history: false`.
- **Temp copies must not start with `_`.** Quarto treats `_`-prefixed files as
  non-project, rendering them *without* the global theme/output-dir (no
  branding, wrong output path). The driver's `--reveal-all` copy is named
  `tmp_revealall_<stem>.qmd` for this reason; follow the same rule if you
  hand-roll a temp deck.
- **Chrome `--screenshot` needs an absolute output path** or it silently writes
  nothing. The driver resolves paths for you; mind this if you script Chrome
  directly.
- **Output is not portable.** `_quarto.yml` sets `embed-resources: false`,
  so a deck's HTML depends on its `_files/` folder. Fine for local
  screenshots; don't email a lone `.html`.
- **`{python}` vs `{.python}`.** A `{python}` cell *executes* at render
  (needs Jupyter + `execute-dir`); `{.python}` (leading dot) only
  highlights. Most course slides only display code — use the dot.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `quarto: command not found` | Install Quarto; ensure it's on PATH (`quarto --version`). |
| Driver: `No Chrome/Edge found` | `SLIDES_CHROME=<full path to chrome.exe>` before the command. |
| Driver: `rendered HTML not found` | You passed `--no-render` but never rendered. Drop `--no-render`. |
| Screenshot is blank / wrong slide | Increase `--wait` (e.g. `--wait 12000`); reveal.js hadn't settled. |
| `--all` shot dividers + duplicate frames | Old symptom of flat `#/N` nav on a vertical deck. The driver now navigates by id; re-run after updating it. |
| Slide looks clean but overflows in the talk | You shot fragment 0. Re-run with `--reveal-all` to render the final state. |
| Temp/preview deck renders unbranded | Its filename starts with `_` (Quarto ignores it). Rename without the leading underscore. |
| Render fails with `os error 32` | Close the editor/preview holding `<deck>_files/`, or just re-run. |
