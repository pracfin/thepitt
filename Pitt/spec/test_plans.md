Test Plans — Tasks 1..8
========================

Purpose
-------
Short, manual test plans for each task. Each plan includes the exact
command(s) to run locally and explicit acceptance criteria so a PM or
developer can validate the task without ambiguity.

Notes
-----
- These are manual (developer-triggered) checks. Where automated tests
  exist, they are referenced.
- All commands assume you are at the repository root and have a Python
  virtualenv activated with dependencies installed.

Common prep
-----------
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Task 1 — CLI & Orchestrator skeleton
------------------------------------
How to run (manual):

```bash
python Pitt/pkg/predictor/cli.py --sample Pitt/samples/prediction_short.json
```

Acceptance criteria (manual verification):
- Exit code is 0 (command returns successfully).
- A file appears under `database/predictions/<TICKER>/` with `.json` suffix.
- The persisted JSON validates with the schema:

```python
python - <<'PY'
from pathlib import Path
from Pitt.pkg.predictor import persistence
f=list(Path('database/predictions').glob('**/*.json'))[0]
print('Found',f)
pred=persistence.load_prediction(str(f))
print('Validated:', pred.schema_version)
PY
```

Pass condition: file exists and `persistence.load_prediction()` returns a
`PredictionOutput` with no validation exceptions.

Automated check:

```bash
pytest -q Pitt/tests/test_cli_run.py
```

Task 2 — Persistence (atomic writes + size limit)
-------------------------------------------------
Automated check (preferred):

```bash
pytest -q Pitt/tests/test_persistence.py
```

Manual checks:
- Create a small prediction by running the CLI (Task 1) and verify no
  `.tmp` files remain and final `.json` file exists.
- To validate size limit manually, run a small script that constructs a
  `PredictionOutput` with a ~11MB blob in `meta` and call
  `persist_prediction()`; it should raise `LargePayloadError`.

Pass condition: the atomic failure test cleans up temp files; large
payloads are rejected with `LargePayloadError`.

Task 3 — Unit & integration tests (tests-first)
----------------------------------------------
How to run:

```bash
pytest -q
```

Pass condition: all tests pass locally. Any test failures must be
investigated and fixed before marking the task done.

Task 4 — Projection & Valuation skeleton
----------------------------------------
Manual validation (post-implementation):

1. Add or run unit tests `Pitt/tests/test_projection_utils.py` and
   `Pitt/tests/test_valuation.py`.

```bash
pytest -q Pitt/tests/test_projection_utils.py Pitt/tests/test_valuation.py
```

2. Example runtime check:

```bash
python - <<'PY'
from Pitt.pkg.predictor.projection import project_fcf_from_revenue
from Pitt.pkg.predictor.valuation import compute_dcf
# run a tiny example and print results
print('Run example...')
PY
```

Pass condition: unit tests pass; `compute_dcf()` returns a
`ValuationResult` with `dcf_value` and `terminal_value` fields populated.

Task 5 — Research & Evidence adapter (local-first)
-------------------------------------------------
Manual validation:

```bash
python - <<'PY'
from Pitt.pkg.predictor.evidence import EvidenceAdapter
ea = EvidenceAdapter()
results = ea.find_evidence('ACME revenue')
print('Evidence count', len(results))
for e in results[:3]:
    print(e.source, e.description)
PY
```

Pass condition: adapter returns a non-empty list for common queries
when local fixtures exist; budget/recursion enforcement logs or raises
an error when limits exceeded.

Task 6 — Integration / E2E harness
----------------------------------
Manual run (example):

```bash
python Pitt/scripts/run_sample.sh
# or: python Pitt/pkg/predictor/cli.py --sample Pitt/samples/prediction_full.json
```

Validation:
- An output JSON is persisted and validates with `persistence.load_prediction()`.
- Execution trace (`trace`) contains steps showing capability invocations.

Pass condition: persisted file valid, `trace` not empty, and essential
fields (`projections`, `valuation`) present (may be partially
populated for skeleton implementations).

Task 7 — ADRs & documentation
----------------------------
Manual check:

```bash
ls Pitt/docs/adr || true
grep -n "ADR" Stock_Analyzer_Engineering_Specification.md || true
```

Pass condition: ADR markdown files exist under `Pitt/docs/adr/` and the
spec references them.

Task 8 — CI (GitHub Actions)
---------------------------
Manual validation (local-first):
- Ensure `.github/workflows/ci.yml` exists locally.
- Verify `pytest -q` passes locally.

Automated validation (after remote exists):
- Push branch to remote and confirm workflow runs and passes on PR.

Pass condition: workflow file present and, once pushed, the workflow
completes successfully on the remote.

-------------------------
If you want, I can add these commands as small executable scripts under
`Pitt/scripts/` to make manual testing one-line and reproducible.
