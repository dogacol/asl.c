"""Tests for scene detection."""

from __future__ import annotations

from unittest.mock import patch

from roughcut_fcpx.pipeline.scene_detect import detect_scenes


def test_fallback_on_import_error():
    """When scenedetect is not installed, fall back to single scene."""
    fake_probe = {"duration": 42.0}
    with (
        patch.dict("sys.modules", {"scenedetect": None}),
        patch("roughcut_fcpx.utils.ffmpeg.ffprobe_media", return_value=fake_probe),
    ):
        boundaries = detect_scenes("/fake/video.mp4", threshold=27.0)

    assert len(boundaries) == 1
    assert boundaries[0] == (0.0, 42.0)
