import json
from pathlib import Path
import shutil
from Pitt.pkg.predictor.cli import main


def test_cli_persists_raw_evidence(tmp_path):
    sample = {
        "id": "sample-raw",
        "ticker": "ACME",
        "evidence": [
            {"source": "rawsrc", "description": "a desc", "confidence": 0.6, "raw_payload": {"text": "big text..."}}
        ]
    }
    sample_path = tmp_path / "sample_raw.json"
    sample_path.write_text(json.dumps(sample), encoding="utf-8")

    evidence_root = tmp_path / "evidence_root"
    raw_root = tmp_path / "raw_root"

    exit_code = main(["run", "--sample", str(sample_path), "--persist-evidence", "--persist-raw", "--evidence-root", str(evidence_root), "--raw-root", str(raw_root)])
    assert exit_code == 0

    # check raw saved
    raw_files = list(raw_root.glob("*.raw.json"))
    assert any("rawsrc" in f.stem for f in raw_files)

    # check evidence saved and references raw_ref
    ev_files = list(evidence_root.glob("*.json"))
    assert ev_files
    # load one and verify raw_ref present
    docs = [json.loads(path.read_text(encoding="utf-8")) for path in ev_files]
    payload_raw_refs = [doc.get("payload", {}).get("raw_ref") for doc in docs if isinstance(doc, dict)]
    assert any(ref is not None for ref in payload_raw_refs)

    # cleanup
    shutil.rmtree(evidence_root)
    shutil.rmtree(raw_root)
