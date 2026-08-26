# SDAIA Quarto Reveal.js Slide Patterns

The reference library for the `run-slides` skill: **what to write inside a
deck**. SDAIA decks are Quarto reveal.js presentations — a `.qmd` markdown
source renders to a self-contained HTML deck. For *rendering and visually
verifying* a deck, see the skill's `SKILL.md` (the driver screenshots slides
so you can actually look at them; you cannot tell from markdown whether
branding applied or text overflowed).

> **Project-specific facts are not here.** The project/course name, module
> layout, and how decks get indexed or distributed (e.g. `tracks.yml`,
> `gen_index.py`, the student-dist build) live in the project's `CLAUDE.md`.
> This file covers only what is constant across SDAIA slide projects: the
> branding and the Quarto authoring patterns.

## Workflow

1. Copy `slides_template/template.qmd` as your starting point (or, in a repo
   that has no `slides_template/`, the skill's `bundle/slides_template/template.qmd`)
   — never hand-write the front matter.
2. Write content with the patterns below; respect the **Design Defaults**.
3. Render + screenshot with the `run-slides` driver and inspect every slide.
4. Register / index the new deck per the project's `CLAUDE.md`.
5. Skim **Common Mistakes** before you call it done — most failures live there.

## Branding is global — keep front matter minimal

This is the single most important thing to get right, and the one most
guides get wrong.

`_quarto.yml` at the repo root applies **all** branding globally: the SDAIA
theme (`slides_template/assets/sdaia.scss`), the logo, transitions, the
title-slide background, slide numbers, and the `splash.lua` filter. **Do
not re-declare any of it per deck.** (That `_quarto.yml` and the
`slides_template/assets/` it points at are what the skill's `bundle/` carries
and `scaffold.py` drops into a fresh project — see the skill's `SKILL.md`.)
A deck's front matter needs only:

```yaml
---
title: "Session Title"
subtitle: "Session Subtitle"
date: today
format: revealjs
---
```

That's the whole header. If you find yourself pasting `theme:`, `logo:`, or
`title-slide-attributes:` into a deck, stop — it's already global, and a
local override risks breaking brand consistency.

## Design Defaults

Apply these unless there's a specific reason not to:

- **One idea per slide**; aim for ~5 bullets max. Split a dense slide in two
  rather than cramming.
- Use **columns** to compare two things side by side.
- Use `incremental` **sparingly** — reveal-on-click everywhere annoys an
  audience. Reserve it for lists you want to walk through deliberately.
- Use `{.smaller}` or `{.scrollable}` for the occasional overflow slide
  rather than shrinking a whole deck.
- For chained-system / failure narratives, prefer a cascade **story** over
  probability math.
- Verify dark slides and diagrams by **screenshot**, not by eye on the source.

## Slide Structure

```markdown
# Section Divider        ← Level-1 heading: a title/section slide
## New Slide             ← Level-2 heading: a normal slide
---                      ← horizontal rule: a slide with no title
```

```markdown
## A Slide

- Point one
- Point two
    - Sub-point
```

## Core Features

### Incremental reveal and pauses

```markdown
::: {.incremental}
- Appears first
- Then this
:::

::: {.nonincremental}
- All at once (use when global incremental is on)
:::

Content before

. . .

Content after (the `. . .` needs a blank line above and below it)
```

### Columns

```markdown
:::: {.columns}
::: {.column width="50%"}
Left
:::
::: {.column width="50%"}
Right
:::
::::
```

### Overflow

```markdown
## Slide {.smaller}      # smaller font
## Slide {.scrollable}   # scroll within the slide (add .nostretch too — see Mistakes)
## Slide {.code-shrink}  # shrink only code/JSON blocks (not title/prose)
::: {.code-shrink}       # …or wrap a single overflowing code block
::: {.code-shrink-xs}    # tighter variant for the worst cases
```

### Speaker notes

```markdown
::: {.notes}
Visible only in speaker view (press S).
:::
```

### Layout helpers

```markdown
::: {.r-stack}             # layer elements on top of each other (pair with fragments)
::: {.r-fit-text}          # make text as large as the slide allows
## Title {.center}         # vertically center this slide's content
![](img.png){.r-stretch}   # resize image to fill remaining vertical space
```

## Code

**Display only** (no execution) — note the **leading dot**. This is what the
vast majority of course slides want:

````markdown
```{.python code-line-numbers="6-8"}
# lines 6-8 highlighted
```

```{.python code-line-numbers="|6|9"}
# progressive: all → line 6 → line 9
```
````

**Executable cell** — runs at render time (needs Jupyter; `execute-dir` is
set in `_quarto.yml`). Code is hidden by default in slides, so add
`#| echo: true` to show it:

````markdown
```{python}
#| echo: true
#| output-location: fragment   # fragment | slide | column | column-fragment
import matplotlib.pyplot as plt
plt.plot([1, 2, 3])
```
````

> `{python}` executes, `{.python}` (leading dot) only highlights. Confusing
> the two is the most common render failure — see Common Mistakes.

## Diagrams

Draw flows with the theme's **`.flowrow` / `.flowconv` classes**, not with
Graphviz. A DOT graph renders with its own fonts, its own spacing and its own
idea of a box, so it lands on the slide as a foreign object beside the deck's
typography, and it cannot read the `--sdaia-*` variables. The HTML classes use
the deck's own type and palette, reflow with the slide, and stay legible at
projector size.

**A chain** — nodes left to right, arrows inserted between them:

````markdown
::: {.flowrow}
[$y_t$]{.flownode .navy}
[[STL]{.flowtitle}[splits off the seasonal part]{.flownote}]{.flownode .navy}
[[Forecast each part]{.flowtitle}[drift · seasonal naive]{.flownote}]{.flownode .teal}
[[Add them back]{.flowtitle}[one forecast]{.flownote}]{.flownode .purple}
:::
````

**A convergence** — several causes, one consequence:

````markdown
::: {.flowconv}
::: {.flowcauses}
[[Scale on the whole series]{.flowtitle}`scaler.fit(spine)`]{.flownode .coral}
[[Centred rolling features]{.flowtitle}`rolling(12, center=True)`]{.flownode .coral}
:::
[[The answer is in the input]{.flowtitle}[CV flatters the model.]{.flownote}]{.flownode .navy}
:::
````

A node carries an optional `[Heading]{.flowtitle}` and `[aside]{.flownote}`,
and inline code renders at a size that fits the box. Accent modifiers are
`.navy` (default), `.teal`, `.coral`, `.purple`; nodes invert automatically on
a `.sdaia-dark` slide. Keep a row to four nodes or fewer, and keep each label
to a few words, or the boxes wrap and the row goes tall.

**Mermaid** stays available for genuinely graph-shaped diagrams a row or a
convergence cannot express (sequence diagrams, gantt charts, a graph with
cycles). Set the theme block once at the top and use `classDef` rather than
per-node `style`, and note it takes **literal hex** colors:

````markdown
```{mermaid}
%%{init: {'theme':'base', 'themeVariables': {
  'fontFamily':'Noto Sans, system-ui, sans-serif', 'fontSize':'18px',
  'primaryColor':'#eef2f7', 'primaryTextColor':'#1C355E',
  'primaryBorderColor':'#1C355E', 'lineColor':'#5b6678'
}}}%%
graph LR
    A["Good path"] --> B["Context fills"]
    classDef good fill:#00AE8D,stroke:#1C355E,stroke-width:2px,color:#fff;
    classDef bad  fill:#E96852,stroke:#1C355E,stroke-width:2px,color:#fff;
    class A good;
    class B bad;
```
````

# SDAIA Brand Styling

## Color palette

Official SDAIA brand colors are used **verbatim on light slides**. The three
accents have a brightened **on-dark variant** used only on dark (navy)
backgrounds, where the brand hue loses contrast. The theme exposes both as
CSS variables and applies the on-dark variant automatically inside
`.sdaia-dark` sections.

| Role | Brand base (light) | On-dark variant | CSS var |
|------|-----|-----|-----|
| Primary Navy | `#1C355E` | — | `--sdaia-navy` |
| Coral | `#E96852` | `#FF7A5C` | `--sdaia-coral` / `--sdaia-coral-on-dark` |
| Teal/Green | `#00AE8D` | `#00C9A7` | `--sdaia-teal` / `--sdaia-teal-on-dark` |
| Purple | `#625D9C` | `#9B8EC0` | `--sdaia-purple` / `--sdaia-purple-on-dark` |
| Sky Blue | `#00C1DE` | — | `--sdaia-cyan` |
| Fresh Green | `#6ABF4B` | — | `--sdaia-green` |
| Warm Yellow | `#FFB548` | — | `--sdaia-yellow` |
| Ink / Dark Navy | `#101820` | — | `--sdaia-black` |

**The rule:** brand base on light slides; the `-on-dark` variant only on
dark backgrounds. In slide markup use `var(--sdaia-teal)` etc. — the theme
swaps to the on-dark variant for you inside `.sdaia-dark`.

## Dark slides

- **Every** dark-background slide must carry the `.sdaia-dark` class, or text
  stays dark-on-dark and is unreadable. This is the most-broken brand rule —
  verify by screenshot.
- **Content** dark slides: navy→purple gradient
  `background-gradient="linear-gradient(135deg, #1C355E, #625D9C)"` (reads
  richer than a flat color).

### Section color rotation — Cyclic Triad

Section dividers follow a **fixed three-color rotation** inspired by the
three gradient families in the SDAIA icon (`slides_template/assets/icon.svg`):

| Position in cycle | Accent | Gradient value |
|---|---|---|
| 1st (A, D, G …) | **Teal** | `linear-gradient(135deg, #1C355E, #00C9A7)` |
| 2nd (B, E, H …) | **Coral** | `linear-gradient(135deg, #1C355E, #FF7A5C)` |
| 3rd (C, F, I …) | **Purple** | `linear-gradient(135deg, #1C355E, #9B8EC0)` |

**Rules:**

1. **Section A always starts Teal.** Every deck opens with the same
   green-accented energy the icon does.
2. **Cycle repeats** — after Purple the next section goes back to Teal.
3. **Closing slide matches the last section.** The `## Questions?` or
   `## Wrap-up` slide reuses the accent of whichever section it belongs to
   (e.g. if the last section was Coral, the closing slide is Coral).
4. All three gradients share the same angle (`135deg`) and start from navy
   (`#1C355E`). The second stop is always the **on-dark variant** of the
   accent (not the brand-base), for contrast on the dark background.

```markdown
# A. First Section  {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #00C9A7)"}

# B. Second Section {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #FF7A5C)"}

# C. Third Section  {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #9B8EC0)"}

# D. Fourth Section {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #00C9A7)"}

## Questions? {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #00C9A7)"}
```

**Content** dark slides (non-dividers) always use navy→purple regardless of
which section they sit in:

```markdown
## Content Slide {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #625D9C)"}
```

## Callouts

```markdown
::: {.callout-important}
## The Rule
Critical information that must not be ignored.
:::

::: {.callout-tip}
## Course Goal
Helpful guidance or objectives.
:::

::: {.callout-note}
## Notice
Supplementary information or observations.
:::
```

## Card boxes

Use the `.cardbox` helper instead of hand-rolled inline styles. On
`.sdaia-dark` slides the card automatically flips to a light-on-dark
treatment.

```markdown
::: {.cardbox}
Content with coral accent border (default)
:::

::: {.cardbox .teal}
Teal accent — also `.purple` and `.navy` modifiers
:::
```

# Motion & Backgrounds

## Backgrounds

```markdown
## Title {background-color="#1C355E"}
## Title {background-gradient="linear-gradient(135deg, #1C355E, #00AE8D)"}
## Title {background-image="image.jpg" background-size="cover" background-opacity="0.5"}
## Title {background-video="video.mp4" background-video-loop="true"}
```

The deck-wide title-slide background is set globally in `_quarto.yml`; don't
re-declare it per deck.

## Fragments

```markdown
::: {.fragment .fade-up}
Fades up into view
:::

::: {.fragment .highlight-red}
Highlights in red
:::

::: {.fragment .highlight-current-blue}
Highlights blue only while it is the current step
:::
```

Common classes: `fade-in`/`fade-out`, `fade-up`/`-down`/`-left`/`-right`,
`fade-in-then-out`, `grow`, `shrink`, `strike`,
`highlight-red`/`green`/`blue`, `highlight-current-*`.

Order fragments explicitly with `fragment-index`:
```markdown
::: {.fragment fragment-index=2}Second:::
::: {.fragment fragment-index=1}First:::
```

Fragments inside columns animate independently:
```markdown
:::: {.columns}
::: {.column width="50%"}
::: {.fragment .fade-in}
Left appears first
:::
:::
::: {.column width="50%"}
::: {.fragment .fade-in}
Right appears second
:::
:::
::::
```

## Transitions

Set globally in `_quarto.yml`. Override per slide only when needed:
```markdown
## Zoom In {transition="zoom"}
## Fade {transition="fade"}
```

## Auto-animate

Add `auto-animate=true` to two adjacent slides; matching elements tween
between them. Tie elements together with `data-id` when automatic matching
can't work.

```markdown
## Concept {auto-animate=true}
::: {data-id="concept"}
**Core concept.**
:::

## Concept Expanded {auto-animate=true}
::: {data-id="concept"}
**Core concept.** Now with additional explanation.
:::
```

# Quick Template (annotated)

```markdown
---
title: "Presentation Title"
subtitle: "Session Description"
date: today
format: revealjs
---

# A. Section One {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #00C9A7)"}

## Key Point {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #625D9C)"}

::: {.callout-important}
## The Rule
Critical information here.
:::

. . .

:::: {.columns}
::: {.column width="50%"}
**Left**
- Point one
- Point two
:::
::: {.column width="50%"}
**Right**
- Point three
- Point four
:::
::::

## Animated Concept {auto-animate=true}
::: {data-id="concept"}
**Core concept.**
:::

## Animated Concept {auto-animate=true}
::: {data-id="concept"}
**Core concept.** Now with explanation.
:::

::: {.fragment .fade-up}
::: {.callout-tip}
## Key Takeaway
Insight revealed on click.
:::
:::

# B. Section Two {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #FF7A5C)"}

## Activity {.sdaia-dark background-color="#00AE8D"}

1. Step one
2. Step two

⏱️ **Time: 10 minutes**

## Questions? {.sdaia-dark background-gradient="linear-gradient(135deg, #1C355E, #FF7A5C)"}

::: {.r-fit-text}
Thank You
:::
```

# Common Mistakes

- **Re-declaring branding per deck.** `theme`, `logo`, transitions, and the
  title-slide background are global in `_quarto.yml`. Keep deck front matter
  to `title`/`subtitle`/`date`/`format: revealjs`.
- **Breaking the section color rotation.** Sections cycle Teal → Coral →
  Purple → repeat. Section A is always Teal. The closing slide matches the
  last section's accent. See "Cyclic Triad" above.
- **Forgetting `.sdaia-dark` on a dark slide.** Text stays dark-on-dark and
  is unreadable. Every dark-background slide needs the class.
- **`{python}` vs `{.python}`.** `{python}` *executes* at render (needs
  Jupyter); `{.python}` (leading dot) only *highlights*. Use the dot to just
  show code.
- **Executable code doesn't appear.** Cells hide code by default — add
  `#| echo: true`.
- **`. . .` pause does nothing.** It must be on its own line with a blank
  line above and below.
- **Diagram colors look off.** DOT/mermaid can't read `--sdaia-*` vars —
  paste literal hex.
- **`.scrollable` clips or distorts.** A slide with a single top-level image
  auto-stretches it, which conflicts with scrolling. Add `.nostretch` on
  scrollable slides (or per image with `{.nostretch}`).
- **Broken images after render.** Paths are relative to the `.qmd` file, not
  the working directory. Keep assets beside the deck.
- **`os error 32` on render (Windows).** A file-watcher (VS Code, a stray
  `quarto preview`) is holding `<deck>_files/`. Transient — just re-render;
  the `run-slides` driver retries once automatically.
- **Emailing a lone `.html`.** `embed-resources: false` is set globally, so a
  deck depends on its `_files/` folder. Fine for local screenshots; not
  portable as a single file.

# Advanced / rarely needed

For absolute positioning, custom presentation size, advanced auto-animate
(easing/duration, `auto-animate-id`), custom CSS fragments, parallax
backgrounds, vertical/nested slides, slide visibility, Reveal plugins, or
custom title-slide partials, see `reference/advanced.md`.
