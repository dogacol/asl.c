"""Configuration loading: YAML file -> CLI overrides -> environment variables."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

_DEFAULT_CONFIG_FILENAME = "config.yaml"


class AppConfig(BaseModel):
    """All tuneable settings for a roughcut-fcpx run."""

    project_title: str = "Rough Cut"
    input_dir: str = "./input"
    work_dir: str = "./work"
    output_dir: str = "./output"

    model_name: str = "mlx-community/gemma-4-e4b-it-4bit"
    fallback_model_name: str = "mlx-community/gemma-4-e2b-it-4bit"

    target_duration_sec: float = 90.0
    style_prompt: str = "poetic observational montage"

    scene_threshold: float = 27.0
    max_video_window_sec: float = 30.0
    frame_sample_fps: int = 1
    max_segments_per_clip: int = 8
    min_segment_duration_sec: float = 1.0

    transcript_enabled: bool = True
    preview_render_enabled: bool = False
    watch_mode: bool = False

    fcpxml_version: str = "1.11"
    proxy_long_edge: int = 960

    # Scoring weights
    weight_keep_probability: float = 0.30
    weight_clarity: float = 0.20
    weight_visual_quality: float = 0.15
    weight_emotional: float = 0.15
    weight_action: float = 0.10
    weight_novelty: float = 0.10

    log_level: str = "INFO"


def load_config(
    config_path: str | Path | None = None,
    overrides: dict | None = None,
) -> AppConfig:
    """Load config from YAML, apply env-var and dict overrides."""
    data: dict = {}

    # 1. YAML file
    if config_path is None:
        config_path = Path(_DEFAULT_CONFIG_FILENAME)
    else:
        config_path = Path(config_path)

    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

    # 2. Environment variable overrides
    env_map = {
        "ROUGHCUT_MODEL": "model_name",
        "ROUGHCUT_INPUT_DIR": "input_dir",
        "ROUGHCUT_WORK_DIR": "work_dir",
        "ROUGHCUT_OUTPUT_DIR": "output_dir",
    }
    for env_key, field in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            data[field] = val

    # 3. Explicit CLI overrides
    if overrides:
        data.update({k: v for k, v in overrides.items() if v is not None})

    return AppConfig(**data)


def ensure_directories(cfg: AppConfig) -> None:
    """Create the work and output directory trees if they don't exist."""
    work = Path(cfg.work_dir)
    for sub in ("proxies", "frames", "snippets", "audio", "transcripts", "analysis", "logs"):
        (work / sub).mkdir(parents=True, exist_ok=True)

    Path(cfg.output_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.input_dir).mkdir(parents=True, exist_ok=True)
