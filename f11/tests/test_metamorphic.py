"""
Section 11: Metamorphic Testing Suite (MR-1 through MR-10).
Verifies 10 core metamorphic relations over randomized orders:
MR-1: Translation linearity: +δ on cost terms lowers P by exactly δ; +δ on Sc raises P by δ.
MR-2: Integer money scaling: k * amounts scales P and components by k (closed window).
MR-3: Line permutation invariance: reordering lines changes nothing.
MR-4: Line split invariance: splitting a line into two equal halves preserves P in open & closed windows.
MR-5: Null-operation invariance: adding qs=0 line or gift card line changes nothing.
MR-6: Refund additivity: sequential refunds equal combined refund.
MR-7: Idempotency & determinism: same inputs, config, as_of -> byte-identical output.
MR-8: Temporal monotonicity: as_of before any refund gives no-refund result.
MR-9: Provision decay: provision never rises with order age, drops to 0 at boundary.
MR-10: Config locality: profile change moves only the values it owns.
"""

import copy
import pytest
from decimal import Decimal
from typing import Dict, Any

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
        "packaging_cost": 0,
        "cogs_coverage_gate": 90.0,
        "suspect_zero_cost_policy": "measured_with_flag",
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "excluded_financial_statuses": ["VOIDED"]
    }


def make_anchor_order(proc_date="2026-08-01T12:00:00Z", price="55.00", qty=2, cost="22.50", ship="10.00", carrier="9.00", fee="3.78"):
    return {
        "id": "gid://shopify/Order/MR", "name": "#MR", "currencyCode": "USD", "processedAt": proc_date,
        "currentShippingPriceSet": {"shopMoney": {"amount": ship, "currencyCode": "USD"}},
        "actual_carrier_cost": carrier,
        "lineItems": [{
            "id": "L1", "quantity": qty, "currentQuantity": qty,
            "originalUnitPriceSet": {"shopMoney": {"amount": price, "currencyCode": "USD"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": cost, "currencyCode": "USD"}}}
        }],
        "transactions": [{"id": "T1", "gateway": "shopify_payments", "fees": [{"amount": {"amount": fee, "currencyCode": "USD"}}]}],
        "refunds": []
    }


def test_mr1_translation_linearity(base_config):
    """MR-1: Raising costs by δ lowers P by δ; raising Sc raises P by δ; raising discount lowers P by δ."""
    engine = F11Engine(base_config)
    base_order = make_anchor_order()
    r0 = engine.evaluate_order(base_order)
    p0 = r0["P"]
    
    # 1. Raise carrier cost by $1.00 (100 minor units)
    o_s = copy.deepcopy(base_order)
    o_s["actual_carrier_cost"] = "10.00"
    r_s = engine.evaluate_order(o_s)
    assert r_s["P"] == p0 - 100
    
    # 2. Raise shipping charged by $1.00
    o_sc = copy.deepcopy(base_order)
    o_sc["currentShippingPriceSet"]["shopMoney"]["amount"] = "11.00"
    r_sc = engine.evaluate_order(o_sc)
    assert r_sc["P"] == p0 + 100
    
    # 3. Raise unit cost by $0.50 per unit (2 units -> 100 minor units)
    o_cogs = copy.deepcopy(base_order)
    o_cogs["lineItems"][0]["variant"]["inventoryItem"]["unitCost"]["amount"] = "23.00"
    r_cogs = engine.evaluate_order(o_cogs)
    assert r_cogs["P"] == p0 - 100
    
    # 4. Add $1.00 discount
    o_d = copy.deepcopy(base_order)
    o_d["lineItems"][0]["discountAllocations"] = [{"allocatedAmountSet": {"shopMoney": {"amount": "1.00", "currencyCode": "USD"}}}]
    r_d = engine.evaluate_order(o_d)
    assert r_d["P"] == p0 - 100


def test_mr2_integer_money_scaling(base_config):
    """MR-2: Scaling all money amounts by integer k scales P and every component by k (closed window)."""
    engine = F11Engine(base_config)
    base_order = make_anchor_order(proc_date="2026-08-01T12:00:00Z", price="50.00", qty=1, cost="20.00", ship="10.00", carrier="8.00", fee="3.00")
    r0 = engine.evaluate_order(base_order)
    
    k = 3
    scaled_order = make_anchor_order(proc_date="2026-08-01T12:00:00Z", price=f"{50.0*k:.2f}", qty=1, cost=f"{20.0*k:.2f}", ship=f"{10.0*k:.2f}", carrier=f"{8.0*k:.2f}", fee=f"{3.0*k:.2f}")
    rk = engine.evaluate_order(scaled_order)
    
    assert rk["L"] == r0["L"] * k
    assert rk["R"] == r0["R"] * k
    assert rk["Sc"] == r0["Sc"] * k
    assert rk["C"] == r0["C"] * k
    assert rk["COGS"] == r0["COGS"] * k
    assert rk["S"] == r0["S"] * k
    assert rk["G"] == r0["G"] * k
    assert rk["P"] == r0["P"] * k


def test_mr3_line_permutation_invariance(base_config):
    """MR-3: Permuting line items changes nothing."""
    engine = F11Engine(base_config)
    order1 = {
        "id": "O1", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "5.00",
        "lineItems": [
            {"id": "L1", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "30.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "12.00"}}}},
            {"id": "L2", "quantity": 2, "originalUnitPriceSet": {"shopMoney": {"amount": "40.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "15.00"}}}},
            {"id": "L3", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "10.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "3.00"}}}}
        ],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.00"}}]}]
    }
    order2 = copy.deepcopy(order1)
    order2["lineItems"] = [order1["lineItems"][2], order1["lineItems"][0], order1["lineItems"][1]]
    
    r1 = engine.evaluate_order(order1)
    r2 = engine.evaluate_order(order2)
    
    assert r1["L"] == r2["L"]
    assert r1["R"] == r2["R"]
    assert r1["COGS"] == r2["COGS"]
    assert r1["P"] == r2["P"]
    assert r1["margin"] == r2["margin"]


def test_mr4_line_split_invariance(base_config):
    """
    MR-4: Splitting a line into two equal lines changes nothing, in both open and closed windows.
    (Tests that provision rounded once per rate group preserves split invariance).
    """
    engine = F11Engine(base_config)
    
    # 1. Closed window
    closed_single = {
        "id": "CS", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "5.00",
        "lineItems": [{"id": "L1", "quantity": 2, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}}],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "2.00"}}]}]
    }
    closed_split = copy.deepcopy(closed_single)
    closed_split["lineItems"] = [
        {"id": "L1a", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}},
        {"id": "L1b", "quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "20.00"}}}}
    ]
    r_cs = engine.evaluate_order(closed_single)
    r_csp = engine.evaluate_order(closed_split)
    assert r_cs["P"] == r_csp["P"]
    
    # 2. Open window (crucial test for Pitfall 4: provision rounded once per group)
    open_single = copy.deepcopy(closed_single)
    open_single["processedAt"] = "2026-09-20T12:00:00Z"
    open_split = copy.deepcopy(closed_split)
    open_split["processedAt"] = "2026-09-20T12:00:00Z"
    
    r_os = engine.evaluate_order(open_single)
    r_osp = engine.evaluate_order(open_split)
    assert r_os["E"] == r_osp["E"], f"Provision broke split invariance: {r_os['E']} != {r_osp['E']}"
    assert r_os["P"] == r_osp["P"]


def test_mr5_null_operation_invariance(base_config):
    """MR-5: Adding a qs = 0 line, or a gift card line, changes nothing."""
    engine = F11Engine(base_config)
    base_order = make_anchor_order()
    r0 = engine.evaluate_order(base_order)
    
    # Add qs = 0 line
    o_qs0 = copy.deepcopy(base_order)
    o_qs0["lineItems"].append({
        "id": "L_ZERO", "quantity": 1, "currentQuantity": 0,
        "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}},
        "variant": {"inventoryItem": {"unitCost": {"amount": "50.00"}}}
    })
    r_qs0 = engine.evaluate_order(o_qs0)
    assert r_qs0["P"] == r0["P"]
    assert r_qs0["COGS"] == r0["COGS"]
    assert r_qs0["R"] == r0["R"]
    
    # Add gift card line
    o_gc = copy.deepcopy(base_order)
    o_gc["lineItems"].append({
        "id": "L_GC", "quantity": 1, "currentQuantity": 1, "isGiftCard": True,
        "originalUnitPriceSet": {"shopMoney": {"amount": "50.00"}},
        "variant": {"inventoryItem": {"unitCost": {"amount": "0.00"}}}
    })
    r_gc = engine.evaluate_order(o_gc)
    assert r_gc["P"] == r0["P"]
    assert r_gc["COGS"] == r0["COGS"]


def test_mr6_refund_additivity(base_config):
    """MR-6: Two sequential refunds equal one combined refund (restock credit counted once)."""
    engine = F11Engine(base_config)
    # Order with 2 units refunded sequentially (unit 1 restocked, unit 2 restocked)
    order_seq = {
        "id": "SEQ", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "0.00"}},
        "actual_carrier_cost": "9.00",
        "lineItems": [{
            "id": "L1", "quantity": 2, "currentQuantity": 0,
            "originalUnitPriceSet": {"shopMoney": {"amount": "55.00"}},
            "variant": {"id": "V1", "inventoryItem": {"unitCost": {"amount": "22.50"}}}
        }],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.78"}}]}],
        "refunds": [
            {"id": "R1", "createdAt": "2026-08-10T12:00:00Z", "totalRefundedSet": {"shopMoney": {"amount": "55.00"}}, "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]},
            {"id": "R2", "createdAt": "2026-08-15T12:00:00Z", "totalRefundedSet": {"shopMoney": {"amount": "55.00"}}, "refundLineItems": [{"lineItemId": "L1", "quantity": 1, "restocked": True}]}
        ]
    }
    
    order_comb = copy.deepcopy(order_seq)
    order_comb["refunds"] = [{
        "id": "R_COMB", "createdAt": "2026-08-15T12:00:00Z",
        "totalRefundedSet": {"shopMoney": {"amount": "110.00"}},
        "refundLineItems": [{"lineItemId": "L1", "quantity": 2, "restocked": True}]
    }]
    
    r_seq = engine.evaluate_order(order_seq)
    r_comb = engine.evaluate_order(order_comb)
    
    assert r_seq["E"] == r_comb["E"]
    assert r_seq["P"] == r_comb["P"]


def test_mr7_determinism(base_config):
    """MR-7: Same inputs, config and as_of give byte-identical output."""
    engine1 = F11Engine(base_config)
    engine2 = F11Engine(base_config)
    order = make_anchor_order()
    
    r1 = engine1.evaluate_order(order)
    r2 = engine2.evaluate_order(order)
    assert r1 == r2


def test_mr8_temporal_monotonicity(base_config):
    """MR-8: as_of before every refund gives the no-refund result."""
    base_order = make_anchor_order(proc_date="2026-08-01T12:00:00Z")
    order_with_refund = copy.deepcopy(base_order)
    order_with_refund["refunds"] = [{
        "id": "R1", "createdAt": "2026-09-15T12:00:00Z",
        "totalRefundedSet": {"shopMoney": {"amount": "55.00"}},
        "refundLineItems": []
    }]
    
    # Configure as_of to be before the refund (e.g. 2026-09-01)
    cfg_early = copy.deepcopy(base_config)
    cfg_early["as_of"] = "2026-09-01T23:59:59Z"
    
    r_no_ref = F11Engine(cfg_early).evaluate_order(base_order)
    r_early = F11Engine(cfg_early).evaluate_order(order_with_refund)
    
    assert r_early["E"] == r_no_ref["E"]
    assert r_early["P"] == r_no_ref["P"]


def test_mr9_provision_decay_with_age(base_config):
    """MR-9: Provision never rises with age; it is 0 from the window boundary onward."""
    engine = F11Engine(base_config)
    
    # Day 5 (open)
    o5 = make_anchor_order(proc_date="2026-09-25T23:59:59Z")
    r5 = engine.evaluate_order(o5)
    
    # Day 25 (open)
    o25 = make_anchor_order(proc_date="2026-09-05T23:59:59Z")
    r25 = engine.evaluate_order(o25)
    
    # Day 30 exactly (boundary: closed)
    o30 = make_anchor_order(proc_date="2026-08-31T23:59:59Z")
    r30 = engine.evaluate_order(o30)
    
    # Day 60 (closed)
    o60 = make_anchor_order(proc_date="2026-08-01T23:59:59Z")
    r60 = engine.evaluate_order(o60)
    
    assert r5["E"] == 550
    assert r25["E"] == 550
    assert r30["E"] == 0
    assert r60["E"] == 0
    assert r5["E"] >= r25["E"] >= r30["E"] == r60["E"]


def test_mr10_config_locality(base_config):
    """MR-10: A config profile change moves only the values it owns."""
    engine_base = F11Engine(base_config)
    
    # Change carrier rate card
    cfg_ship = copy.deepcopy(base_config)
    cfg_ship["shipping_rate_card"]["default_zone"]["base_cost"] = 800
    engine_ship = F11Engine(cfg_ship)
    
    order = {
        "id": "O_SHIP", "currencyCode": "USD", "processedAt": "2026-08-01T12:00:00Z",
        "currentShippingPriceSet": {"shopMoney": {"amount": "10.00"}},
        # carrier cost missing -> estimated via rate card
        "lineItems": [{"quantity": 1, "originalUnitPriceSet": {"shopMoney": {"amount": "100.00"}}, "variant": {"inventoryItem": {"unitCost": {"amount": "40.00"}}}}],
        "transactions": [{"gateway": "shopify_payments", "fees": [{"amount": {"amount": "3.00"}}]}]
    }
    
    r_base = engine_base.evaluate_order(order)
    r_ship = engine_ship.evaluate_order(order)
    
    # S changed from 650 to 800
    assert r_base["S"] == 650
    assert r_ship["S"] == 800
    # COGS, G, R, Sc, L MUST REMAIN IDENTICAL
    assert r_base["L"] == r_ship["L"]
    assert r_base["R"] == r_ship["R"]
    assert r_base["Sc"] == r_ship["Sc"]
    assert r_base["COGS"] == r_ship["COGS"]
    assert r_base["G"] == r_ship["G"]
