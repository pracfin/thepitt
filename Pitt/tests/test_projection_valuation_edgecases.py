from decimal import Decimal
import pytest

from Pitt.pkg.predictor.projection import generate_constant_growth_series, compute_growth_rates
from Pitt.pkg.predictor.valuation import dcf_from_fcf
from schemas.schema import ProjectionSeries, ProjectionEntry


def test_dcf_raises_on_empty_series():
    with pytest.raises(ValueError):
        dcf_from_fcf(ProjectionSeries(name="Empty", currency="USD", unit="USD", entries=[]))


def test_dcf_raises_on_bad_rates():
    fcf = generate_constant_growth_series("FCF", 2026, Decimal("10"), Decimal("0.05"), 3)
    with pytest.raises(ValueError):
        dcf_from_fcf(fcf, discount_rate=Decimal("0.02"), terminal_growth=Decimal("0.02"))


def test_projection_single_entry_and_growth_compute():
    # single entry projection: compute_growth_rates should keep None growth
    entry = ProjectionEntry(period="2026", value=Decimal("100.0"), growth_rate=None)
    series = ProjectionSeries(name="Single", currency="USD", unit="USD", entries=[entry])
    out = compute_growth_rates(series)
    assert len(out.entries) == 1
    assert out.entries[0].growth_rate is None
