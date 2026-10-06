from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.schemas.intelligence import FeatureContribution, PredictionResponse

MODEL_DIR = Path(__file__).resolve().parents[1] / "ml_models"


@lru_cache(maxsize=2)
def load_bundle(name: str) -> dict[str, Any]:
    bundle = joblib.load(MODEL_DIR / name)
    # Small hosted CPUs benefit from batching, not a thread per available CPU.
    bundle["pipeline"].set_params(model__n_jobs=1)
    return bundle


def predict_days(name: str, features: list[dict[str, Any]]) -> list[int]:
    if not features:
        return []
    estimates = load_bundle(name)["pipeline"].predict(pd.DataFrame(features))
    return [max(1, round(float(value))) for value in estimates]


def predict(name: str, features: dict[str, Any]) -> PredictionResponse:
    bundle = load_bundle(name)
    pipeline = bundle["pipeline"]
    reference = bundle["reference_values"]
    rows = [features] + [
        {**features, feature: reference_value} for feature, reference_value in reference.items()
    ]
    estimates = pipeline.predict(pd.DataFrame(rows))
    days = max(1, round(float(estimates[0])))
    effects = [
        (feature, abs(float(days) - float(comparison)))
        for feature, comparison in zip(reference, estimates[1:], strict=True)
    ]
    ranked = sorted(effects, key=lambda item: item[1], reverse=True)[:3]
    total_effect = sum(value for _, value in ranked) or 1.0
    top = [
        FeatureContribution(
            feature=feature,
            importance=round(float(value) / total_effect, 4),
        )
        for feature, value in ranked
    ]
    risk = "high" if days >= 150 else "medium" if days >= 75 else "low"
    return PredictionResponse(
        predicted_days_remaining=days,
        risk_band=risk,
        top_features=top,
        model_version=bundle["version"],
        holdout_mae_days=bundle["metrics"]["mae_days"],
    )
