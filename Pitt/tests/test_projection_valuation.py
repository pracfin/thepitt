from decimal import Decimal
from Pitt.pkg.predictor.projection import generate_constant_growth_series, compute_growth_rates
from Pitt.pkg.predictor.valuation import dcf_from_fcf


def test_generate_constant_growth_series():
    s = generate_constant_growth_series("Revenue", 2026, Decimal("100.0"), Decimal("0.10"), 3)
    assert s.name == "Revenue"
    assert len(s.entries) == 3
    assert s.entries[0].value == Decimal("100.0")
    assert s.entries[1].growth_rate == Decimal("0.1000")


def test_compute_growth_rates():
    s = generate_constant_growth_series("Revenue", 2026, Decimal("100.0"), Decimal("0.10"), 3)
    s2 = compute_growth_rates(s)
    assert s2.entries[1].growth_rate == Decimal("0.1000")


def test_dcf_from_fcf_basic():
    fcf = generate_constant_growth_series("FCF", 2026, Decimal("10.0"), Decimal("0.05"), 5)
    val = dcf_from_fcf(fcf, discount_rate=Decimal("0.10"), terminal_growth=Decimal("0.02"))
    assert val.dcf_value > 0
    assert len(val.sensitivities) == 3
