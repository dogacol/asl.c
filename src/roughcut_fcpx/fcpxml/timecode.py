"""Time conversion utilities for FCPXML rational time values."""

from __future__ import annotations

import math
from fractions import Fraction


def sec_to_fcpx_time(seconds: float, fps: float) -> str:
    """Convert seconds to FCPXML rational time string (e.g. '3600/600s').

    FCPXML uses rational numbers whose denominator typically equals
    fps * 100 (for integer fps) or the actual timebase denominator.
    """
    if seconds <= 0:
        return "0/1s"

    # Use a timebase that is a clean multiple of fps
    if fps == int(fps):
        timebase = int(fps) * 100
    else:
        # For non-integer fps (e.g. 29.97) use 30000/1001-style
        frac = Fraction(fps).limit_denominator(10000)
        timebase = int(frac.numerator * 100)

    numerator = round(seconds * timebase)
    # Simplify
    gcd = math.gcd(numerator, timebase)
    return f"{numerator // gcd}/{timebase // gcd}s"


def sec_to_frames(seconds: float, fps: float) -> int:
    """Convert seconds to a frame count."""
    return round(seconds * fps)


def frames_to_sec(frames: int, fps: float) -> float:
    """Convert a frame count back to seconds."""
    return frames / fps if fps else 0.0


def duration_fcpx(start_sec: float, end_sec: float, fps: float) -> str:
    """Convenience: duration between two points as an FCPXML time string."""
    return sec_to_fcpx_time(max(0.0, end_sec - start_sec), fps)
