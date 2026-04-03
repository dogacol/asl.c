"""Pre-processing: proxy generation and audio extraction."""

from __future__ import annotations

import logging
from pathlib import Path

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import MediaAsset
from roughcut_fcpx.utils.ffmpeg import extract_audio, make_proxy

logger = logging.getLogger(__name__)

# Only create proxies for files whose long edge exceeds the configured limit
_PROXY_THRESHOLD_FACTOR = 1.2  # only proxy if source is 20 % larger than target


def preprocess_assets(assets: list[MediaAsset], cfg: AppConfig) -> list[MediaAsset]:
    """Create low-res proxies and extract audio where needed."""
    proxy_dir = Path(cfg.work_dir) / "proxies"
    audio_dir = Path(cfg.work_dir) / "audio"

    for asset in assets:
        long_edge = max(asset.width, asset.height)
        if long_edge > cfg.proxy_long_edge * _PROXY_THRESHOLD_FACTOR:
            proxy_path = proxy_dir / f"{asset.id}.mp4"
            if not proxy_path.exists():
                try:
                    make_proxy(asset.path, str(proxy_path), cfg.proxy_long_edge)
                    logger.info("Created proxy for %s", asset.filename)
                except Exception:
                    logger.exception("Proxy generation failed for %s", asset.filename)
                    continue
            asset.proxy_path = str(proxy_path)

        if asset.has_audio:
            audio_path = audio_dir / f"{asset.id}.wav"
            if not audio_path.exists():
                try:
                    extract_audio(asset.path, str(audio_path))
                except Exception:
                    logger.exception("Audio extraction failed for %s", asset.filename)

    return assets
