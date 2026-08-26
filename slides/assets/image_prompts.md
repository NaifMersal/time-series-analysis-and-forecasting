# Image prompt manifest

Illustrative imagery only. **Anything a `{python}` cell can draw must be drawn by one** —
that is what keeps the slides and the labs from drifting apart, so a chart of data never
belongs in this file.

Record an image here *before* generating it, and mark its point of use in the deck with

```markdown
<!-- IMAGE: filename.png — prompt -->
```

Generated files live beside this manifest in `slides/assets/`, and are referenced from a
deck as `assets/filename.png` (paths resolve relative to the `.qmd`).

| File | Deck | Slide | Prompt | Status |
|---|---|---|---|---|
| _(none yet)_ | | | | |

## Notes

Days 1 and 2 currently use **no** illustrative images: every visual is either an
executable `{python}` chart or a `.flowrow` / `.flowconv` HTML diagram. That is deliberate
and worth preserving
— add a row here only when a picture would carry something the data cannot.

If a Day 3 deck needs, say, a conceptual illustration of transfer learning, that is the
kind of thing that belongs here.
