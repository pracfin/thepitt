# Stock Analyzer — Phase 1 (Predictor)

Purpose
-------
This repository contains the Phase 1 implementation artifacts for the
Stock Analyzer Predictor. The goal is to provide a small, local-first
toolkit for developing, testing, and persisting schema-validated
predictions.

Local-first policy
-------------------
- Work is local-first by default. Commits and feature branches live on
  the local machine until an explicit project decision is made to add a
  remote. See `Stock_Analyzer_Engineering_Specification.md` and
  `Pitt/spec/plan.md` for the project policy and plan.

Quick start (developer)
------------------------
1. Create a python virtual environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. Run tests:

```bash
pytest -q
```

3. Run the CLI smoke runner (example):

```bash
python Pitt/pkg/predictor/cli.py --sample Pitt/samples/prediction_short.json
```

Branching & commits
--------------------
- Keep a stable `main` branch locally.
- Create short-lived feature branches named like `feat/xyz` or `fix/abc`.
- Commit frequently and run tests before merging locally.

Files of interest
-----------------
- `schemas/schema.py` — canonical Pydantic models.
- `Pitt/pkg/predictor/` — implementation skeleton (CLI, orchestrator, persistence).
- `Pitt/tests/` — smoke and robustness tests.
- `Pitt/spec/plan.md` — the implementation plan.
- `Pitt/spec/tasks.md` — concise task list derived from the plan.

When to add a remote
---------------------
Only add a remote if you want cross-machine backup or code review.
Record any remote decision in the ADR log and update the plan.

Contact
-------
Project lead / owner: (TBD)
