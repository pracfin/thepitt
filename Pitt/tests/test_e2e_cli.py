import json
import os
from pathlib import Path
from Pitt.pkg.predictor.cli import main


def test_cli_run_persist_and_report(tmp_path):
    # prepare sample payload
    sample = {
        "id": "s1",
        "ticker": "TST",
        "projections": [],
        "evidence": [{"source": "ex-1", "description": "evidence note", "confidence": 0.9}],
    }
    sample_path = tmp_path / "sample.json"
    sample_path.write_text(json.dumps(sample), encoding="utf-8")

    evidence_root = tmp_path / "evidence"
    raw_root = tmp_path / "raw"
    out_report = tmp_path / "report.md"

    # run CLI main
    rc = main([
        "run",
        "--sample",
        str(sample_path),
        "--evidence-root",
        str(evidence_root),
        "--persist-evidence",
        "--persist-raw",
        "--raw-root",
        str(raw_root),
        "--export-report",
        str(out_report),
        "--report-format",
        "md",
    ])
    assert rc == 0

    # persisted evidence file should exist
    files = list(evidence_root.glob("*.json"))
    assert any(f.name.startswith("ex-1") for f in files)

    # report file should exist
    assert out_report.exists()
