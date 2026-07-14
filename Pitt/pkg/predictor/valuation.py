from __future__ import annotations
from decimal import Decimal, getcontext
from typing import List, Dict, Any
from datetime import datetime

from schemas.schema import ProjectionSeries, ProjectionEntry, ValuationResult, ValuationSensitivity


getcontext().prec = 28


def dcf_from_fcf(
    fcf_series: ProjectionSeries,
    discount_rate: Decimal = Decimal("0.10"),
    terminal_growth: Decimal = Decimal("0.02"),
    terminal_method: str = "gordon",
) -> ValuationResult:
    """Compute a simple DCF valuation from a projected FCF series.

    - `fcf_series` must be ordered chronologically and contain numeric `value` entries.
    - returns `ValuationResult` with base DCF and simple sensitivity scenarios.
    """
    # Basic validation and hardening
    if not fcf_series or not getattr(fcf_series, 'entries', None):
        raise ValueError("fcf_series must contain at least one ProjectionEntry")

    if discount_rate <= terminal_growth:
        raise ValueError("discount_rate must be greater than terminal_growth to compute Gordon terminal value")

    # Discount projected cash flows
    pv_total = Decimal(0)
    for idx, entry in enumerate(fcf_series.entries):
        t = idx + 1
        fcf = Decimal(entry.value)
        pv = fcf / (Decimal(1) + discount_rate) ** t
        pv_total += pv

    # Terminal value via Gordon Growth
    last_fcf = Decimal(fcf_series.entries[-1].value)
    if terminal_method == "gordon":
        terminal_value = (last_fcf * (Decimal(1) + terminal_growth)) / (discount_rate - terminal_growth)
    else:
        terminal_value = Decimal(0)

    # Discount terminal value back
    terminal_pv = terminal_value / (Decimal(1) + discount_rate) ** len(fcf_series.entries)
    dcf_value = (pv_total + terminal_pv).quantize(Decimal("0.01"))

    assumptions: Dict[str, Any] = {
        "discount_rate": str(discount_rate),
        "terminal_growth": str(terminal_growth),
        "terminal_method": terminal_method,
    }

    # Sensitivity: vary discount rate +/- 200 bps
    sensitivities: List[ValuationSensitivity] = []
    for name, dr in [("Base", discount_rate), ("Down -200bps", discount_rate - Decimal("0.02")), ("Up +200bps", discount_rate + Decimal("0.02"))]:
        pv = Decimal(0)
        for idx, entry in enumerate(fcf_series.entries):
            t = idx + 1
            fcf = Decimal(entry.value)
            pv += fcf / (Decimal(1) + dr) ** t
        if terminal_method == "gordon":
            tv = (last_fcf * (Decimal(1) + terminal_growth)) / (dr - terminal_growth)
        else:
            tv = Decimal(0)
        tv_pv = tv / (Decimal(1) + dr) ** len(fcf_series.entries)
        total = (pv + tv_pv).quantize(Decimal("0.01"))
        sensitivities.append(ValuationSensitivity(name=name, valuation_value=total, note=None))

    val = ValuationResult(
        valuation_date=datetime.utcnow(),
        dcf_value=dcf_value,
        terminal_value=terminal_value.quantize(Decimal("0.01")),
        assumptions=assumptions,
        sensitivities=sensitivities,
    )
    return val
