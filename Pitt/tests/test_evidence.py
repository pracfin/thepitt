from Pitt.pkg.predictor.evidence import EvidenceStore
from pathlib import Path
import shutil


def test_evidence_save_and_load(tmp_path):
    root = tmp_path / "evidence"
    store = EvidenceStore(root=str(root))

    # save without 'note' or 'description' should raise
    try:
        store.save("test1", {"foo": "bar"})
        raise AssertionError("Expected ValueError for missing note/description")
    except ValueError:
        pass

    # proper save
    item = store.save("test2", {"note": "a note", "confidence": 0.9})
    assert item.id == "test2"

    loaded = store.load("test2")
    assert loaded is not None
    assert loaded.payload.get("note") == "a note"

    ids = store.list_ids()
    assert "test2" in ids

    # simple query by confidence
    results = store.query(min_confidence=0.5)
    assert "test2" in results

    # cleanup explicit to be nice (tmp_path normally isolated)
    shutil.rmtree(root)
