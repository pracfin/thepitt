from schemas.schema import PredictionOutput, EvidenceItem, ProjectionSeries, ProjectionEntry
from Pitt.pkg.predictor.persistence import persist_prediction, LargePayloadError
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import shutil


def make_large_prediction(tmp_path):
    # create a prediction with a huge evidence payload
    evidence = [
        {"source": "unit-test", "description": "big", "confidence": Decimal("0.9"), "raw_payload": {"text": "x" * 2_000_000}}
    ]
    pred = {
        "id": "bigpred",
        "ticker": "ACME",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "projections": [],
        "evidence": evidence,
        "meta": {}
    }
    return pred


def test_persist_offloads_evidence(tmp_path):
    pred = make_large_prediction(tmp_path)
    base = tmp_path / "db"
    # use a small max size to force offload
    # pass raw dict so offload can access original raw_payload
    out = persist_prediction(pred, base_dir=str(base), max_payload_size=1024)
    # check that raw file exists
    raw_base = base / "raw_news" / "ACME"
    assert raw_base.exists()
    files = list(raw_base.glob("*.raw.json"))
    assert files
    # cleanup
    shutil.rmtree(base)
    