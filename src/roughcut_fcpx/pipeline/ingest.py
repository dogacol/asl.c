"""Media ingestion: discover files and probe metadata."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from roughcut_fcpx.models.schemas import MediaAsset
from roughcut_fcpx.utils.ffmpeg import ffprobe_media

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".m4v", ".wav", ".mp3"}


def stable_id(path: str) -> str:
    """Deterministic short ID from absolute path."""
    return hashlib.sha256(Path(path).resolve().as_posix().encode()).hexdigest()[:12]


def derive_reel_name(path: str) -> str:
    """Use the parent directory name as a reel identifier."""
    return Path(path).parent.name


def ingest_media(input_dir: str) -> list[MediaAsset]:
    """Scan *input_dir* for supported media and return probed assets."""
    root = Path(input_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    files = sorted(
        p for p in root.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS and p.is_file()
    )

    if not files:
        logger.warning("No supported media files found in %s", input_dir)
        return []

    assets: list[MediaAsset] = []
    for fp in files:
        try:
            probe = ffprobe_media(str(fp))
        except Exception:
            logger.exception("Failed to probe %s – skipping", fp)
            continue

        assets.append(
            MediaAsset(
                id=stable_id(str(fp)),
                path=str(fp.resolve()),
                filename=fp.name,
                duration_sec=probe["duration"],
                fps=probe["fps"],
                width=probe["width"],
                height=probe["height"],
                audio_channels=probe.get("audio_channels"),
                has_audio=probe.get("has_audio", False),
                creation_time=probe.get("creation_time"),
                reel_name=derive_reel_name(str(fp)),
            )
        )
        logger.info("Ingested %s (%.1fs, %dx%d)", fp.name, probe["duration"], probe["width"], probe["height"])

    return assets
