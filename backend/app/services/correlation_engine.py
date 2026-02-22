"""
Correlation engine: remove features with correlation > threshold (multicollinearity).
"""
from typing import List, Set, Tuple

import numpy as np
import pandas as pd

CORRELATION_THRESHOLD = 0.85


class CorrelationEngine:
    """Remove highly correlated features to reduce multicollinearity."""

    @staticmethod
    def _get_numeric_columns(df: pd.DataFrame) -> List[str]:
        return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    @staticmethod
    def find_correlated_pairs(
        df: pd.DataFrame,
        threshold: float = CORRELATION_THRESHOLD,
    ) -> List[Tuple[str, str, float]]:
        """Return list of (col_a, col_b, abs_corr) where abs_corr > threshold."""
        numeric = CorrelationEngine._get_numeric_columns(df)
        if len(numeric) < 2:
            return []
        sub = df[numeric].select_dtypes(include=[np.number])
        if sub.shape[1] < 2:
            return []
        try:
            corr = sub.corr()
        except Exception:
            return []
        pairs = []
        for i, a in enumerate(numeric):
            for b in numeric[i + 1:]:
                try:
                    v = abs(corr.loc[a, b])
                    if not np.isnan(v) and v >= threshold:
                        pairs.append((a, b, v))
                except Exception:
                    pass
        return pairs

    @staticmethod
    def remove_high_correlation(
        df: pd.DataFrame,
        threshold: float = CORRELATION_THRESHOLD,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Iteratively drop one of each highly correlated pair (drop the second in sorted order).
        Returns (df with columns removed, list of removed column names).
        """
        df = df.copy()
        removed: List[str] = []
        to_drop: Set[str] = set()
        pairs = CorrelationEngine.find_correlated_pairs(df, threshold=threshold)
        for a, b, _ in pairs:
            # Prefer dropping the one that appears later alphabetically to keep order stable
            drop = max(a, b, key=lambda x: (x not in to_drop, x))
            to_drop.add(drop)
        for col in to_drop:
            if col in df.columns:
                df = df.drop(columns=[col])
                removed.append(col)
        return df, removed
