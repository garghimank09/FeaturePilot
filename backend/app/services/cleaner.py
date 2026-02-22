"""
Cleaner: remove duplicates, fill missing values (median for numeric, mode for categorical),
and ensure column names are standardized.
"""
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from .schema_detector import SchemaDetector


class Cleaner:
    """Clean DataFrame: dedupe, fill missing, standardize names."""

    @staticmethod
    def _get_column_dtype_kind(df: pd.DataFrame, col: str) -> str:
        """Return numeric, categorical, datetime, boolean, or text."""
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            return "numeric"
        if pd.api.types.is_bool_dtype(s):
            return "boolean"
        if pd.api.types.is_datetime64_any_dtype(s):
            return "datetime"
        return "categorical"

    @staticmethod
    def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
        """
        Numeric -> median, Categorical/boolean -> mode.
        Datetime -> forward fill then backward fill (or leave as NaT).
        """
        df = df.copy()
        for col in df.columns:
            if df[col].isna().all():
                continue
            kind = Cleaner._get_column_dtype_kind(df, col)
            if kind == "numeric":
                median_val = df[col].median()
                if pd.notna(median_val):
                    df[col] = df[col].fillna(median_val)
            elif kind in ("categorical", "boolean"):
                mode_vals = df[col].mode()
                if len(mode_vals) > 0:
                    df[col] = df[col].fillna(mode_vals.iloc[0])
            elif kind == "datetime":
                df[col] = df[col].ffill().bfill()
        return df

    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Remove duplicate rows; return (cleaned_df, count_removed)."""
        n_before = len(df)
        df_clean = df.drop_duplicates()
        removed = n_before - len(df_clean)
        return df_clean, removed

    @staticmethod
    def clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Full clean: ensure standardized names (via SchemaDetector), remove duplicates,
        fill missing. Returns (cleaned_df, duplicates_removed).
        """
        # Names already standardized if we ran SchemaDetector.detect_and_normalize
        df_clean, removed = Cleaner.remove_duplicates(df)
        df_clean = Cleaner.fill_missing(df_clean)
        return df_clean, removed
