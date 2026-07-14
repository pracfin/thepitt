# Phase 1 MVP Traceability Matrix

Date: 2026-07-14

## Functional Requirements

| Requirement | Status | Implementation | Tests | Notes |
|---|---|---|---|---|
| FR1 Structured prediction package | Done | `Pitt/pkg/predictor/orchestrator.py`, `schemas/schema.py` | `Pitt/tests/test_integration_e2e.py`, `Pitt/tests/test_e2e_cli.py`, `tests/test_schemas.py` | Produces projections, valuation, evidence, trace |
| FR2 Evidence Request routing + resume | Partial | `Pitt/pkg/predictor/orchestrator.py`, `Pitt/pkg/predictor/evidence.py` | `Pitt/tests/test_evidence.py`, `Pitt/tests/test_evidence_adapter.py` | Basic retrieval/ingest exists; explicit request lifecycle semantics still lightweight |
| FR3 Manual disclosure upload integration | Partial | `Pitt/pkg/predictor/cli.py`, `Pitt/pkg/predictor/evidence.py` | `Pitt/tests/test_cli_persist_raw_evidence.py`, `Pitt/tests/test_cli_persist_evidence.py` | Manual evidence persistence exists; disclosure-specific validation/workflow still limited |
| FR4 Persist outputs + execution metadata | Done | `Pitt/pkg/predictor/persistence.py`, `Pitt/pkg/predictor/cli.py` | `Pitt/tests/test_persistence.py`, `Pitt/tests/test_persistence_offload.py`, `Pitt/tests/test_cli_run.py` | Atomic writes and load validation implemented |

## Non-Functional Requirements

| Requirement | Status | Implementation | Tests | Notes |
|---|---|---|---|---|
| NFR1 Schema constrained I/O | Done | `schemas/schema.py`, `Pitt/pkg/predictor/persistence.py` | `tests/test_schemas.py`, persistence tests | Uses Pydantic validation |
| NFR2 Explainable execution trace | Done | `schemas/schema.py`, `Pitt/pkg/predictor/orchestrator.py` | `Pitt/tests/test_cli_run.py`, `Pitt/tests/test_integration_e2e.py` | Trace entries persisted in output |
| NFR3 Budget + recursion constraints | Partial | `Pitt/pkg/predictor/evidence.py` | `Pitt/tests/test_evidence_adapter.py` | Guardrails exist, but full orchestrator-level enforcement can be expanded |
| NFR4 Codespaces Python 3.10/3.11 target | Done | `requirements.txt`, CI workflow | CI run | CI pins Python 3.11 |

## Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| AC1 10 sample tickers persisted with schema validation | Done | Archived run `artifacts/ac1_runs/20260714T154902Z` with report `artifacts/ac1_runs/20260714T154902Z/ac1_validation_report.json` (10/10 passed) |
| AC2 Every prediction has at least one evidence item with source/retrieved_at | Partial | Supported by orchestrator mapping and evidence persistence tests |
| AC3 Orchestrator enforces evidence iteration limits and records assumptions | Partial | Assumption recording present; iteration-limit behavior needs hard checks |
| AC4 Reject malformed requests via Pydantic | Done | Schema validation tests and persistence loading behavior |
