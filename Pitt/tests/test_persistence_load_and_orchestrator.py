import json
import sys
from pathlib import Path

import pytest

# Ensure repo root is on sys.path for imports when pytest runs
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Pitt.pkg.predictor import orchestrator, persistence
from schemas.schema import PredictionOutput


def test_orchestrator_creates_valid_prediction():
    sample = {"ticker": "UNIT", "id": "u-1", "projections": [], "evidence": [], "valuation": None}
    pred = orchestrator.run_prediction({"sample": sample, "ticker": "UNIT"})
    assert isinstance(pred, PredictionOutput)
    assert pred.ticker == "UNIT"
    assert pred.id is not None


def test_persist_and_load_roundtrip(tmp_path):
    # Create a minimal PredictionOutput
    d = {
        "ticker": "RT",
        "generated_at": "2026-07-10T12:00:00",
        "id": "rt-1",
        "projections": [],
        "valuation": {
            "valuation_date": "2026-07-10T12:00:00",
            "dcf_value": "10.0",
            "terminal_value": "1.0",
        },
        "evidence": [{"source": "unit-test", "description": "roundtrip"}],
    }
    pred = PredictionOutput.model_validate(d)

    base = tmp_path / "db"
    out_path = persistence.persist_prediction(pred, base_dir=str(base))
    assert Path(out_path).exists()

    loaded = persistence.load_prediction(out_path)
    assert isinstance(loaded, PredictionOutput)
    assert loaded.ticker == pred.ticker
