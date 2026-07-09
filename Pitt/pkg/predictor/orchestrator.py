from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from pathlib import Path
import sys

# When run as a script ensure repo root is on sys.path so imports work
REPO_ROOT = Path(__file__).resolve().parents[2].parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from schemas.schema import PredictionOutput


def run_prediction(context: Dict[str, Any]) -> PredictionOutput:
    """Simple orchestrator skeleton: accepts a sample input dict and returns a PredictionOutput.

    For Task 1 this is a minimal implementation that wraps the sample payload and ensures
    required top-level fields exist.
    """
    sample = context.get("sample", {})
    ticker = context.get("ticker") or sample.get("ticker") or "UNKNOWN"
    generated_at = datetime.utcnow().isoformat() + "Z"

    pred_dict = {
        "id": sample.get("id") or f"pred-{ticker}-{generated_at}",
        "ticker": ticker,
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "projections": sample.get("projections", []),
        "evidence": sample.get("evidence", []),
        "valuation": sample.get("valuation"),
        "trace": sample.get("trace", []),
        "meta": {"generated_by": "pitt-skeleton"},
    }

    # Validate via Pydantic model
    pred = PredictionOutput.model_validate(pred_dict)
    return pred
