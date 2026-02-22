"""
In-memory store for cleaned and engineered datasets (Phase 1 & 2).
Keys: download_id -> { "df", "filename" }
"""
from typing import Any, Dict, Optional

import pandas as pd


def get_store() -> Dict[str, Dict[str, Any]]:
    """Return the cleaned dataset store (mutable)."""
    return _cleaned_store


def get_engineered_store() -> Dict[str, Dict[str, Any]]:
    """Return the engineered dataset store (mutable)."""
    return _engineered_store


# download_id -> { "df": DataFrame, "filename": str }
_cleaned_store: Dict[str, Dict[str, Any]] = {}
_engineered_store: Dict[str, Dict[str, Any]] = {}
