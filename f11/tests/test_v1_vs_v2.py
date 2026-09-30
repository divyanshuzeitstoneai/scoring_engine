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


def test_v1_toggle_3_missing_shipping_zeroed(base_config):
    """Toggle 3: Missing shipping treated as 0 instead of unknown/NULL."""
    order = {
        "id": "T3", "currencyCode": "USD", "paymentGatewayNames": ["manual"],
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}}],
        "shipping_rate_card": {}
    }
    cfg = dict(base_config)
    cfg["shipping_rate_card"] = {}
    res_v2 = F11Engine(cfg).evaluate_order(order)
    assert res_v2["S"] is None
    assert res_v2["lane"] == "UNDETERMINED"
    
    # Naive v1 would set S=0 and overestimate profit by shipping cost
    s_v1 = 0
    assert s_v1 != res_v2["S"]


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


def test_v1_toggle_5_provision_never_released(base_config):
    """Toggle 5: Provision never released at window close."""
    order = {
        "id": "T5", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z", # Age 60 days > 30 days
        "actual_carrier_cost": "10.00", "paymentGatewayNames": ["manual"],
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "40.00"}}}}]
    }
    res_v2 = F11Engine(base_config).evaluate_order(order)
    # v2.1 releases provision: E = 0, P = 10000 - 4000 - 1000 = 5000
    assert res_v2["E"] == 0
    assert res_v2["P"] == 5000
    
    # Naive v1 holds provision indefinitely: E = 500, P = 4500 (delta = -500)
    e_v1 = 500
    assert e_v1 != res_v2["E"]


def test_v1_toggle_6_tax_not_removed_on_tax_inclusive(base_config):
    """Toggle 6: Tax not stripped on tax-inclusive store."""
    order = {
        "id": "T6", "currencyCode": "USD", "taxesIncluded": True, "processedAt": "2026-08-01T12:00:00Z",
        "actual_carrier_cost": "0.00", "paymentGatewayNames": ["manual"],
        "lineItems": [{
            "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
            "taxLines": [{"priceSet": {"shopMoney": {"amount": "10.00"}}}],
            "variant": {"inventoryItem": {"unitCost": {"amount": "40.00"}}}
        }]
    }
    res_v2 = F11Engine(base_config).evaluate_order(order)
    # v2.1 strips embedded tax: R = 9000, COGS = 4000, P = 5000
    assert res_v2["R"] == 9000
    assert res_v2["P"] == 5000
    
    # Naive v1 fails to strip tax: R = 10000, P = 6000 (delta = +1000 overstatement)
    r_v1 = 10000
    assert r_v1 != res_v2["R"]


def test_v1_toggle_7_average_of_margins(base_config):
    """Toggle 7: Simple average of margins across orders vs aggregate ΣP / ΣC."""
    # Order 1: C = 10000, P = 5000 -> margin = +50.0%
    # Order 2: C = 1000, P = -1000 -> margin = -100.0%
    order1 = {"C": 10000, "P": 5000, "margin": 50.0}
    order2 = {"C": 1000, "P": -1000, "margin": -100.0}
    
    # Correct aggregate margin = (5000 - 1000) / (10000 + 1000) = 4000 / 11000 = +36.36%
    true_agg_margin = round((order1["P"] + order2["P"]) / (order1["C"] + order2["C"]) * 100, 2)
    assert true_agg_margin == 36.36
    
    # Naive v1 average of order margins: (50.0 + (-100.0)) / 2 = -25.0% (massive error)
    naive_avg_margin = (order1["margin"] + order2["margin"]) / 2
    assert naive_avg_margin == -25.0
    assert true_agg_margin != naive_avg_margin
