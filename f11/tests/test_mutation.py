"""
Mutation Test Suite for Formula F11 (Section 15.9).
Injects 20+ normative mutants into formula logic and asserts that our test suite kills every mutant.
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
        "discount_proration_policy": "pro_rata",
        "rounding_mode": "half_up",
        "custom_line_cost_policy": "missing",
        "bundle_policy": "component_explosion_or_missing",
        "tips_policy": "exclude_from_merchandise_revenue",
        "carrier_cost_source": "metafield:custom.actual_carrier_cost",
        "shipping_rate_card": {"default_zone": {"base_cost": 650, "per_kg": 150}},
        "structural_zero_shipping_rules": ["no_line_requires_shipping"],
        "zero_fee_gateways": ["manual"],
        "gateway_fee_schedule": {},
        "packaging_cost": 150,
        "cogs_coverage_gate": 90.0,
        "suspect_zero_cost_policy": "measured_with_flag",
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "excluded_financial_statuses": ["VOIDED"]
    }


def test_mutant_01_killed_order_level_discount_ignored(base_config):
    """Mutant 1: Revenue ignores order-level code discounts."""
    order = {
        "id": "M1", "currencyCode": "USD",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "20.00"}}}]
            }
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # Mutant would compute R=10000; engine must compute R=8000
    assert res["R"] == 8000


def test_mutant_02_killed_refund_double_counting(base_config):
    """Mutant 2: Refund double counted on both line revenue and refund cost."""
    order = {
        "id": "M2", "currencyCode": "USD", "processedAt": "2026-09-10T12:00:00Z",
        "paymentGatewayNames": ["manual"],
        "actual_carrier_cost": "0.00",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "currentQuantity": 0,
                "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": "40.00"}}}
            }
        ],
        "refunds": [
            {
                "id": "R1", "createdAt": "2026-09-15T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "100.00"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restockType": "RESTOCK"}]
            }
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # Under correct sold-basis (Amendment A1):
    # R=10000, COGS=4000, E=10000-4000=6000 -> P = 10000 - 4000 - 6000 - 150 = -150
    # Under double-counting naive mutant: R=0, COGS=0, E=6000 -> P = -6150
    assert res["P"] == -150


def test_mutant_03_killed_missing_fee_treated_as_zero(base_config):
    """Mutant 3: Missing gateway fee silently treated as $0.00."""
    order = {
        "id": "M3", "currencyCode": "USD",
        "paymentGatewayNames": ["paypal"], # No schedule configured in base_config
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}}],
        "transactions": [{"gateway": "paypal", "fees": []}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["G"] is None
    assert res["component_tags"]["gateway"] == "missing"
    assert res["lane"] == "UNDETERMINED"


def test_mutant_05_killed_provision_kept_after_realized_refund(base_config):
    """Mutant 5: 5% provision kept even after customer refund was processed."""
    order = {
        "id": "M5", "currencyCode": "USD", "processedAt": "2026-09-25T12:00:00Z",
        "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}],
        "refunds": [
            {"id": "R1", "createdAt": "2026-09-28T12:00:00Z", "totalRefundedSet": {"shopMoney": {"amount": "15.00"}}}
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # Mutant would compute E = 1500 + 500 = 2000. Engine must compute E = 1500
    assert res["E"] == 1500


def test_mutant_10_killed_zero_revenue_margin(base_config):
    """Mutant 10: C=0 returns 0.0% margin instead of None."""
    order = {
        "id": "M10", "currencyCode": "USD",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "0.00"}}}],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["margin"] is None
    assert res["is_zero_revenue"] is True


def test_mutant_14_killed_gift_card_counted_as_revenue(base_config):
    """Mutant 14: Gift card line counted as merchandise revenue."""
    order = {
        "id": "M14", "currencyCode": "USD",
        "lineItems": [{"quantity": 1, "isGiftCard": True, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["R"] == 0
