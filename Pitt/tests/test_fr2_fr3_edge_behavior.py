import json
from pathlib import Path

import pytest

from Pitt.pkg.predictor.evidence import EvidenceStore
from Pitt.pkg.predictor.orchestrator import run_prediction
from Pitt.pkg.predictor.cli import main


def test_fr2_missing_evidence_ids_records_assumption(tmp_path):
    root = tmp_path / "evidence"
    root.mkdir(parents=True, exist_ok=True)

    pred = run_prediction({
        "ticker": "ACME",
        "evidence_ids": ["missing-1", "missing-2"],
        "evidence_root": str(root),
    })
    data = pred.model_dump()

    assert "meta" in data
    assumptions = data["meta"].get("assumptions", [])
    assert assumptions
    assert any("missing evidence ids" in str(item).lower() for item in assumptions)


def test_fr2_iteration_limit_in_context_records_assumption(tmp_path):
    root = tmp_path / "evidence"
    root.mkdir(parents=True, exist_ok=True)

    pred = run_prediction({
        "ticker": "ACME",
        "evidence_root": str(root),
        "evidence_iterations": 3,
        "max_evidence_iterations": 3,
    })
    data = pred.model_dump()

    assumptions = data["meta"].get("assumptions", [])
    assert any("evidence iteration limit reached" in str(item).lower() for item in assumptions)


def test_fr3_manual_upload_roundtrip_with_raw_payload(tmp_path):
    sample = {
        "id": "sample-fr3",
        "ticker": "ACME",
        "evidence": [
            {
                "source": "manual-disclosure-1",
                "description": "Quarterly disclosure",
                "confidence": 0.88,
                "raw_payload": {"doc_type": "quarterly", "period": "Q1"},
            }
        ],
    }
    sample_path = tmp_path / "sample.json"
    sample_path.write_text(json.dumps(sample), encoding="utf-8")

    evidence_root = tmp_path / "evidence"
    raw_root = tmp_path / "raw"

    rc = main([
        "run",
        "--sample",
        str(sample_path),
        "--persist-evidence",
        "--persist-raw",
        "--evidence-root",
        str(evidence_root),
        "--raw-root",
        str(raw_root),
    ])
    assert rc == 0

    stored = list(evidence_root.glob("*.json"))
    assert stored

    stored_doc = json.loads(stored[0].read_text(encoding="utf-8"))
    payload = stored_doc.get("payload", {})
    raw_ref = payload.get("raw_ref")
    assert raw_ref
    assert Path(raw_ref).exists()


def test_fr3_invalid_manual_upload_is_rejected(tmp_path):
    invalid = {
        "id": "sample-invalid",
        "ticker": "ACME",
        "evidence": [
            {
                "description": "Missing source should fail schema",
            }
        ],
    }
    sample_path = tmp_path / "invalid.json"
    sample_path.write_text(json.dumps(invalid), encoding="utf-8")

    rc = main(["run", "--sample", str(sample_path)])
    assert rc == 1
