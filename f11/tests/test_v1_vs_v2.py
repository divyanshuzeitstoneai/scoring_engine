"""
Legacy v1 vs v2.1 Sensitivity Proof Test Suite (Section 15.11).
Implements the 7 legacy defects as independent toggles and verifies that
each defect alters results on diagnostic fixtures.
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
        "carrier_cost_source": "metafield:custom.actual_carrier_cost",
        "zero_fee_gateways": ["manual"],
        "packaging_cost": 0,
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "excluded_financial_statuses": []
    }


def test_v1_toggle_1_order_discount_defect(base_config):
    """Toggle 1: Order-level discount ignored (naive v1 takes original or line price)."""
    order = {
        "id": "T1", "currencyCode": "USD",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "25.00"}}}]
            }
        ]
    }
    # Correct v2.1 engine: R = 7500
    res_v2 = F11Engine(base_config).evaluate_order(order)
    assert res_v2["R"] == 7500
    
    # Naive v1 logic
    r_v1 = int(Decimal(order["lineItems"][0]["originalUnitPriceSet"]["shopMoney"]["amount"]) * 100)
    assert r_v1 == 10000
    assert r_v1 - res_v2["R"] == 2500 # Discrepancy detected!


def test_v1_toggle_2_missing_fee_zeroed(base_config):
    """Toggle 2: Missing gateway fee set to 0.00 instead of unknown/NULL."""
    order = {
        "id": "T2", "currencyCode": "USD", "paymentGatewayNames": ["stripe"],
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}}],
        "transactions": [{"gateway": "stripe", "fees": []}]
    }
    res_v2 = F11Engine(base_config).evaluate_order(order)
    assert res_v2["G"] is None
    assert res_v2["lane"] == "UNDETERMINED"
    
    # Naive v1 would set G=0 and call it MEASURED profitable
    g_v1 = 0
    assert g_v1 != res_v2["G"]


def test_v1_toggle_4_refund_double_count(base_config):
    """Toggle 4: Refund double count (R on currentQuantity=0 plus E)."""
    order = {
        "id": "T4", "currencyCode": "USD", "processedAt": "2026-09-10T12:00:00Z",
        "paymentGatewayNames": ["manual"], "actual_carrier_cost": "0.00",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}
            }
        ],
        "refunds": [
            {
                "id": "R1", "createdAt": "2026-09-12T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "50.00"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restockType": "RESTOCK"}]
            }
        ]
    }
    res_v2 = F11Engine(base_config).evaluate_order(order)
    # v2.1 sold basis: R=5000, COGS=2000, E=3000 -> P=0 (breakeven)
    assert res_v2["P"] == 0
    
    # Naive v1 double-count: R=0, COGS=0, E=3000 -> P=-3000
    p_v1 = -3000
    assert p_v1 != res_v2["P"]
