"""Keyframe and snippet extraction via ffmpeg."""

from __future__ import annotations

import logging
from pathlib import Path

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import SceneSegment
from roughcut_fcpx.utils.ffmpeg import ffmpeg_extract_frame, ffmpeg_extract_snippet

logger = logging.getLogger(__name__)


def extract_keyframe(video_path: str, segment: SceneSegment, cfg: AppConfig) -> str | None:
    """Extract a single representative frame from the segment midpoint."""
    frames_dir = Path(cfg.work_dir) / "frames"
    out_path = frames_dir / f"{segment.id}.jpg"

    if out_path.exists():
        return str(out_path)

    midpoint = (segment.start_sec + segment.end_sec) / 2.0
    try:
        ffmpeg_extract_frame(video_path, midpoint, str(out_path))
        return str(out_path)
    except Exception:
        logger.exception("Keyframe extraction failed for segment %s", segment.id)
        return None


def extract_snippet(video_path: str, segment: SceneSegment, cfg: AppConfig) -> str | None:
    """Extract a short low-fps video snippet for the segment."""
    snippets_dir = Path(cfg.work_dir) / "snippets"
    out_path = snippets_dir / f"{segment.id}.mp4"

    if out_path.exists():
        return str(out_path)

    duration = min(segment.duration_sec, cfg.max_video_window_sec)
    try:
        ffmpeg_extract_snippet(
            video_path,
            start=segment.start_sec,
            duration=duration,
            fps=cfg.frame_sample_fps,
            output_path=str(out_path),
        )
        return str(out_path)
    except Exception:
        logger.exception("Snippet extraction failed for segment %s", segment.id)
        return None
