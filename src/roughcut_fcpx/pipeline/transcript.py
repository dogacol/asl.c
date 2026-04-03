"""Speech transcription using mlx-whisper."""

from __future__ import annotations

import logging
from pathlib import Path

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import MediaAsset

logger = logging.getLogger(__name__)


def transcribe_asset(asset: MediaAsset, cfg: AppConfig) -> dict | None:
    """Transcribe an asset's audio and return the result dict.

    Returns a dict with at least ``"text"`` and optionally ``"segments"``
    with word-level timestamps. Returns *None* on failure.
    """
    if not asset.has_audio:
        return None

    audio_path = Path(cfg.work_dir) / "audio" / f"{asset.id}.wav"
    if not audio_path.exists():
        audio_path = Path(asset.path)

    # Check cache
    cache_path = Path(cfg.work_dir) / "transcripts" / f"{asset.id}.json"
    if cache_path.exists():
        import json

        with open(cache_path) as f:
            logger.info("Using cached transcript for %s", asset.filename)
            return json.load(f)

    try:
        import mlx_whisper
    except ImportError:
        logger.warning("mlx-whisper not installed – skipping transcription for %s", asset.filename)
        return None

    try:
        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
            word_timestamps=True,
        )
        # Cache result
        import json

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(result, f, ensure_ascii=False)

        logger.info("Transcribed %s (%d chars)", asset.filename, len(result.get("text", "")))
        return result
    except Exception:
        logger.exception("Transcription failed for %s", asset.filename)
        return None


def align_transcript_to_segment(
    transcript: dict | None, start_sec: float, end_sec: float
) -> str | None:
    """Extract the portion of a transcript that falls within [start_sec, end_sec]."""
    if transcript is None:
        return None

    segments = transcript.get("segments")
    if not segments:
        return transcript.get("text")

    parts: list[str] = []
    for seg in segments:
        seg_start = seg.get("start", 0.0)
        seg_end = seg.get("end", 0.0)
        # Overlap check
        if seg_end > start_sec and seg_start < end_sec:
            parts.append(seg.get("text", "").strip())

    return " ".join(parts) if parts else None
