"""
Section 10: Aggregation Tests.
Verifies:
1. Average-of-margins trap avoided (weighted sum ΣP / ΣC used, never unweighted average).
2. Strict lane separation:
   - MEASURED aggregate
   - ESTIMATED aggregate
   - UNDETERMINED (count, revenue, headroom only; strictly excluded from ΣP)
   - CONFIRMED_LOSS (count, revenue, at-least-lost headroom; strictly excluded from ΣP)
   - Zero blended profit or blended margin field anywhere in schema.
3. Empty set returns margin NULL, counts 0, no exception.
4. Single order matches order-level margin.
5. All-excluded set handled cleanly.
6. Input-order permutation invariance.
7. Segment sums equal parent per lane.
"""

import pytest
import random
from decimal import Decimal
from typing import List, Dict, Any

from f11.engine.pipeline import aggregate_orders, AggregatedLaneResult, PipelineSummary
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
        "gateway_fee_schedule": {"paypal": {"rate": 0.029, "fixed": 30}},
        "packaging_cost": 0,
        "cogs_coverage_gate": 90.0,
        "suspect_zero_cost_policy": "measured_with_flag",
        "band_thresholds": {"high": 30.0, "acceptable": 10.0, "at_risk": 0.0},
        "excluded_financial_statuses": ["VOIDED"],
        "test_order_policy": "exclude"
    }


def test_average_of_margins_trap(base_config):
    """
    Section 10 Trap Test:
    Order 1: C = 10,000, P = 5,000 (margin 50.0%)
    Order 2: C = 1,000, P = -1,000 (margin -100.0%)
    Naive average of margins: (50.0 - 100.0) / 2 = -25.0% (completely misleading!).
    Correct aggregate margin: ΣP / ΣC = (5000 - 1000) / (10000 + 1000) = 4000 / 11000 = 36.3636% (~36.36%).
    """
    order1_res = {
        "order_id": "O1", "C": 10000, "P": 5000, "lane": "MEASURED", "P_upper": 5000,
        "COGS": 4000, "S": 700, "G": 300, "E": 0, "O": 0
    }
    order2_res = {
        "order_id": "O2", "C": 1000, "P": -1000, "lane": "MEASURED", "P_upper": -1000,
        "COGS": 1500, "S": 400, "G": 100, "E": 0, "O": 0
    }
    
    summary = aggregate_orders([order1_res, order2_res])
    measured = summary.lanes["MEASURED"]
    
    assert measured.order_count == 2
    assert measured.total_revenue == 11000
    assert measured.total_profit == 4000
    # True margin: 4000 / 11000 * 100 = 36.3636%
    assert round(float(measured.margin), 2) == 36.36
    # Assert wrong average (-25.0%) is never returned
    assert float(measured.margin) != -25.0


def test_strict_lane_separation(base_config):
    """
    Section 10 Lane Separation Test:
    M1 (MEASURED, C 10,000, P 4,000)
    M2 (MEASURED, C 5,000, P -500)
    E1 (ESTIMATED, C 8,000, P 2,000)
    U1 (UNDETERMINED, C 6,000, headroom 3,000)
    X1 (CONFIRMED_LOSS, C 2,000, P_upper -300)
    
    Expected:
    - MEASURED: ΣP = 3,500, ΣC = 15,000, margin = 23.33%
    - ESTIMATED: ΣP = 2,000, ΣC = 8,000, margin = 25.00%
    - UNDETERMINED: count=1, C=6,000, headroom=3,000, strictly NO ΣP
    - CONFIRMED_LOSS: count=1, C=2,000, at least 300 lost, strictly NO ΣP
    - Output schema contains no blended profit or blended margin field.
    """
    orders = [
        {"order_id": "M1", "C": 10000, "P": 4000, "lane": "MEASURED", "P_upper": 4000, "COGS": 5000, "S": 700, "G": 300, "E": 0, "O": 0},
        {"order_id": "M2", "C": 5000, "P": -500, "lane": "MEASURED", "P_upper": -500, "COGS": 4500, "S": 800, "G": 200, "E": 0, "O": 0},
        {"order_id": "E1", "C": 8000, "P": 2000, "lane": "ESTIMATED", "P_upper": 2500, "COGS": 4000, "S": 650, "G": 320, "E": 1030, "O": 0},
        {"order_id": "U1", "C": 6000, "P": None, "lane": "UNDETERMINED", "P_upper": 3000, "COGS": None, "S": 800, "G": 200, "E": 0, "O": 0},
        {"order_id": "X1", "C": 2000, "P": None, "lane": "CONFIRMED_LOSS", "P_upper": -300, "COGS": None, "S": 2000, "G": 300, "E": 0, "O": 0}
    ]
    
    summary = aggregate_orders(orders)
    summary_dict = summary.to_dict()
    
    # 1. Check MEASURED
    m = summary.lanes["MEASURED"]
    assert m.order_count == 2
    assert m.total_revenue == 15000
    assert m.total_profit == 3500
    assert round(float(m.margin), 2) == 23.33
    
    # 2. Check ESTIMATED
    e = summary.lanes["ESTIMATED"]
    assert e.order_count == 1
    assert e.total_revenue == 8000
    assert e.total_profit == 2000
    assert round(float(e.margin), 2) == 25.00
    
    # 3. Check UNDETERMINED
    u = summary.lanes["UNDETERMINED"]
    assert u.order_count == 1
    assert u.total_revenue == 6000
    assert u.total_profit is None  # Strictly NO ΣP
    assert u.margin is None        # Strictly NO margin
    assert u.headroom == 3000
    
    # 4. Check CONFIRMED_LOSS
    x = summary.lanes["CONFIRMED_LOSS"]
    assert x.order_count == 1
    assert x.total_revenue == 2000
    assert x.total_profit is None  # Strictly NO ΣP
    assert x.margin is None
    assert x.headroom == -300
    
    # 5. Schema invariant: assert NO blended profit or blended margin field
    assert "blended_profit" not in summary_dict
    assert "blended_margin" not in summary_dict
    assert "total_blended_profit" not in summary_dict


def test_empty_set_aggregate():
    """Empty set returns margin NULL, count 0, no exception."""
    summary = aggregate_orders([])
    for lane_name, lane in summary.lanes.items():
        assert lane.order_count == 0
        assert lane.total_revenue == 0
        assert lane.total_profit is None or lane.total_profit == 0
        assert lane.margin is None


def test_single_order_aggregate():
    """Single order aggregate margin equals individual order margin."""
    order = {"order_id": "SO1", "C": 10000, "P": 3500, "lane": "MEASURED", "P_upper": 3500, "COGS": 5000, "S": 1000, "G": 500, "E": 0, "O": 0}
    summary = aggregate_orders([order])
    m = summary.lanes["MEASURED"]
    assert m.order_count == 1
    assert m.total_revenue == 10000
    assert m.total_profit == 3500
    assert float(m.margin) == 35.00


def test_all_excluded_set():
    """All-excluded set: 0 orders evaluated, all captured in excluded summary."""
    orders = [
        {"order_id": f"EX_{i}", "C": 0, "P": 0, "lane": "EXCLUDED", "P_upper": 0, "exclusion_reason": "CANCELLED"}
        for i in range(5)
    ]
    summary = aggregate_orders(orders)
    assert summary.total_orders == 5
    assert summary.active_orders == 0
    assert summary.excluded_orders == 5


def test_input_order_permutation_invariance():
    """Permuting the input order list produces identical aggregate results."""
    orders = [
        {"order_id": f"O_{i}", "C": 1000 * i, "P": 200 * i, "lane": "MEASURED", "P_upper": 200 * i, "COGS": 600 * i, "S": 100 * i, "G": 100 * i, "E": 0, "O": 0}
        for i in range(1, 10)
    ]
    summary1 = aggregate_orders(orders)
    
    permuted = list(orders)
    random.seed(42)
    random.shuffle(permuted)
    summary2 = aggregate_orders(permuted)
    
    assert summary1.lanes["MEASURED"].total_revenue == summary2.lanes["MEASURED"].total_revenue
    assert summary1.lanes["MEASURED"].total_profit == summary2.lanes["MEASURED"].total_profit
    assert summary1.lanes["MEASURED"].margin == summary2.lanes["MEASURED"].margin


def test_segment_sums_equal_parent():
    """Any segmentation sums to the parent per lane."""
    orders_group1 = [
        {"order_id": f"G1_{i}", "C": 5000, "P": 1500, "lane": "MEASURED", "P_upper": 1500, "COGS": 2500, "S": 600, "G": 400, "E": 0, "O": 0}
        for i in range(3)
    ]
    orders_group2 = [
        {"order_id": f"G2_{i}", "C": 8000, "P": 2400, "lane": "MEASURED", "P_upper": 2400, "COGS": 4000, "S": 1000, "G": 600, "E": 0, "O": 0}
        for i in range(4)
    ]
    
    all_orders = orders_group1 + orders_group2
    
    s1 = aggregate_orders(orders_group1)
    s2 = aggregate_orders(orders_group2)
    s_tot = aggregate_orders(all_orders)
    
    m1 = s1.lanes["MEASURED"]
    m2 = s2.lanes["MEASURED"]
    mt = s_tot.lanes["MEASURED"]
    
    assert m1.total_revenue + m2.total_revenue == mt.total_revenue
    assert m1.total_profit + m2.total_profit == mt.total_profit
    assert m1.order_count + m2.order_count == mt.order_count
