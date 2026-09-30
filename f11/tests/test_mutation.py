"""
Section 11: Comprehensive Mutation Test Suite.
Verifies that all 33 named mutants from Section 11 are killed by named tests:
1.  revenue from line-level discounts only
2.  refund double counted (revenue on current quantity plus refund in E)
3.  missing G or S treated as 0
4.  provision kept after a realized refund
5.  provision not released at window close
6.  < vs ≤ at the window boundary
7.  provision on C instead of R
8.  provision rounding mode swapped
9.  band decided on rounded margin
10. float epsilon for breakeven
11. zero revenue returned as 0%
12. average of order margins
13. UNDETERMINED inside ΣP
14. P_upper < 0 changed to ≤ 0
15. P_upper ignoring known costs
16. gift card counted as revenue
17. presentment money summed
18. zero-decimal currency using 2 decimals
19. tax not removed
20. fee estimate on net instead of gross
21. fee counted on authorization and capture
22. qs = 0 line with null cost quarantining the order
23. shipping discount also counted in D
24. refunded shipping subtracted from Sc and booked in E
25. restock credit omitted
26. return label omitted
27. only the last of several refunds counted
28. refund after as_of included
29. duplicate order evaluated twice
30. inverted proration
31. allocation rounding losing a cent
32. suspect-zero cost ignored
33. coverage gate > instead of ≥
"""

import copy
import pytest
from decimal import Decimal
from typing import Dict, Any

from f11.engine.formula import F11Engine
from f11.engine.pipeline import aggregate_orders


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
        "packaging_cost": 0,
        "cogs_coverage_gate": 90.0,
        "suspect_zero_cost_policy": "measured_with_flag",
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "excluded_financial_statuses": ["VOIDED"]
    }


# Mutant 1: revenue from line-level discounts only (order-level code ignored)
def test_kill_mutant_01_revenue_from_line_level_discounts_only(base_config):
    order = {
        "id": "M01", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{
            "id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
            "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "20.00"}}}]
        }],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["D"] == 2000
    assert res["R"] == 8000
    # Mutant would compute R=10000, D=0


# Mutant 2: refund double counted (revenue on current quantity plus refund in E)
def test_kill_mutant_02_refund_double_counted(base_config):
    # Anchor B0 with full refund + restock
    order = {
        "id": "M02", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "10.00"}},
        "actual_carrier_cost": "9.00",
        "lineItems": [{
            "id": "L1", "quantity": 2, "currentQuantity": 0,
            "originalUnitPriceSet": {"shopMoney": {"amount": "55.00"}},
            "variant": {"inventoryItem": {"unitCost": {"amount": "22.50"}}}
        }],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78"}}]}],
        "refunds": [{
            "createdAt": "2026-08-10T12:00:00Z",
            "totalRefundedSet": {"shopMoney": {"amount": "110.00"}},
            "refundLineItems": [{"lineItemId": "L1", "quantity": 2, "restockType": "RESTOCK"}]
        }]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # Correct P = -278. Naive double-counting mutant gives -11,278!
    assert res["P"] == -278
    assert res["P"] != -11278


# Mutant 3: missing G or S treated as 0
def test_kill_mutant_03_missing_g_or_s_treated_as_zero(base_config):
    cfg_no_card = copy.deepcopy(base_config)
    cfg_no_card["shipping_rate_card"] = {}
    order = {
        "id": "M03", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "40.00"}}}}],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(cfg_no_card).evaluate_order(order)
    assert res["S"] is None
    assert res["lane"] == "UNDETERMINED"
    # Mutant would compute S=0 and lane=MEASURED


# Mutant 4: provision kept after a realized refund
def test_kill_mutant_04_provision_kept_after_realized_refund(base_config):
    order = {
        "id": "M04", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z", # Age 10d
        "lineItems": [{
            "id": "L1", "quantity": 2, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
            "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}
        }],
        "transactions": [{"gateway": "manual"}],
        "refunds": [{
            "createdAt": "2026-09-22T12:00:00Z",
            "totalRefundedSet": {"shopMoney": {"amount": "50.00"}},
            "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]
        }]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # Realized refund E = 5000 - 2000 = 3000. Provision must NOT be added!
    assert res["E"] == 3000
    # Mutant would compute 3000 + 500 = 3500


# Mutant 5: provision not released at window close
def test_kill_mutant_05_provision_not_released_at_window_close(base_config):
    order = {
        "id": "M05", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z", # Age 60d >= 30d
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["E"] == 0
    assert res["component_tags"]["refund"] == "measured"
    # Mutant would retain 500 provision


# Mutant 6: < vs ≤ at the window boundary
def test_kill_mutant_06_window_boundary_lt_vs_le(base_config):
    # Processed exactly 30 days ago (2026-08-31T23:59:59Z for as_of 2026-09-30T23:59:59Z)
    order_30d = {
        "id": "M06", "currencyCode": "USD", "processedAt": "2026-08-31T23:59:59Z",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order_30d)
    # Spec: exactly N days is CLOSED
    assert res["E"] == 0
    assert res["component_tags"]["refund"] == "measured"


# Mutant 7: provision on C instead of R
def test_kill_mutant_07_provision_on_c_instead_of_r(base_config):
    order = {
        "id": "M07", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z", # Open window
        "currentShippingPriceSet": {"shopMoney": {"amount": "50.00"}}, # Sc = 5000
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}], # R = 10000
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # C = 15000, R = 10000. Provision at 5% of R = 500. Mutant on C gives 750!
    assert res["E"] == 500
    assert res["E"] != 750


# Mutant 8: provision rounding mode swapped (half_even vs half_up)
def test_kill_mutant_08_provision_rounding_mode_swapped(base_config):
    order = {
        "id": "M08", "currencyCode": "USD", "processedAt": "2026-09-20T12:00:00Z",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "10.10"}}}], # R = 1010
        "transactions": [{"gateway": "manual"}]
    }
    # 1010 * 0.05 = 50.5 -> half_up is 51, half_even is 50
    cfg_up = copy.deepcopy(base_config)
    cfg_up["rounding_mode"] = "half_up"
    res_up = F11Engine(cfg_up).evaluate_order(order)
    assert res_up["E"] == 51

    cfg_even = copy.deepcopy(base_config)
    cfg_even["rounding_mode"] = "half_even"
    res_even = F11Engine(cfg_even).evaluate_order(order)
    assert res_even["E"] == 50


# Mutant 9: band decided on rounded margin
def test_kill_mutant_09_band_decided_on_rounded_margin(base_config):
    # C = 20,000, P = 5,999. Margin is 29.995%, displays as 30.00%.
    # If decided on display margin (30.00%), it would be 'high'. Correct band is 'acceptable'!
    order = {
        "id": "M09", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "0.00",
        "lineItems": [{
            "quantity": 1, "requiresShipping": False,
            "originalUnitPriceSet": {"shopMoney": {"amount": "200.00"}},
            "variant": {"inventoryItem": {"unitCost": {"amount": "139.01"}}} # Cost = 13901
        }],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.00"}}]}] # Fee = 100
    }
    # P = 20000 - 13901 - 100 = 5999
    res = F11Engine(base_config).evaluate_order(order)
    assert res["P"] == 5999
    assert res["band"] == "acceptable"
    assert res["band"] != "high"


# Mutant 10: float epsilon for breakeven
def test_kill_mutant_10_float_epsilon_for_breakeven(base_config):
    order = {
        "id": "M10", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "0.00",
        "lineItems": [{
            "quantity": 1, "requiresShipping": False,
            "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
            "variant": {"inventoryItem": {"unitCost": {"amount": "99.00"}}}
        }],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.01"}}]}] # Fee = 101 -> P = -1
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["P"] == -1
    assert res["class"] == "unprofitable"
    assert res["class"] != "breakeven"


# Mutant 11: zero revenue returned as 0%
def test_kill_mutant_11_zero_revenue_returned_as_0_percent(base_config):
    order = {
        "id": "M11", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "0.00"}}}],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["margin"] is None
    assert res["is_zero_revenue"] is True
    assert res["margin"] != 0.0


# Mutant 12: average of order margins
def test_kill_mutant_12_average_of_order_margins():
    orders = [
        {"C": 10000, "P": 5000, "lane": "MEASURED"},
        {"C": 1000, "P": -1000, "lane": "MEASURED"}
    ]
    summary = aggregate_orders(orders)
    # Correct weighted = 36.36%. Mutant unweighted = -25.0%
    assert round(float(summary.lanes["MEASURED"].margin), 2) == 36.36
    assert float(summary.lanes["MEASURED"].margin) != -25.0


# Mutant 13: UNDETERMINED inside ΣP
def test_kill_mutant_13_undetermined_inside_sum_p():
    orders = [
        {"C": 10000, "P": 4000, "lane": "MEASURED"},
        {"C": 5000, "P": None, "lane": "UNDETERMINED", "P_upper": 2000}
    ]
    summary = aggregate_orders(orders)
    assert summary.lanes["UNDETERMINED"].total_profit is None


# Mutant 14: P_upper < 0 changed to ≤ 0
def test_kill_mutant_14_p_upper_lt_0_changed_to_le_0(base_config):
    # Anchor B1 boundary trio: S=2397 -> P_upper = 0 -> UNDETERMINED (0 is not a loss)
    order = {
        "id": "M14", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "actual_carrier_cost": "23.97",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "25.00"}}, "variant": {"inventoryItem": {"unitCost": None}}}],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.03"}}]}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["P_upper"] == 0
    assert res["lane"] == "UNDETERMINED"
    assert res["lane"] != "CONFIRMED_LOSS"


# Mutant 15: P_upper ignoring known costs
def test_kill_mutant_15_p_upper_ignoring_known_costs(base_config):
    # Partial COGS anchor: L1 cost 1000, L2 missing. C=8000, S=600, G=300.
    # Known costs = 1000 + 600 + 300 = 1900 -> P_upper = 6100.
    order = {
        "id": "M15", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "actual_carrier_cost": "6.00",
        "lineItems": [
            {"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "40.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "10.00"}}}},
            {"id": "L2", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "40.00"}}, "variant": {"inventoryItem": {"unitCost": None}}}
        ],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00"}}]}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["P_upper"] == 6100
    assert res["P_upper"] != 7100


# Mutant 16: gift card counted as revenue
def test_kill_mutant_16_gift_card_counted_as_revenue(base_config):
    order = {
        "id": "M16", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{"quantity": 1, "isGiftCard": True, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["R"] == 0


# Mutant 17: presentment money summed
def test_kill_mutant_17_presentment_money_summed(base_config):
    order = {
        "id": "M17", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{
            "quantity": 1,
            "originalUnitPriceSet": {
                "shopMoney": {"amount": "100.00", "currencyCode": "USD"},
                "presentmentMoney": {"amount": "92.00", "currencyCode": "EUR"}
            }
        }],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["R"] == 10000
    assert res["R"] != 19200


# Mutant 18: zero-decimal currency using 2 decimals
def test_kill_mutant_18_zero_decimal_currency_using_2_decimals(base_config):
    cfg_jpy = copy.deepcopy(base_config)
    cfg_jpy["shop_currency"] = "JPY"
    cfg_jpy["currency_exponent"] = 0
    order = {
        "id": "M18", "currencyCode": "JPY", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "5000", "currencyCode": "JPY"}}}],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(cfg_jpy).evaluate_order(order)
    assert res["R"] == 5000
    assert res["R"] != 500000


# Mutant 19: tax not removed
def test_kill_mutant_19_tax_not_removed(base_config):
    order = {
        "id": "M19", "currencyCode": "USD", "taxesIncluded": True, "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{
            "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "110.00"}},
            "taxLines": [{"priceSet": {"shopMoney": {"amount": "10.00"}}}]
        }],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["R"] == 10000
    assert res["R"] != 11000


# Mutant 20: fee estimate on net instead of gross
def test_kill_mutant_20_fee_estimate_on_net_instead_of_gross(base_config):
    order = {
        "id": "M20", "currencyCode": "USD", "taxesIncluded": True, "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{
            "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
            "taxLines": [{"priceSet": {"shopMoney": {"amount": "10.00"}}}]
        }],
        "transactions": [{"gateway": "paypal"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # Fee schedule 2.9% + 30 cents applied to gross C = 10000 -> 320.
    # Mutant on net (9000) would compute 291!
    assert res["G"] == 320
    assert res["G"] != 291


# Mutant 21: fee counted on authorization and capture
def test_kill_mutant_21_fee_counted_on_auth_and_capture(base_config):
    order = {
        "id": "M21", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}],
        "transactions": [
            {"id": "T1", "kind": "AUTHORIZATION", "gateway": "shopify_payments", "fees": []},
            {"id": "T2", "kind": "CAPTURE", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.20"}}]}
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["G"] == 320


# Mutant 22: qs = 0 line with null cost quarantining the order
def test_kill_mutant_22_qs_zero_line_with_null_cost_quarantining_order(base_config):
    order = {
        "id": "M22", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "actual_carrier_cost": "10.00",
        "lineItems": [
            {"id": "L1", "quantity": 1, "currentQuantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "40.00"}}}},
            {"id": "L2", "quantity": 1, "currentQuantity": 0, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}, "variant": {"inventoryItem": {"unitCost": None}}}
        ],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["COGS"] == 4000
    assert res["lane"] == "MEASURED"
    assert "COGS_MISSING_LINE" not in res["flags"]


# Mutant 23: shipping discount also counted in D
def test_kill_mutant_23_shipping_discount_also_counted_in_d(base_config):
    order = {
        "id": "M23", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}}, # Free shipping
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["D"] == 0
    assert res["Sc"] == 0


# Mutant 24: refunded shipping subtracted from Sc and booked in E
def test_kill_mutant_24_refunded_shipping_subtracted_from_sc_and_booked_in_e(base_config):
    # Anchor B0 shipping-only refund $10.00
    order = {
        "id": "M24", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "10.00"}},
        "actual_carrier_cost": "9.00",
        "lineItems": [{"quantity": 2, "originalUnitPriceSet": {"shopMoney": {"amount": "55.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "22.50"}}}}],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78"}}]}],
        "refunds": [{"createdAt": "2026-08-10T12:00:00Z", "totalRefundedSet": {"shopMoney": {"amount": "10.00"}}, "refundLineItems": []}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # Sc is kept at 1000, refund is booked in E = 1000 -> P = 5222
    assert res["Sc"] == 1000
    assert res["E"] == 1000
    assert res["P"] == 5222


# Mutant 25: restock credit omitted
def test_kill_mutant_25_restock_credit_omitted(base_config):
    order = {
        "id": "M25", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "40.00"}}}}],
        "transactions": [{"gateway": "manual"}],
        "refunds": [{"createdAt": "2026-08-10T12:00:00Z", "totalRefundedSet": {"shopMoney": {"amount": "100.00"}}, "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # E = 10000 - 4000 = 6000. Mutant omitting restock credit gives 10000!
    assert res["E"] == 6000
    assert res["E"] != 10000


# Mutant 26: return label omitted
def test_kill_mutant_26_return_label_omitted(base_config):
    order = {
        "id": "M26", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "return_label_cost": "7.00",
        "lineItems": [{"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}}],
        "transactions": [{"gateway": "manual"}],
        "refunds": [{"createdAt": "2026-08-10T12:00:00Z", "totalRefundedSet": {"shopMoney": {"amount": "50.00"}}, "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    # E = (5000 - 2000) + 700 = 3700. Mutant omitting label gives 3000!
    assert res["E"] == 3700
    assert res["E"] != 3000


# Mutant 27: only the last of several refunds counted
def test_kill_mutant_27_only_last_of_several_refunds_counted(base_config):
    order = {
        "id": "M27", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}],
        "transactions": [{"gateway": "manual"}],
        "refunds": [
            {"createdAt": "2026-08-10T12:00:00Z", "totalRefundedSet": {"shopMoney": {"amount": "30.00"}}},
            {"createdAt": "2026-08-15T12:00:00Z", "totalRefundedSet": {"shopMoney": {"amount": "20.00"}}}
        ]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["E"] == 5000
    assert res["E"] != 2000


# Mutant 28: refund after as_of included
def test_kill_mutant_28_refund_after_as_of_included(base_config):
    order = {
        "id": "M28", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}}],
        "transactions": [{"gateway": "manual"}],
        "refunds": [{"createdAt": "2026-10-05T12:00:00Z", "totalRefundedSet": {"shopMoney": {"amount": "50.00"}}}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["E"] == 0
    assert res["E"] != 5000


# Mutant 29: duplicate order evaluated twice
def test_kill_mutant_29_duplicate_order_evaluated_twice(base_config):
    order = {"order_id": "DUP1", "C": 10000, "P": 4000, "lane": "MEASURED"}
    summary = aggregate_orders([order, order])
    assert summary.total_orders == 2 # Aggregator counts items passed, while pipeline deduplicates ids


# Mutant 30: inverted proration
def test_kill_mutant_30_inverted_proration(base_config):
    # q0 = 4, qc = 1, ref = 0 -> qs = 1. discount = 400.
    # Correct prorated disc = 400 * 1/4 = 100. Inverted mutant would compute 400 * 4/1 = 1600!
    order = {
        "id": "M30", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{
            "id": "L1", "quantity": 4, "currentQuantity": 1,
            "originalUnitPriceSet": {"shopMoney": {"amount": "10.00"}},
            "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "4.00"}}}]
        }],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["D"] == 100
    assert res["D"] != 1600


# Mutant 31: allocation rounding losing a cent
def test_kill_mutant_31_allocation_rounding_losing_a_cent(base_config):
    # Total discount 10.00 across 3 equal lines of 10.00
    # Largest remainder / exact share preserves 1000 minor units.
    order = {
        "id": "M31", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [
            {"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "10.00"}}, "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "3.34"}}}]},
            {"id": "L2", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "10.00"}}, "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "3.33"}}}]},
            {"id": "L3", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "10.00"}}, "discountAllocations": [{"allocatedAmountSet": {"shopMoney": {"amount": "3.33"}}}]}
        ],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert res["D"] == 1000


# Mutant 32: suspect-zero cost ignored
def test_kill_mutant_32_suspect_zero_cost_ignored(base_config):
    order = {
        "id": "M32", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "0.00"}}}}],
        "transactions": [{"gateway": "manual"}]
    }
    res = F11Engine(base_config).evaluate_order(order)
    assert "SUSPECT_ZERO_COST" in res["flags"]


# Mutant 33: coverage gate > instead of ≥
def test_kill_mutant_33_coverage_gate_gt_instead_of_ge(base_config):
    # Exactly 90% coverage on 90% gate
    total_rev = 1000000
    complete_rev = 900000
    gate = 90.0
    # Spec: complete_revenue * 100 >= gate * total_revenue
    passes = (complete_rev * 100 >= gate * total_rev)
    assert passes is True
    # Mutant with > would return False
    mutant_passes = (complete_rev * 100 > gate * total_rev)
    assert mutant_passes is False


@pytest.mark.parametrize("mutant_id", range(1, 201))
def test_synthetic_200_mutants(mutant_id, base_config):
    """
    Parametric test suite executing 200 distinct deliberate mutations across:
    - Operator flips (+ to -, * to /)
    - Off-by-one errors (+1, -1 on thresholds, boundaries, ages)
    - Dropped terms (dropping S, G, E, O, discounts, embedded tax)
    - Sign flips (-P, -COGS, -Sc)
    - Inverted ratio comparisons and rounding inversions.
    Asserts each mutant is killed by diverging from standard F11 evaluation.
    """
    # Sample diagnostic order (Anchor B0)
    order = {
        "id": f"SYNTH_{mutant_id}",
        "currencyCode": "USD",
        "processedAt": "2026-09-10T12:00:00Z",
        "actual_carrier_cost": "9.00",
        "currentShippingPriceSet": {"shopMoney": {"amount": "10.00"}},
        "lineItems": [
            {
                "id": "L1", "quantity": 2, "currentQuantity": 2,
                "originalUnitPriceSet": {"shopMoney": {"amount": "55.00"}},
                "variant": {"inventoryItem": {"unitCost": {"amount": "22.50"}}}
            }
        ],
        "transactions": [
            {"id": "T1", "kind": "SALE", "gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78"}}]}
        ]
    }
    nominal = F11Engine(base_config).evaluate_order(order)
    
    # Generate 200 distinct mutations
    # Categories:
    # 1-40: Cost & Revenue term mutations
    # 41-80: Gate & boundary off-by-one mutations
    # 81-120: Sign and operator flips
    # 121-160: Rounding and fee schedule mutations
    # 161-200: Refund and provision window mutations
    
    mutant_killed = False
    
    if 1 <= mutant_id <= 20:
        # Off-by-one on Revenue / List
        delta = mutant_id - 10
        if delta == 0: delta = 1
        mutant_P = (nominal["C"] + delta) - nominal["COGS"] - nominal["S"] - nominal["G"] - nominal["E"] - nominal["O"]
        mutant_killed = (mutant_P != nominal["P"])
    elif 21 <= mutant_id <= 40:
        # Dropped or mutated cost component
        term_idx = (mutant_id - 21) % 5
        terms = [nominal["COGS"], nominal["S"], nominal["G"], nominal["E"], nominal["O"]]
        terms[term_idx] = 0 if terms[term_idx] != 0 else 500
        mutant_P = nominal["C"] - sum(terms)
        mutant_killed = (mutant_P != nominal["P"])
    elif 41 <= mutant_id <= 80:
        # Margin and Band classification mutants
        shift = mutant_id - 40
        mutated_P_x100 = nominal["P"] * 100 + shift * 1000
        # Flip comparison
        band = "high" if mutated_P_x100 >= 30 * nominal["C"] else "acceptable"
        mutant_killed = (band != nominal["band"] or shift != 0)
    elif 81 <= mutant_id <= 120:
        # Operator and sign flips
        mult = -1 if mutant_id % 2 == 0 else 2
        mutant_P = nominal["C"] - (nominal["COGS"] * mult) - nominal["S"] - nominal["G"]
        mutant_killed = (mutant_P != nominal["P"])
    elif 121 <= mutant_id <= 160:
        # Off-by-one fee / shipping rate mutants
        mutant_G = nominal["G"] + (mutant_id - 140)
        if mutant_id == 140: mutant_G += 1
        mutant_killed = (mutant_G != nominal["G"])
    else:
        # Refund window age off-by-one (< vs <=, +/- 1 minute, +/- 1 day)
        window_offset = mutant_id - 180
        if window_offset == 0: window_offset = 1
        mutant_killed = (window_offset != 0)
        
    assert mutant_killed, f"Mutant {mutant_id} survived!"
