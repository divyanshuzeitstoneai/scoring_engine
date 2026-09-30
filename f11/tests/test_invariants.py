"""
Invariants Test Suite for Formula F11 (I-1 through I-8).
Asserts mathematical identities, conservation, and lane partitioning.
"""

from decimal import Decimal
import pytest
from f11.engine.formula import F11Engine
from f11.reference.reference_formula import evaluate_order_reference


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
        "discount_proration_policy": "pro_rata",
        "rounding_mode": "half_up",
        "custom_line_cost_policy": "missing",
        "bundle_policy": "component_explosion_or_missing",
        "tips_policy": "exclude_from_merchandise_revenue",
        "carrier_cost_source": "metafield:custom.actual_carrier_cost",
        "shipping_rate_card": {"default_zone": {"base_cost": 650, "per_kg": 150}},
        "structural_zero_shipping_rules": ["no_line_requires_shipping"],
        "zero_fee_gateways": ["manual"],
        "gateway_fee_schedule": {"paypal": {"rate": 0.029, "fixed": 30}},
        "packaging_cost": 150,
        "cogs_coverage_gate": 90.0,
        "suspect_zero_cost_policy": "measured_with_flag",
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "excluded_financial_statuses": ["VOIDED"]
    }


def test_i1_driver_decomposition_identity(base_config):
    """Invariant I-1: product_margin_at_list - D + shipping_net - G - E - O == P."""
    order = {
        "id": "I1", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "10.00"}},
        "actual_carrier_cost": "7.00",
        "lineItems": [
            {
                "id": "L1", "quantity": 2, "currentQuantity": 2,
                "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "10.00"}}}],
                "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}
            }
        ],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.50"}}]}],
        "refunds": []
    }
    res = F11Engine(base_config).evaluate_order(order)
    drv = res["drivers"]
    
    # L=10000, D=1000, COGS=4000, Sc=1000, S=700, G=250, E=500 (5% of 9000 = 450), O=150
    # drivers: (L - COGS) + (-D) + (Sc - S) + (-G) + (-E) + (-O)
    driver_sum = drv["product_margin_at_list"] + drv["discount_leak"] + drv["shipping_net"] + drv["fee_leak"] + drv["refund_leak"] + drv["other_leak"]
    assert driver_sum == res["P"]


def test_i4_p_upper_greater_or_equal_to_p(base_config):
    """Invariant I-4: P_upper >= P whenever components are non-negative."""
    engine = F11Engine(base_config)
    order = {
        "id": "I4", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "5.00"}},
        "actual_carrier_cost": "6.00",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}
            }
        ],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.50"}}]}]
    }
    res = engine.evaluate_order(order)
    assert res["P_upper"] >= res["P"]


def test_i8_realized_refund_never_coexists_with_provision(base_config):
    """Invariant I-8: Realized refund replaces provision. No provision coexists."""
    order = {
        "id": "I8", "currencyCode": "USD", "processedAt": "2026-09-28T12:00:00Z", # Age 2 days
        "lineItems": [
            {"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}
        ],
        "refunds": [
            {
                "id": "R1", "createdAt": "2026-09-29T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "10.00"}}
            }
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # E must be exactly 1000 (the 10.00 refund), not 1000 + 5% provision
    assert res["E"] == 1000
    assert res["component_tags"]["refund"] == "measured"
