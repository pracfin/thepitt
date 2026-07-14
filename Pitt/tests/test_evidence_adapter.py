import tempfile
import shutil
from pathlib import Path
from Pitt.pkg.predictor.evidence import EvidenceStore


def test_evidence_save_load_list_query_reindex(tmp_path):
    root = tmp_path / "evidence"
    store = EvidenceStore(root)

    # save items
    item1 = store.save("id1", {"note": "first note", "source": "s1", "confidence": 0.8})
    item2 = store.save("id2", {"description": "second", "source": "s2", "confidence": 0.5})

    # load
    loaded = store.load("id1")
    assert loaded is not None
    assert loaded.id == "id1"
    assert loaded.payload["note"] == "first note"

    # list ids
    ids = store.list_ids()
    assert set(ids) == {"id1", "id2"}

    # query
    q = store.query(min_confidence=0.6)
    assert q == ["id1"]

    # reindex after manual file add
    extra = root / "id3.json"
    extra.write_text('{"id":"id3","created_at":"2020-01-01T00:00:00Z","payload":{"description":"x","confidence":0.9}}')
    store.reindex()
    ids2 = store.list_ids()
    assert set(ids2) == {"id1", "id2", "id3"}


def test_evidence_ingest_normalization(tmp_path):
    store = EvidenceStore(tmp_path / "evidence2")

    # ingest from raw text
    it = store.ingest("This is a raw note", source="scraper", confidence=0.7)
    assert it is not None
    loaded = store.load(it.id)
    assert loaded is not None
    assert "This is a raw note" in loaded.payload.get("description", "")
    assert loaded.payload.get("source") == "scraper"

    # ingest from dict
    it2 = store.ingest({"note": "dict note", "id": "provided-id"}, confidence=0.9)
    assert it2.id == "provided-id"
    l2 = store.load("provided-id")
    assert l2.payload["note"] == "dict note"


def test_orchestrator_ingests_raw_evidence(tmp_path, monkeypatch):
    # ensure orchestrator uses our tmp evidence root
    from Pitt.pkg.predictor.orchestrator import run_prediction

    sample = {"ticker": "TST", "evidence_raw": ["a quick note", {"note": "structured"} ]}
    ctx = {"sample": sample, "evidence_root": str(tmp_path / "evidence_root")}
    pred = run_prediction(ctx)
    # prediction evidence should contain at least two items from ingestion
    ev = pred.evidence
    assert isinstance(ev, list)
    assert len(ev) >= 2


def test_validation_enforced(tmp_path):
    store = EvidenceStore(tmp_path / "evval")
    # if pydantic is available, missing text should raise
    try:
        store.save("x", {"source": "s"})
        raised = False
    except Exception:
        raised = True
    # either the save raises (pydantic) or our save validation in code raises
    assert raised


def test_search_fallback_scan(tmp_path):
    root = tmp_path / "e"
    root.mkdir()
    p1 = root / "a.json"
    p1.write_text('{"id":"a","payload":{"description":"findme"}}')
    p2 = root / "b.json"
    p2.write_text('{"id":"b","payload":{"description":"other"}}')

    store = EvidenceStore(root)
    results = list(store.search_exa(root, "findme"))
    assert any(r.name == "a.json" for r in results)


def test_search_uses_external_tool(tmp_path, monkeypatch):
    root = tmp_path / "e2"
    root.mkdir()
    p1 = root / "a.json"
    p1.write_text('{"id":"a","payload":{"description":"findme"}}')

    store = EvidenceStore(root)

    # monkeypatch shutil.which to claim rg exists
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda name: "/usr/bin/rg" if name == "rg" else None)

    # monkeypatch subprocess.run to return a fake output
    class Dummy:
        def __init__(self):
            self.returncode = 0
            self.stdout = str(p1)

    def fake_run(cmdlist, capture_output, text, timeout):
        return Dummy()

    monkeypatch.setattr("subprocess.run", fake_run)

    results = list(store.search_exa(root, "findme"))
    assert any(r.name == "a.json" for r in results)
