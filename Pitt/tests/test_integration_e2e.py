from Pitt.pkg.predictor.evidence import EvidenceStore
from Pitt.pkg.predictor.orchestrator import run_prediction
from pathlib import Path
import shutil


def test_orchestrator_includes_evidence(tmp_path):
    root = tmp_path / "evidence"
    store = EvidenceStore(root=str(root))

    # save an evidence item
    store.save("ev-1", {"note": "test-evidence", "value": 123})

    pred = run_prediction({"ticker": "ACME", "evidence_ids": ["ev-1"], "evidence_root": str(root)})
    # prediction returns a pydantic model-like object; convert to dict for assertions
    pd = pred.model_dump()
    assert "evidence" in pd
    ev = pd["evidence"]
    assert isinstance(ev, list)
    # Evidence items map `source` to the stored id
    assert any(e.get("source") == "ev-1" for e in ev)

    # cleanup
    shutil.rmtree(root)
