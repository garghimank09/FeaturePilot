"""
Schema detector: infer column types (numeric, categorical, datetime, text, boolean),
detect numbers inside strings (currency, %), and normalize them.
"""
import re
from typing import Any, List, Optional, Set, Tuple

import numpy as np
import pandas as pd


# Common currency symbols and patterns
CURRENCY_SYMBOLS = "₹$€£¥Rs"
CURRENCY_PATTERN = re.compile(
    r"^[\s]*[" + re.escape(CURRENCY_SYMBOLS) + r"]?\s*([-]?\d+[.,]?\d*)\s*[KkMmBb]?[\s]*$"
)
PERCENT_PATTERN = re.compile(r"^[\s]*([-]?\d+[.,]?\d*)\s*%?\s*$", re.IGNORECASE)
BOOLEAN_TRUE = {"yes", "true", "1", "y", "on"}
BOOLEAN_FALSE = {"no", "false", "0", "n", "off"}


class SchemaDetector:
    """Detect and normalize column types and values."""

    @staticmethod
    def _standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Lowercase, replace spaces with underscore, strip."""
        df = df.copy()
        new_columns = []
        for c in df.columns:
            s = str(c).strip().lower().replace(" ", "_")
            s = re.sub(r"_+", "_", s)
            new_columns.append(s or "unnamed")
        df.columns = new_columns
        return df

    @staticmethod
    def _is_boolean_series(s: pd.Series) -> bool:
        """Check if series looks like boolean (Yes/No, True/False, 0/1)."""
        if s.dtype == bool:
            return True
        drop_na = s.dropna().astype(str).str.strip().str.lower()
        if drop_na.empty:
            return False
        unique_vals = set(drop_na.unique())
        if len(unique_vals) > 3:
            return False
        return unique_vals.issubset(BOOLEAN_TRUE | BOOLEAN_FALSE | {""})

    @staticmethod
    def _is_datetime_series(s: pd.Series) -> bool:
        """Check if series is or can be parsed as datetime."""
        if pd.api.types.is_datetime64_any_dtype(s):
            return True
        try:
            sample = s.dropna().head(100)
            if sample.empty:
                return False
            pd.to_datetime(sample, errors="coerce")
            return True
        except Exception:
            return False

    @staticmethod
    def _is_numeric_series(s: pd.Series) -> bool:
        """Check if series is numeric (int/float)."""
        return pd.api.types.is_numeric_dtype(s)

    @staticmethod
    def _extract_numeric_from_string(val: Any) -> Optional[float]:
        """Extract numeric from string like '₹5000', '45%', '1,234.56'."""
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        if not s:
            return None
        # Remove commas
        s_clean = s.replace(",", "")
        # Try percentage first
        m = PERCENT_PATTERN.match(s_clean)
        if m:
            return float(m.group(1))
        # Try currency
        m = CURRENCY_PATTERN.match(s_clean)
        if m:
            num = float(m.group(1).replace(",", "."))
            if "k" in s.lower():
                num *= 1000
            elif "m" in s.lower():
                num *= 1_000_000
            elif "b" in s.lower():
                num *= 1_000_000_000
            return num
        # Plain number
        try:
            return float(s_clean)
        except ValueError:
            return None

    @staticmethod
    def _column_has_numeric_strings(s: pd.Series) -> bool:
        """True if column is object/string and most non-null values parse as numbers (currency/%)."""
        if not (s.dtype == object or pd.api.types.is_string_dtype(s)):
            return False
        sample = s.dropna().astype(str).head(200)
        if sample.empty:
            return False
        parsed = sample.apply(SchemaDetector._extract_numeric_from_string)
        valid = parsed.notna()
        return valid.sum() / max(len(sample), 1) >= 0.5

    @staticmethod
    def _convert_numeric_string_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Convert column that has numeric inside strings (currency, %) to float."""
        df = df.copy()
        is_pct = False
        sample = df[col].dropna().astype(str).head(20)
        for v in sample:
            if "%" in str(v):
                is_pct = True
                break
        def convert(x):
            if x is None or (isinstance(x, float) and np.isnan(x)):
                return np.nan
            n = SchemaDetector._extract_numeric_from_string(x)
            if n is None:
                return np.nan
            if is_pct and "%" in str(x).lower():
                return n / 100.0
            return n
        df[col] = df[col].apply(convert)
        df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    @staticmethod
    def _convert_boolean_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Map Yes/No, True/False to boolean."""
        df = df.copy()
        def to_bool(x):
            if pd.isna(x):
                return np.nan
            s = str(x).strip().lower()
            if s in BOOLEAN_TRUE:
                return True
            if s in BOOLEAN_FALSE:
                return False
            return np.nan
        df[col] = df[col].apply(to_bool)
        return df

    @staticmethod
    def _infer_dtype(s: pd.Series, col: str) -> str:
        """Return one of: numeric, categorical, datetime, text, boolean."""
        if SchemaDetector._is_boolean_series(s):
            return "boolean"
        if SchemaDetector._is_numeric_series(s):
            return "numeric"
        if SchemaDetector._is_datetime_series(s):
            return "datetime"
        if SchemaDetector._column_has_numeric_strings(s):
            return "numeric"  # will be converted
        unique_ratio = s.nunique() / max(s.notna().sum(), 1)
        if s.dtype == object or pd.api.types.is_string_dtype(s):
            if unique_ratio < 0.5 or s.nunique() < 50:
                return "categorical"
            return "text"
        return "categorical"

    @staticmethod
    def detect_and_normalize(df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names, detect types, convert:
        - Boolean-like -> boolean
        - Datetime-like -> datetime
        - Numeric-in-string (currency, %) -> float
        Returns DataFrame with normalized types.
        """
        df = SchemaDetector._standardize_column_names(df)
        for col in list(df.columns):
            s = df[col]
            dtype_kind = SchemaDetector._infer_dtype(s, col)
            if dtype_kind == "boolean":
                df = SchemaDetector._convert_boolean_column(df, col)
            elif dtype_kind == "datetime":
                df[col] = pd.to_datetime(df[col], errors="coerce")
            elif dtype_kind == "numeric" and (s.dtype == object or pd.api.types.is_string_dtype(s)):
                df = SchemaDetector._convert_numeric_string_column(df, col)
        return df
