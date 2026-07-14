import json
import os
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

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


def persist_prediction(pred: Union[PredictionOutput, dict], base_dir: Optional[str] = None, max_payload_size: int = 10 * 1024 * 1024) -> str:
    base = Path(base_dir or os.path.join(os.getcwd(), "database", "predictions"))
    # support callers passing either a validated PredictionOutput or the original raw dict
    if isinstance(pred, dict):
        pred_dict = pred
        ticker = pred_dict.get("ticker") or "unknown"
    else:
        pred_dict = pred.model_dump()
        ticker = pred.ticker or "unknown"
    ensure_dir(base / ticker)

    if isinstance(pred, dict):
        gen_at = pred_dict.get("generated_at") or datetime.utcnow().isoformat() + "Z"
        pred_id = pred_dict.get("id")
    else:
        gen_at = pred.generated_at.isoformat() if hasattr(pred, "generated_at") else str(pred.generated_at)
        pred_id = pred.id
    filename = f"{gen_at.replace(':', '-')}_{pred_id or 'pred'}.json"
    final_path = base / ticker / filename
    tmp_path = base / ticker / (filename + ".tmp")

    # Serialize to dict first so we can offload large evidence payloads if needed
    payload = json.dumps(pred_dict, indent=2, default=str)
    if len(payload.encode("utf-8")) > max_payload_size:
        # Attempt to offload evidence to keep prediction payload small.
        evidence = pred_dict.get("evidence", [])
        if evidence:
            raw_base = Path(base_dir or os.path.join(os.getcwd(), "database")) / "raw_news" / ticker
            raw_base.mkdir(parents=True, exist_ok=True)
            raw_name = f"{pred_id or 'pred'}-{gen_at.replace(':','-')}-evidence.raw.json"
            raw_path = raw_base / raw_name
            with raw_path.open("w", encoding="utf-8") as rf:
                json.dump(evidence, rf, default=str)
            # remove inline evidence and add pointer
            pred_dict["evidence"] = []
            meta = pred_dict.get("meta") or {}
            meta["evidence_raw_ref"] = str(raw_path)
            pred_dict["meta"] = meta
            payload = json.dumps(pred_dict, indent=2, default=str)
            if len(payload.encode("utf-8")) > max_payload_size:
                raise LargePayloadError("PredictionOutput too large (>max_payload_size) after evidence offload.")
        else:
            raise LargePayloadError("PredictionOutput too large (>max_payload_size) and no evidence to offload.")

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
