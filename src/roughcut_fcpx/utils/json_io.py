"""JSON I/O helpers with caching support."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_json(path: str | Path) -> dict:
    """Load a JSON file."""
    with open(path) as f:
        return json.load(f)


def save_json(data: dict, path: str | Path) -> None:
    """Save a dict as pretty-printed JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def cache_key(
    file_path: str,
    segment_start: float,
    segment_end: float,
    model_name: str,
    style_prompt: str,
) -> str:
    """Deterministic cache key for an analysis result."""
    p = Path(file_path)
    stat = p.stat()
    raw = f"{p.resolve()}|{stat.st_mtime}|{stat.st_size}|{segment_start}|{segment_end}|{model_name}|{style_prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
