"""
Outlier engine: Z-score and IQR detection; option to cap or remove; log transform for skewed numeric.
"""
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


# Z-score threshold; beyond this we consider outlier
ZSCORE_THRESHOLD = 3.0
# IQR multiplier (1.5 = standard)
IQR_MULTIPLIER = 1.5
# Skewness above this -> consider log transform
SKEW_THRESHOLD = 1.0


class OutlierEngine:
    """Detect and handle outliers; optional log transform for skewed features."""

    @staticmethod
    def _get_numeric_columns(df: pd.DataFrame) -> List[str]:
        return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    @staticmethod
    def zscore_mask(series: pd.Series, threshold: float = ZSCORE_THRESHOLD) -> pd.Series:
        """Boolean mask: True where value is within threshold (not outlier)."""
        if series.std() == 0 or pd.isna(series.std()):
            return pd.Series(True, index=series.index)
        z = np.abs((series - series.mean()) / series.std())
        return z <= threshold

    @staticmethod
    def iqr_bounds(series: pd.Series, k: float = IQR_MULTIPLIER) -> Tuple[float, float]:
        """Return (lower, upper) bounds for non-outlier range."""
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - k * iqr
        upper = q3 + k * iqr
        return lower, upper

    @staticmethod
    def cap_outliers(df: pd.DataFrame, columns: Optional[List[str]] = None, method: str = "iqr") -> pd.DataFrame:
        """
        Cap outliers to boundary values (IQR or Z-score). Does not remove rows.
        method: "iqr" or "zscore"
        """
        df = df.copy()
        if columns is None:
            columns = OutlierEngine._get_numeric_columns(df)
        for col in columns:
            if col not in df.columns:
                continue
            s = df[col]
            if not pd.api.types.is_numeric_dtype(s) or s.std() == 0:
                continue
            if method == "zscore":
                mean, std = s.mean(), s.std()
                lower = mean - ZSCORE_THRESHOLD * std
                upper = mean + ZSCORE_THRESHOLD * std
                df[col] = s.clip(lower=lower, upper=upper)
            else:
                lower, upper = OutlierEngine.iqr_bounds(s)
                df[col] = s.clip(lower=lower, upper=upper)
        return df

    @staticmethod
    def remove_outlier_rows(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "iqr",
    ) -> pd.DataFrame:
        """Remove rows where any of the given numeric columns is an outlier."""
        if columns is None:
            columns = OutlierEngine._get_numeric_columns(df)
        mask = pd.Series(True, index=df.index)
        for col in columns:
            if col not in df.columns:
                continue
            s = df[col]
            if not pd.api.types.is_numeric_dtype(s):
                continue
            if method == "zscore":
                mask = mask & OutlierEngine.zscore_mask(s)
            else:
                lower, upper = OutlierEngine.iqr_bounds(s)
                mask = mask & (s >= lower) & (s <= upper)
        return df.loc[mask].reset_index(drop=True)

    @staticmethod
    def log_transform_skewed(df: pd.DataFrame, skew_threshold: float = SKEW_THRESHOLD) -> Tuple[pd.DataFrame, List[str]]:
        """
        Apply log1p to numeric columns that are positively skewed and non-negative (or shift).
        Returns (df, list of column names that got log transform).
        """
        df = df.copy()
        transformed: List[str] = []
        for col in OutlierEngine._get_numeric_columns(df):
            s = df[col]
            if s.min() <= 0:
                s = s - s.min() + 1e-6  # shift so positive
            skew = s.skew()
            if pd.isna(skew) or skew < skew_threshold:
                continue
            df[col + "_log"] = np.log1p(s)
            df = df.drop(columns=[col])
            transformed.append(col + "_log")
        return df, transformed

    @staticmethod
    def run(
        df: pd.DataFrame,
        cap: bool = True,
        remove_rows: bool = False,
        apply_log_skew: bool = True,
    ) -> Tuple[pd.DataFrame, List[str], int]:
        """
        Run outlier handling: optionally log-transform skewed, then cap or remove.
        Returns (df, list of columns log-transformed, number of rows removed if remove_rows=True).
        """
        n_before = len(df)
        log_created: List[str] = []
        if apply_log_skew:
            df, log_created = OutlierEngine.log_transform_skewed(df)
        if cap:
            df = OutlierEngine.cap_outliers(df, method="iqr")
        if remove_rows:
            df = OutlierEngine.remove_outlier_rows(df, method="iqr")
        n_after = len(df)
        return df, log_created, n_before - n_after
