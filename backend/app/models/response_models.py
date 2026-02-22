"""
Pydantic models for API responses.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    """Schema info for a single column."""

    column: str
    dtype: str = Field(..., description="Detected data type: numeric, categorical, datetime, text, boolean")
    sample_values: Optional[List[Any]] = Field(default=None, description="Sample values for preview")
    unique_count: Optional[int] = None


class SchemaSummary(BaseModel):
    """Summary of detected schema per column."""

    columns: List[ColumnSchema] = Field(default_factory=list)


class MissingSummary(BaseModel):
    """Missing value counts and fill strategy per column."""

    columns: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Column name -> {count, pct, filled_with}",
    )
    total_missing: int = 0


class StatsSummary(BaseModel):
    """Basic statistics summary (numeric and categorical)."""

    numeric: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Numeric column -> {min, max, mean, median, std}",
    )
    categorical: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Categorical column -> {unique_count, top_value, top_count}",
    )
    datetime: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Datetime column -> {min, max}",
    )


class UploadResponse(BaseModel):
    """Response from POST /upload."""

    schema_summary: SchemaSummary
    missing_summary: MissingSummary
    stats_summary: StatsSummary
    preview: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="First 20 rows of cleaned data",
    )
    total_rows: int = 0
    total_columns: int = 0
    duplicates_removed: int = 0
    message: str = "File processed successfully"
    download_id: Optional[str] = Field(default=None, description="Use with GET /download to get cleaned CSV")


# --- Phase 2: Feature Engineering ---


class FeatureEngineeringRequest(BaseModel):
    """Request body for POST /feature-engineering."""

    download_id: Optional[str] = Field(default=None, description="ID from /upload; use latest if omitted")
    target_column: Optional[str] = Field(default=None, description="Optional target for encoding/selection")
    apply_scaling: bool = Field(default=True, description="Apply StandardScaler to numeric columns")
    apply_outlier_handling: bool = Field(default=True, description="Cap outliers and log-transform skewed")
    apply_feature_selection: bool = Field(default=False, description="Select top N by RF importance")
    top_n_features: Optional[int] = Field(default=20, description="When feature selection enabled")


class FeatureEngineeringResponse(BaseModel):
    """Response from POST /feature-engineering."""

    engineered_preview: List[Dict[str, Any]] = Field(default_factory=list, description="First 20 rows")
    features_created: List[str] = Field(default_factory=list)
    features_removed: List[str] = Field(default_factory=list)
    selected_features: List[str] = Field(default_factory=list)
    feature_importance: Dict[str, float] = Field(default_factory=dict)
    download_id: Optional[str] = Field(default=None, description="Use with GET /download/engineered")
    total_rows: int = 0
    total_columns: int = 0
    message: str = "Feature engineering completed"
