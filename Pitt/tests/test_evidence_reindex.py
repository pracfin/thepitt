from Pitt.pkg.predictor.evidence import EvidenceStore
from pathlib import Path
import shutil


def test_reindex_builds_index(tmp_path):
    root = tmp_path / "evidence"
    store = EvidenceStore(root=str(root))
    # create two evidence files directly
    p1 = root / "a.json"
    p1.write_text('{"id":"a","created_at":"2026-01-01T00:00:00Z","payload":{"source":"s1","confidence":0.5}}')
    p2 = root / "b.json"
    p2.write_text('{"id":"b","created_at":"2026-01-02T00:00:00Z","payload":{"source":"s2","confidence":0.8}}')
    # remove index and reindex
    (root / "index.json").unlink()
    store.reindex()
    ids = store.list_ids()
    assert "a" in ids and "b" in ids
    shutil.rmtree(root)
    