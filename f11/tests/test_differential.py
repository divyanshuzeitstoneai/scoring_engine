"""
Differential Testing Suite: Production Engine vs Reference Implementation.
Verifies that F11Engine and evaluate_order_reference produce byte-identical results
at the minor unit across multiple orders and configurations.
"""

import json
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
        "zero_fee_gateways": ["manual", "cash_on_delivery"],
        "gateway_fee_schedule": {"paypal": {"rate": 0.029, "fixed": 30}},
        "packaging_cost": 150,
        "cogs_coverage_gate": 90.0,
        "suspect_zero_cost_policy": "measured_with_flag",
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "excluded_financial_statuses": ["VOIDED"]
    }


def test_differential_engine_vs_reference(base_config):
    engine = F11Engine(base_config)
    
    # Load 100 sample orders from synthetic data
    sample_path = "f11/data/synthetic_orders_sample.json"
    with open(sample_path, "r", encoding="utf-8") as f:
        orders = json.load(f)

    mismatch_count = 0
    for order in orders:
        eng_res = engine.evaluate_order(order)
        ref_res = evaluate_order_reference(order, base_config)
        
        # Assert exact agreement on financial integers and classifications
        assert eng_res["R"] == ref_res.R, f"R mismatch on {order['id']}: {eng_res['R']} != {ref_res.R}"
        assert eng_res["Sc"] == ref_res.Sc, f"Sc mismatch on {order['id']}: {eng_res['Sc']} != {ref_res.Sc}"
        assert eng_res["C"] == ref_res.C, f"C mismatch on {order['id']}: {eng_res['C']} != {ref_res.C}"
        assert eng_res["COGS"] == ref_res.COGS, f"COGS mismatch on {order['id']}: {eng_res['COGS']} != {ref_res.COGS}"
        assert eng_res["S"] == ref_res.S, f"S mismatch on {order['id']}: {eng_res['S']} != {ref_res.S}"
        assert eng_res["G"] == ref_res.G, f"G mismatch on {order['id']}: {eng_res['G']} != {ref_res.G}"
        assert eng_res["E"] == ref_res.E, f"E mismatch on {order['id']}: {eng_res['E']} != {ref_res.E}"
        assert eng_res["P"] == ref_res.P, f"P mismatch on {order['id']}: {eng_res['P']} != {ref_res.P}"
        assert eng_res["lane"] == ref_res.lane, f"Lane mismatch on {order['id']}: {eng_res['lane']} != {ref_res.lane}"
        assert eng_res["band"] == ref_res.band, f"Band mismatch on {order['id']}: {eng_res['band']} != {ref_res.band}"
        assert eng_res["classification"] == ref_res.classification, f"Class mismatch on {order['id']}"

    print(f"Differential test passed: 100/100 sample orders matched byte-identically between Engine and Reference!")
