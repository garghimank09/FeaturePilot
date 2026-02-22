"""
Upload and download endpoints for the data structuring API.
"""
import io
import uuid
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
import pandas as pd

from app.models.response_models import UploadResponse
from app.services.analyzer import (
    build_missing_summary_before_fill,
    build_schema_summary,
    build_stats_summary,
    records_for_preview,
)
from app.data_store import get_store
from app.services.cleaner import Cleaner
from app.services.file_handler import FileHandler, FileHandlerError
from app.services.schema_detector import SchemaDetector

router = APIRouter(prefix="", tags=["upload"])


def _cleaned_store():
    return get_store()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """
    Accept CSV, Excel, or JSON file. Detect schema, clean (dedupe, fill missing),
    and return schema summary, missing summary, stats summary, and first 20 rows preview.
    """
    # Validate file type
    name = file.filename or "data"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ("csv", "xlsx", "xls", "json"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use .csv, .xlsx, .xls, or .json",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        df_raw, safe_name = FileHandler.to_dataframe(content, name)
    except FileHandlerError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Detect schema and normalize types (currency, %, boolean, datetime)
    df_typed = SchemaDetector.detect_and_normalize(df_raw)

    # Remove duplicates
    df_dedup, duplicates_removed = Cleaner.remove_duplicates(df_typed)

    # Fill missing (numeric -> median, categorical -> mode)
    df_clean = Cleaner.fill_missing(df_dedup)

    # Build summaries
    schema_summary = build_schema_summary(df_clean)
    missing_summary = build_missing_summary_before_fill(df_dedup, df_clean)
    stats_summary = build_stats_summary(df_clean)
    preview = records_for_preview(df_clean, 20)

    # Store for download (key by download_id)
    download_id = str(uuid.uuid4())
    store = _cleaned_store()
    store[download_id] = {"df": df_clean, "filename": safe_name}

    # Prune old entries (keep last 10 to avoid unbounded growth)
    while len(store) > 10:
        oldest = next(iter(store))
        del store[oldest]

    return UploadResponse(
        schema_summary=schema_summary,
        missing_summary=missing_summary,
        stats_summary=stats_summary,
        preview=preview,
        total_rows=len(df_clean),
        total_columns=len(df_clean.columns),
        duplicates_removed=duplicates_removed,
        message="File processed successfully",
        download_id=download_id,
    )


@router.get("/download", response_class=StreamingResponse)
async def download_cleaned_csv(
    download_id: Optional[str] = Query(None, description="ID returned from /upload"),
):
    """
    Return the cleaned dataset as CSV. Pass download_id from the upload response.
    If no download_id, returns the most recently uploaded file (if any).
    """
    store = _cleaned_store()
    if download_id and download_id in store:
        entry = store[download_id]
    elif store:
        # Latest entry (last added)
        entry = next(reversed(store.values()))
    else:
        raise HTTPException(
            status_code=404,
            detail="No cleaned file available. Upload a file first.",
        )
    df: pd.DataFrame = entry["df"]
    filename = entry.get("filename", "cleaned_data")
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}_cleaned.csv"',
        },
    )