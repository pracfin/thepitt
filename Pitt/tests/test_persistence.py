import os
import json
from pathlib import Path
import sys
import pytest

# Ensure repo root is on sys.path so Pitt package is importable during pytest
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Pitt.pkg.predictor import persistence
from schemas.schema import PredictionOutput


def make_sample_prediction(tmp_path):
    # Minimal prediction dict matching schema keys used by persistence
    d = {
        "ticker": "TEST",
        "generated_at": "2026-07-10T12:00:00",
        "id": "test-1",
        "projections": [],
        "valuation": {
            "valuation_date": "2026-07-10T12:00:00",
            "dcf_value": "100.0",
            "terminal_value": "10.0",
        },
        "evidence": [
            {"source": "unit-test", "description": "synthetic"}
        ],
    }
    return PredictionOutput.model_validate(d)


def test_atomic_write_failure_cleanup(tmp_path, monkeypatch):
    pred = make_sample_prediction(tmp_path)
    base = tmp_path / "database" / "predictions"
    # Ensure replace raises after tmp write
    called = {"replace": False}

    original_replace = os.replace

    def fake_replace(src, dst):
        called["replace"] = True
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", fake_replace)

    with pytest.raises(OSError):
        persistence.persist_prediction(pred, base_dir=str(base))

    # tmp file should not remain
    ticker_dir = base / "TEST"
    assert ticker_dir.exists()
    tmp_files = list(ticker_dir.glob("*.tmp"))
    assert tmp_files == []

    # restore
    monkeypatch.setattr(os, "replace", original_replace)


def test_size_limit_rejected(tmp_path):
    # Build a prediction whose JSON representation is >10MB
    # Use a large string in evidence to inflate size
    large_text = "x" * (11 * 1024 * 1024)
    d = {
        "ticker": "BIG",
        "generated_at": "2026-07-10T12:00:00",
        "id": "big-1",
        "projections": [],
        "valuation": {
            "valuation_date": "2026-07-10T12:00:00",
            "dcf_value": "1.0",
            "terminal_value": "0.1",
        },
        # Place the large payload into meta to inflate size while keeping evidence valid
        "evidence": [{"source": "unit-test", "description": "big", "raw_ref": None}],
        "meta": {"big_blob": large_text},
    }
    pred = PredictionOutput.model_validate(d)

    with pytest.raises(persistence.LargePayloadError):
        persistence.persist_prediction(pred, base_dir=str(tmp_path / "db"))
