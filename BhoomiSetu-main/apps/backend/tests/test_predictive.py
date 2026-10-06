import asyncio
import threading
import uuid
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from app.api import intelligence
from app.services.predictive import load_bundle, predict, predict_days

FEATURES = {
    "project_type": "Highway",
    "state": "Maharashtra",
    "district": "Pune",
    "current_stage": "verification",
    "parcel_count": 1,
    "objection_count": 2,
    "document_turnaround_days": 12,
    "officer_open_load": 20,
    "days_in_compensation": 0,
}


@pytest.mark.parametrize("name", ["delay_model.joblib", "compensation_timeline_model.joblib"])
def test_batched_inference_preserves_estimates_and_explanations(name: str) -> None:
    bundle = load_bundle(name)
    pipeline = bundle["pipeline"]
    cases = [
        FEATURES,
        {**FEATURES, "current_stage": "compensation", "days_in_compensation": 18},
        {**FEATURES, "objection_count": 0, "officer_open_load": 0},
    ]
    expected = [
        max(1, round(float(pipeline.predict(pd.DataFrame([case]))[0]))) for case in cases
    ]
    assert predict_days(name, cases) == expected
    assert predict_days(name, []) == []

    for case, days in zip(cases, expected, strict=True):
        effects = {
            feature: abs(
                days - float(pipeline.predict(pd.DataFrame([{**case, feature: value}]))[0])
            )
            for feature, value in bundle["reference_values"].items()
        }
        ranked = sorted(effects, key=effects.get, reverse=True)[:3]
        total = sum(effects[key] for key in ranked) or 1.0
        result = predict(name, case)
        assert result.predicted_days_remaining == days
        assert [(item.feature, item.importance) for item in result.top_features] == [
            (key, round(effects[key] / total, 4)) for key in ranked
        ]


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["delay", "compensation", "aggregate"])
async def test_model_work_does_not_block_other_api_tasks(monkeypatch, route: str) -> None:
    started, release = threading.Event(), threading.Event()

    def slow_model(*args):
        started.set()
        release.wait(timeout=3)
        return [100] if route == "aggregate" else "prediction result"

    monkeypatch.setattr(intelligence, "predict", slow_model)
    monkeypatch.setattr(intelligence, "predict_days", slow_model)
    monkeypatch.setattr(intelligence, "accessible_case_or_404", AsyncMock())
    monkeypatch.setattr(intelligence, "_prediction_features", AsyncMock(return_value=FEATURES))
    monkeypatch.setattr(intelligence, "_row_features", lambda *args: FEATURES)
    db = AsyncMock()
    rows = MagicMock()
    rows.all.return_value = [(None, None, 0, 0)]
    db.execute.return_value = rows
    if route == "aggregate":
        request = intelligence.aggregate_predictions(state=None, project_type=None, db=db)
    else:
        handler = (
            intelligence.delay_prediction if route == "delay"
            else intelligence.compensation_prediction
        )
        request = handler(case_id=uuid.uuid4(), db=db, actor=None)
    task = asyncio.create_task(request)
    try:
        assert await asyncio.to_thread(started.wait, 2)
        # The event loop must run this task while model inference is still waiting.
        assert not task.done(), "Model inference blocked the API event loop"
    finally:
        release.set()
        await task
