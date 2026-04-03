"""Tests for media ingestion."""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from roughcut_fcpx.pipeline.ingest import (
    SUPPORTED_EXTENSIONS,
    derive_reel_name,
    ingest_media,
    stable_id,
)


def test_stable_id_deterministic():
    assert stable_id("/a/b/c.mp4") == stable_id("/a/b/c.mp4")


def test_stable_id_differs():
    assert stable_id("/a/b/c.mp4") != stable_id("/a/b/d.mp4")


def test_derive_reel_name():
    assert derive_reel_name("/project/DAY1/clip.mp4") == "DAY1"


def test_supported_extensions():
    assert ".mp4" in SUPPORTED_EXTENSIONS
    assert ".mov" in SUPPORTED_EXTENSIONS
    assert ".txt" not in SUPPORTED_EXTENSIONS


def test_ingest_empty_dir(tmp_path):
    assets = ingest_media(str(tmp_path))
    assert assets == []


def test_ingest_missing_dir():
    with pytest.raises(FileNotFoundError):
        ingest_media("/nonexistent/path")


def test_ingest_with_mock_ffprobe(tmp_path):
    # Create a dummy mp4 file
    (tmp_path / "clip.mp4").write_bytes(b"\x00" * 100)

    fake_probe = {
        "duration": 10.5,
        "fps": 30.0,
        "width": 1920,
        "height": 1080,
        "has_audio": True,
        "audio_channels": 2,
        "creation_time": None,
    }
    with patch("roughcut_fcpx.pipeline.ingest.ffprobe_media", return_value=fake_probe):
        assets = ingest_media(str(tmp_path))

    assert len(assets) == 1
    assert assets[0].filename == "clip.mp4"
    assert assets[0].duration_sec == 10.5
    assert assets[0].width == 1920
    assert assets[0].has_audio is True
