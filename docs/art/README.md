# docs/art — Documentation Asset Generators

Scripts that generate charts, diagrams, and illustrations for the user guide.
Run these at release time, not on every build.

## When to run

- When cutting a new version (after features are stable)
- When the UI color scheme changes
- When new tutorial pages are added that need generated charts
- Never during automated CI — output PNGs are committed to the repo

## Scripts

| Script | Output | Pages |
| --- | --- | --- |
| `generate_charts.py` | `docs/guide/media/*.png` + `*.caption.md` | your-first-funscript, reading-assessment |

## How to run

```bash
# From the repo root
python docs/art/generate_charts.py
```

Generated files go to `docs/guide/media/`. Commit them alongside the release tag.

## Adding a new chart

1. Add a function to `generate_charts.py` that returns a `dict` with keys:
   `image`, `page`, `task`, `type`, `tags`, `description`
2. Call `write_caption(meta, MEDIA_DIR)` to generate the companion `.caption.md`
3. Call your function from `if __name__ == "__main__"`

## Caption files

Every PNG gets a `.caption.md` sidecar:

```
your-first-funscript--phrase-overview.png
your-first-funscript--phrase-overview.caption.md
```

The caption file is what Carta ingests for visual search — it contains the
LLM-ready description, page reference, task context, and search tags.
When a user asks "what does the phrase chart look like?", Carta finds the
caption chunk and returns the image alongside the text answer.

## What can be generated vs. what needs screenshots

| Asset | Generated? | Tool |
| --- | --- | --- |
| Phrase overview chart | Yes | matplotlib (`generate_charts.py`) |
| Phrase detail chart | Yes | matplotlib (`generate_charts.py`) |
| Behavioral tag waveforms | Planned | matplotlib (future script) |
| App screenshot — file load | No | Manual screenshot |
| App screenshot — progress bar | No | Manual screenshot |
| App screenshot — phrase list | No | Manual screenshot |

Screenshot placeholders in the docs are marked `> TODO: insert screenshot`.
