"""
Section 15.5 Classification and Band Boundary Test Suite.
Tests integer cross-multiplication on exact edges:
- C=20000:
  - P=6000 (30.000%) -> high
  - P=5999 (29.995% rounds up to 30.00 on display, must remain acceptable band)
  - P=2000 (10.000%) -> acceptable
  - P=1999 (9.995% rounds up to 10.00 on display, must remain at_risk band)
  - P=1 (0.005%) -> at_risk
  - P=0 (0%) -> breakeven, at_risk
  - P=-1 (-0.005%) -> unprofitable, cash_drain
- Awkward denominator C=3333
- Zero revenue C=0
- Breakeven by construction (half_up vs half_even)
"""

from decimal import Decimal
import pytest
from f11.engine.formula import F11Engine


@pytest.fixture
def base_config():
    return {
        "api_version": "2024-10",
        "as_of": "2026-09-30T23:59:59Z",
        "shop_currency": "USD",
        "currency_exponent": 2,
        "money_basis": "shopMoney",
        "refund_window_days": {"Default": 30},
        "window_start_event": "processedAt",
        "refund_provision_rate": {"Default": 0.05},
        "rounding_mode": "half_up",
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "packaging_cost": 0,
        "structural_zero_shipping_rules": ["no_line_requires_shipping"],
        "zero_fee_gateways": ["manual"],
        "excluded_financial_statuses": []
    }


def make_order_with_p(C_cents: int, target_P_cents: int):
    # Construct order with inflow C and costs resulting in target_P
    cost = C_cents - target_P_cents
    return {
        "id": f"O_{C_cents}_{target_P_cents}",
        "currencyCode": "USD",
        "processedAt": "2026-08-01T12:00:00Z", # Window closed, E=0
        "paymentGatewayNames": ["manual"],
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "0.00",
        "lineItems": [
            {
                "quantity": 1, "requiresShipping": False,
                "originalUnitPriceSet": {"shopMoney": {"amount": str(C_cents / 100)}},
                "variant": {"inventoryItem": {"unitCost": {"amount": str(cost / 100)}}}
            }
        ],
        "transactions": [{"gateway": "manual"}] # G=0
    }


def test_band_boundaries_c20000(base_config):
    engine = F11Engine(base_config)
    C = 20000
    
    # 1. P = 6000 (30.00%) -> high
    r = engine.evaluate_order(make_order_with_p(C, 6000))
    assert r["classification"] == "profitable"
    assert r["band"] == "high"

    # 2. P = 5999 (29.995%) -> acceptable (NOT high even though display rounds to 30.00!)
    r = engine.evaluate_order(make_order_with_p(C, 5999))
    assert r["classification"] == "profitable"
    assert r["band"] == "acceptable"

    # 3. P = 2000 (10.00%) -> acceptable
    r = engine.evaluate_order(make_order_with_p(C, 2000))
    assert r["classification"] == "profitable"
    assert r["band"] == "acceptable"

    # 4. P = 1999 (9.995%) -> at_risk (NOT acceptable even though display rounds to 10.00!)
    r = engine.evaluate_order(make_order_with_p(C, 1999))
    assert r["classification"] == "profitable"
    assert r["band"] == "at_risk"

    # 5. P = 1 (0.005%) -> profitable, at_risk
    r = engine.evaluate_order(make_order_with_p(C, 1))
    assert r["classification"] == "profitable"
    assert r["band"] == "at_risk"

    # 6. P = 0 (0.00%) -> breakeven, at_risk
    r = engine.evaluate_order(make_order_with_p(C, 0))
    assert r["classification"] == "breakeven"
    assert r["band"] == "at_risk"

    # 7. P = -1 (-0.005%) -> unprofitable, cash_drain
    r = engine.evaluate_order(make_order_with_p(C, -1))
    assert r["classification"] == "unprofitable"
    assert r["band"] == "cash_drain"


def test_awkward_denominator_c3333(base_config):
    engine = F11Engine(base_config)
    C = 3333
    
    # P = 1000 (1000 * 100 = 100,000 >= 30 * 3333 = 99,990) -> high
    r = engine.evaluate_order(make_order_with_p(C, 1000))
    assert r["band"] == "high"
    
    # P = 999 (999 * 100 = 99,900 < 99,990) -> acceptable
    r = engine.evaluate_order(make_order_with_p(C, 999))
    assert r["band"] == "acceptable"


def test_zero_revenue_set(base_config):
    engine = F11Engine(base_config)
    
    # C = 0, costs = 2300 -> P = -2300, margin NULL, unprofitable, band zero_revenue
    order = {
        "id": "ZR1", "currencyCode": "USD",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "23.00",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "0.00"}}}],
        "transactions": [{"gateway": "manual"}]
    }
    r = engine.evaluate_order(order)
    assert r["C"] == 0
    assert r["P"] == -2300
    assert r["margin"] is None
    assert r["is_zero_revenue"] is True
    assert r["band"] == "zero_revenue"
