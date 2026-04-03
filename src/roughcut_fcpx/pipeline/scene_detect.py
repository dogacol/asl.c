"""Scene detection using PySceneDetect."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def detect_scenes(video_path: str, threshold: float = 27.0) -> list[tuple[float, float]]:
    """Return a list of (start_sec, end_sec) scene boundaries.

    Falls back to treating the entire clip as one scene if PySceneDetect
    is not installed or detection fails.
    """
    try:
        from scenedetect import ContentDetector, open_video, SceneManager
    except ImportError:
        logger.warning("scenedetect not installed – treating entire clip as one scene")
        return _fallback_single_scene(video_path)

    try:
        video = open_video(video_path)
        sm = SceneManager()
        sm.add_detector(ContentDetector(threshold=threshold))
        sm.detect_scenes(video)
        scene_list = sm.get_scene_list()

        if not scene_list:
            return _fallback_single_scene(video_path)

        boundaries: list[tuple[float, float]] = []
        for start_tc, end_tc in scene_list:
            boundaries.append((start_tc.get_seconds(), end_tc.get_seconds()))

        logger.info("Detected %d scenes in %s", len(boundaries), video_path)
        return boundaries
    except Exception:
        logger.exception("Scene detection failed for %s", video_path)
        return _fallback_single_scene(video_path)


def _fallback_single_scene(video_path: str) -> list[tuple[float, float]]:
    """Treat the whole file as one scene using ffprobe duration."""
    from roughcut_fcpx.utils.ffmpeg import ffprobe_media

    try:
        probe = ffprobe_media(video_path)
        return [(0.0, probe["duration"])]
    except Exception:
        logger.exception("Cannot determine duration for %s", video_path)
        return []
