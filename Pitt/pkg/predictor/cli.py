import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

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
    p.add_argument("command", nargs="?", choices=["run", "reindex", "prune"], help="command to run")
    p.add_argument("--sample", help="Path to sample PredictionOutput JSON to use as input")
    p.add_argument("--ticker", help="Ticker to run prediction for")
    p.add_argument("--evidence-root", help="Path to evidence root for persistence")
    p.add_argument("--persist-evidence", action="store_true", help="Persist evidence items from prediction into the evidence store")
    p.add_argument("--persist-raw", action="store_true", help="Persist raw evidence payloads to disk and set raw_ref")
    p.add_argument("--raw-root", help="Path to store raw evidence payloads (e.g. database/raw_news)")
    # projection / valuation options
    p.add_argument("--proj-type", choices=["constant-growth", "linear-trend"], default="constant-growth", help="Projection generation type when none provided")
    p.add_argument("--proj-years", type=int, default=5, help="Number of years to project when generating projections")
    p.add_argument("--discount-rate", type=float, default=0.10, help="Discount rate to use for DCF (decimal, e.g. 0.10 for 10%)")
    p.add_argument("--terminal-growth", type=float, default=0.02, help="Terminal growth rate for DCF (decimal)")
    p.add_argument("--export-report", help="Path to write a human-readable report (Markdown).")
    p.add_argument("--report-format", choices=["md","pdf","docx","pptx"], default="md", help="Report output format (markdown written natively; convert externally for PDF/DOCX/PPTX)")
    # prune options
    p.add_argument("--older-than-days", type=int, help="Prune raw files older than given days")
    p.add_argument("--orphan-only", action="store_true", help="Prune raw files not referenced by evidence index/files")
    p.add_argument("--dry-run", action="store_true", help="List files that would be deleted but do not delete them")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    cmd = args.command or "run"
    sample_path = args.sample
    if cmd == "run" and sample_path:
        path = Path(sample_path)
        if not path.exists():
            print(f"Sample not found: {path}", file=sys.stderr)
            return 2
        data = json.loads(path.read_text(encoding="utf-8"))
        # Let orchestrator produce PredictionOutput from sample
        # Pass projection and valuation options into the orchestrator via context
        context = {
            "sample": data,
            "ticker": args.ticker,
            "proj_type": args.proj_type,
            "proj_years": args.proj_years,
            "discount_rate": args.discount_rate,
            "terminal_growth": args.terminal_growth,
        }
        try:
            pred = run_prediction(context=context)
        except Exception as exc:
            print(f"Failed to run prediction: {exc}", file=sys.stderr)
            return 1
        # Persist
        out_path = persistence.persist_prediction(pred)
        print(f"Persisted: {out_path}")
        # Optional report export
        if args.export_report:
            from Pitt.pkg.predictor.reporting import export_prediction_report

            report_path = Path(args.export_report)
            try:
                exported = export_prediction_report(pred, report_path, fmt=args.report_format)
                print(f"Report written: {exported}")
            except RuntimeError as exc:
                print(f"Failed to export report: {exc}", file=sys.stderr)
                return 3
        # Optionally persist evidence items returned in the prediction
        if args.persist_evidence:
            from Pitt.pkg.predictor.evidence import EvidenceStore

            root = args.evidence_root or "database/evidence"
            store = EvidenceStore(root=root)
            pd = pred.model_dump()
            evs = pd.get("evidence", [])
            # keep original sample evidence to access any raw_payload that is not
            # preserved by the validated PredictionOutput schema
            original_evidence = data.get("evidence", [])
            original_map = {o.get("source"): o for o in original_evidence}
            saved_ids = []
            for i, e in enumerate(evs):
                eid = e.get("source") or f"{pd.get('ticker')}-e{ i }-{int(datetime.utcnow().timestamp())}"
                conf = e.get("confidence")
                try:
                    # coerce possible Decimal to float for JSON
                    if conf is not None:
                        conf = float(conf)
                except Exception:
                    conf = None
                payload = {"description": e.get("description"), "confidence": conf, "raw_ref": e.get("raw_ref"), "source": e.get("source")}

                # Optionally persist raw payloads if requested
                if args.persist_raw:
                    raw_root = args.raw_root or "database/raw_news"
                    raw_root_path = Path(raw_root)
                    raw_root_path.mkdir(parents=True, exist_ok=True)
                    # Prefer raw_payload from the original sample (it may be stripped
                    # by the PredictionOutput schema). Fall back to fields present in `e`.
                    original = original_map.get(e.get("source"))
                    raw_payload = None
                    if original is not None:
                        raw_payload = original.get("raw_payload") or original.get("payload")
                    if raw_payload is None:
                        raw_payload = e.get("raw_payload") or e.get("payload")
                    if raw_payload is not None:
                        raw_filename = f"{eid}.raw.json"
                        raw_path = raw_root_path / raw_filename
                        try:
                            raw_path.write_text(json.dumps(raw_payload), encoding="utf-8")
                            payload["raw_ref"] = str(raw_path)
                        except Exception as exc:
                            print(f"Failed to save raw evidence for {eid}: {exc}", file=sys.stderr)

                try:
                    store.save(eid, payload)
                    saved_ids.append(eid)
                except Exception as exc:
                    print(f"Failed to save evidence {eid}: {exc}", file=sys.stderr)
            if saved_ids:
                print(f"Saved evidence ids: {', '.join(saved_ids)}")
        return 0
    if cmd == "reindex":
        from Pitt.pkg.predictor.evidence import EvidenceStore

        root = args.evidence_root or "database/evidence"
        store = EvidenceStore(root=root)
        store.reindex()
        print(f"Reindexed evidence store at: {root}")
        return 0

    if cmd == "prune":
        # prune raw files by age or orphan status
        raw_root = Path(args.raw_root or "database/raw_news")
        evidence_root = Path(args.evidence_root or "database/evidence")
        deleted = []
        now = datetime.utcnow().timestamp()
        # collect referenced raw_refs from evidence files
        referenced = set()
        if evidence_root.exists():
            for p in evidence_root.glob("*.json"):
                try:
                    d = json.loads(p.read_text(encoding="utf-8"))
                    payload = d.get("payload", {})
                    rr = payload.get("raw_ref")
                    if rr:
                        referenced.add(str(Path(rr).resolve()))
                except Exception:
                    continue

        if not raw_root.exists():
            print(f"Raw root does not exist: {raw_root}")
            return 0

        for f in raw_root.rglob("*"):
            if not f.is_file():
                continue
            try:
                remove = False
                if args.orphan_only:
                    if str(f.resolve()) not in referenced:
                        remove = True
                if args.older_than_days is not None:
                    age = (now - f.stat().st_mtime) / 86400.0
                    if age > args.older_than_days:
                        remove = True
                if remove:
                    if args.dry_run:
                        deleted.append(str(f))
                    else:
                        f.unlink()
                        deleted.append(str(f))
            except Exception:
                continue

        if deleted:
            print(f"Deleted {len(deleted)} raw files")
        else:
            print("No files deleted")
        return 0

    # fallback when run was requested but no sample provided
    print("No action specified. Use --sample SAMPLE.json or specify command 'reindex'/'prune'", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
