Pitt Predictor CLI - Usage
==========================

Quick summary
-------------
The CLI entrypoint is `Pitt/pkg/predictor/cli.py`. Use the `run` command with a `--sample` file to generate and persist a `PredictionOutput`.

Flags
-----
- `--sample <file>` : Path to a JSON sample used as input for the orchestrator.
- `--ticker <TICKER>` : Optional ticker to override sample.
- `--evidence-root <path>` : Directory to store evidence metadata files (default `database/evidence`).
- `--persist-evidence` : When set, persist evidence items found in the output into the EvidenceStore under `--evidence-root`.
- `--persist-raw` : When set together with `--persist-evidence`, persist raw evidence payloads to disk and set `raw_ref` in the stored metadata.
- `--raw-root <path>` : Directory to store raw payload files (default `database/raw_news`).

Examples
--------
- Persist a prediction and its evidence metadata:

```bash
python3 -m Pitt.pkg.predictor.cli run --sample samples/prediction_short.json --persist-evidence --evidence-root database/evidence
```

- Persist raw evidence payloads (store raw files under `database/raw_news`):

```bash
python3 -m Pitt.pkg.predictor.cli run --sample samples/prediction_with_raw.json --persist-evidence --persist-raw --raw-root database/raw_news
```

Notes
-----
- `--persist-raw` looks for `raw_payload` in the original sample evidence. When using `--sample`, the CLI preserves the original sample content and prefers `raw_payload` there when writing raw files.
- The CLI will print saved evidence ids to stdout when persistence succeeds.

Testing
-------
There are integration tests under `Pitt/tests/` that exercise the CLI persistence behavior. Run these locally:

```bash
python3 -m pytest -q Pitt/tests/test_cli_persist_evidence.py
python3 -m pytest -q Pitt/tests/test_cli_persist_raw_evidence.py
```
