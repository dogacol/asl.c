"""Tests for FCPXML timecode conversion."""

from __future__ import annotations

from roughcut_fcpx.fcpxml.timecode import (
    duration_fcpx,
    frames_to_sec,
    sec_to_fcpx_time,
    sec_to_frames,
)


def test_zero_seconds():
    assert sec_to_fcpx_time(0, 30.0) == "0/1s"


def test_one_second_at_30fps():
    result = sec_to_fcpx_time(1.0, 30.0)
    # Should be a rational time ending in 's'
    assert result.endswith("s")
    num, den = result.rstrip("s").split("/")
    assert float(num) / float(den) == 1.0


def test_half_second_at_24fps():
    result = sec_to_fcpx_time(0.5, 24.0)
    assert result.endswith("s")
    num, den = result.rstrip("s").split("/")
    assert abs(float(num) / float(den) - 0.5) < 1e-6


def test_frames_roundtrip():
    fps = 24.0
    frames = sec_to_frames(2.5, fps)
    assert frames == 60
    assert abs(frames_to_sec(frames, fps) - 2.5) < 1e-6


def test_duration_fcpx():
    result = duration_fcpx(1.0, 3.0, 30.0)
    assert result.endswith("s")
    num, den = result.rstrip("s").split("/")
    assert abs(float(num) / float(den) - 2.0) < 1e-6


def test_negative_seconds():
    assert sec_to_fcpx_time(-5.0, 30.0) == "0/1s"
