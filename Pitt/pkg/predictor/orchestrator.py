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
from Pitt.pkg.predictor.evidence import EvidenceStore
from Pitt.pkg.predictor.projection import generate_constant_growth_series
from Pitt.pkg.predictor.valuation import dcf_from_fcf
from decimal import Decimal


def run_prediction(context: Dict[str, Any]) -> PredictionOutput:
    """Simple orchestrator skeleton: accepts a sample input dict and returns a PredictionOutput.

    For Task 1 this is a minimal implementation that wraps the sample payload and ensures
    required top-level fields exist.
    """
    sample = context.get("sample", {})
    ticker = context.get("ticker") or sample.get("ticker") or "UNKNOWN"
    generated_at = datetime.utcnow().isoformat() + "Z"

    # Evidence handling: instantiate store and collect items
    evidence_items = []
    assumptions = []
    evid_ids = context.get("evidence_ids") or []
    raw_evidence = sample.get("evidence_raw") or []
    evidence_root = context.get("evidence_root", "database/evidence")
    store = EvidenceStore(root=evidence_root)

    missing_evidence_ids = []
    if evid_ids:
        for eid in evid_ids:
            item = store.load(eid)
            if item:
                # Map internal EvidenceItem to the public schema shape expected by PredictionOutput
                mapped = {
                    "source": item.id,
                    "description": item.payload.get("note") or item.payload.get("description") or f"evidence:{item.id}",
                    "confidence": item.payload.get("confidence"),
                    "retrieved_at": item.created_at,
                    "raw_ref": item.payload.get("raw_ref"),
                }
                evidence_items.append(mapped)
            else:
                missing_evidence_ids.append(eid)

    if missing_evidence_ids:
        assumptions.append(f"Missing evidence ids: {', '.join(missing_evidence_ids)}")

    evidence_iterations = context.get("evidence_iterations")
    max_evidence_iterations = context.get("max_evidence_iterations")
    if evidence_iterations is not None and max_evidence_iterations is not None:
        try:
            if int(evidence_iterations) >= int(max_evidence_iterations):
                assumptions.append("Evidence iteration limit reached; proceeding with documented assumptions.")
        except Exception:
            pass

    # ingest raw evidence entries and append
    for raw in raw_evidence:
        try:
            created = store.ingest(raw)
            evidence_items.append({
                "source": created.id,
                "description": created.payload.get("description") or created.payload.get("note"),
                "confidence": created.payload.get("confidence"),
                "retrieved_at": created.created_at,
                "raw_ref": None,
            })
        except Exception:
            continue

    # If no projections provided, create simple placeholders (Revenue, FCF)
    projections = sample.get("projections")
    if not projections:
        proj_type = context.get("proj_type", "constant-growth")
        years = int(context.get("proj_years", 5))
        start_year = int(generated_at[:4])
        if proj_type == "constant-growth":
            rev = generate_constant_growth_series("Revenue", start_year,  Decimal("100.0"), Decimal("0.05"), years)
            fcf = generate_constant_growth_series("FCF", start_year, Decimal("10.0"), Decimal("0.05"), years)
        else:
            # fallback to constant growth for unknown types for now
            rev = generate_constant_growth_series("Revenue", start_year,  Decimal("100.0"), Decimal("0.05"), years)
            fcf = generate_constant_growth_series("FCF", start_year, Decimal("10.0"), Decimal("0.05"), years)
        # Use pydantic models for projection entries; projection.generate returns ProjectionSeries
        projections = [rev, fcf]

    # If valuation absent and FCF series present, compute a simple DCF
    valuation = sample.get("valuation")
    if not valuation:
        # find FCF series
        fcf_series = None
        for s in projections:
            if s.name == "FCF":
                fcf_series = s
                break
        if fcf_series:
            discount_rate = Decimal(str(context.get("discount_rate", 0.10)))
            terminal_growth = Decimal(str(context.get("terminal_growth", 0.02)))
            valuation = dcf_from_fcf(fcfs := fcf_series, discount_rate=discount_rate, terminal_growth=terminal_growth)

    pred_dict = {
        "id": sample.get("id") or f"pred-{ticker}-{generated_at}",
        "ticker": ticker,
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "projections": projections,
        "evidence": sample.get("evidence", []) or evidence_items,
        "valuation": valuation,
        "trace": sample.get("trace", []),
        "meta": {"generated_by": "pitt-skeleton", "assumptions": assumptions},
    }

    # Validate via Pydantic model
    pred = PredictionOutput.model_validate(pred_dict)
    return pred
