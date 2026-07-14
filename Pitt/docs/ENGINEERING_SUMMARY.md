Engineering Summary — Evidence & CLI (Phase 1)
===============================================

Feature Implemented
-------------------
- Local-first evidence adapter with atomic, indexed storage.
- CLI flags to persist evidence metadata and raw payloads.
- Orchestrator flow improved to generate placeholder projections and a DCF valuation when input lacks them.
- Automatic offloading of large evidence payloads to `database/raw_news/<ticker>/...` when serialized prediction exceeds size threshold.

Engineering Specification Coverage
---------------------------------
- Offloading behavior aligns with the engineering spec decision to store large raw evidence externally and reference via `raw_ref`.
- Evidence model mapped to `schemas.schema.EvidenceItem` and validated during prediction creation.

Files Modified
--------------
- `Pitt/pkg/predictor/evidence.py` — EvidenceStore implementation (save/load/list/query/reindex).
- `Pitt/pkg/predictor/cli.py` — CLI flags and persistence flow.
- `Pitt/pkg/predictor/orchestrator.py` — Evidence loading, projection and valuation wiring.
- `Pitt/pkg/predictor/persistence.py` — Offload logic for large predictions.
- `Pitt/tests/*` — New/updated unit & integration tests for the above.

Architecture Impact
-------------------
- Adds a local evidence store that decouples heavy raw payloads from the prediction JSONs.
- Keeps the codebase file-based and dependency-free for local-first development and testing.

Documentation Updated
---------------------
- `Pitt/docs/EVIDENCE_README.md`
- `Pitt/docs/CLI_USAGE.md`
- `Pitt/docs/ENGINEERING_SUMMARY.md`

Assumptions
-----------
- Local filesystem is acceptable for raw evidence storage in Phase 1.
- All consumers of `PredictionOutput` understand `meta.evidence_raw_ref` if present.

Known Limitations
-----------------
- No remote storage backend (S3) implemented.
- Index is simple JSON and may need compaction/locking in heavy concurrent scenarios.

Recommended Next Task
---------------------
- Add reindex/repair CLI command and a small `prune` utility to manage index growth and raw file lifecycle.

