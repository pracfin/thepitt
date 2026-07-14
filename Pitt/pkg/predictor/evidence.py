from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime
import tempfile
import os
import re
import subprocess
from typing import Iterable
import shutil


@dataclass
class EvidenceItem:
    id: str
    created_at: str
    payload: Dict[str, Any]


class EvidenceStore:
    """A tiny local-first evidence adapter.

    Responsibilities:
    - store evidence items as JSON files under a local `evidence/` folder
    - list and load items

    This is intentionally small and synchronous for the MVP.
    """

    def __init__(self, root: Path | str = "database/evidence", *, search_cmd: str | None = None, search_timeout: float = 5.0):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        # index file to accelerate simple queries
        self._index_path = self.root / "index.json"
        if not self._index_path.exists():
            with self._index_path.open("w", encoding="utf-8") as f:
                json.dump({}, f)
        # search configuration
        self.search_cmd = search_cmd
        self.search_timeout = float(search_timeout)

    def _path_for(self, item_id: str) -> Path:
        return self.root / f"{item_id}.json"

    def save(self, item_id: str, payload: Dict[str, Any]) -> EvidenceItem:
        """Save with atomic write and minimal payload validation.

        Requires at least one of `note` or `description` in payload for now.
        """
        if not (payload.get("note") or payload.get("description")):
            raise ValueError("payload must include 'note' or 'description'")

        now = datetime.utcnow().isoformat() + "Z"
        item = EvidenceItem(id=item_id, created_at=now, payload=payload)
        p = self._path_for(item_id)

        # atomic write: write to temp file then rename
        fd, tmp_path = tempfile.mkstemp(dir=str(self.root), prefix=item_id, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"id": item.id, "created_at": item.created_at, "payload": item.payload}, f)
            os.replace(tmp_path, str(p))
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        # update index
        try:
            with self._index_path.open("r", encoding="utf-8") as f:
                idx = json.load(f)
        except Exception:
            idx = {}
        idx[item_id] = {"created_at": item.created_at, "source": payload.get("source"), "confidence": payload.get("confidence")}
        with self._index_path.open("w", encoding="utf-8") as f:
            json.dump(idx, f)

        return item

    def ingest(self, raw: Any, *, source: str | None = None, confidence: float | None = None) -> EvidenceItem:
        """High-level ingestion API.

        - `raw` can be a string, a Path to a file, or a dict payload.
        - normalizes payload to include at least `description` or `note`.
        - generates a stable id when possible, otherwise a timestamp-based id.
        """
        # Normalize input
        if isinstance(raw, dict):
            payload = dict(raw)
        elif isinstance(raw, (str, Path)):
            # if Path, read contents
            if isinstance(raw, Path):
                try:
                    payload_text = raw.read_text(encoding="utf-8")
                except Exception:
                    payload_text = str(raw)
            else:
                payload_text = raw
            payload = {"description": payload_text}
        else:
            payload = {"description": str(raw)}

        # Attach provided metadata
        if source and not payload.get("source"):
            payload["source"] = source
        if confidence is not None and payload.get("confidence") is None:
            try:
                payload["confidence"] = float(confidence)
            except Exception:
                payload["confidence"] = None
        # Generate an id: prefer provided id fields, else use timestamp
        item_id = payload.get("id") or payload.get("ref") or datetime.utcnow().strftime("evidence-%Y%m%d%H%M%S%f")

        # normalize and validate before saving
        np = self._normalize_payload(payload)
        # If pydantic model available on the class, validate and coerce fields
        model_cls = getattr(self.__class__, "_EvidencePayloadModel", None)
        ValidationErr = getattr(self.__class__, "ValidationError", Exception)
        if model_cls is not None:
            try:
                validated_model = model_cls(**np)
                # pydantic v2 uses model_dump, v1 uses dict()
                if hasattr(validated_model, "model_dump"):
                    np = validated_model.model_dump()
                else:
                    np = validated_model.dict()
            except ValidationErr:
                # re-raise to surface validation failures to callers
                raise

        return self.save(item_id, np)

    def _strip_html(self, text: str) -> str:
        # very small and permissive HTML tag stripper for MVP
        return re.sub(r"<[^>]+>", "", text)

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # ensure description or note exists
        p = dict(payload)
        if p.get("description") is None and p.get("note") is not None:
            p["description"] = p.get("note")

        # coerce confidence to float in [0,1]
        conf = p.get("confidence")
        if conf is not None:
            try:
                f = float(conf)
                if f < 0:
                    f = 0.0
                if f > 1:
                    f = 1.0
                p["confidence"] = f
            except Exception:
                p["confidence"] = None

        # strip simple HTML from text fields
        for k in ("description", "note"):
            if isinstance(p.get(k), str):
                p[k] = self._strip_html(p[k]).strip()

        return p

    # Pydantic-based validation for evidence payloads
    try:
        from pydantic import BaseModel, root_validator, ValidationError

        class _EvidencePayloadModel(BaseModel):
            id: Optional[str] = None
            note: Optional[str] = None
            description: Optional[str] = None
            source: Optional[str] = None
            confidence: Optional[float] = None
            raw_ref: Optional[str] = None

            @root_validator
            def ensure_text_present(cls, values):
                note = values.get("note")
                desc = values.get("description")
                if not (note or desc):
                    raise ValueError("evidence payload must include 'note' or 'description'")
                conf = values.get("confidence")
                if conf is not None:
                    try:
                        f = float(conf)
                        if f < 0:
                            f = 0.0
                        if f > 1:
                            f = 1.0
                        values["confidence"] = f
                    except Exception:
                        values["confidence"] = None
                return values
    except Exception:
        _EvidencePayloadModel = None
        ValidationError = Exception

    def search_exa(self, root: Path | str, pattern: str) -> Iterable[Path]:
        """Use the `exa` binary to search under `root` for files matching `pattern`.

        This is optional: if `exa` is not available or fails, fall back to local file scan.
        Returns an iterable of Path objects for matching files.
        """
        rootp = Path(root)
        cmd = self.search_cmd
        # Prepare candidates for external search. Prefer configured command, then rg, then grep.
        candidates: List = []
        if cmd:
            candidates.append(cmd)
        candidates.extend(["rg", "grep"])

        for candidate in candidates:
            # Normalize candidate into a list form
            if isinstance(candidate, (list, tuple)):
                base = list(candidate)
            else:
                base = [str(candidate)]

            bin_name = base[0]
            # skip if binary not found on PATH
            if shutil.which(bin_name) is None:
                continue

            # Build command arguments safely
            if bin_name.endswith("rg") or bin_name == "rg":
                cmdlist = base + ["-l", pattern, str(rootp)]
            elif bin_name.endswith("grep") or bin_name == "grep":
                cmdlist = base + ["-R", "-l", pattern, str(rootp)]
            else:
                cmdlist = base + [str(rootp), pattern]

            try:
                proc = subprocess.run(cmdlist, capture_output=True, text=True, timeout=self.search_timeout)
                # returncode 0 means matches found; non-zero often means no matches
                if proc.returncode == 0 and proc.stdout:
                    for ln in proc.stdout.splitlines():
                        yield Path(ln).resolve()
                    return
            except subprocess.TimeoutExpired:
                # try next candidate
                continue
            except Exception:
                continue

        # fallback: naive scan of json files containing pattern
        for p in rootp.rglob("*.json"):
            try:
                txt = p.read_text(encoding="utf-8")
                if pattern in txt:
                    yield p
            except Exception:
                continue

    def load(self, item_id: str) -> Optional[EvidenceItem]:
        p = self._path_for(item_id)
        if not p.exists():
            return None
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return EvidenceItem(id=data.get("id"), created_at=data.get("created_at"), payload=data.get("payload", {}))

    def list_ids(self) -> List[str]:
        # consult index if present
        try:
            with self._index_path.open("r", encoding="utf-8") as f:
                idx = json.load(f)
            return sorted(idx.keys())
        except Exception:
            # skip the index file itself when falling back to filesystem listing
            return [p.stem for p in sorted(self.root.glob("*.json")) if p.name != self._index_path.name]

    def query(self, min_confidence: float | None = None) -> List[str]:
        """Return list of ids matching simple indexed criteria."""
        try:
            with self._index_path.open("r", encoding="utf-8") as f:
                idx = json.load(f)
        except Exception:
            return []
        results = []
        for k, v in idx.items():
            conf = v.get("confidence")
            try:
                conf_val = float(conf) if conf is not None else None
            except Exception:
                conf_val = None
            if min_confidence is None or (conf_val is not None and conf_val >= float(min_confidence)):
                results.append(k)
        return sorted(results)

    def reindex(self) -> None:
        """Rebuild `index.json` from files on disk.

        This reads each JSON file in the root and constructs the index mapping.
        """
        idx: Dict[str, Dict[str, Any]] = {}
        for p in sorted(self.root.glob("*.json")):
            # skip the index file itself
            if p.name == self._index_path.name:
                continue
            try:
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                item_id = data.get("id") or p.stem
                payload = data.get("payload", {})
                idx[item_id] = {"created_at": data.get("created_at"), "source": payload.get("source"), "confidence": payload.get("confidence")}
            except Exception:
                continue
        with self._index_path.open("w", encoding="utf-8") as f:
            json.dump(idx, f)
