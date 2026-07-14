
Plan: Speckit Implementation Workplan (Detailed)

Flow: Specify -> Plan -> Implement (this document finalizes Plan)

Purpose
-------
This file is the rigorous Plan artifact for Phase 1 implementation. It maps the spec to executable tasks, with measurable acceptance criteria, time estimates, test artifacts, file targets, and dependencies. Follow this plan exactly before broad implementation to preserve spec-driven development.

Local-first Git workflow (project policy)
----------------------------------------
This plan assumes a local-first development policy for Phase 1. By
default work is performed and committed locally on feature branches and
merged into `main` locally. Adding a remote is an explicit project
decision and must be recorded in the ADR log. This keeps the project
lightweight and avoids repeating repository setup for new contributors.

Phases (summary)
-----------------
- Specify: completed. Canonical spec at repository root and a copy in `Pitt/spec/engineering_specification.md`.
- Plan: this document (complete). Contains detailed tasks and subtasks.
- Implement: follow the ordered tasks below; each task must pass its acceptance criteria and tests before moving to the next.

Task Ordering & Rationale
-------------------------
Order: 1) Skeleton CLI/orchestrator, 2) Persistence (atomic, validated), 3) Unit tests, 4) Projection & Valuation logic, 5) Research & Evidence adapter, 6) Integration tests, 7) ADRs & documentation, 8) CI and release. This sequence minimizes rework while enabling an early, verifiable artifact (persisted PredictionOutput) for AC1-AC4.

Detailed Tasks
--------------

Task 1: `pkg/predictor` skeleton (CLI + orchestrator entry)
- Goal: produce a runnable CLI that loads a sample input, calls the orchestrator skeleton, and persists the resulting `PredictionOutput` using the persistence module stub.
- File targets:
   - Pitt/pkg/predictor/__init__.py
   - Pitt/pkg/predictor/cli.py (entry: `run --ticker TICKER --sample FILE`)
   - Pitt/pkg/predictor/orchestrator.py (function: `run_prediction(context) -> PredictionOutput`)
   - Pitt/pkg/predictor/__main__.py (allow `python -m pitt.pkg.predictor`)
- Subtasks:
   1. Create package and CLI; parse args and support `--sample`.
   2. Implement orchestrator skeleton returning a minimal `PredictionOutput` from sample input.
   3. Wire canonical schemas import via `from schemas.schema import PredictionOutput`.
   4. Call persistence.persist_prediction(pred) (stub initially).
- Acceptance criteria:
   - CLI runs without exceptions and returns exit code 0 when invoked with `--sample Pitt/samples/prediction_short.json`.
   - A file is created under `database/predictions/` (temp name then final) when the run completes.
- Tests:
   - Pitt/tests/test_cli_run.py: calls CLI with sample and asserts output file exists and validates against `PredictionOutput` model.
- Estimate: 2-4 hours (Confidence: high)

Task 2: Persistence module (atomic validated writes)
- Goal: Implement `persist_prediction` and `load_prediction` with strict schema validation, atomic commit, and size checks.
- File targets:
   - Pitt/pkg/predictor/persistence.py
   - Tests: Pitt/tests/test_persistence.py
- Subtasks:
   1. Implement `validate_prediction(pred: PredictionOutput) -> None` using Pydantic `model_validate`.
   2. Implement `persist_prediction(pred: PredictionOutput, base_dir='database/predictions') -> path`:
       - Serialize to JSON with `model_dump_json()`.
       - If >10MB, raise specific `LargePayloadError` (caller may strip large evidence via `raw_ref`).
       - Write to tmp file then `os.replace()` to final path.
   3. Implement `load_prediction(path) -> PredictionOutput` with validation and migration warning if `schema_version` != current.
- Acceptance criteria:
   - Unit tests verify validation fails for malformed payload and succeeds for sample payloads.
   - Atomicity test: simulate process crash during write and ensure no partial file exists at final path.
- Tests:
   - Pitt/tests/test_persistence.py: validation, round-trip write/read, atomicity simulation.
- Estimate: 3-6 hours (Confidence: high)

Task 3: Unit tests & test fixtures (tests-first approach)
- Goal: Add definitive unit tests for models, persistence, projection utilities, and orchestrator flow.
- File targets:
   - Pitt/tests/test_schemas.py (re-use canonical tests)
   - Pitt/tests/test_persistence.py
   - Pitt/tests/test_projection_utils.py
   - Pitt/tests/test_orchestrator_skeleton.py
- Subtasks:
   1. Port existing root-level tests into `Pitt/tests/` for local CI.
   2. Add tests that assert AC1-AC4 behaviors at unit level (schema validations, evidence presence, iteration enforcement).
- Acceptance criteria:
   - `pytest -q` in repo root passes all unit tests locally.
- Estimate: 2-4 hours (Confidence: high)

Task 4: Projection utilities and Valuation skeleton (deterministic)
- Goal: Implement deterministic projection functions and a valuation stub that computes DCF given `ProjectionSeries`.
- File targets:
   - Pitt/pkg/predictor/projection.py (functions: `apply_constant_growth`, `interpolate_growth_curve`, `project_fcf_from_revenue`)
   - Pitt/pkg/predictor/valuation.py (function: `compute_dcf(projections, assumptions) -> ValuationResult`)
   - Tests: Pitt/tests/test_projection_utils.py, Pitt/tests/test_valuation.py
- Subtasks:
   1. Implement projection formulas using `Decimal` for all arithmetic.
   2. Implement DCF discounting with terminal value via Gordon Growth.
   3. Implement sensitivity generator (vary discount rate +/- 200 bps).
- Acceptance criteria:
   - Unit tests validate arithmetic and sensitivity outputs.
   - Output `ValuationResult` conforms to schema and includes `assumptions`.
- Estimate: 6-10 hours (Confidence: medium)

Task 5: Research & Evidence adapter (local-first)
- Goal: Implement a Research adapter that prioritizes local/manual uploads, then cached search, then live API (if configured and budget permits).
- File targets:
   - Pitt/pkg/predictor/evidence.py (class: `EvidenceAdapter` with `find_evidence` and `fetch_raw`)
   - Tests: Pitt/tests/test_evidence_adapter.py
- Subtasks:
   1. Implement local upload handler scanning `database/fundamental_data/` and `database/raw_news/`.
   2. Implement a simple cache layer (file-based index) for prior API results.
   3. Implement a stubbed Exa API adapter for Phase 1; add configuration to enable real Exa integration later.
   4. Enforce recursion/hop and budget limits per execution context.
- Acceptance criteria:
   - Adapter returns `EvidenceItem[]` for sample queries; when budget exhausted, adapter returns partial results and records budget usage.
- Estimate: 6-12 hours (Confidence: medium-low; depends on Exa API access)

Task 6: Integration tests and E2E harness
- Goal: Run the full orchestrator loop with canned evidence and market prices, persist output, and validate AC1-AC4.
- File targets:
   - Pitt/tests/test_integration_e2e.py
   - A small CLI runner script under `Pitt/scripts/run_sample.sh`
- Subtasks:
   1. Create canned fixtures for market_prices and evidence (use Pitt/samples/).
   2. Run CLI to produce a persisted PredictionOutput and assert schema validity and evidence presence.
   3. Test evidence-missing flow resulting in recorded assumptions or structured failure.
- Acceptance criteria:
   - E2E tests pass locally in Codespaces within acceptable time (goal: <2 minutes per run on average hardware).
- Estimate: 4-8 hours (Confidence: medium)

Task 7: ADRs & documentation
- Goal: Persist ADRs from the spec as individual markdown files and add implementation runbook and README updates.
- File targets:
   - Pitt/docs/adr/008-schema-library.md
   - Pitt/docs/adr/009-numeric-types.md
   - Pitt/docs/adr/010-evidence-storage.md
   - Pitt/docs/adr/011-persistence.md
   - Pitt/README.md (update with run instructions)
- Subtasks:
   1. Create ADR files with decision template (title, context, options, recommendation, impact).
   2. Link ADRs from `Pitt/spec/engineering_specification.md` or the root spec.
- Acceptance criteria:
   - ADR files exist and are referenced in the spec; changes approved by reviewer.
- Estimate: 1-2 hours (Confidence: high)

Task 8: CI (GitHub Actions) and release gating
- Goal: Add a minimal CI that runs `pytest` and lints on PRs and pushes to `main`.
- File targets:
   - .github/workflows/ci.yml
- Subtasks:
   1. Author a workflow that sets up Python 3.11, installs requirements, runs `pytest -q`.
   2. Add a `make test` helper in repo root README or `Pitt/scripts/`.
- Acceptance criteria:
   - CI runs and passes for all branches; PRs cannot be merged without passing tests (enforced by branch protection later).
- Estimate: 2-4 hours (Confidence: high)

Cross-Cutting Concerns
----------------------
- Tests-first: implement unit tests before production code for each task.
- Schema safety: all persisted outputs must pass Pydantic validation (strict reject on failure).
- Logging and trace: every orchestration run must append trace entries to `execution_trace` for traceability.
- Secrets: do not commit credentials; use env vars and Codespaces secrets.

Dependencies & Blockers
-----------------------
- Access to Exa or other search APIs is optional — we will use a stub for Phase 1. If you opt for live Exa, provide API keys.
- Market pricing adapters (Zerodha/ICICI) require developer credentials; for initial testing use canned price fixtures.

Risk Register (top items)
-------------------------
- Risk: Unavailable external APIs — Mitigation: local-first adapter and canned fixtures (low impact).
- Risk: Ambiguity in spec fields — Mitigation: implement minimal canonical schemas and add ADRs for unresolved choices (medium impact).
- Risk: Unexpected file sizes — Mitigation: enforce 10MB limit and use `raw_ref` pattern (low impact).

Milestones
----------
- M1 (Day 0.5): Task 1 complete — CLI skeleton runs and persists a sample file.
- M2 (Day 1): Task 2 & 3 complete — persistence validated and core tests pass.
- M3 (Days 2–4): Task 4 & 5 complete — deterministic projection & valuation implemented and evidence adapter stubbed.
- M4 (Day 5): Integration tests and CI configured; ready for initial demo.

Owners & Review
----------------
- Owner (implementation lead): TBD (insert assignee)
- Reviewer: PM / Architect (as required per ADR)

Change Control
--------------
- Any deviation from this plan that impacts delivery >1 day or costs >$100/month must be recorded as an Evidence Request and escalated to the PM per `copilot-instructions.md`.

Plan complete. Proceed to Implement Task 1 when ready.

