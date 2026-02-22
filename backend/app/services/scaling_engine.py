"""
Scaling engine: StandardScaler for numeric columns.
Applied only when user enables scaling.
"""
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


class ScalingEngine:
    """Apply StandardScaler to numeric columns."""

    @staticmethod
    def _get_numeric_columns(df: pd.DataFrame) -> List[str]:
        return [
            c for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c])
        ]

    @staticmethod
    def scale(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Z-score standardize numeric columns (zero mean, unit variance).
        Handles constant columns (std=0) by leaving them unchanged.
        """
        df = df.copy()
        if columns is None:
            columns = ScalingEngine._get_numeric_columns(df)
        for col in columns:
            if col not in df.columns:
                continue
            s = df[col]
            if not pd.api.types.is_numeric_dtype(s):
                continue
            mean, std = s.mean(), s.std()
            if pd.isna(std) or std == 0:
                continue
            df[col] = (s - mean) / std
        return df
