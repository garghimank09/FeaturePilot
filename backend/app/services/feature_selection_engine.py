"""
Feature selection engine: variance threshold, Random Forest importance, select top N.
"""
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Default top N features to keep when selection is enabled
TOP_N_FEATURES = 20
# Minimum variance to keep (variance threshold)
VARIANCE_THRESHOLD = 1e-8


class FeatureSelectionEngine:
    """Variance threshold + RF importance ranking; return top N features."""

    @staticmethod
    def _get_numeric_columns(df: pd.DataFrame, exclude: Optional[List[str]] = None) -> List[str]:
        exclude = set(exclude or [])
        return [
            c for c in df.columns
            if c not in exclude and pd.api.types.is_numeric_dtype(df[c])
        ]

    @staticmethod
    def variance_threshold_drop(df: pd.DataFrame, threshold: float = VARIANCE_THRESHOLD) -> Tuple[pd.DataFrame, List[str]]:
        """Drop columns with variance below threshold. Returns (df, list of dropped columns)."""
        df = df.copy()
        dropped: List[str] = []
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            if df[col].var() < threshold or (df[col].var() != df[col].var()):  # NaN var
                df = df.drop(columns=[col])
                dropped.append(col)
        return df, dropped

    @staticmethod
    def random_forest_importance(
        df: pd.DataFrame,
        target_column: Optional[str] = None,
    ) -> Tuple[Dict[str, float], pd.DataFrame]:
        """
        Compute feature importance via Random Forest.
        If target_column given, use it as y; else use first column or skip.
        Returns (dict of feature_name -> importance, df unchanged).
        """
        try:
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            from sklearn.preprocessing import LabelEncoder
        except ImportError:
            return {}, df

        numeric = FeatureSelectionEngine._get_numeric_columns(df)
        if not numeric:
            return {}, df

        X = df[numeric].copy()
        for c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce")
        X = X.fillna(X.median())

        if target_column and target_column in df.columns:
            y = df[target_column]
            if not pd.api.types.is_numeric_dtype(y):
                y = LabelEncoder().fit_transform(y.astype(str))
            y = np.ravel(y)
        else:
            # No target: use last column as pseudo-target for unsupervised-like importance
            if len(numeric) < 2:
                return {c: 1.0 for c in numeric}, df
            target_column = numeric[-1]
            y = X[target_column].values
            X = X.drop(columns=[target_column])
            numeric = [c for c in numeric if c != target_column]
            if not numeric:
                return {}, df

        if len(np.unique(y)) < 2:
            return {c: 1.0 / max(len(numeric), 1) for c in numeric}, df

        is_classification = len(np.unique(y)) < min(20, len(y) // 5)
        n_est = min(50, max(10, len(X) // 10))
        try:
            if is_classification:
                model = RandomForestClassifier(n_estimators=n_est, random_state=42, max_depth=10)
            else:
                model = RandomForestRegressor(n_estimators=n_est, random_state=42, max_depth=10)
            model.fit(X, y)
            imp = dict(zip(X.columns, model.feature_importances_))
            return imp, df
        except Exception:
            return {c: 1.0 / max(len(numeric), 1) for c in numeric}, df

    @staticmethod
    def select_top_n(
        df: pd.DataFrame,
        importance: Dict[str, float],
        top_n: int = TOP_N_FEATURES,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Keep only top_n features by importance; drop the rest.
        Returns (df with only top columns, list of dropped column names).
        """
        if not importance:
            return df, []
        sorted_features = sorted(importance.keys(), key=lambda x: importance.get(x, 0), reverse=True)
        keep = sorted_features[:top_n]
        drop = [c for c in df.columns if c not in keep]
        df = df[[c for c in df.columns if c in keep]]
        return df, drop

    @staticmethod
    def run(
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        top_n: int = TOP_N_FEATURES,
    ) -> Tuple[pd.DataFrame, Dict[str, float], List[str]]:
        """
        Apply variance threshold, then RF importance, then select top_n.
        Returns (df with selected features, feature_importance dict, list of removed columns).
        """
        df, _ = FeatureSelectionEngine.variance_threshold_drop(df)
        importance, df = FeatureSelectionEngine.random_forest_importance(df, target_column=target_column)
        if not importance:
            return df, {}, []
        df, removed = FeatureSelectionEngine.select_top_n(df, importance, top_n=top_n)
        return df, importance, removed
