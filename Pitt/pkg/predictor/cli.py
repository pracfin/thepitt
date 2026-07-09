import argparse
import json
import sys
from pathlib import Path

from pathlib import Path
import sys

# Ensure repository root is on sys.path so top-level packages (schemas) import
# correctly when this file is executed as a script.
REPO_ROOT = Path(__file__).resolve().parents[2].parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from schemas.schema import PredictionOutput

from Pitt.pkg.predictor.orchestrator import run_prediction
from Pitt.pkg.predictor import persistence


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="pitt-predictor")
    p.add_argument("run", nargs="?", help="run command placeholder")
    p.add_argument("--sample", help="Path to sample PredictionOutput JSON to use as input")
    p.add_argument("--ticker", help="Ticker to run prediction for")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    sample_path = args.sample
    if sample_path:
        path = Path(sample_path)
        if not path.exists():
            print(f"Sample not found: {path}", file=sys.stderr)
            return 2
        data = json.loads(path.read_text(encoding="utf-8"))
        # Let orchestrator produce PredictionOutput from sample
        pred = run_prediction(context={"sample": data, "ticker": args.ticker})
        # Persist
        out_path = persistence.persist_prediction(pred)
        print(f"Persisted: {out_path}")
        return 0
    else:
        print("No action specified. Use --sample SAMPLE.json", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
