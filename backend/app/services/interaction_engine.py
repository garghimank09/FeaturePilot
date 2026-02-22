"""
Interaction engine: numeric interactions and ratios for top correlated features only.
Avoids feature explosion by limiting to pairs with high correlation to target or top N.
"""
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

# Max number of interaction pairs to add (e.g. top 10 pairs)
MAX_INTERACTION_PAIRS = 10
# Max ratio features
MAX_RATIO_FEATURES = 5


class InteractionEngine:
    """Generate interaction and ratio features for numeric columns."""

    @staticmethod
    def _get_numeric_columns(df: pd.DataFrame, exclude: Optional[List[str]] = None) -> List[str]:
        exclude = set(exclude or [])
        return [
            c for c in df.columns
            if c not in exclude and pd.api.types.is_numeric_dtype(df[c])
        ]

    @staticmethod
    def _safe_ratio(a: pd.Series, b: pd.Series) -> pd.Series:
        """A/B with division-by-zero -> 0."""
        r = a / b.replace(0, np.nan)
        return r.fillna(0)

    @staticmethod
    def get_top_correlated_pairs(
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        top_n: int = MAX_INTERACTION_PAIRS,
    ) -> List[Tuple[str, str]]:
        """
        Return list of (col_a, col_b) pairs to use for interactions.
        If target given, prefer pairs that correlate with target; else use pair correlation matrix.
        """
        numeric = InteractionEngine._get_numeric_columns(df, exclude=[target_column] if target_column else None)
        if len(numeric) < 2:
            return []
        sub = df[numeric].select_dtypes(include=[np.number]).dropna(how="all")
        if sub.empty or sub.shape[1] < 2:
            return []
        try:
            corr = sub.corr()
        except Exception:
            return []
        pairs: List[Tuple[str, str, float]] = []
        for i, a in enumerate(numeric):
            for b in numeric[i + 1:]:
                if a == b:
                    continue
                try:
                    v = abs(corr.loc[a, b])
                    if not np.isnan(v) and v < 1:
                        pairs.append((a, b, v))
                except Exception:
                    pass
        # Sort by correlation (desc) and take top_n
        pairs.sort(key=lambda x: x[2], reverse=True)
        return [(a, b) for a, b, _ in pairs[:top_n]]

    @staticmethod
    def add_interactions(
        df: pd.DataFrame,
        pairs: Optional[List[Tuple[str, str]]] = None,
        target_column: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Add A*B for each pair. If pairs is None, derive from top correlated.
        Returns (df, list of new column names).
        """
        df = df.copy()
        if pairs is None:
            pairs = InteractionEngine.get_top_correlated_pairs(df, target_column=target_column)
        created: List[str] = []
        for a, b in pairs:
            if a not in df.columns or b not in df.columns:
                continue
            name = f"{a}_x_{b}"
            if name in df.columns:
                continue
            df[name] = df[a] * df[b]
            created.append(name)
        return df, created

    @staticmethod
    def add_ratio_features(
        df: pd.DataFrame,
        pairs: Optional[List[Tuple[str, str]]] = None,
        target_column: Optional[str] = None,
        max_ratios: int = MAX_RATIO_FEATURES,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Add A/B for safe pairs (B has no zeros or we handle). Limit to max_ratios.
        """
        df = df.copy()
        if pairs is None:
            pairs = InteractionEngine.get_top_correlated_pairs(df, target_column=target_column, top_n=max_ratios)
        created: List[str] = []
        for a, b in pairs[:max_ratios]:
            if a not in df.columns or b not in df.columns:
                continue
            name = f"{a}_div_{b}"
            if name in df.columns:
                continue
            df[name] = InteractionEngine._safe_ratio(df[a], df[b])
            created.append(name)
        return df, created

    @staticmethod
    def run(
        df: pd.DataFrame,
        target_column: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Add interaction and ratio features for top correlated pairs only.
        Returns (df, list of new feature names).
        """
        all_created: List[str] = []
        pairs = InteractionEngine.get_top_correlated_pairs(df, target_column=target_column)
        df, inter = InteractionEngine.add_interactions(df, pairs=pairs, target_column=target_column)
        all_created.extend(inter)
        df, ratios = InteractionEngine.add_ratio_features(df, pairs=pairs, target_column=target_column)
        all_created.extend(ratios)
        return df, all_created
