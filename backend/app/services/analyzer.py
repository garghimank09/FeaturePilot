"""
Build schema summary, missing summary, and stats summary from a DataFrame.
"""
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.models.response_models import (
    ColumnSchema,
    MissingSummary,
    SchemaSummary,
    StatsSummary,
)
from app.services.cleaner import Cleaner


def _dtype_name(s: pd.Series) -> str:
    """Human-readable dtype: numeric, categorical, datetime, text, boolean."""
    if pd.api.types.is_numeric_dtype(s):
        return "numeric"
    if pd.api.types.is_bool_dtype(s):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "datetime"
    return "categorical"


def build_schema_summary(df: pd.DataFrame) -> SchemaSummary:
    """Build schema summary from cleaned DataFrame."""
    columns = []
    for col in df.columns:
        s = df[col]
        dtype = _dtype_name(s)
        sample = s.dropna().head(5).tolist()
        # Convert non-JSON-serializable types for API
        sample_clean = []
        for v in sample:
            if pd.isna(v):
                continue
            if isinstance(v, (np.integer, np.floating)):
                sample_clean.append(float(v) if isinstance(v, np.floating) else int(v))
            elif hasattr(v, "isoformat"):
                sample_clean.append(v.isoformat())
            else:
                sample_clean.append(str(v))
        columns.append(
            ColumnSchema(
                column=col,
                dtype=dtype,
                sample_values=sample_clean[:5],
                unique_count=int(s.nunique()),
            )
        )
    return SchemaSummary(columns=columns)


def build_missing_summary_before_fill(
    df: pd.DataFrame, filled_df: pd.DataFrame
) -> MissingSummary:
    """
    Build missing summary from df (before fill) and filled_df (after fill)
    to report count, pct, and filled_with (median/mode).
    """
    columns: Dict[str, Dict[str, Any]] = {}
    total_missing = 0
    n_rows = len(df)
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        total_missing += missing_count
        pct = round(100.0 * missing_count / n_rows, 2) if n_rows else 0
        filled_with = "unchanged"
        if missing_count > 0 and col in filled_df.columns:
            kind = Cleaner._get_column_dtype_kind(filled_df, col)
            if kind == "numeric":
                filled_with = "median"
            elif kind in ("categorical", "boolean"):
                filled_with = "mode"
            elif kind == "datetime":
                filled_with = "ffill/bfill"
        columns[col] = {
            "count": missing_count,
            "pct": pct,
            "filled_with": filled_with,
        }
    return MissingSummary(columns=columns, total_missing=total_missing)


def build_stats_summary(df: pd.DataFrame) -> StatsSummary:
    """Basic stats: numeric (min, max, mean, median, std), categorical (unique_count, top)."""
    numeric: Dict[str, Dict[str, Any]] = {}
    categorical: Dict[str, Dict[str, Any]] = {}
    datetime_cols: Dict[str, Dict[str, Any]] = {}

    for col in df.columns:
        s = df[col].dropna()
        if s.empty:
            continue
        kind = Cleaner._get_column_dtype_kind(df, col)
        if kind == "numeric":
            numeric[col] = {
                "min": float(s.min()) if pd.notna(s.min()) else None,
                "max": float(s.max()) if pd.notna(s.max()) else None,
                "mean": float(s.mean()) if pd.notna(s.mean()) else None,
                "median": float(s.median()) if pd.notna(s.median()) else None,
                "std": float(s.std()) if pd.notna(s.std()) else None,
            }
        elif kind == "datetime":
            datetime_cols[col] = {
                "min": s.min().isoformat() if hasattr(s.min(), "isoformat") else str(s.min()),
                "max": s.max().isoformat() if hasattr(s.max(), "isoformat") else str(s.max()),
            }
        else:
            top = s.mode()
            top_value = top.iloc[0] if len(top) else None
            if hasattr(top_value, "isoformat"):
                top_value = top_value.isoformat()
            elif isinstance(top_value, (np.integer, np.floating)):
                top_value = int(top_value) if isinstance(top_value, np.integer) else float(top_value)
            categorical[col] = {
                "unique_count": int(s.nunique()),
                "top_value": top_value,
                "top_count": int((s == s.mode().iloc[0]).sum()) if len(s.mode()) else 0,
            }

    return StatsSummary(
        numeric=numeric,
        categorical=categorical,
        datetime=datetime_cols,
    )


def records_for_preview(df: pd.DataFrame, n: int = 20) -> List[Dict[str, Any]]:
    """First n rows as list of dicts with JSON-serializable values."""
    head = df.head(n)
    records = []
    for _, row in head.iterrows():
        d = {}
        for k, v in row.items():
            if pd.isna(v):
                d[k] = None
            elif isinstance(v, (np.integer, np.int64)):
                d[k] = int(v)
            elif isinstance(v, (np.floating, np.float64)):
                d[k] = float(v)
            elif isinstance(v, (np.bool_, bool)):
                d[k] = bool(v)
            elif hasattr(v, "isoformat"):
                d[k] = v.isoformat()
            else:
                d[k] = str(v)
        records.append(d)
    return records
