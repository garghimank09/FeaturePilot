"""
Utility helpers for safe type conversion and common operations.
"""
from typing import Any, Optional, Union


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Convert value to float; return default on failure."""
    if value is None or (isinstance(value, float) and __import__("math").isnan(value)):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return default
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Convert value to int; return default on failure."""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != value:  # NaN
            return default
        return int(value) if value == int(value) else default
    s = str(value).strip()
    if not s:
        return default
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default
