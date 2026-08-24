# Advanced / Rarely Needed Quarto Reveal.js Features

Common features (fragments, transitions, basic auto-animate, layout helpers, backgrounds) live in SKILL.md. This file covers the genuinely rare cases.

## Slide Visibility

```markdown
## Hidden Slide {visibility="hidden"}
## Optional Extra {visibility="uncounted"}   # excluded from progress bar / numbering
```

## Presentation Size

```yaml
format:
  revealjs:
    width: 1050      # default
    height: 700      # default
    margin: 0.1      # 0-1, empty space around content
    min-scale: 0.2
    max-scale: 2.0
```

## Absolute Positioning

Place elements at exact coordinates with the `.absolute` class (units default to px):

```markdown
![](a.png){.absolute top=200 left=0 width="350" height="300"}
![](b.png){.absolute top=50 right=50 width="450" height="250"}
![](c.png){.absolute bottom=20 right=100 width="300" height="300"}
```

Attributes: `width`, `height`, `top`, `left`, `bottom`, `right`.

## Auto-Animate — Advanced

### Element matching with data-id

When automatic matching can't work (e.g. empty boxes), tie elements together explicitly:

```markdown
## {auto-animate=true}
::: {data-id="box1" style="background:#2780e3; width:200px; height:150px;"}:::

## {auto-animate=true}
::: {data-id="box1" style="background:#2780e3; width:350px; height:350px; border-radius:200px;"}:::
```

### Animation settings

Global:
```yaml
format:
  revealjs:
    auto-animate-easing: ease-in-out
    auto-animate-unmatched: false
    auto-animate-duration: 0.8
```

Per-slide / per-element attributes:
- `auto-animate-easing` — CSS easing function
- `auto-animate-unmatched` — true/false: fade in elements with no match
- `auto-animate-duration` — seconds
- `auto-animate-delay` — seconds (element-level only)
- `auto-animate-id` — id tying slides together
- `auto-animate-restart` — break apart two adjacent auto-animate slides

## Custom Fragments (CSS-defined effects)

```markdown
::: {.fragment .custom .blur}
Becomes focused when stepped to
:::
```

```css
.reveal .slides section .fragment.blur { filter: blur(5px); }
.reveal .slides section .fragment.blur.visible { filter: none; }
```

`.custom` tells Reveal to skip its default fade-in. The `.visible` class is applied as each fragment is stepped through.

### Nested fragments

```markdown
::: {.fragment .fade-in}
::: {.fragment .highlight-red}
::: {.fragment .semi-fade-out}
in > red > semi-out
:::
:::
:::
```

## Parallax Background

```yaml
format:
  revealjs:
    parallax-background-image: bg.png
    parallax-background-size: "2100px 900px"
    parallax-background-horizontal: 200   # optional
    parallax-background-vertical: 50      # optional
```

## Vertical / Nested Slides

```yaml
format:
  revealjs:
    navigation-mode: vertical   # linear | vertical | grid
    controls-layout: bottom-right
    controls-tutorial: true
```

Structure: `#` = horizontal axis, `##` = vertical axis beneath it.

```markdown
# Topic 1
## Topic 1 detail A
## Topic 1 detail B
# Topic 2
## Topic 2 detail A
```

Navigation modes: `linear` (arrows step through everything), `vertical` (left/right horizontal, up/down vertical), `grid` (keeps vertical index when moving horizontally).

**Warning:** audiences often don't realize vertical slides exist and skip them. Use only for optional drill-down content. `controls-layout: bottom-right` is incompatible with `logo`.

## Touch Navigation

```yaml
format:
  revealjs:
    touch: false
    controls: true   # give phone/tablet users on-screen controls
```

## Reveal Plugins

```yaml
format:
  revealjs:
    revealjs-plugins:
      - myplugin
```

Plugin folder layout:
```
myplugin/
├── plugin.yml      # name: RevealPluginFn  /  script: [plugin.js]
└── plugin.js
```

Built in already (no need to add): Multiplex, RevealMenu, RevealChalkboard, PdfExport.

## Custom Title Slide

```yaml
format:
  revealjs:
    template-partials:
      - title-slide.html     # your own HTML structure
    center-title-slide: false  # stop the title slide from vertically centering
```

Start from Quarto's "fancy" title-slide partial in the quarto-cli repo and customize, saving as `title-slide.html` beside the presentation.
