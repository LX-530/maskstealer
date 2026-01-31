from __future__ import annotations

from pathlib import Path
import sys


def resource_path(*relative_parts: str) -> str:
    """Return an absolute path relative to the project root."""
    try:
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    except Exception:
        base_path = Path(__file__).resolve().parents[2]
    return str(base_path.joinpath(*relative_parts))
