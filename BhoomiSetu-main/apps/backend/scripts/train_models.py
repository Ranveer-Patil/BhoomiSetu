"""Train and evaluate BhoomiSetu's procedural models on reproducible synthetic history."""

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "app" / "ml_models"
DATA_DIR = ROOT / "scripts" / "data"
CATEGORICAL = ["project_type", "state", "district", "current_stage"]
NUMERIC = [
    "parcel_count",
    "objection_count",
    "document_turnaround_days",
    "officer_open_load",
    "days_in_compensation",
]


def generate_history(rows: int = 1800, seed: int = 26016) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    stages = np.array(
        ["notification", "verification", "objection", "award", "compensation", "possession"]
    )
    frame = pd.DataFrame(
        {
            "project_type": rng.choice(["highway", "rail", "irrigation", "urban_transit"], rows),
            "state": rng.choice(["Maharashtra", "Gujarat", "Karnataka", "Madhya Pradesh"], rows),
            "district": rng.choice(
                ["Pune", "Nashik", "Nagpur", "Satara", "Ahmedabad", "Indore"], rows
            ),
            "current_stage": rng.choice(stages, rows),
            "parcel_count": rng.integers(1, 7, rows),
            "objection_count": rng.poisson(1.5, rows),
            "document_turnaround_days": rng.integers(2, 46, rows),
            "officer_open_load": rng.integers(4, 52, rows),
            "days_in_compensation": rng.integers(0, 121, rows),
        }
    )
    stage_index = (
        frame["current_stage"].map({stage: i for i, stage in enumerate(stages)}).to_numpy()
    )
    noise = rng.normal(0, 14, rows)
    frame["delay_days_remaining"] = np.maximum(
        7,
        230
        - stage_index * 37
        + frame.objection_count * 19
        + frame.document_turnaround_days * 1.4
        + frame.officer_open_load * 0.7
        + noise,
    ).round()
    frame["compensation_days"] = np.maximum(
        5,
        34
        + frame.objection_count * 10
        + frame.document_turnaround_days * 0.8
        + frame.officer_open_load * 0.45
        + frame.days_in_compensation * 0.35
        + noise * 0.45,
    ).round()
    return frame


def build_pipeline() -> Pipeline:
    preprocess = ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
            ("numeric", "passthrough", NUMERIC),
        ]
    )
    return Pipeline(
        [
            ("preprocess", preprocess),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=180,
                    max_depth=12,
                    min_samples_leaf=3,
                    random_state=26016,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def evaluate(frame: pd.DataFrame, target: str) -> dict[str, float | int]:
    training, holdout = train_test_split(frame, test_size=0.2, random_state=26016)
    pipeline = build_pipeline()
    pipeline.fit(training[CATEGORICAL + NUMERIC], training[target])
    estimated = pipeline.predict(holdout[CATEGORICAL + NUMERIC])
    baseline = np.repeat(training[target].median(), len(holdout))
    return {
        "holdout_rows": len(holdout),
        "mae_days": round(float(mean_absolute_error(holdout[target], estimated)), 2),
        "rmse_days": round(float(root_mean_squared_error(holdout[target], estimated)), 2),
        "r2": round(float(r2_score(holdout[target], estimated)), 3),
        "baseline_mae_days": round(float(mean_absolute_error(holdout[target], baseline)), 2),
    }


def train(
    frame: pd.DataFrame,
    target: str,
    metrics: dict[str, float | int],
    dataset_sha256: str,
) -> dict:
    pipeline = build_pipeline()
    pipeline.fit(frame[CATEGORICAL + NUMERIC], frame[target])
    feature_names = list(pipeline.named_steps["preprocess"].get_feature_names_out())
    references = {
        **{column: str(frame[column].mode().iloc[0]) for column in CATEGORICAL},
        **{column: float(frame[column].median()) for column in NUMERIC},
    }
    return {
        "pipeline": pipeline,
        "feature_names": feature_names,
        "reference_values": references,
        "metrics": metrics,
        "training_rows": len(frame),
        "dataset_sha256": dataset_sha256,
        "synthetic_training_data": True,
        "version": "phase3-rf-v2",
    }


if __name__ == "__main__":
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = generate_history()
    dataset_path = DATA_DIR / "synthetic_case_history.csv"
    history.to_csv(dataset_path, index=False)
    dataset_sha256 = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    model_targets = {
        "delay_model.joblib": "delay_days_remaining",
        "compensation_timeline_model.joblib": "compensation_days",
    }
    evaluations = {target: evaluate(history, target) for target in model_targets.values()}
    for filename, target in model_targets.items():
        joblib.dump(
            train(history, target, evaluations[target], dataset_sha256), MODEL_DIR / filename
        )
    model_card = {
        "version": "phase3-rf-v2",
        "dataset": {
            "name": "BhoomiSetu reproducible synthetic case history",
            "rows": len(history),
            "sha256": dataset_sha256,
            "seed": 26016,
            "real_records": 0,
        },
        "holdout": {"method": "80/20 split", "random_state": 26016},
        "metrics": evaluations,
        "intended_use": [
            "procedural delay-risk triage",
            "compensation-disbursal timeline planning",
        ],
        "prohibited_use": [
            "land valuation or compensation amount calculation",
            "legal, ownership, eligibility, or payment decisions",
            "claims of real-world accuracy before approved historical validation",
        ],
    }
    (DATA_DIR / "model_card.json").write_text(
        json.dumps(model_card, indent=2, sort_keys=True) + "\n"
    )
    print(
        f"trained 2 models on {len(history)} reproducible synthetic cases; "
        f"holdout metrics written to {DATA_DIR / 'model_card.json'}"
    )
