from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field
from pydantic import ConfigDict


class EvidenceItem(BaseModel):
    """A single piece of evidence supporting a prediction."""
    source: str = Field(..., description="Source identifier (e.g., 'SEC 10-K', 'Reuters')")
    description: str = Field(..., description="Brief description of the evidence")
    confidence: Optional[Decimal] = Field(None, ge=0, le=1, description="Confidence score between 0 and 1")
    retrieved_at: Optional[datetime] = Field(None, description="When the evidence was retrieved")
    raw_ref: Optional[str] = Field(None, description="Optional reference/URI to raw evidence stored separately")

    model_config = ConfigDict(json_schema_extra={"example": {
        "source": "Reuters",
        "description": "Q1 revenue beat consensus",
        "confidence": "0.85",
        "retrieved_at": "2026-07-01T12:00:00Z",
        "raw_ref": "database/raw_evidence/acme/q1-2026.txt"
    }})


class ProjectionEntry(BaseModel):
    """A projection point (e.g., a single year or date)."""
    period: str = Field(..., description="Period label (e.g., '2026', '2026-12-31')")
    value: Decimal = Field(..., description="Projected numeric value (e.g., revenue, EPS)")
    growth_rate: Optional[Decimal] = Field(None, description="Implied growth rate as decimal (e.g., 0.12)")

    model_config = ConfigDict(json_schema_extra={"example": {
        "period": "2026",
        "value": "123.45",
        "growth_rate": "0.12"
    }})


class ProjectionSeries(BaseModel):
    """A named series of projections (e.g., revenue series)."""
    name: str = Field(..., description="Series name (e.g., 'Revenue')")
    currency: Optional[str] = Field("USD", description="Currency code for numeric values")
    unit: Optional[str] = Field("USD", description="Unit description")
    entries: List[ProjectionEntry] = Field(..., description="Ordered list of projection entries")

    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "Revenue",
        "currency": "USD",
        "unit": "USD",
        "entries": [
            {"period": "2024", "value": "100.0", "growth_rate": "0.10"}
        ]
    }})


class ValuationSensitivity(BaseModel):
    """A single sensitivity scenario for valuation outputs."""
    name: str = Field(..., description="Scenario name (e.g., 'Base', 'Down -10%')")
    valuation_value: Decimal = Field(..., description="Valuation result under this scenario")
    note: Optional[str] = Field(None, description="Optional note explaining the scenario")

    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "Base",
        "valuation_value": "1500.0",
        "note": "Base assumptions"
    }})


class ValuationResult(BaseModel):
    """Result of valuation calculations with optional sensitivity table."""
    valuation_date: datetime = Field(..., description="Date/time when valuation was computed")
    dcf_value: Decimal = Field(..., description="Discounted cash flow result")
    terminal_value: Decimal = Field(..., description="Terminal value used in the DCF")
    assumptions: Dict[str, Any] = Field(default_factory=dict, description="Key assumptions used for valuation")
    sensitivities: List[ValuationSensitivity] = Field(default_factory=list, description="Sensitivity scenarios")

    model_config = ConfigDict(json_schema_extra={"example": {
        "valuation_date": "2026-07-02T09:00:00Z",
        "dcf_value": "1200.0",
        "terminal_value": "300.0",
        "assumptions": {"discount_rate": "0.10", "terminal_growth": "0.02"},
        "sensitivities": [{"name": "Base", "valuation_value": "1500.0"}]
    }})


class ExecutionTraceEntry(BaseModel):
    """A trace entry describing execution steps / provenance."""
    step: str = Field(..., description="Short label for the step")
    timestamp: datetime = Field(..., description="Timestamp for the step")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional free-form details for debugging/provenance")

    model_config = ConfigDict(json_schema_extra={"example": {
        "step": "fetch_financials",
        "timestamp": "2026-07-02T09:00:00Z",
        "duration_ms": 125,
        "details": {"endpoint": "financials/v1"}
    }})


class PredictionOutput(BaseModel):
    """Top-level prediction output containing projections, evidence, valuation, and execution trace."""
    id: Optional[str] = Field(None, description="Optional unique id for the prediction")
    ticker: Optional[str] = Field(None, description="Ticker or identifier for the subject")
    schema_version: str = Field("1.0.0", description="Schema semantic version for the PredictionOutput")
    generated_at: datetime = Field(..., description="When the prediction was generated")
    projections: List[ProjectionSeries] = Field(default_factory=list, description="Projection series (revenue, EPS, etc.)")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Supporting evidence items")
    valuation: Optional[ValuationResult] = Field(None, description="Valuation results")
    trace: List[ExecutionTraceEntry] = Field(default_factory=list, description="Execution / provenance trace")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "pred-0001",
        "ticker": "ACME",
        "schema_version": "1.0.0",
        "generated_at": "2026-07-02T09:15:00Z"
    }})
