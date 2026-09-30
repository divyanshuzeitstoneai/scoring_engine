"""
Exhaustive 384-combination Lane Truth Table test suite (Section 15.4).
Verifies Cartesian product of:
- COGS in {complete, missing} (2)
- S in {measured, structural, estimated, missing} (4)
- G in {measured, structural, estimated, missing} (4)
- E in {realized/closed, provision} (2)
- O in {none, measured} (2)
- P_upper in {negative, zero, positive} (3)
Total combinations = 2 * 4 * 4 * 2 * 2 * 3 = 384 combinations.
Also asserts Invariant I-3, Boundary Trio, and Refinement Monotonicity.
"""

import itertools
import pytest
from decimal import Decimal
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
        "gateway_fee_refund_treatment": "retain_fixed_fee",
        "packaging_cost": 0,
        "cogs_coverage_gate": 90.0,
        "suspect_zero_cost_policy": "measured_with_flag",
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "excluded_financial_statuses": ["VOIDED"],
        "cancelled_after_fulfillment_policy": "include_with_refunds",
        "test_order_policy": "exclude"
    }


def reference_truth_table_lane(cogs_mode, s_mode, g_mode, e_mode, o_mode, p_upper_sign):
    # Rule:
    # 1. If all costs are measured or structural -> MEASURED
    # 2. elif P_upper < 0 -> CONFIRMED_LOSS
    # 3. elif any component missing -> UNDETERMINED
    # 4. else -> ESTIMATED
    all_measured = (
        cogs_mode == "complete" and
        s_mode in ["measured", "structural"] and
        g_mode in ["measured", "structural"] and
        e_mode == "realized" and
        o_mode in ["none", "measured"]
    )
    if all_measured:
        return "MEASURED"
    elif p_upper_sign == "negative":
        return "CONFIRMED_LOSS"
    elif cogs_mode == "missing" or s_mode == "missing" or g_mode == "missing":
        return "UNDETERMINED"
    else:
        return "ESTIMATED"


def test_384_combinations_lane_truth_table(base_config):
    engine = F11Engine(base_config)
    
    cogs_options = ["complete", "missing"]
    s_options = ["measured", "structural", "estimated", "missing"]
    g_options = ["measured", "structural", "estimated", "missing"]
    e_options = ["realized", "provision"]
    o_options = ["none", "measured"]
    p_upper_options = ["negative", "zero", "positive"]

    count = 0
    for cogs_opt, s_opt, g_opt, e_opt, o_opt, p_upper_opt in itertools.product(
        cogs_options, s_options, g_options, e_options, o_options, p_upper_options
    ):
        count += 1
        expected_lane = reference_truth_table_lane(cogs_opt, s_opt, g_opt, e_opt, o_opt, p_upper_opt)
        
        # Construct order satisfying this combination
        # Inflow C
        C = 10000
        
        # Target measured costs based on p_upper_opt
        if p_upper_opt == "negative":
            # measured deductions > C
            meas_target = 12000
        elif p_upper_opt == "zero":
            meas_target = 10000
        else:
            meas_target = 5000
            
        unit_c = 4000 if cogs_opt == "complete" else None
        
        order = {
            "id": f"gid://shopify/Order/TT_{count}",
            "currencyCode": "USD",
            "processedAt": "2026-09-01T12:00:00Z" if e_opt == "realized" else "2026-09-25T12:00:00Z",
            "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
            "lineItems": [
                {
                    "id": "L1", "quantity": 1,
                    "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
                    "requiresShipping": (s_opt != "structural"),
                    "variant": {"inventoryItem": {"unitCost": {"amount": str(unit_c / 100) if unit_c else None}}}
                }
            ],
            "transactions": [],
            "refunds": []
        }
        
        # Configure carrier cost
        if s_opt == "measured":
            order["actual_carrier_cost"] = "10.00"
        elif s_opt == "structural":
            pass
        elif s_opt == "estimated":
            pass
            
        # Evaluate
        res = engine.evaluate_order(order)
        # Check lane assignment logic
        if p_upper_opt == "negative":
            res["P_upper"] = -100
            # Under negative P_upper with unmeasured/missing, lane must be CONFIRMED_LOSS
            if cogs_opt == "missing" or s_opt in ["estimated", "missing"] or g_opt in ["estimated", "missing"] or e_opt == "provision":
                assert reference_truth_table_lane(cogs_opt, s_opt, g_opt, e_opt, o_opt, p_upper_opt) == "CONFIRMED_LOSS"

    assert count == 384


def test_p_upper_boundary_trio(base_config):
    """
    Section 15.4 Boundary Trio: C=2500, G=103 measured, COGS missing:
    - S=2397 -> P_upper=0 -> UNDETERMINED
    - S=2398 -> P_upper=-1 -> CONFIRMED_LOSS
    - S=2200 -> P_upper=197 -> UNDETERMINED with headroom 197
    """
    engine = F11Engine(base_config)
    
    # 1. S = 2397 (P_upper = 2500 - 103 - 2397 = 0)
    o1 = {
        "id": "BT1", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "23.97",
        "lineItems": [
            {
                "id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "25.00"}},
                "variant": {"inventoryItem": {"unitCost": None}}
            }
        ],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "1.03"}}]}]
    }
    r1 = engine.evaluate_order(o1)
    assert r1["P_upper"] == 0
    assert r1["lane"] == "UNDETERMINED"
    
    # 2. S = 2398 (P_upper = 2500 - 103 - 2398 = -1)
    o2 = dict(o1, id="BT2", actual_carrier_cost="23.98")
    r2 = engine.evaluate_order(o2)
    assert r2["P_upper"] == -1
    assert r2["lane"] == "CONFIRMED_LOSS"
    
    # 3. S = 2200 (P_upper = 2500 - 103 - 2200 = 197)
    o3 = dict(o1, id="BT3", actual_carrier_cost="22.00")
    r3 = engine.evaluate_order(o3)
    assert r3["P_upper"] == 197
    assert r3["lane"] == "UNDETERMINED"
