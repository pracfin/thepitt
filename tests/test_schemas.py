import json
import sys
from pathlib import Path

import pytest

# Ensure repository root is on sys.path for imports when pytest runs
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from schemas.schema import PredictionOutput

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "schemas" / "samples"


def load_sample(name: str):
    p = SAMPLES_DIR / name
    assert p.exists(), f"Sample not found: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


def assert_roundtrip(data: dict):
    obj = PredictionOutput.model_validate(data)
    dumped = obj.model_dump()
    reobj = PredictionOutput.model_validate(dumped)
    assert reobj.model_dump() == obj.model_dump()


def test_prediction_short_validate_and_roundtrip():
    data = load_sample("prediction_short.json")
    assert_roundtrip(data)


def test_prediction_full_validate_and_roundtrip():
    data = load_sample("prediction_full.json")
    # Basic sanity checks
    assert "projections" in data and len(data["projections"]) >= 1
    obj = PredictionOutput.model_validate(data)
    assert obj.ticker == "ACME"
    assert obj.generated_at is not None
    # Roundtrip
    dumped_json = obj.model_dump_json()
    obj2 = PredictionOutput.model_validate_json(dumped_json)
    assert obj2.model_dump() == obj.model_dump()
