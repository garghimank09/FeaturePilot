"""
Feature engineering pipeline: orchestrates encoding, scaling, outlier, datetime,
interaction, correlation, and feature selection.
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from app.services.cleaner import Cleaner
from app.services.correlation_engine import CorrelationEngine
from app.services.datetime_engine import DatetimeEngine
from app.services.encoding_engine import EncodingEngine
from app.services.feature_selection_engine import FeatureSelectionEngine
from app.services.interaction_engine import InteractionEngine
from app.services.outlier_engine import OutlierEngine
from app.services.scaling_engine import ScalingEngine


class FeatureEngineeringPipeline:
    """
    Full feature engineering pipeline. Operates on cleaned DataFrame.
    """

    def __init__(self, df: pd.DataFrame, target_column: Optional[str] = None):
        self.df = df.copy()
        self.target = target_column
        self._features_created: List[str] = []
        self._features_removed: List[str] = []
        self._feature_importance: Dict[str, float] = {}

    def run_datetime_extraction(self, drop_original: bool = True) -> "FeatureEngineeringPipeline":
        """Extract year, month, day, weekday, is_weekend from datetime columns."""
        self.df, created = DatetimeEngine.extract(self.df, drop_original=drop_original)
        self._features_created.extend(created)
        return self

    def run_encoding(self) -> "FeatureEngineeringPipeline":
        """One-hot (low cardinality), label (binary), optional target encoding."""
        self.df, created = EncodingEngine.run(self.df, target_column=self.target)
        self._features_created.extend(created)
        return self

    def run_outlier_handling(
        self,
        cap: bool = True,
        remove_rows: bool = False,
        apply_log_skew: bool = True,
    ) -> "FeatureEngineeringPipeline":
        """Log transform skewed, cap or remove outliers."""
        self.df, log_created, _ = OutlierEngine.run(
            self.df, cap=cap, remove_rows=remove_rows, apply_log_skew=apply_log_skew
        )
        self._features_created.extend(log_created)
        return self

    def run_scaling(self) -> "FeatureEngineeringPipeline":
        """StandardScaler on numeric columns."""
        self.df = ScalingEngine.scale(self.df)
        return self

    def run_feature_interactions(self) -> "FeatureEngineeringPipeline":
        """Add interaction and ratio features for top correlated pairs."""
        self.df, created = InteractionEngine.run(self.df, target_column=self.target)
        self._features_created.extend(created)
        return self

    def remove_multicollinearity(self, threshold: float = 0.85) -> "FeatureEngineeringPipeline":
        """Drop features with correlation > threshold."""
        self.df, removed = CorrelationEngine.remove_high_correlation(self.df, threshold=threshold)
        self._features_removed.extend(removed)
        return self

    def run_feature_selection(self, top_n: int = 20) -> "FeatureEngineeringPipeline":
        """Variance threshold + RF importance + select top_n."""
        self.df, importance, removed = FeatureSelectionEngine.run(
            self.df, target_column=self.target, top_n=top_n
        )
        self._feature_importance = importance
        self._features_removed.extend(removed)
        return self

    def run_full_pipeline(
        self,
        apply_scaling: bool = False,
        apply_outlier_handling: bool = True,
        apply_feature_selection: bool = False,
        multicollinearity_threshold: float = 0.85,
        top_n_features: int = 20,
    ) -> pd.DataFrame:
        """
        Run pipeline in sensible order:
        datetime -> encoding -> outlier -> interactions -> multicollinearity -> scaling -> selection
        """
        # 1) Datetime extraction
        self.run_datetime_extraction(drop_original=True)
        # 2) Encoding (categorical -> numeric)
        self.run_encoding()
        # 3) Outlier handling (cap, optional log)
        if apply_outlier_handling:
            self.run_outlier_handling(cap=True, remove_rows=False, apply_log_skew=True)
        # 4) Feature interactions (before correlation so we can trim)
        self.run_feature_interactions()
        # 5) Remove multicollinearity
        self.remove_multicollinearity(threshold=multicollinearity_threshold)
        # 6) Scaling (optional)
        if apply_scaling:
            self.run_scaling()
        # 7) Feature selection (optional)
        if apply_feature_selection:
            self.run_feature_selection(top_n=top_n_features)
        return self.df

    @property
    def features_created(self) -> List[str]:
        return self._features_created

    @property
    def features_removed(self) -> List[str]:
        return self._features_removed

    @property
    def feature_importance(self) -> Dict[str, float]:
        return self._feature_importance

    @property
    def selected_features(self) -> List[str]:
        return list(self.df.columns)
