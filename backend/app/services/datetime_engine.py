"""
Datetime engine: extract year, month, day, weekday, is_weekend; optionally drop original.
"""
from typing import List, Tuple

import pandas as pd


class DatetimeEngine:
    """Extract numeric/time features from datetime columns."""

    @staticmethod
    def _get_datetime_columns(df: pd.DataFrame) -> List[str]:
        return [
            c for c in df.columns
            if pd.api.types.is_datetime64_any_dtype(df[c])
        ]

    @staticmethod
    def extract(df: pd.DataFrame, drop_original: bool = True) -> Tuple[pd.DataFrame, List[str]]:
        """
        For each datetime column: add year, month, day, weekday, is_weekend.
        Returns (df, list of new column names created).
        """
        df = df.copy()
        created: List[str] = []
        cols = DatetimeEngine._get_datetime_columns(df)
        for col in cols:
            prefix = col + "_"
            df[prefix + "year"] = df[col].dt.year
            df[prefix + "month"] = df[col].dt.month
            df[prefix + "day"] = df[col].dt.day
            df[prefix + "weekday"] = df[col].dt.weekday  # 0=Monday
            df[prefix + "is_weekend"] = (df[col].dt.weekday >= 5).astype(int)
            created.extend([prefix + "year", prefix + "month", prefix + "day", prefix + "weekday", prefix + "is_weekend"])
            if drop_original:
                df = df.drop(columns=[col])
        return df, created
