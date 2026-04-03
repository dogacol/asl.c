"""Optional low-res preview render via ffmpeg."""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from roughcut_fcpx.config import AppConfig
from roughcut_fcpx.models.schemas import EditDecision, MediaAsset

logger = logging.getLogger(__name__)


def render_preview(
    decisions: list[EditDecision],
    assets: list[MediaAsset],
    cfg: AppConfig,
) -> str:
    """Render a flattened low-res preview MP4 from edit decisions.

    Returns the path to the rendered file.
    """
    asset_map = {a.id: a for a in assets}
    output_path = str(Path(cfg.output_dir) / "preview.mp4")

    # Build a concat-demuxer file list with per-segment trim
    segments_dir = Path(cfg.work_dir) / "preview_segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    segment_files: list[str] = []
    for i, d in enumerate(decisions):
        asset = asset_map.get(d.asset_id)
        if asset is None:
            logger.warning("Asset %s not found – skipping decision %d", d.asset_id, i)
            continue

        seg_path = segments_dir / f"seg_{i:04d}.mp4"
        dur = max(0.0, d.source_out_sec - d.source_in_sec)
        if dur <= 0:
            continue

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(d.source_in_sec),
            "-i", asset.proxy_path or asset.path,
            "-t", str(dur),
            "-vf", f"scale={cfg.proxy_long_edge}:-2",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "64k",
            "-an" if not asset.has_audio else "-shortest",
            str(seg_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            segment_files.append(str(seg_path))
        except subprocess.CalledProcessError:
            logger.exception("Failed to render preview segment %d", i)

    if not segment_files:
        logger.error("No segments rendered – cannot create preview")
        return output_path

    # Concat
    concat_list = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", dir=str(segments_dir), delete=False
    )
    for sf in segment_files:
        concat_list.write(f"file '{sf}'\n")
    concat_list.close()

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list.name,
        "-c", "copy",
        output_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info("Preview rendered to %s", output_path)
    except subprocess.CalledProcessError:
        logger.exception("Preview concat failed")

    return output_path
