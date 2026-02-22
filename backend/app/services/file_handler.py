"""
File handler: accept CSV, Excel, JSON and convert to Pandas DataFrame safely.
Limits file size and row count for large-file safety.
"""
import io
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

# Safety limits (configurable)
MAX_FILE_SIZE_MB = 50
MAX_ROWS = 500_000


class FileHandlerError(Exception):
    """Raised when file handling fails."""
    pass


class FileHandler:
    """Handles CSV, Excel, and JSON uploads with size/row limits."""

    @staticmethod
    def _bytes_to_dataframe(
        content: bytes,
        filename: str,
        max_rows: int = MAX_ROWS,
    ) -> pd.DataFrame:
        """
        Convert file bytes to DataFrame based on extension.
        Raises FileHandlerError on failure.
        """
        ext = Path(filename).suffix.lower()
        try:
            if ext == ".csv":
                return FileHandler._read_csv(content, max_rows)
            if ext in (".xlsx", ".xls"):
                return FileHandler._read_excel(content, ext, max_rows)
            if ext == ".json":
                return FileHandler._read_json(content, max_rows)
        except Exception as e:
            raise FileHandlerError(f"Failed to parse file: {e}") from e
        raise FileHandlerError(f"Unsupported file type: {ext}. Use .csv, .xlsx, .xls, or .json")

    @staticmethod
    def _read_csv(content: bytes, max_rows: int) -> pd.DataFrame:
        """Read CSV with encoding fallback and row limit."""
        buffer = io.BytesIO(content)
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                buffer.seek(0)
                df = pd.read_csv(buffer, encoding=encoding, nrows=max_rows, low_memory=False)
                return df
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        raise FileHandlerError("Could not decode CSV with utf-8, latin-1, or cp1252")

    @staticmethod
    def _read_excel(content: bytes, ext: str, max_rows: int) -> pd.DataFrame:
        """Read Excel file (first sheet only) with row limit."""
        buffer = io.BytesIO(content)
        engine = "openpyxl" if ext == ".xlsx" else None
        df = pd.read_excel(buffer, engine=engine, nrows=max_rows)
        return df

    @staticmethod
    def _read_json(content: bytes, max_rows: int) -> pd.DataFrame:
        """Read JSON (array of objects or lines) with row limit."""
        buffer = io.BytesIO(content)
        try:
            df = pd.read_json(buffer, orient="records", nrows=max_rows)
        except (ValueError, TypeError):
            buffer.seek(0)
            df = pd.read_json(buffer, lines=True, nrows=max_rows)
        return df

    @staticmethod
    def validate_size(content: bytes) -> None:
        """Raise FileHandlerError if content exceeds MAX_FILE_SIZE_MB."""
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise FileHandlerError(
                f"File too large: {size_mb:.1f} MB. Maximum allowed: {MAX_FILE_SIZE_MB} MB"
            )

    @staticmethod
    def to_dataframe(
        content: bytes,
        filename: str,
        max_file_size_mb: Optional[float] = None,
        max_rows: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, str]:
        """
        Validate size, parse file, return (DataFrame, sanitized_filename).
        """
        max_file_size_mb = max_file_size_mb or MAX_FILE_SIZE_MB
        max_rows = max_rows or MAX_ROWS
        FileHandler.validate_size(content)
        df = FileHandler._bytes_to_dataframe(content, filename, max_rows=max_rows)
        if df.empty:
            raise FileHandlerError("File produced an empty dataset")
        # Sanitize filename for download later
        safe_name = Path(filename).stem or "data"
        return df, safe_name
