"""
Encoding engine: one-hot (low cardinality), label (binary), optional target encoding.
Avoids explosion on high cardinality; safe for small datasets.
"""
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

# Max unique values for one-hot; above that we use label encoding only
ONE_HOT_MAX_CARDINALITY = 10


class EncodingEngine:
    """Encode categorical and boolean columns."""

    @staticmethod
    def _is_categorical_or_bool(df: pd.DataFrame, col: str) -> bool:
        s = df[col]
        if pd.api.types.is_bool_dtype(s):
            return True
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_datetime64_any_dtype(s):
            return False
        return s.dtype == object or pd.api.types.is_string_dtype(s)

    @staticmethod
    def _get_categorical_columns(df: pd.DataFrame, exclude: Optional[List[str]] = None) -> List[str]:
        exclude = set(exclude or [])
        return [
            c for c in df.columns
            if c not in exclude and EncodingEngine._is_categorical_or_bool(df, c)
        ]

    @staticmethod
    def one_hot_encode(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, List[str]]:
        """
        One-hot encode columns with < ONE_HOT_MAX_CARDINALITY unique values.
        Returns (df with new columns, list of new column names created).
        """
        df = df.copy()
        if columns is None:
            columns = EncodingEngine._get_categorical_columns(df)
        created: List[str] = []
        for col in columns:
            if col not in df.columns:
                continue
            n_unique = df[col].nunique()
            # Binary -> label only; one-hot only for 3..10
            if n_unique < 3 or n_unique > ONE_HOT_MAX_CARDINALITY:
                continue
            dummies = pd.get_dummies(df[col], prefix=col, prefix_sep="_", dtype=float)
            # Drop first to avoid multicollinearity (optional; we can keep all for clarity)
            df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
            created.extend(dummies.columns.tolist())
        return df, created

    @staticmethod
    def label_encode_binary(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, List[str]]:
        """
        Label-encode binary columns (exactly 2 unique values). Idempotent for already numeric.
        Returns (df, list of columns that were label-encoded).
        """
        df = df.copy()
        if columns is None:
            columns = EncodingEngine._get_categorical_columns(df)
        encoded: List[str] = []
        for col in columns:
            if col not in df.columns:
                continue
            n_unique = df[col].nunique()
            if n_unique != 2:
                continue
            uniques = df[col].dropna().unique().tolist()
            mapping = {v: i for i, v in enumerate(sorted(str(x) for x in uniques))}
            # Map original values
            df[col] = df[col].astype(str).map(lambda x: mapping.get(x, np.nan))
            encoded.append(col)
        return df, encoded

    @staticmethod
    def target_encode(
        df: pd.DataFrame,
        target_column: str,
        columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Target encoding: replace category with mean of target for that category.
        Only applied if target exists and is numeric. Uses global mean for unseen categories.
        """
        if target_column not in df.columns or not pd.api.types.is_numeric_dtype(df[target_column]):
            return df, []
        df = df.copy()
        if columns is None:
            columns = EncodingEngine._get_categorical_columns(df, exclude=[target_column])
        global_mean = df[target_column].mean()
        encoded: List[str] = []
        for col in columns:
            if col not in df.columns or col == target_column:
                continue
            means = df.groupby(col)[target_column].mean()
            df[col + "_te"] = df[col].map(means).fillna(global_mean)
            df = df.drop(columns=[col])
            encoded.append(col + "_te")
        return df, encoded

    @staticmethod
    def run(
        df: pd.DataFrame,
        target_column: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Full encoding: label for binary, one-hot for low cardinality, optional target for rest if target given.
        Returns (encoded_df, list of all new/encoded column names).
        """
        all_created: List[str] = []
        # 1) Label encode binary
        df, binary_encoded = EncodingEngine.label_encode_binary(df)
        all_created.extend(binary_encoded)
        # 2) One-hot for low cardinality (excluding target)
        cat_cols = EncodingEngine._get_categorical_columns(df, exclude=[target_column] if target_column else None)
        df, onehot_created = EncodingEngine.one_hot_encode(df, columns=cat_cols)
        all_created.extend(onehot_created)
        # 3) If target provided, target-encode remaining categoricals (high cardinality)
        remaining = EncodingEngine._get_categorical_columns(df, exclude=[target_column] if target_column else None)
        if target_column and remaining:
            df, te_created = EncodingEngine.target_encode(df, target_column, columns=remaining)
            all_created.extend(te_created)
        return df, all_created
