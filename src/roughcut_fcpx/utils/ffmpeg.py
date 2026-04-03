"""ffmpeg / ffprobe wrapper utilities."""

from __future__ import annotations

import json
import subprocess


def ffprobe_media(path: str) -> dict:
    """Probe a media file and return normalised metadata.

    Returns a dict with keys: duration, fps, width, height, has_audio,
    audio_channels, creation_time.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"), None
    )
    audio_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None
    )

    fmt = data.get("format", {})

    # FPS parsing (e.g. "30000/1001" -> 29.97)
    fps = 30.0
    if video_stream:
        r_frame_rate = video_stream.get("r_frame_rate", "30/1")
        if "/" in r_frame_rate:
            num, den = r_frame_rate.split("/")
            fps = float(num) / float(den) if float(den) else 30.0
        else:
            fps = float(r_frame_rate)

    return {
        "duration": float(fmt.get("duration", 0)),
        "fps": round(fps, 3),
        "width": int(video_stream["width"]) if video_stream else 0,
        "height": int(video_stream["height"]) if video_stream else 0,
        "has_audio": audio_stream is not None,
        "audio_channels": int(audio_stream.get("channels", 0)) if audio_stream else None,
        "creation_time": fmt.get("tags", {}).get("creation_time"),
    }


def make_proxy(input_path: str, output_path: str, long_edge: int = 960) -> None:
    """Create a low-resolution proxy suitable for analysis."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"scale={long_edge}:-2",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "64k",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def extract_audio(input_path: str, output_path: str) -> None:
    """Extract audio track as 16 kHz mono WAV for transcription."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def ffmpeg_extract_frame(video_path: str, time_sec: float, output_path: str) -> None:
    """Extract a single frame as JPEG at the given timestamp."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(time_sec),
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def ffmpeg_extract_snippet(
    video_path: str,
    start: float,
    duration: float,
    fps: int,
    output_path: str,
) -> None:
    """Extract a short low-fps video snippet."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-vf", f"fps={fps}",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
        "-an",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
