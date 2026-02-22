"""
Feature engineering endpoint (Phase 2).
"""
import io
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import pandas as pd

from app.data_store import get_engineered_store, get_store
from app.models.response_models import FeatureEngineeringRequest, FeatureEngineeringResponse
from app.services.analyzer import records_for_preview
from app.services.feature_pipeline import FeatureEngineeringPipeline

router = APIRouter(prefix="", tags=["feature-engineering"])


@router.post("/feature-engineering", response_model=FeatureEngineeringResponse)
async def run_feature_engineering(body: FeatureEngineeringRequest) -> FeatureEngineeringResponse:
    """
    Run feature engineering on the last uploaded (cleaned) dataset.
    Pass download_id from /upload to use a specific dataset; otherwise uses latest.
    """
    store = get_store()
    if body.download_id and body.download_id in store:
        entry = store[body.download_id]
    elif store:
        entry = next(reversed(store.values()))
    else:
        raise HTTPException(
            status_code=404,
            detail="No cleaned dataset available. Upload a file first.",
        )

    df: pd.DataFrame = entry["df"].copy()
    filename = entry.get("filename", "data")

    if df.empty:
        raise HTTPException(status_code=400, detail="Dataset is empty.")

    # Target column must exist if provided
    if body.target_column and body.target_column not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Target column '{body.target_column}' not found in dataset.",
        )

    top_n = body.top_n_features or 20
    pipeline = FeatureEngineeringPipeline(df, target_column=body.target_column or None)
    try:
        pipeline.run_full_pipeline(
            apply_scaling=body.apply_scaling,
            apply_outlier_handling=body.apply_outlier_handling,
            apply_feature_selection=body.apply_feature_selection,
            top_n_features=top_n,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature engineering failed: {str(e)}") from e

    engineered_df = pipeline.df
    preview = records_for_preview(engineered_df, 20)

    # Store for download
    eng_id = str(uuid.uuid4())
    eng_store = get_engineered_store()
    eng_store[eng_id] = {"df": engineered_df, "filename": filename}
    while len(eng_store) > 10:
        oldest = next(iter(eng_store))
        del eng_store[oldest]

    return FeatureEngineeringResponse(
        engineered_preview=preview,
        features_created=pipeline.features_created,
        features_removed=pipeline.features_removed,
        selected_features=pipeline.selected_features,
        feature_importance=pipeline.feature_importance,
        download_id=eng_id,
        total_rows=len(engineered_df),
        total_columns=len(engineered_df.columns),
        message="Feature engineering completed",
    )


@router.get("/download/engineered", response_class=StreamingResponse)
async def download_engineered_csv(
    download_id: Optional[str] = Query(None, description="ID from POST /feature-engineering"),
):
    """Return the engineered dataset as CSV."""
    store = get_engineered_store()
    if download_id and download_id in store:
        entry = store[download_id]
    elif store:
        entry = next(reversed(store.values()))
    else:
        raise HTTPException(
            status_code=404,
            detail="No engineered file available. Run feature engineering first.",
        )
    df: pd.DataFrame = entry["df"]
    filename = entry.get("filename", "engineered_data")
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}_engineered.csv"',
        },
    )
