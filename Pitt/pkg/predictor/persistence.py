import json
import os
from pathlib import Path
from typing import Optional

from pathlib import Path
import sys

# When run as a script ensure repo root is on sys.path so imports work
REPO_ROOT = Path(__file__).resolve().parents[2].parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from schemas.schema import PredictionOutput


class LargePayloadError(Exception):
    pass


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def persist_prediction(pred: PredictionOutput, base_dir: Optional[str] = None) -> str:
    base = Path(base_dir or os.path.join(os.getcwd(), "database", "predictions"))
    ticker = pred.ticker or "unknown"
    ensure_dir(base / ticker)

    gen_at = (
        pred.generated_at.isoformat() if hasattr(pred, "generated_at") else str(pred.generated_at)
    )
    filename = f"{gen_at.replace(':', '-')}_{pred.id or 'pred'}.json"
    final_path = base / ticker / filename
    tmp_path = base / ticker / (filename + ".tmp")

    # Serialize and size check
    payload = pred.model_dump_json(indent=2)
    if len(payload.encode("utf-8")) > 10 * 1024 * 1024:
        raise LargePayloadError("PredictionOutput too large (>10MB). Use raw_ref for evidence.")

    # Atomic write
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(payload)
    try:
        os.replace(tmp_path, final_path)
    except Exception:
        # Attempt to remove the temporary file to avoid leaving partial data
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
        raise
    return str(final_path)


def load_prediction(path: str) -> PredictionOutput:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return PredictionOutput.model_validate(data)
