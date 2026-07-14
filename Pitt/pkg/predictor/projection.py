from __future__ import annotations
from decimal import Decimal, getcontext
from typing import List
from datetime import datetime

from schemas.schema import ProjectionSeries, ProjectionEntry


getcontext().prec = 28


def generate_constant_growth_series(
    name: str,
    start_period: int,
    start_value: Decimal,
    growth_rate: Decimal,
    years: int,
    currency: str = "USD",
    unit: str = "USD",
) -> ProjectionSeries:
    """Generate a simple constant-growth projection series.

    - `start_period` is the first year as an integer (e.g., 2026).
    - `start_value` is the numeric value for the first period.
    - `growth_rate` is expressed as a decimal (0.10 == 10%).
    - returns a `ProjectionSeries` with `years` entries.
    """
    entries: List[ProjectionEntry] = []
    prev = Decimal(start_value)
    for i in range(years):
        period = str(start_period + i)
        if i == 0:
            gr = None
            value = prev
        else:
            value = (prev * (Decimal(1) + Decimal(growth_rate))).quantize(Decimal("0.0001"))
            gr = (value / prev - Decimal(1)).quantize(Decimal("0.0001"))
            prev = value

        entries.append(ProjectionEntry(period=period, value=Decimal(value), growth_rate=gr))

    return ProjectionSeries(name=name, currency=currency, unit=unit, entries=entries)


def compute_growth_rates(series: ProjectionSeries) -> ProjectionSeries:
    """Fill missing growth_rate fields for a ProjectionSeries and return a new series."""
    entries: List[ProjectionEntry] = []
    prev_value: Decimal | None = None
    for entry in series.entries:
        if prev_value is None:
            entries.append(ProjectionEntry(period=entry.period, value=entry.value, growth_rate=None))
            prev_value = entry.value
            continue
        if prev_value == 0:
            gr = None
        else:
            gr = (entry.value / prev_value - Decimal(1)).quantize(Decimal("0.0001"))
        entries.append(ProjectionEntry(period=entry.period, value=entry.value, growth_rate=gr))
        prev_value = entry.value

    return ProjectionSeries(name=series.name, currency=series.currency, unit=series.unit, entries=entries)
