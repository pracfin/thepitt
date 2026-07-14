import json
from pathlib import Path
import shutil
from Pitt.pkg.predictor.cli import main


def test_reindex_and_prune(tmp_path):
    # setup evidence root with one evidence referencing a raw file
    evidence_root = tmp_path / "evidence"
    raw_root = tmp_path / "raw"
    evidence_root.mkdir()
    raw_root.mkdir()

    # create referenced raw file and evidence file pointing to it
    raw_file = raw_root / "ref.raw.json"
    raw_file.write_text(json.dumps({"text": "keep me"}), encoding="utf-8")
    evid = evidence_root / "e1.json"
    evid.write_text(json.dumps({"id": "e1", "created_at": "2026-01-01T00:00:00Z", "payload": {"source": "s", "raw_ref": str(raw_file)}}))

    # create an orphan raw file
    orphan = raw_root / "orphan.raw.json"
    orphan.write_text(json.dumps({"text": "delete me"}), encoding="utf-8")

    # run reindex
    rc = main(["reindex", "--evidence-root", str(evidence_root)])
    assert rc == 0

    # run prune as dry-run first
    rc_dry = main(["prune", "--orphan-only", "--raw-root", str(raw_root), "--evidence-root", str(evidence_root), "--dry-run"]) 
    assert rc_dry == 0
    # dry-run should not delete
    assert orphan.exists()

    # now run actual prune
    rc2 = main(["prune", "--orphan-only", "--raw-root", str(raw_root), "--evidence-root", str(evidence_root)])
    assert rc2 == 0

    # orphan should be deleted
    assert not orphan.exists()
    assert raw_file.exists()

    # cleanup
    shutil.rmtree(evidence_root)
    shutil.rmtree(raw_root)
    