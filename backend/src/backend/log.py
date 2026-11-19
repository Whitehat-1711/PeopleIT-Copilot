"""Minimal timestamped logger for CLI step visibility."""

import sys
from datetime import datetime


def log(message: str) -> None:
    """Print a timestamped step to stderr so it doesn't mix with answer output."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {message}", file=sys.stderr, flush=True)
