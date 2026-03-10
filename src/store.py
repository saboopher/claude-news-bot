"""Track which articles have already been sent."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.config import SEEN_ARTICLES_FILE


def _path() -> Path:
    p = Path(SEEN_ARTICLES_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_seen() -> set[str]:
    p = _path()
    if not p.exists():
        return set()
    with open(p) as f:
        return set(json.load(f))


def save_seen(seen: set[str]) -> None:
    p = _path()
    with open(p, "w") as f:
        json.dump(sorted(seen), f, indent=2)
