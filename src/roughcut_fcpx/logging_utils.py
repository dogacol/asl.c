"""Logging setup for roughcut-fcpx."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line for machine-readable logs."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def setup_logging(log_level: str = "INFO", log_dir: str | Path | None = None) -> None:
    """Configure root logger with console (human) and optional file (JSON) handlers."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Console handler – human-friendly
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(console)

    # File handler – machine-readable JSON
    if log_dir is not None:
        log_path = Path(log_dir) / f"run_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(JSONFormatter())
        root.addHandler(fh)
