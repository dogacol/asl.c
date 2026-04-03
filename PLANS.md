# PLANS.md

## Project
roughcut-fcpx

## Goal
Build a local macOS app and CLI that turns a folder of raw video clips into:
1. a valid `project.fcpxml` importable into Final Cut Pro
2. an `edit_decisions.json` sidecar explaining the cut
3. an optional `preview.mp4`
4. a human-readable `report.md`

The system must run fully locally on Apple Silicon with 16 GB RAM, using Gemma 4 as the primary multimodal model.

## Primary model choice
- Primary: `mlx-community/gemma-4-e4b-it-4bit`
- Fallback: `mlx-community/gemma-4-e2b-it-4bit`

## Why this architecture
Do **not** build a live GUI-driving editing agent for v1.

Build a **rough-cut generator**:
- user drops clips into a folder
- pipeline analyzes clips locally
- pipeline selects ranges and order
- pipeline writes FCPXML
- user imports the result into Final Cut Pro

This is more reliable, more testable, and far more realistic on a 16 GB machine.

## Product shape
### v1
CLI-first local tool.

### v2
Small macOS desktop wrapper around the CLI.

## Inputs
- folder of `.mp4`, `.mov`, `.m4v`, `.wav`, `.mp3`
- user style prompt, for example:
  - `poetic observational montage`
  - `dialogue-first interview rough cut`
  - `experimental associative edit`
  - `trailer-like`

## Outputs
- `output/project.fcpxml`
- `output/edit_decisions.json`
- `output/report.md`
- `output/preview.mp4` optional

## Constraints
- fully local
- no cloud inference
- Apple Silicon optimized
- must work on 16 GB RAM
- deterministic file outputs
- modular pipeline
- easy to test from CLI
- no Final Cut GUI automation in v1

## Core stack
- Python 3.11+
- `ffmpeg` / `ffprobe`
- `PySceneDetect`
- `mlx-whisper`
- `mlx-vlm`
- `pydantic`
- `lxml`
- `watchdog`
- optional later: `Tauri` desktop wrapper

## Directory layout at runtime
```text
/project
  /input
  /work
    /proxies
    /frames
    /snippets
    /audio
    /transcripts
    /analysis
    /logs
  /output
    project.fcpxml
    edit_decisions.json
    report.md
    preview.mp4
```

## Main user flow
1. User drops media into `input/`
2. User runs CLI command
3. App scans media and extracts metadata
4. App creates low-res proxies if needed
5. App detects scene boundaries
6. App transcribes speech
7. App extracts keyframes and short snippets
8. Gemma 4 scores and describes segments
9. Ranking logic selects ranges
10. Edit strategy orders the selected ranges
11. App writes valid FCPXML
12. App optionally renders a preview
13. User imports the FCPXML into Final Cut Pro

## MVP scope
Implement only this first:
- CLI entrypoint
- media scan with ffprobe
- proxy generation
- scene detection
- transcript extraction
- keyframe extraction
- Gemma 4 scoring with strict JSON output
- ranking and selection
- basic FCPXML generation with one sequence and one spine
- XML validation
- simple preview export

Do **not** implement these in v1:
- direct Final Cut GUI control
- complex transitions
- multicam editing
- advanced audio mixing
- color correction
- subtitles
- background music search
- plugin/effect authoring
- timeline relinking UI
- cloud services

## Success condition
A user can:
1. put clips in a folder
2. run one command
3. import the resulting FCPXML into Final Cut Pro
4. see a sensible rough-cut timeline referencing the original media correctly

## Development milestones
### Milestone 1
Single command ingests one clip and prints metadata.

### Milestone 2
Scene detection plus transcript extraction works.

### Milestone 3
Gemma 4 returns valid JSON analysis for each segment.

### Milestone 4
Ranking selects segments and writes `edit_decisions.json`.

### Milestone 5
FCPXML is generated and imports into Final Cut Pro.

### Milestone 6
Preview render works.

### Milestone 7
App wrapper exists.

## Non-goals
- perfect editing taste
- frame-perfect artistic polish
- autonomous long-form documentary editing
- replacing a human editor
- direct manipulation of Final Cut's GUI in v1
