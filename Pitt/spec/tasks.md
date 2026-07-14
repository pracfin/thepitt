Tasks (derived from `Pitt/spec/plan.md`)
=====================================

This file is a concise, actionable task list extracted from the speckit
plan. It is intended as a developer checklist for implementation.

- Task 1: `pkg/predictor` skeleton (CLI + orchestrator entry)
  - Target: `Pitt/pkg/predictor/cli.py`, `orchestrator.py`
  - Status: done

- Task 2: Persistence module (atomic validated writes)
  - Target: `Pitt/pkg/predictor/persistence.py`
  - Status: done

- Task 3: Unit tests & test fixtures
  - Target: `Pitt/tests/*`
  - Status: done

- Task 4: Projection utilities & Valuation skeleton
  - Target: `Pitt/pkg/predictor/projection.py`, `valuation.py`
  - Status: not-started

- Task 5: Research & Evidence adapter (local-first)
  - Target: `Pitt/pkg/predictor/evidence.py`
  - Status: not-started

- Task 6: Integration tests and E2E harness
  - Target: `Pitt/tests/test_integration_e2e.py`
  - Status: not-started

- Task 7: ADRs & documentation
  - Target: `Pitt/docs/adr/`
  - Status: not-started

- Task 8: CI (GitHub Actions)
  - Target: `.github/workflows/ci.yml`
  - Status: not-started

Use this file as the short-lived task list during implementation.