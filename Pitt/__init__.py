"""Pitt package root for Speckit workspace."""
"""Top-level package to expose Pitt workspace modules for `python -m pitt` style runs.

This file makes the Pitt workspace importable by ensuring the repo root is on
sys.path and re-exporting the `pkg` package under the `pitt` namespace.
"""
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Pitt.pkg import *  # noqa: E402,F401
