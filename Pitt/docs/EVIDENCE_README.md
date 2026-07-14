Evidence Adapter (local-first)
===============================

Overview
--------
`Pitt/pkg/predictor/evidence.py` implements a small, local-first evidence adapter optimized for the Phase 1 MVP.

Key features
------------
- Filesystem-backed store under a configurable `root` (default `database/evidence`).
- Atomic writes (write to `.tmp` then `os.replace`) to avoid partial files.
- Minimal payload validation: `save()` requires either `note` or `description` in the payload.
- `index.json` maintained in the evidence root for quick listing and simple queries.
- `query(min_confidence=...)` helper and `reindex()` to rebuild the index from disk.

Public API
----------
- `EvidenceStore(root: str)` - create/open an evidence store.
- `save(item_id: str, payload: Dict[str,Any]) -> EvidenceItem` - validate and persist an evidence item.
- `load(item_id: str) -> Optional[EvidenceItem]` - load item by id.
- `list_ids() -> List[str]` - return ids from index.
- `query(min_confidence: float | None) -> List[str]` - query ids by confidence.
- `reindex()` - rebuild index.json from disk files.

Storage layout
--------------
- Evidence items: `database/evidence/<id>.json`
- Index: `database/evidence/index.json`

Notes & rationale
-----------------
- The adapter intentionally uses simple JSON files to remain easy to inspect and recover.
- Validation is intentionally minimal for the MVP; expand with a JSON schema or Pydantic validation if needed.

Known limitations
-----------------
- No compacting or index pruning; `reindex()` is provided to repair or rebuild.
- No support for remote backends (S3, etc.) — could be added later behind a small adapter interface.
