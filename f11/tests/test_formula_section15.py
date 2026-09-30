"""
Normative In-Depth Formula Unit & Regression Test Suite for Section 15.
Tests all hand-computed numeric fixtures for FT-R, FT-C, FT-S, FT-G, FT-E, FT-O, B0, B1, Doc-2.
Asserts full output row: exact integer minor units, lanes, bands, drivers, top loss driver.
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
        "shipping_rate_card": {
            "default_zone": {"base_cost": 650, "per_kg": 150}
        },
        "structural_zero_shipping_rules": ["no_line_requires_shipping", "local_pickup"],
        "zero_fee_gateways": ["manual", "cash_on_delivery", "bank_deposit"],
        "gateway_fee_schedule": {
            "paypal": {"rate": 0.029, "fixed": 30}
        },
        "gateway_fee_refund_treatment": "retain_fixed_fee",
        "packaging_cost": 150,
        "cogs_coverage_gate": 90.0,
        "suspect_zero_cost_policy": "measured_with_flag",
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "excluded_financial_statuses": ["VOIDED", "PENDING", "AUTHORIZED"],
        "cancelled_after_fulfillment_policy": "include_with_refunds",
        "test_order_policy": "exclude"
    }


# =============================================================================
# 1. REFERENCE CASES: B0, B1, DOC-2
# =============================================================================

def test_case_b0_prior_spec_example_a(base_config):
    """Case B0: u=55.00, qs=2, cost=22.50, Sc=10.00, G=3.78, S=9.00, window open."""
    order = {
        "id": "gid://shopify/Order/B0",
        "name": "#B0",
        "currencyCode": "USD",
        "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "9.00",
        "lineItems": [
            {
                "id": "gid://shopify/LineItem/B0_1",
                "quantity": 2,
                "currentQuantity": 2,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00", "currencyCode": "USD"}},
                "discountAllocations": [],
                "variant": {
                    "id": "gid://shopify/ProductVariant/B0_V1",
                    "inventoryItem": {"unitCost": {"amount": "22.50", "currencyCode": "USD"}}
                }
            }
        ],
        "transactions": [
            {
                "id": "gid://shopify/OrderTransaction/B0_TX",
                "gateway": "shopify_payments",
                "fees": [{"amount": {"amount": "3.78", "currencyCode": "USD"}}]
            }
        ],
        "refunds": []
    }
    
    engine = F11Engine(base_config)
    res = engine.evaluate_order(order)
    ref = evaluate_order_reference(order, base_config)
    
    assert res["R"] == 11000
    assert res["Sc"] == 1000
    assert res["C"] == 12000
    assert res["COGS"] == 4500
    assert res["S"] == 900
    assert res["G"] == 378
    assert res["E"] == 550
    assert res["O"] == 150
    assert res["P"] == 5522
    assert res["lane"] == "ESTIMATED"
    assert res["band"] == "high"
    assert res["classification"] == "profitable"
    
    # Assert engine equals reference
    assert res["P"] == ref.P
    assert res["lane"] == ref.lane


def test_case_b1_prior_spec_example_b_cash_drain(base_config):
    """Case B1: Item 30.00, disc 5.00, free ship Sc=0, S=8.50, G=1.03, COGS=18.00."""
    order = {
        "id": "gid://shopify/Order/B1",
        "name": "#B1",
        "currencyCode": "USD",
        "processedAt": "2026-09-20T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00", "currencyCode": "USD"}},
        "actual_carrier_cost": "8.50",
        "lineItems": [
            {
                "id": "gid://shopify/LineItem/B1_1",
                "quantity": 1,
                "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "30.00", "currencyCode": "USD"}},
                "discountAllocations": [
                    {"allocatedAmountSet": {"shopMoney": {"amount": "5.00", "currencyCode": "USD"}}}
                ],
                "variant": {
                    "id": "gid://shopify/ProductVariant/B1_V1",
                    "inventoryItem": {"unitCost": {"amount": "18.00", "currencyCode": "USD"}}
                }
            }
        ],
        "transactions": [
            {
                "id": "gid://shopify/OrderTransaction/B1_TX",
                "gateway": "shopify_payments",
                "fees": [{"amount": {"amount": "1.03", "currencyCode": "USD"}}]
            }
        ],
        "refunds": []
    }
    
    engine = F11Engine(base_config)
    res = engine.evaluate_order(order)
    
    assert res["R"] == 2500
    assert res["Sc"] == 0
    assert res["C"] == 2500
    assert res["COGS"] == 1800
    assert res["S"] == 850
    assert res["G"] == 103
    assert res["E"] == 125
    assert res["O"] == 150
    assert res["P"] == -528
    assert res["lane"] == "CONFIRMED_LOSS"
    assert res["band"] == "cash_drain"
    assert res["classification"] == "unprofitable"
    assert res["top_loss_driver"] == "shipping_subsidy"


# =============================================================================
# 2. REVENUE & DISCOUNTS (FT-R: R01 to R15)
# =============================================================================

def test_ft_r01_gross_no_discount(base_config):
    order = {
        "id": "R01", "currencyCode": "USD",
        "lineItems": [{"quantity": 2, "currentQuantity": 2, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["L"] == 10000
    assert res["R"] == 10000
    assert res["D"] == 0


def test_ft_r03_order_level_code_discount(base_config):
    order = {
        "id": "R03", "currencyCode": "USD",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "30.00"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "6.00"}}}]
            },
            {
                "id": "L2", "quantity": 1, "currentQuantity": 1,
                "originalUnitPriceSet": {"shopMoney": {"amount": "70.00"}},
                "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "14.00"}}}]
            }
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["L"] == 10000
    assert res["D"] == 2000
    assert res["R"] == 8000


def test_ft_r10_gift_card_line_excluded(base_config):
    order = {
        "id": "R10", "currencyCode": "USD",
        "lineItems": [
            {"id": "GC", "quantity": 1, "isGiftCard": True, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}},
            {"id": "IT", "quantity": 1, "isGiftCard": False, "originalUnitPriceSet": {"shopMoney": {"amount": "30.00"}}}
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["R"] == 3000
    assert res["L"] == 3000


def test_ft_r11_free_gift_line(base_config):
    order = {
        "id": "R11", "currencyCode": "USD",
        "lineItems": [
            {
                "id": "FG", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "0.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": "5.00"}}}
            }
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["R"] == 0
    assert res["COGS"] == 500


def test_ft_r15_jpy_zero_decimal_currency(base_config):
    cfg = dict(base_config)
    cfg["shop_currency"] = "JPY"
    cfg["currency_exponent"] = 0
    order = {
        "id": "R15", "currencyCode": "JPY", "processedAt": "2026-09-20T12:00:00Z",
        "lineItems": [{"quantity": 1, "currentQuantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "1005"}}}]
    }
    res = F11Engine(cfg).evaluate_order(order)
    assert res["R"] == 1005
    assert res["E"] == 50 # 5% of 1005 = 50.25 -> 50 integer minor units


# =============================================================================
# 3. COGS & MISSING SOURCING (FT-C: C01 to C10)
# =============================================================================

def test_ft_c02_missing_cogs_headroom_undetermined(base_config):
    order = {
        "id": "C02", "currencyCode": "USD",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "6.00",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "80.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": None}}}
            }
        ],
        "transactions": [
            {"gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00"}}]}
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["COGS"] is None
    assert res["lane"] == "UNDETERMINED"
    assert res["P_upper"] == 8000 - 600 - 300 - 150 # C - S - G - O = 6950


def test_ft_c04_suspect_zero_cost_flag(base_config):
    order = {
        "id": "C04", "currencyCode": "USD",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "40.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": "0.00"}}}
            }
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert "SUSPECT_ZERO_COST" in res["flags"]
    assert res["COGS"] == 0


def test_ft_c07_confirmed_loss_when_upper_negative(base_config):
    """C07: Missing COGS but measured shipping and fees already exceed revenue."""
    order = {
        "id": "C07", "currencyCode": "USD",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "30.00",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "20.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": None}}}
            }
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["P_upper"] < 0
    assert res["lane"] == "CONFIRMED_LOSS"


# =============================================================================
# 4. SHIPPING & LOGISTICS (FT-S: S01 to S08)
# =============================================================================

def test_ft_s04_all_digital_structural_zero_shipping(base_config):
    order = {
        "id": "S04", "currencyCode": "USD",
        "lineItems": [
            {"id": "D1", "quantity": 1, "requiresShipping": False, "originalUnitPriceSet": {"shopMoney": {"amount": "25.00"}}}
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["S"] == 0
    assert res["component_tags"]["shipping"] == "structural"


# =============================================================================
# 5. GATEWAY FEES (FT-G: G01 to G11)
# =============================================================================

def test_ft_g03_paypal_fee_schedule_estimation(base_config):
    order = {
        "id": "G03", "currencyCode": "USD",
        "paymentGatewayNames": ["paypal"],
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "120.00"}}}],
        "transactions": [{"gateway": "paypal", "fees": []}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # 2.9% of 12000 = 348 + 30 = 378
    assert res["G"] == 378
    assert res["component_tags"]["gateway"] == "estimated"


def test_ft_g06_cod_manual_structural_zero_fee(base_config):
    order = {
        "id": "G06", "currencyCode": "USD",
        "paymentGatewayNames": ["cash_on_delivery"],
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["G"] == 0
    assert res["component_tags"]["gateway"] == "structural"


# =============================================================================
# 6. REFUNDS, RETURNS & PROVISIONS (FT-E: E01 to E20)
# =============================================================================

def test_ft_e02_window_closed_zero_provision_measured(base_config):
    order = {
        "id": "E02", "currencyCode": "USD",
        "processedAt": "2026-08-01T12:00:00Z", # Age > 30 days
        "actual_carrier_cost": "6.00",
        "lineItems": [
            {
                "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}
            }
        ],
        "transactions": [
            {"gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.50"}}]}
        ],
        "refunds": []
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["E"] == 0
    assert res["lane"] == "MEASURED"


def test_ft_e03_full_refund_with_restock_recovery(base_config):
    order = {
        "id": "E03", "currencyCode": "USD",
        "processedAt": "2026-09-10T12:00:00Z",
        "actual_carrier_cost": "9.00",
        "currentShippingPriceSet": {"shopMoney": {"amount": "10.00"}},
        "lineItems": [
            {
                "id": "L1", "quantity": 2, "originalUnitPriceSet": {"shopMoney": {"amount": "55.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": "22.50"}}}
            }
        ],
        "transactions": [
            {"gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78"}}]}
        ],
        "refunds": [
            {
                "id": "R1", "createdAt": "2026-09-15T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "110.00"}},
                "refundLineItems": [{"lineItemId": "L1", "quantity": 2, "restockType": "RESTOCK"}]
            }
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # E = 11000 - 4500 = 6500
    # P = 12000 - 4500 - 900 - 378 - 6500 - 150 = -428
    assert res["E"] == 6500
    assert res["P"] == -428
    assert res["lane"] == "MEASURED"
    assert res["classification"] == "unprofitable"


def test_ft_e14_realized_refund_replaces_provision_invariant(base_config):
    order = {
        "id": "E14", "currencyCode": "USD",
        "processedAt": "2026-09-25T12:00:00Z", # Age < 30 days
        "lineItems": [
            {"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}
        ],
        "refunds": [
            {
                "id": "R1", "createdAt": "2026-09-28T12:00:00Z",
                "totalRefundedSet": {"shopMoney": {"amount": "20.00"}}
            }
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["E"] == 2000 # Exactly the realized refund, no 5% provision!
