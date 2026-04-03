# roughcut-fcpx

Local rough-cut generator for Final Cut Pro. Drop clips in a folder, run one command, import the FCPXML.

Uses **Gemma 4** on Apple Silicon (via MLX) to analyze scenes, score segments, and assemble a timeline – fully offline, no cloud required.

## Quick start

```bash
# Install
pip install -e ".[dev]"

# Put your clips in ./input, then:
roughcut-fcpx run --input ./input --output ./output --style "poetic observational montage" --duration 90

# Import output/project.fcpxml into Final Cut Pro
```

## Requirements

- Python 3.11+
- macOS with Apple Silicon (M1/M2/M3/M4) and 16 GB RAM
- `ffmpeg` and `ffprobe` on PATH
- Gemma 4 model weights (downloaded automatically on first run via `mlx-vlm`)

## What it does

1. Scans media and probes metadata with ffprobe
2. Creates low-res proxies for heavy files
3. Detects scene boundaries (PySceneDetect)
4. Transcribes speech (mlx-whisper)
5. Extracts keyframes and short snippets
6. Scores each segment with Gemma 4 (keep probability, clarity, emotion, action, novelty, visual quality)
7. Ranks and selects segments to fit target duration
8. Orders clips by editorial strategy (chronological, dialogue-first, trailer-like, experimental, etc.)
9. Writes a valid FCPXML with proper timecodes and asset references
10. Optionally renders a low-res preview MP4

## CLI commands

```bash
roughcut-fcpx run       --input ./input --output ./output --style "..." --duration 90
roughcut-fcpx watch     --input ./input --style "dialogue-first interview rough cut"
roughcut-fcpx validate  ./output/project.fcpxml
roughcut-fcpx inspect   ./output/project.fcpxml
roughcut-fcpx preview   --input ./input --plan ./output/edit_decisions.json
```

## Outputs

| File | Description |
|---|---|
| `project.fcpxml` | Import directly into Final Cut Pro |
| `edit_decisions.json` | Machine-readable cut list with rationale |
| `report.md` | Human-readable summary with scores |
| `preview.mp4` | Optional low-res flattened preview |

## Configuration

Copy `examples/config.example.yaml` to `config.yaml` and adjust. CLI flags override the YAML. Environment variables (`ROUGHCUT_MODEL`, `ROUGHCUT_INPUT_DIR`, etc.) also work.

## Style prompts

| Prompt | Effect |
|---|---|
| `poetic observational montage` | Slow, contemplative, wide shots |
| `dialogue-first interview rough cut` | Prioritises spoken content |
| `experimental associative edit` | Non-linear, mood-based juxtaposition |
| `trailer-like` | High energy, builds to a peak |
| `action-first` | Favours motion and dynamic framing |
| `mood piece` | Emotional arc, quiet moments |

## Tests

```bash
pytest
```

## Project structure

```
src/roughcut_fcpx/
  cli.py              # Click CLI
  config.py           # YAML + env + CLI config
  logging_utils.py    # JSON + console logging
  models/schemas.py   # Pydantic data models
  pipeline/           # Ingest -> preprocess -> scene detect -> transcript -> keyframes -> Gemma analysis -> ranking -> edit plan -> preview
  fcpxml/             # FCPXML writer, validator, timecode, resources, sequence
  utils/              # ffmpeg wrappers, file helpers, prompts
```

See [PLANS.md](PLANS.md) for the full design document.
