import subprocess
import sys
from pathlib import Path


def test_cli_sample_run(tmp_path, monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    sample = repo_root / "Pitt" / "samples" / "prediction_short.json"
    assert sample.exists()

    # Run the CLI script directly to avoid module import path issues
    cli_script = repo_root / "Pitt" / "pkg" / "predictor" / "cli.py"
    cmd = [sys.executable, str(cli_script), "--sample", str(sample)]
    # Run from repo root so relative database/ path is correct
    proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
    print(proc.stdout)
    assert proc.returncode == 0

    # Find persisted files under database/predictions
    preds_dir = repo_root / "database" / "predictions"
    assert preds_dir.exists()
    # There should be at least one file under any ticker
    found = False
    for ticker_dir in preds_dir.iterdir():
        if ticker_dir.is_dir():
            for f in ticker_dir.iterdir():
                if f.suffix == ".json":
                    found = True
                    break
    assert found, "No prediction JSON persisted"
