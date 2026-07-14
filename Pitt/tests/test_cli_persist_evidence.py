import json
from pathlib import Path
import shutil
from Pitt.pkg.predictor.cli import main


def test_cli_persists_evidence(tmp_path, monkeypatch):
    sample = {
        "id": "sample-1",
        "ticker": "ACME",
        "evidence": [
            {"source": "evsrc", "description": "a desc", "confidence": 0.75}
        ]
    }
    sample_path = tmp_path / "sample.json"
    sample_path.write_text(json.dumps(sample), encoding="utf-8")

    evidence_root = tmp_path / "evidence_root"

    # Run main as if CLI: args include --sample, --persist-evidence and --evidence-root
    exit_code = main(["run", "--sample", str(sample_path), "--persist-evidence", "--evidence-root", str(evidence_root)])
    assert exit_code == 0

    # check evidence saved
    files = list(evidence_root.glob("*.json"))
    assert any(f.stem == "evsrc" or "evsrc" in f.stem for f in files)

    # cleanup
    shutil.rmtree(evidence_root)