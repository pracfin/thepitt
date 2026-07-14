"""Minimal Exa API client for Stock Analyzer.

Reads `EXA_API_KEY` from the environment (do NOT hardcode secrets).

Usage:
    from Pitt.pkg.predictor import exa_client
    resp = exa_client.search("recent product announcements", numResults=3)

This module intentionally keeps behavior small and synchronous for easy
integration into the CLI/orchestrator. It raises clear errors when the
environment is not configured.
"""
from __future__ import annotations
import os
from typing import Any, Dict, Optional
import requests

EXA_API_KEY = os.getenv("EXA_API_KEY")
if not EXA_API_KEY:
    raise RuntimeError("EXA_API_KEY environment variable is not set. Add it to your shell or .env file.")

BASE_URL = "https://api.exa.ai/search"


def _headers() -> Dict[str, str]:
    return {"x-api-key": EXA_API_KEY, "Content-Type": "application/json"}


def search(
    query: str,
    type: str = "auto",
    numResults: int = 10,
    contents: Optional[Dict[str, Any]] = None,
    systemPrompt: Optional[str] = None,
    outputSchema: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Perform a POST /search to Exa and return parsed JSON.

    Keeps a small, explicit payload shape so callers can easily adapt it.
    Raises RuntimeError on HTTP errors.
    """
    if contents is None:
        contents = {"highlights": True}

    payload: Dict[str, Any] = {"query": query, "type": type, "numResults": numResults, "contents": contents}
    if systemPrompt is not None:
        payload["systemPrompt"] = systemPrompt
    if outputSchema is not None:
        payload["outputSchema"] = outputSchema

    resp = requests.post(BASE_URL, headers=_headers(), json=payload, timeout=timeout)
    try:
        resp.raise_for_status()
    except Exception as exc:
        # Avoid printing the API key in any error paths.
        raise RuntimeError(f"Exa API request failed: {resp.status_code} - {resp.text}") from exc

    return resp.json()
