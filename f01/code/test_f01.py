"""
Automated Test Suite for Formula F01: Promotional Margin Leakage.
Validates TC-01 through TC-32 unit tests covering:
- Basic healthy and leaking discounted orders
- Shopify discount separation (line, cart, stacked, codes)
- Same SKU across multiple discount scenarios
- Multi-SKU cart discount allocations
- Pricing edge cases (free gifts, zero price, null/corrupted price)
- Multi-unit quantities
- 4-Tier COGS waterfall & input sanity guards
- Target margin hierarchy (metafield, product_margin, taxonomy, product type, storewide default)
- Boundary margin conditions
- Refund and cancellation lifecycle
- Arithmetic reproducibility and double-counting prevention
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from core.fallbacks.cogs import resolve_cogs
from core.fallbacks.margin import resolve_target_margin
from core.historical_index import HistoricalCogsIndex
from formulas.f01_discount_leakage.cohort import is_order_discounted
from formulas.f01_discount_leakage.formula import evaluate_line_item, evaluate_order
from formulas.f01_discount_leakage.runner import run_f01_pipeline
from formulas.f01_discount_leakage.score import calculate_f01_score

class TestCaseResult:
    def __init__(
        self,
        test_id: str,
        case_name: str,
        input_data: str,
        formula_steps: str,
        expected_output: str,
        actual_output: str,
        passed: bool
    ):
        self.test_id = test_id
        self.case_name = case_name
        self.input_data = input_data
        self.formula_steps = formula_steps
        self.expected_output = expected_output
        self.actual_output = actual_output
        self.passed = passed

def run_f01_unit_tests() -> List[TestCaseResult]:
    results: List[TestCaseResult] = []

    # =========================================================================
    # SECTION A: BASIC DISCOUNT CASES
    # =========================================================================

    # TC-01: Healthy discounted order
    ord_01 = {
        "id": 9000000001, "name": "#9000000001", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "10.00",
        "line_items": [{
            "id": 1, "variant_id": 101, "product_id": 201, "sku": "SKU-BASIC-01",
            "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00",
            "discount_allocations": [{"amount": "10.00", "code": "SAVE10", "discount_application_index": 0}]
        }],
        "_variants": [{"id": 101, "product_id": 201, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}]
    }
    cat_01 = {"product_type": "Apparel", "category": "Apparel & Accessories > Clothing", "true_cogs": 30.0, "original_price": 100.0}
    eval_01 = evaluate_order(ord_01, catalog_by_variant_id={101: cat_01})
    # Steps: MSRP=$100, Net=$90, COGS=$30. Target Margin=52% -> Target Profit=$52. Actual Profit=$90-$30=$60. Actual > Target.
    p_01 = (eval_01.f01_flagged is False and eval_01.f01_dollar_loss == 0.0 and eval_01.actual_gross_profit == 60.0 and eval_01.target_minimum_profit == 52.0)
    results.append(TestCaseResult(
        "TC-01", "Healthy discounted order (Actual profit > Target profit)",
        "MSRP=$100.00, Net Price=$90.00, COGS=$30.00, Target Margin=52%",
        "Target Profit=$100*0.52=$52.00; Actual Profit=$90-$30=$60.00; 60.00 >= 52.00",
        "flagged=False, Loss=$0.00, Actual Profit=$60.00",
        f"flagged={eval_01.f01_flagged}, Loss=${eval_01.f01_dollar_loss:.2f}, Actual Profit=${eval_01.actual_gross_profit:.2f}",
        p_01
    ))

    # TC-02: Leaking discounted order
    ord_02 = {
        "id": 9000000002, "name": "#9000000002", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "40.00",
        "line_items": [{
            "id": 2, "variant_id": 102, "product_id": 202, "sku": "SKU-BASIC-02",
            "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00",
            "discount_allocations": [{"amount": "40.00", "code": "FLASH40", "discount_application_index": 0}]
        }],
        "_variants": [{"id": 102, "product_id": 202, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}]
    }
    eval_02 = evaluate_order(ord_02, catalog_by_variant_id={102: cat_01})
    # Steps: MSRP=$100, Net=$60, COGS=$30. Target Margin=52% -> Target Profit=$52. Actual Profit=$60-$30=$30. Leakage=$52-$30=$22.
    p_02 = (eval_02.f01_flagged is True and abs(eval_02.f01_dollar_loss - 22.0) < 0.01 and eval_02.actual_gross_profit == 30.0)
    results.append(TestCaseResult(
        "TC-02", "Leaking discounted order (Actual profit < Target profit)",
        "MSRP=$100.00, Net Price=$60.00, COGS=$30.00, Target Margin=52%",
        "Target Profit=$52.00; Actual Profit=$60-$30=$30.00; Leakage=$52-$30=$22.00",
        "flagged=True, Loss=$22.00, Actual Profit=$30.00",
        f"flagged={eval_02.f01_flagged}, Loss=${eval_02.f01_dollar_loss:.2f}, Actual Profit=${eval_02.actual_gross_profit:.2f}",
        p_02
    ))

    # TC-03: Zero-discount order exclusion
    ord_03 = {
        "id": 9000000003, "name": "#9000000003", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "0.00",
        "line_items": [{"id": 3, "variant_id": 103, "product_id": 203, "sku": "SKU-NODISC-03", "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00"}],
        "_variants": [{"id": 103, "product_id": 203, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}]
    }
    eval_03 = evaluate_order(ord_03)
    p_03 = (eval_03.status == "excluded" and eval_03.exclusion_reason == "non_discounted")
    results.append(TestCaseResult(
        "TC-03", "Zero-discount order excluded from cohort",
        "total_discounts=0.00, compare_at=price=$100.00",
        "Order has no promotional discount; excluded under F01 cohort rules",
        "status=excluded, reason=non_discounted",
        f"status={eval_03.status}, reason={eval_03.exclusion_reason}",
        p_03
    ))

    # TC-04: Compare-at markdown detection
    ord_04 = {
        "id": 9000000004, "name": "#9000000004", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "0.00",
        "line_items": [{"id": 4, "variant_id": 104, "product_id": 204, "sku": "SKU-COMPARE-04", "price": "75.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00"}],
        "_variants": [{"id": 104, "product_id": 204, "price": "75.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}]
    }
    is_d_04 = is_order_discounted(ord_04)
    eval_04 = evaluate_order(ord_04)
    p_04 = (is_d_04 is True and eval_04.status == "evaluated" and eval_04.line_items[0].discount_type == "product_markdown")
    results.append(TestCaseResult(
        "TC-04", "Compare-at markdown with total_discounts=0",
        "compare_at=$100.00, price=$75.00, total_discounts=0",
        "compare_at > price qualifies as product markdown discount",
        "is_discounted=True, status=evaluated, discount_type=product_markdown",
        f"is_discounted={is_d_04}, status={eval_04.status}, discount_type={eval_04.line_items[0].discount_type if eval_04.line_items else None}",
        p_04
    ))

    # =========================================================================
    # SECTION B: COGS WATERFALL & SANITY GUARDS
    # =========================================================================

    # TC-05: Missing COGS: Historical lookup (Tier 2 COGS)
    hist = HistoricalCogsIndex()
    t_hist = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    t_ord = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
    hist.history[105] = [(t_hist.timestamp(), 42.50)]
    c_05, s_05, e_05, q_05, _ = resolve_cogs(raw_cost=None, original_price=100.0, unit_price=80.0, variant_id=105, order_created_at=t_ord, historical_lookup_fn=hist.lookup)
    p_05 = (s_05 == "historical" and abs(c_05 - 42.50) < 0.01 and e_05 is True and not q_05)
    results.append(TestCaseResult(
        "TC-05", "Missing COGS: 90-day Historical lookup (Tier 2 COGS)",
        "raw_cost=None, historical cost=$42.50 within 90 days",
        "Resolve cost from 90-day historical index",
        "source=historical, cost=42.50, is_estimated=True",
        f"source={s_05}, cost={c_05:.2f}, is_estimated={e_05}",
        p_05
    ))

    # TC-06: Missing COGS: Category target margin imputation (Tier 3 COGS)
    c_06, s_06, e_06, _, _ = resolve_cogs(raw_cost=None, original_price=100.0, unit_price=80.0, category_target_margin=0.62, is_category_margin_configured=True)
    p_06 = (s_06 == "category_estimate" and abs(c_06 - 38.00) < 0.01 and e_06 is True)
    results.append(TestCaseResult(
        "TC-06", "Missing COGS: Category imputation (Tier 3 COGS)",
        "raw_cost=None, original_price=100.0, Category Margin=0.62",
        "Imputed COGS = $100 * (1 - 0.62) = $38.00",
        "source=category_estimate, cost=38.00",
        f"source={s_06}, cost={c_06:.2f}",
        p_06
    ))

    # TC-07: Missing COGS: Storewide fallback (Tier 4 COGS)
    c_07, s_07, e_07, _, _ = resolve_cogs(raw_cost=None, original_price=100.0, unit_price=80.0, category_target_margin=0.35, is_category_margin_configured=False)
    p_07 = (s_07 == "storewide_default" and abs(c_07 - 65.00) < 0.01 and e_07 is True)
    results.append(TestCaseResult(
        "TC-07", "Missing COGS: Storewide fallback (Tier 4 COGS)",
        "raw_cost=None, Uncategorized SKU, Storewide Default=0.35",
        "Imputed COGS = $100 * (1 - 0.35) = $65.00",
        "source=storewide_default, cost=65.00",
        f"source={s_07}, cost={c_07:.2f}",
        p_07
    ))

    # TC-08: Missing COGS: Unresolved at all tiers -> Quarantine
    c_08, s_08, _, q_08, _ = resolve_cogs(raw_cost=None, original_price=0.0, unit_price=0.0, force_unresolved=True)
    ord_08 = {
        "id": 9000000008, "name": "#9000000008", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "5.00",
        "line_items": [{"id": 8, "variant_id": None, "price": "0.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00"}]
    }
    eval_08 = evaluate_order(ord_08, force_unresolved_cogs=True)
    p_08 = (s_08 == "unresolved" and q_08 is True and eval_08.status == "quarantined")
    results.append(TestCaseResult(
        "TC-08", "Missing COGS: Unresolved at all tiers -> Quarantined",
        "raw_cost=None, price=0.00, force_unresolved=True",
        "Unable to resolve COGS at any tier; route order to quarantine",
        "source=unresolved, status=quarantined",
        f"source={s_08}, status={eval_08.status}",
        p_08
    ))

    # TC-09: Corrupted COGS Input Sanity Guard (cost > price)
    _, s_09, _, q_09, r_09 = resolve_cogs(raw_cost=150.0, original_price=100.0, unit_price=90.0)
    p_09 = (q_09 is True and s_09 == "unresolved" and "sanity_guard_cost_exceeds_price" in str(r_09))
    results.append(TestCaseResult(
        "TC-09", "Corrupted COGS Sanity Guard: cost exceeds price",
        "cost=$150.00 on benchmark price=$100.00",
        "Sanity guard rejects implausible cost exceeding price; routes to quarantine",
        "quarantined=True, reason=sanity_guard_cost_exceeds_price",
        f"quarantined={q_09}, reason={r_09}",
        p_09
    ))

    # TC-10: Corrupted COGS Sanity Guard: negative cost
    _, s_10, _, q_10, r_10 = resolve_cogs(raw_cost=-25.0, original_price=100.0, unit_price=90.0)
    p_10 = (q_10 is True and s_10 == "unresolved" and "sanity_guard_negative_cost" in str(r_10))
    results.append(TestCaseResult(
        "TC-10", "Corrupted COGS Sanity Guard: negative cost",
        "cost=-$25.00 on price=$100.00",
        "Sanity guard rejects negative cost; routes to quarantine",
        "quarantined=True, reason=sanity_guard_negative_cost",
        f"quarantined={q_10}, reason={r_10}",
        p_10
    ))

    # TC-11: Corrupted COGS Sanity Guard: zero cost on non-free item
    _, s_11, _, q_11, r_11 = resolve_cogs(raw_cost=0.0, original_price=100.0, unit_price=90.0, is_free_gift=False)
    p_11 = (q_11 is True and s_11 == "unresolved" and "sanity_guard_zero_cost_non_free_item" in str(r_11))
    results.append(TestCaseResult(
        "TC-11", "Corrupted COGS Sanity Guard: zero cost on non-free item",
        "cost=$0.00 on non-free item ($100.00 MSRP)",
        "Sanity guard flags $0 cost as corrupted for standard catalog product",
        "quarantined=True, reason=sanity_guard_zero_cost_non_free_item",
        f"quarantined={q_11}, reason={r_11}",
        p_11
    ))

    # =========================================================================
    # SECTION C: TARGET MARGIN HIERARCHY
    # =========================================================================

    # TC-12: Unconfigured category margin -> 35% storewide default
    m_12, s_12, e_12 = resolve_target_margin(metafields=[], category_name=None, product_type=None)
    p_12 = (abs(m_12 - 0.35) < 0.001 and s_12 == "storewide_default" and e_12 is True)
    results.append(TestCaseResult(
        "TC-12", "Target Margin: Unconfigured category -> 35% storewide default",
        "metafields=[], category=None, product_type=None",
        "No explicit config found; cascade to configured business default of 35%",
        "margin=0.35, source=storewide_default",
        f"margin={m_12:.2f}, source={s_12}",
        p_12
    ))

    # TC-13: SKU Metafield override (Tier 1 Target Margin)
    meta_13 = [{"namespace": "custom", "key": "target_margin", "value": "0.58"}]
    m_13, s_13, e_13 = resolve_target_margin(metafields=meta_13, category_name="Apparel & Accessories > Clothing")
    p_13 = (abs(m_13 - 0.58) < 0.001 and s_13 == "metafield" and e_13 is False)
    results.append(TestCaseResult(
        "TC-13", "Target Margin: SKU Metafield override (Tier 1)",
        "custom.target_margin='0.58', category='Apparel & Accessories > Clothing' (52%)",
        "Metafield has highest priority; overrides category table (0.58 vs 0.52)",
        "margin=0.58, source=metafield",
        f"margin={m_13:.2f}, source={s_13}",
        p_13
    ))

    # =========================================================================
    # SECTION D: BOUNDARY & SCORING CASES
    # =========================================================================

    # TC-14: Zero discounted orders safe fallback
    sc_14, b_14, t_14, _ = calculate_f01_score([])
    p_14 = (sc_14 == 100.0 and b_14 == "Healthy" and t_14 == 0.0)
    results.append(TestCaseResult(
        "TC-14", "Scoring: Zero discounted orders in batch safe fallback",
        "0 evaluated discounted orders",
        "Zero-safe division check: returns 100.0% score",
        "score=100.00%, band=Healthy",
        f"score={sc_14:.2f}%, band={b_14}",
        p_14
    ))

    # TC-15: Exact tie Actual == Target
    ord_15 = {
        "id": 9000000015, "name": "#9000000015", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "20.00",
        "line_items": [{"id": 15, "variant_id": 115, "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00", "discount_allocations": [{"amount": "20.00", "code": "TIE20"}]}],
        "_variants": [{"id": 115, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}]
    }
    cat_15 = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 30.0, "original_price": 100.0}
    eval_15 = evaluate_order(ord_15, catalog_by_variant_id={115: cat_15})
    # Target Profit=$100*0.50=$50. Actual Profit=$80-$30=$50. Exact tie -> not flagged.
    p_15 = (eval_15.actual_gross_profit == eval_15.target_minimum_profit and eval_15.f01_flagged is False and eval_15.f01_dollar_loss == 0.0)
    results.append(TestCaseResult(
        "TC-15", "Boundary: Exact tie Actual Profit == Target Profit",
        "Target Profit=$50.00, Actual Profit=$50.00",
        "Strict inequality check: Actual < Target is False; flagged=False",
        "flagged=False, Loss=$0.00",
        f"flagged={eval_15.f01_flagged}, Loss=${eval_15.f01_dollar_loss:.2f}",
        p_15
    ))

    # TC-16: Boundary: Slightly above target margin
    ord_16 = {
        "id": 9000000016, "name": "#9000000016", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "19.99",
        "line_items": [{"id": 16, "variant_id": 116, "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00", "discount_allocations": [{"amount": "19.99"}]}],
        "_variants": [{"id": 116, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}]
    }
    eval_16 = evaluate_order(ord_16, catalog_by_variant_id={116: cat_15})
    p_16 = (eval_16.actual_gross_profit > eval_16.target_minimum_profit and eval_16.f01_flagged is False)
    results.append(TestCaseResult(
        "TC-16", "Boundary: Slightly above target margin",
        "Net Price=$80.01, COGS=$30.00 -> Actual=$50.01 vs Target=$50.00",
        "Actual > Target: not flagged, $0 loss",
        "flagged=False, Loss=$0.00",
        f"flagged={eval_16.f01_flagged}, Loss=${eval_16.f01_dollar_loss:.2f}",
        p_16
    ))

    # TC-17: Boundary: Slightly below target margin
    ord_17 = {
        "id": 9000000017, "name": "#9000000017", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "20.01",
        "line_items": [{"id": 17, "variant_id": 117, "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00", "discount_allocations": [{"amount": "20.01"}]}],
        "_variants": [{"id": 117, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}]
    }
    eval_17 = evaluate_order(ord_17, catalog_by_variant_id={117: cat_15})
    p_17 = (eval_17.actual_gross_profit < eval_17.target_minimum_profit and eval_17.f01_flagged is True and abs(eval_17.f01_dollar_loss - 0.01) < 0.005)
    results.append(TestCaseResult(
        "TC-17", "Boundary: Slightly below target margin",
        "Net Price=$79.99, COGS=$30.00 -> Actual=$49.99 vs Target=$50.00",
        "Actual < Target: flagged=True, Loss=$0.01",
        "flagged=True, Loss=$0.01",
        f"flagged={eval_17.f01_flagged}, Loss=${eval_17.f01_dollar_loss:.2f}",
        p_17
    ))

    # TC-18: Negative gross profit preservation (Actual profit < 0 preserved)
    ord_18 = {
        "id": 9000000018, "name": "#9000000018", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "80.00",
        "line_items": [{"id": 18, "variant_id": 118, "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00", "discount_allocations": [{"amount": "80.00"}]}],
        "_variants": [{"id": 118, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "50.00"}}]
    }
    cat_18 = {"product_type": "Home Goods", "metafield_margin": 0.40, "true_cogs": 50.0, "original_price": 100.0}
    eval_18 = evaluate_order(ord_18, catalog_by_variant_id={118: cat_18})
    p_18 = (eval_18.actual_gross_profit == -30.0 and eval_18.negative_gross_profit is True and eval_18.f01_dollar_loss == 70.0)
    results.append(TestCaseResult(
        "TC-18", "Financial integrity: Negative gross profit preserved without flooring",
        "MSRP=$100, Net=$20, COGS=$50, Target Margin=40%",
        "Actual Profit=$20-$50=-$30.00; Target=$40.00; Loss=$40-(-$30)=$70.00",
        "actual_profit=-$30.00, negative_gross_profit=True, Loss=$70.00",
        f"actual_profit=${eval_18.actual_gross_profit:.2f}, negative_gross_profit={eval_18.negative_gross_profit}, Loss=${eval_18.f01_dollar_loss:.2f}",
        p_18
    ))

    # =========================================================================
    # SECTION E: ORDER LIFECYCLE & REFUNDS
    # =========================================================================

    # TC-19: Partial cash refund flipping healthy to leaking
    ord_19 = {
        "id": 9000000019, "name": "#9000000019", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "partially_paid", "cancelled_at": None, "total_discounts": "10.00",
        "line_items": [{"id": 19, "variant_id": 119, "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00", "discount_allocations": [{"amount": "10.00"}]}],
        "refunds": [{"id": 8801, "order_id": 9000000019, "created_at": "2026-06-10T14:00:00Z", "refund_line_items": [], "transactions": [{"amount": "20.00", "status": "success"}]}],
        "_variants": [{"id": 119, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "40.00"}}]
    }
    cat_19 = {"product_type": "Home Goods", "metafield_margin": 0.45, "true_cogs": 40.0, "original_price": 100.0}
    eval_19 = evaluate_order(ord_19, catalog_by_variant_id={119: cat_19})
    # Target Profit=$100*0.45=$45. Net revenue=$90-$20 refund=$70. Actual Profit=$70-$40=$30. Loss=$45-$30=$15.
    p_19 = (eval_19.f01_flagged is True and abs(eval_19.f01_dollar_loss - 15.0) < 0.01 and eval_19.actual_gross_profit == 30.0)
    results.append(TestCaseResult(
        "TC-19", "Partial cash refund flips healthy order to leaking",
        "$20.00 monetary refund deducted from net revenue ($90 -> $70)",
        "Net Revenue=$70; Actual Profit=$70-$40=$30; Target=$45; Loss=$15.00",
        "flagged=True, Loss=$15.00, Actual=$30.00",
        f"flagged={eval_19.f01_flagged}, Loss=${eval_19.f01_dollar_loss:.2f}, Actual=${eval_19.actual_gross_profit:.2f}",
        p_19
    ))

    # TC-20: Full refund exclusion
    ord_20 = {
        "id": 9000000020, "name": "#9000000020", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "refunded", "cancelled_at": None, "total_discounts": "15.00",
        "line_items": [{"id": 20, "variant_id": 120, "price": "100.00", "quantity": 1, "current_quantity": 0, "total_discount": "0.00"}]
    }
    eval_20 = evaluate_order(ord_20)
    p_20 = (eval_20.status == "excluded" and eval_20.exclusion_reason == "fully_refunded")
    results.append(TestCaseResult(
        "TC-20", "Full refund (current_quantity=0 across lines) excluded",
        "financial_status=refunded, current_quantity=0",
        "Order has 0 active inventory units; excluded from evaluation cohort",
        "status=excluded, reason=fully_refunded",
        f"status={eval_20.status}, reason={eval_20.exclusion_reason}",
        p_20
    ))

    # TC-21: Physical return line collapse
    ord_21 = {"id": 9000000021, "price": "100.00", "quantity": 1, "current_quantity": 0, "total_discount": "0.00"}
    eval_21 = evaluate_line_item(9000000021, ord_21, {"price": "100.00", "inventory_item": {"cost": "40.00"}}, {"product_type": "Apparel"}, datetime(2026, 6, 10, tzinfo=timezone.utc), 0.0)
    p_21 = (eval_21.target_profit == 0.0 and eval_21.actual_gross_profit == 0.0 and eval_21.f01_dollar_loss == 0.0 and eval_21.active_quantity == 0)
    results.append(TestCaseResult(
        "TC-21", "Physical return: current_quantity=0 collapses line target and actual to $0",
        "current_quantity=0 on returned line item",
        "Active quantity is 0; Target Profit=$0.00, Actual Gross Profit=$0.00",
        "target=0.00, actual=0.00, loss=0.00",
        f"target={eval_21.target_profit:.2f}, actual={eval_21.actual_gross_profit:.2f}, loss={eval_21.f01_dollar_loss:.2f}",
        p_21
    ))

    # TC-22: Order cancellation exclusion
    ord_22 = {
        "id": 9000000022, "name": "#9000000022", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "voided", "cancelled_at": "2026-06-10T13:00:00Z", "total_discounts": "20.00",
        "line_items": [{"id": 22, "variant_id": 122, "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00"}]
    }
    eval_22 = evaluate_order(ord_22)
    p_22 = (eval_22.status == "excluded" and eval_22.exclusion_reason == "cancelled")
    results.append(TestCaseResult(
        "TC-22", "Order cancellation: cancelled_at populated excluded entirely",
        "cancelled_at='2026-06-10T13:00:00Z', total_discounts=$20.00",
        "Cancelled orders are voided before fulfillment; excluded from cohort",
        "status=excluded, reason=cancelled",
        f"status={eval_22.status}, reason={eval_22.exclusion_reason}",
        p_22
    ))

    # TC-23: Duplicate webhook deliveries deduplicated
    res_23 = run_f01_pipeline([ord_01, ord_01, ord_02], [])
    p_23 = (res_23.total_orders_received == 3 and res_23.duplicate_payloads_dropped == 1 and res_23.total_unique_orders == 2)
    results.append(TestCaseResult(
        "TC-23", "Webhook deduplication: duplicate order payloads dropped",
        "3 received payloads containing 1 duplicate order ID",
        "Deduplication retains only unique order IDs",
        "received=3, dropped=1, unique=2",
        f"received={res_23.total_orders_received}, dropped={res_23.duplicate_payloads_dropped}, unique={res_23.total_unique_orders}",
        p_23
    ))

    # =========================================================================
    # SECTION F: SHOPIFY DISCOUNT MECHANISMS & MULTI-LINE ALLOCATIONS
    # =========================================================================

    # TC-24: 100%-off Free Gift Item (TC-19 pattern)
    ord_24 = {
        "id": 9000000024, "name": "#9000000024", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "80.00",
        "line_items": [{
            "id": 24, "variant_id": 124, "sku": "SKU-GIFT-24", "price": "0.00", "quantity": 1, "current_quantity": 1,
            "original_unit_price": "80.00", "total_discount": "80.00", "is_free_gift": True
        }],
        "_variants": [{"id": 124, "price": "80.00", "compare_at_price": "80.00", "inventory_item": {"cost": "25.00"}}]
    }
    cat_24 = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 25.0, "original_price": 80.0}
    eval_24 = evaluate_order(ord_24, catalog_by_variant_id={124: cat_24})
    line_24 = eval_24.line_items[0]
    # Target Profit=$80*0.50=$40. Net revenue=$0. Actual Profit=$0-$25=-$25. Loss=$40-(-$25)=$65.
    p_24 = (line_24.target_profit == 40.0 and line_24.actual_gross_profit == -25.0 and eval_24.f01_dollar_loss == 65.0 and line_24.leakage_reason == "100_percent_free_gift")
    results.append(TestCaseResult(
        "TC-24", "100%-off Free Gift: Anchors target to MSRP, Actual=-COGS, Loss=Target+COGS",
        "MSRP=$80.00, Net Price=$0.00, COGS=$25.00, Target Margin=50%",
        "Target=$40.00; Actual=-$25.00; Loss=$40-(-$25)=$65.00",
        "target=$40.00, actual=-$25.00, loss=$65.00, reason=100_percent_free_gift",
        f"target=${line_24.target_profit:.2f}, actual=${line_24.actual_gross_profit:.2f}, loss=${eval_24.f01_dollar_loss:.2f}, reason={line_24.leakage_reason}",
        p_24
    ))

    # TC-25: Stacked discounts: Product discount + Order coupon
    ord_25 = {
        "id": 9000000025, "name": "#9000000025", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "23.50",
        "line_items": [{
            "id": 25, "variant_id": 125, "sku": "SKU-STACK-25", "price": "100.00", "quantity": 1, "current_quantity": 1,
            "original_unit_price": "100.00", "total_discount": "10.00",
            "discount_allocations": [{"amount": "13.50", "code": "CART15"}]
        }],
        "_variants": [{"id": 125, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "45.00"}}]
    }
    cat_25 = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 45.0, "original_price": 100.0}
    eval_25 = evaluate_order(ord_25, catalog_by_variant_id={125: cat_25})
    line_25 = eval_25.line_items[0]
    # Total discount=$10 line + $13.50 cart = $23.50. Net revenue=$100 - $23.50 = $76.50.
    # Actual profit=$76.50 - $45 = $31.50. Target profit=$100*0.50=$50. Loss=$50-$31.50=$18.50.
    p_25 = (line_25.discount_type == "stacked" and line_25.total_discount_amount == 23.50 and line_25.net_revenue == 76.50 and eval_25.f01_dollar_loss == 18.50)
    results.append(TestCaseResult(
        "TC-25", "Stacked discounts: Product markdown ($10) + Cart coupon ($13.50)",
        "MSRP=$100, Line Disc=$10, Cart Alloc=$13.50, COGS=$45, Target Margin=50%",
        "Total Disc=$23.50 (no double count); Net=$76.50; Actual=$31.50; Target=$50; Loss=$18.50",
        "total_discount=$23.50, net=$76.50, loss=$18.50, type=stacked",
        f"total_discount=${line_25.total_discount_amount:.2f}, net=${line_25.net_revenue:.2f}, loss=${eval_25.f01_dollar_loss:.2f}, type={line_25.discount_type}",
        p_25
    ))

    # TC-26: Multi-SKU order sharing one order-level cart discount
    ord_26 = {
        "id": 9000000026, "name": "#9000000026", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "80.00",
        "line_items": [
            {
                "id": 261, "variant_id": 1261, "sku": "SKU-A", "price": "100.00", "quantity": 1, "current_quantity": 1,
                "original_unit_price": "100.00", "total_discount": "0.00",
                "discount_allocations": [{"amount": "20.00", "code": "CART80"}]
            },
            {
                "id": 262, "variant_id": 1262, "sku": "SKU-B", "price": "300.00", "quantity": 1, "current_quantity": 1,
                "original_unit_price": "300.00", "total_discount": "0.00",
                "discount_allocations": [{"amount": "60.00", "code": "CART80"}]
            }
        ],
        "_variants": [
            {"id": 1261, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}},
            {"id": 1262, "price": "300.00", "compare_at_price": "300.00", "inventory_item": {"cost": "120.00"}}
        ]
    }
    cat_261 = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 30.0, "original_price": 100.0}
    cat_262 = {"product_type": "Electronics", "metafield_margin": 0.30, "true_cogs": 120.0, "original_price": 300.0}
    eval_26 = evaluate_order(ord_26, catalog_by_variant_id={1261: cat_261, 1262: cat_262})
    # Line 1: Net=$80, COGS=$30, Target=$50, Actual=$50 -> Tie, $0 loss
    # Line 2: Net=$240, COGS=$120, Target=$90, Actual=$120 -> Healthy, $0 loss
    # Order: Target=$140, Actual=$170, Flagged=False, Loss=$0
    p_26 = (len(eval_26.line_items) == 2 and
            eval_26.line_items[0].order_discount_allocation == 20.0 and
            eval_26.line_items[1].order_discount_allocation == 60.0 and
            eval_26.total_discounts == 80.0 and
            eval_26.f01_dollar_loss == 0.0 and
            eval_26.actual_gross_profit == 170.0 and
            eval_26.target_minimum_profit == 140.0)
    results.append(TestCaseResult(
        "TC-26", "Multi-SKU order sharing order-level discount allocated proportionally",
        "SKU-A ($100) allocated $20; SKU-B ($300) allocated $60; Cart discount=$80",
        "Line allocations strictly match Shopify allocations; Order profit=$170 vs Target=$140",
        "allocated_A=$20.00, allocated_B=$60.00, total_disc=$80.00, Loss=$0.00",
        f"allocated_A=${eval_26.line_items[0].order_discount_allocation:.2f}, allocated_B=${eval_26.line_items[1].order_discount_allocation:.2f}, total_disc=${eval_26.total_discounts:.2f}, Loss=${eval_26.f01_dollar_loss:.2f}",
        p_26
    ))

    # =========================================================================
    # SECTION G: SAME SKU WITH DIFFERENT DISCOUNTS ACROSS ORDERS
    # =========================================================================

    # Same SKU (SKU-ALPHA: MSRP=$100.00, COGS=$40.00, Target Margin=50% -> Target Profit=$50)
    # Scenario A: 0% discount (Full price $100) -> Excluded from cohort
    ord_27 = {
        "id": 9000000027, "name": "#9000000027", "created_at": "2026-06-10T12:00:00Z", "financial_status": "paid",
        "total_discounts": "0.00",
        "line_items": [{"id": 27, "variant_id": 999, "sku": "SKU-ALPHA", "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00"}],
        "_variants": [{"id": 999, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "40.00"}}]
    }
    eval_27 = evaluate_order(ord_27)
    p_27 = (eval_27.status == "excluded" and eval_27.exclusion_reason == "non_discounted")
    results.append(TestCaseResult(
        "TC-27", "Same SKU across orders (Scenario A): 0% discount",
        "SKU-ALPHA in Order 27: full price $100.00",
        "Excluded from discount leakage evaluation cohort",
        "status=excluded, reason=non_discounted",
        f"status={eval_27.status}, reason={eval_27.exclusion_reason}",
        p_27
    ))

    # Scenario B: 10% product-level markdown -> Net=$90, COGS=$40 -> Actual=$50 == Target=$50 -> Healthy
    ord_28 = {
        "id": 9000000028, "name": "#9000000028", "created_at": "2026-06-10T12:00:00Z", "financial_status": "paid",
        "total_discounts": "10.00",
        "line_items": [{"id": 28, "variant_id": 999, "sku": "SKU-ALPHA", "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "10.00"}],
        "_variants": [{"id": 999, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "40.00"}}]
    }
    cat_alpha = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 40.0, "original_price": 100.0}
    eval_28 = evaluate_order(ord_28, catalog_by_variant_id={999: cat_alpha})
    p_28 = (eval_28.f01_flagged is False and eval_28.f01_dollar_loss == 0.0 and eval_28.actual_gross_profit == 50.0)
    results.append(TestCaseResult(
        "TC-28", "Same SKU across orders (Scenario B): 10% product discount",
        "SKU-ALPHA in Order 28: 10% product discount -> Net=$90.00",
        "Actual Profit=$90-$40=$50 == Target=$50; Healthy, Loss=$0",
        "flagged=False, Loss=$0.00, Actual=$50.00",
        f"flagged={eval_28.f01_flagged}, Loss=${eval_28.f01_dollar_loss:.2f}, Actual=${eval_28.actual_gross_profit:.2f}",
        p_28
    ))

    # Scenario C: 20% cart discount coupon -> Net=$80, COGS=$40 -> Actual=$40 < Target=$50 -> Leaking $10
    ord_29 = {
        "id": 9000000029, "name": "#9000000029", "created_at": "2026-06-10T12:00:00Z", "financial_status": "paid",
        "total_discounts": "20.00",
        "line_items": [{"id": 29, "variant_id": 999, "sku": "SKU-ALPHA", "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "0.00", "discount_allocations": [{"amount": "20.00", "code": "SAVE20"}]}],
        "_variants": [{"id": 999, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "40.00"}}]
    }
    eval_29 = evaluate_order(ord_29, catalog_by_variant_id={999: cat_alpha})
    p_29 = (eval_29.f01_flagged is True and eval_29.f01_dollar_loss == 10.0 and eval_29.actual_gross_profit == 40.0)
    results.append(TestCaseResult(
        "TC-29", "Same SKU across orders (Scenario C): 20% cart coupon",
        "SKU-ALPHA in Order 29: 20% cart discount -> Net=$80.00",
        "Actual Profit=$80-$40=$40 < Target=$50; Leaking Loss=$10.00",
        "flagged=True, Loss=$10.00, Actual=$40.00",
        f"flagged={eval_29.f01_flagged}, Loss=${eval_29.f01_dollar_loss:.2f}, Actual=${eval_29.actual_gross_profit:.2f}",
        p_29
    ))

    # Scenario D: Stacked 10% product + 20% cart -> Total discount=$30 -> Net=$70, COGS=$40 -> Actual=$30 < Target=$50 -> Leaking $20
    ord_30 = {
        "id": 9000000030, "name": "#9000000030", "created_at": "2026-06-10T12:00:00Z", "financial_status": "paid",
        "total_discounts": "30.00",
        "line_items": [{"id": 30, "variant_id": 999, "sku": "SKU-ALPHA", "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "10.00", "discount_allocations": [{"amount": "20.00", "code": "EXTRA20"}]}],
        "_variants": [{"id": 999, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "40.00"}}]
    }
    eval_30 = evaluate_order(ord_30, catalog_by_variant_id={999: cat_alpha})
    p_30 = (eval_30.f01_flagged is True and eval_30.f01_dollar_loss == 20.0 and eval_30.actual_gross_profit == 30.0)
    results.append(TestCaseResult(
        "TC-30", "Same SKU across orders (Scenario D): Stacked product ($10) + cart ($20)",
        "SKU-ALPHA in Order 30: Stacked discounts -> Net=$70.00",
        "Actual Profit=$70-$40=$30 < Target=$50; Leaking Loss=$20.00",
        "flagged=True, Loss=$20.00, Actual=$30.00",
        f"flagged={eval_30.f01_flagged}, Loss=${eval_30.f01_dollar_loss:.2f}, Actual=${eval_30.actual_gross_profit:.2f}",
        p_30
    ))

    # =========================================================================
    # SECTION H: QUANTITY & DATA INTEGRITY CASES
    # =========================================================================

    # TC-31: Multi-unit quantity calculation (Quantity = 3)
    ord_31 = {
        "id": 9000000031, "name": "#9000000031", "created_at": "2026-06-10T12:00:00Z", "financial_status": "paid",
        "total_discounts": "30.00",
        "line_items": [{"id": 31, "variant_id": 131, "sku": "SKU-QTY-31", "price": "100.00", "quantity": 3, "current_quantity": 3, "total_discount": "30.00"}],
        "_variants": [{"id": 131, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "40.00"}}]
    }
    cat_31 = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 40.0, "original_price": 100.0}
    eval_31 = evaluate_order(ord_31, catalog_by_variant_id={131: cat_31})
    line_31 = eval_31.line_items[0]
    # Original line value=$300. Total discount=$30. Net revenue=$270. Total COGS=3*$40=$120.
    # Target profit=$300*0.50=$150. Actual profit=$270-$120=$150. Exact tie -> not flagged, loss=$0.
    p_31 = (line_31.original_line_value == 300.0 and line_31.net_revenue == 270.0 and line_31.total_cogs == 120.0 and
            eval_31.target_minimum_profit == 150.0 and eval_31.actual_gross_profit == 150.0 and eval_31.f01_dollar_loss == 0.0)
    results.append(TestCaseResult(
        "TC-31", "Quantity > 1 multi-unit calculation: Qty=3",
        "Qty=3, MSRP=$100 ($300 total), Discount=$30 ($10/unit), COGS=$40 ($120 total)",
        "Original Value=$300; Net=$270; COGS=$120; Actual=$150; Target=$150; Loss=$0",
        "original_val=$300.00, net=$270.00, target=$150.00, actual=$150.00, Loss=$0.00",
        f"original_val=${line_31.original_line_value:.2f}, net=${line_31.net_revenue:.2f}, target=${eval_31.target_minimum_profit:.2f}, actual=${eval_31.actual_gross_profit:.2f}, Loss=${eval_31.f01_dollar_loss:.2f}",
        p_31
    ))

    # TC-32: Missing/Null price data quality guard -> quarantined instead of silent $0
    ord_32 = {
        "id": 9000000032, "name": "#9000000032", "created_at": "2026-06-10T12:00:00Z", "financial_status": "paid",
        "total_discounts": "5.00",
        "line_items": [{"id": 32, "variant_id": 132, "sku": "SKU-NULLPRICE-32", "price": None, "quantity": 1, "current_quantity": 1, "total_discount": "0.00"}],
        "_variants": [{"id": 132, "price": None, "compare_at_price": None, "inventory_item": {"cost": None}}]
    }
    eval_32 = evaluate_order(ord_32, force_unresolved_cogs=True)
    p_32 = (eval_32.status == "quarantined")
    results.append(TestCaseResult(
        "TC-32", "Data Quality Guard: Missing/Null price and cost routed to quarantine",
        "price=None, compare_at=None, cost=None",
        "Record cannot be mathematically evaluated; quarantined with reason logged",
        "status=quarantined",
        f"status={eval_32.status}",
        p_32
    ))

    # =========================================================================
    # SECTION I: 90-DAY ROLLING MARGIN, PRECEDENCE & ARITHMETIC IDENTITIES
    # =========================================================================

    # TC-33: 90-Day Rolling Historical Target Margin with 2.5% Trimmed Mean (N >= 5)
    from core.historical_index import HistoricalMarginIndex
    idx_33 = HistoricalMarginIndex()
    # Add 5 historical sales in prior 90 days for variant 999: margins 0.40, 0.42, 0.45, 0.48, 0.50
    t_base = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    idx_33.add_observation(999, t_base, 0.40)
    idx_33.add_observation(999, t_base, 0.42)
    idx_33.add_observation(999, t_base, 0.45)
    idx_33.add_observation(999, t_base, 0.48)
    idx_33.add_observation(999, t_base, 0.50)
    idx_33.finalize()

    t_order_33 = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
    hist_m_33 = idx_33.lookup(999, t_order_33, min_obs=5)
    # Mean of (0.40, 0.42, 0.45, 0.48, 0.50) = 2.25 / 5 = 0.45
    p_33 = (hist_m_33 is not None and abs(hist_m_33 - 0.45) < 0.001)
    results.append(TestCaseResult(
        "TC-33", "90-Day Rolling Historical Target Margin: N >= 5 with trimmed mean",
        "5 prior sales with margins [0.40, 0.42, 0.45, 0.48, 0.50] in 90d window",
        "Mean of qualifying observations = 0.4500",
        "margin=0.4500",
        f"margin={hist_m_33}",
        p_33
    ))

    # TC-34: 90-Day Rolling Historical Margin Fallback to Tier 5 Storewide Default (N < 5)
    idx_34 = HistoricalMarginIndex()
    idx_34.add_observation(888, t_base, 0.42)
    idx_34.add_observation(888, t_base, 0.44) # Only 2 observations (< 5)
    idx_34.finalize()
    hist_m_34 = idx_34.lookup(888, t_order_33, min_obs=5)
    m_34, s_34, e_34 = resolve_target_margin(
        variant_id=888,
        order_created_at=t_order_33,
        historical_margin_fn=idx_34.lookup
    )
    p_34 = (hist_m_34 is None and m_34 == 0.35 and s_34 == "storewide_default" and e_34 is True)
    results.append(TestCaseResult(
        "TC-34", "90-Day Historical Margin Fallback: N < 5 -> Tier 5 Storewide Default (35%)",
        "Only 2 historical observations (< 5 min required)",
        "Historical lookup returns None; cascade to storewide default 35%",
        "hist_margin=None, resolved_margin=0.35, source=storewide_default",
        f"hist_margin={hist_m_34}, resolved_margin={m_34:.2f}, source={s_34}",
        p_34
    ))

    # TC-35: 90-Day Rolling Window: Strict Future Data Exclusion (t_obs >= t_order)
    idx_35 = HistoricalMarginIndex()
    # One observation in past, one in future
    idx_35.add_observation(777, datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc), 0.40)
    idx_35.add_observation(777, datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc), 0.80) # Future relative to June 10
    idx_35.finalize()
    # At June 10, future observation at June 15 must be excluded; only 1 observation remains (< 5)
    hist_m_35 = idx_35.lookup(777, datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc), min_obs=2)
    p_35 = (hist_m_35 is None) # Because only 1 past observation exists
    results.append(TestCaseResult(
        "TC-35", "90-Day Rolling Window: Strict future data exclusion (t_obs >= t_order)",
        "1 past observation (June 5), 1 future observation (June 15); query at June 10, min_obs=2",
        "Future transaction at June 15 is strictly excluded; qualifying obs count=1 < 2 -> None",
        "lookup=None",
        f"lookup={hist_m_35}",
        p_35
    ))

    # TC-36: Historical Index Qualifying Exclusions: Cancelled, Voided, Free Gifts
    test_orders_36 = [
        # Cancelled order
        {"id": 1, "cancelled_at": "2026-06-02T00:00:00Z", "created_at": "2026-06-01T12:00:00Z",
         "line_items": [{"variant_id": 666, "price": "100.00", "quantity": 1, "current_quantity": 1}]},
        # Voided order
        {"id": 2, "financial_status": "voided", "created_at": "2026-06-01T12:00:00Z",
         "line_items": [{"variant_id": 666, "price": "100.00", "quantity": 1, "current_quantity": 1}]},
        # Free gift (net revenue = 0)
        {"id": 3, "created_at": "2026-06-01T12:00:00Z",
         "line_items": [{"variant_id": 666, "price": "0.00", "quantity": 1, "current_quantity": 1}]},
    ]
    idx_36 = HistoricalMarginIndex.from_orders_and_catalog(test_orders_36, {666: {"true_cogs": 40.0}})
    # Index must have 0 observations for variant 666
    p_36 = (666 not in idx_36.history or len(idx_36.history[666]) == 0)
    results.append(TestCaseResult(
        "TC-36", "Historical Index Builder: Cancelled, voided, and free gift exclusions",
        "3 invalid orders (cancelled, voided, $0 free gift)",
        "All 3 invalid transactions excluded from historical index",
        "qualifying_observations=0",
        f"qualifying_observations={len(idx_36.history.get(666, []))}",
        p_36
    ))

    # TC-37: 6-Tier Target Margin Precedence Hierarchy
    # Verify Tier 1 > Tier 2 > Tier 3 > Tier 4 > Tier 5 > Tier 6
    m_mf = [{"namespace": "custom", "key": "target_margin", "value": "0.55"}]
    t_hist_fn = lambda vid, dt: 0.42
    product_margin_table_37 = {9001: 0.44}  # Product ID 9001 has a product-specific margin
    # Tier 1 Metafield beats Tier 2 Product
    m_t1, s_t1, _ = resolve_target_margin(metafields=m_mf, product_id=9001, product_margin_table=product_margin_table_37, category_name="Apparel & Accessories > Clothing", historical_margin_fn=t_hist_fn)
    # Tier 2 Product margin beats Tier 3 Taxonomy
    m_t2, s_t2, _ = resolve_target_margin(product_id=9001, product_margin_table=product_margin_table_37, category_name="Apparel & Accessories > Clothing", product_type="Electronics", historical_margin_fn=t_hist_fn)
    # Tier 3 Taxonomy beats Tier 4 Product Type
    m_t3, s_t3, _ = resolve_target_margin(category_name="Apparel & Accessories > Clothing", product_type="Electronics", historical_margin_fn=t_hist_fn)
    # Tier 4 Product Type beats Tier 5 Historical Margin
    m_t4, s_t4, _ = resolve_target_margin(product_type="Apparel", variant_id=123, order_created_at=t_order_33, historical_margin_fn=t_hist_fn)
    # Tier 5 Historical Margin beats Tier 6 Storewide Default
    m_t5, s_t5, _ = resolve_target_margin(variant_id=123, order_created_at=t_order_33, historical_margin_fn=t_hist_fn)
    p_37 = (s_t1 == "metafield" and m_t1 == 0.55 and
            s_t2 == "product_margin" and m_t2 == 0.44 and
            s_t3 == "taxonomy" and m_t3 == 0.52 and
            s_t4 == "product_type" and m_t4 == 0.52 and
            s_t5 == "historical_margin" and m_t5 == 0.42)
    results.append(TestCaseResult(
        "TC-37", "6-Tier Target Margin Precedence: Tier 1 > Tier 2 > Tier 3 > Tier 4 > Tier 5 > Tier 6",
        "Combinations of metafield, product_margin, taxonomy, product type, and historical margin",
        "Higher priority tiers strictly override lower tiers",
        "T1=metafield (0.55), T2=product_margin (0.44), T3=taxonomy (0.52), T4=product_type (0.52), T5=historical (0.42)",
        f"T1={s_t1} ({m_t1}), T2={s_t2} ({m_t2}), T3={s_t3} ({m_t3}), T4={s_t4} ({m_t4}), T5={s_t5} ({m_t5})",
        p_37
    ))

    # TC-38: Quarantine Sibling Line Isolation in Multi-line Order
    ord_38 = {
        "id": 9000000038, "name": "#9000000038", "created_at": "2026-06-10T12:00:00Z", "financial_status": "paid",
        "total_discounts": "10.00",
        "line_items": [
            # Line 1: Corrupted cost > price ($150 > $100) -> triggers quarantine
            {"id": 1001, "variant_id": 501, "sku": "SKU-BAD-501", "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "5.00"},
            # Line 2: Valid healthy line ($100 price, $30 cost) -> sibling quarantined
            {"id": 1002, "variant_id": 502, "sku": "SKU-GOOD-502", "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "5.00"}
        ],
        "_variants": [
            {"id": 501, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "150.00"}},
            {"id": 502, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}
        ]
    }
    eval_38 = evaluate_order(ord_38)
    p_38 = (eval_38.status == "quarantined" and len(eval_38.line_items) == 2 and
            eval_38.line_items[0].input_confidence == "quarantined" and
            "sanity_guard_cost_exceeds_price" in str(eval_38.line_items[0].quarantine_reason))
    results.append(TestCaseResult(
        "TC-38", "Quarantine Sibling Line Isolation: Entire order quarantined, lineage preserved",
        "Order with Line 1 (corrupted cost > price) and Line 2 (valid healthy line)",
        "Order status=quarantined; Line 1 has trigger reason; Line 2 details preserved",
        "order_status=quarantined, lines_count=2, line1_quarantined=True",
        f"order_status={eval_38.status}, lines_count={len(eval_38.line_items)}, line1_quarantined={eval_38.line_items[0].input_confidence == 'quarantined'}",
        p_38
    ))

    # TC-39: F01 vs F03 Operational Cash Partitioning Boundary
    ord_39 = {
        "id": 9000000039, "name": "#9000000039", "created_at": "2026-06-10T12:00:00Z", "financial_status": "paid",
        "total_discounts": "20.00",
        "line_items": [{"id": 39, "variant_id": 539, "sku": "SKU-F03-39", "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "20.00"}],
        "_variants": [{"id": 539, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "90.00"}}]
    }
    cat_39 = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 90.0, "original_price": 100.0}
    eval_39 = evaluate_order(ord_39, catalog_by_variant_id={539: cat_39})
    # Actual GP = $80 - $90 = -$10.00 (negative gross profit).
    # Since carrier shipping cost and gateway fee are None, F03 escalation status MUST be 'unable_to_determine'
    p_39 = (eval_39.actual_gross_profit == -10.0 and eval_39.negative_gross_profit is True and
            eval_39.f03_escalation_status == "unable_to_determine" and
            eval_39.f03_escalation_reason == "missing_f03_operational_cost_data")
    results.append(TestCaseResult(
        "TC-39", "F03 Boundary: Negative GP with missing operational costs -> unable_to_determine",
        "Actual GP = -$10.00, carrier_shipping_cost=None, gateway_fee=None",
        "Negative GP does NOT assume F03 escalation; status must be 'unable_to_determine'",
        "status=unable_to_determine, reason=missing_f03_operational_cost_data",
        f"status={eval_39.f03_escalation_status}, reason={eval_39.f03_escalation_reason}",
        p_39
    ))

    # TC-40: Inherent Deficit Isolation & Exact Shortfall Arithmetic Identity
    # Case: MSRP=$100, COGS=$60, Target Margin=50% -> Target Profit=$50.
    # Baseline Profit = $100 - $60 = $40.
    # Inherent COGS Deficit = $50 - $40 = $10 (pre-existing deficit before discount).
    # Discount=$30 -> Net=$70. Actual GP = $70 - $60 = $10.
    # Total Target Shortfall = Target Profit ($50) - Actual GP ($10) = $40.
    # Incremental Promotional Leakage = Total Shortfall ($40) - Inherent Deficit ($10) = $30.
    # Identity: Total Target Shortfall ($40) == Inherent Deficit ($10) + Promotional Leakage ($30).
    ord_40 = {
        "id": 9000000040, "name": "#9000000040", "created_at": "2026-06-10T12:00:00Z", "financial_status": "paid",
        "total_discounts": "30.00",
        "line_items": [{"id": 40, "variant_id": 540, "sku": "SKU-DEFICIT-40", "price": "100.00", "quantity": 1, "current_quantity": 1, "total_discount": "30.00"}],
        "_variants": [{"id": 540, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "60.00"}}]
    }
    cat_40 = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 60.0, "original_price": 100.0}
    eval_40 = evaluate_order(ord_40, catalog_by_variant_id={540: cat_40})
    l_40 = eval_40.line_items[0]
    identity_holds = (abs(l_40.total_target_shortfall - (l_40.inherent_cogs_deficit + l_40.f01_dollar_loss)) < 0.001)
    p_40 = (l_40.inherent_cogs_deficit == 10.0 and l_40.f01_dollar_loss == 30.0 and
            l_40.total_target_shortfall == 40.0 and identity_holds and
            l_40.leakage_reason == "promotional_leakage_plus_pre_existing_deficit")
    results.append(TestCaseResult(
        "TC-40", "Arithmetic Identity: Total Shortfall = Inherent Deficit + Promotional Leakage",
        "MSRP=$100, Target=50%, COGS=$60, Discount=$30",
        "Target Shortfall ($40) = Inherent Deficit ($10) + Promotional Loss ($30)",
        "Total Shortfall=$40.00, Inherent=$10.00, Promo Loss=$30.00, Identity=True",
        f"Total Shortfall=${l_40.total_target_shortfall:.2f}, Inherent=${l_40.inherent_cogs_deficit:.2f}, Promo Loss=${l_40.f01_dollar_loss:.2f}, Identity={identity_holds}",
        p_40
    ))

    # =========================================================================
    # SECTION J: 5 TARGETED PRODUCTION FIXES (TC-41 through TC-46)
    # =========================================================================

    # TC-41: MSRP / Baseline Definition — explicit priority chain
    # Rule: original_unit_price > compare_at (when > catalog price) > catalog price > compare_at > price
    # Case 1: original_unit_price is present -> must be used as MSRP
    li_41a = {
        "id": 411, "variant_id": 4100, "price": "80.00", "quantity": 1, "current_quantity": 1,
        "original_unit_price": "120.00",  # Explicit MSRP from Shopify
        "total_discount": "40.00"
    }
    var_41a = {"price": "100.00", "compare_at_price": "110.00", "inventory_item": {"cost": "30.00"}}
    prod_41a = {"product_type": "Apparel"}
    eval_41a = evaluate_line_item(
        9000000041, li_41a, var_41a, prod_41a,
        datetime(2026, 6, 10, tzinfo=timezone.utc), 0.0
    )
    # MSRP must be original_unit_price=$120 (highest priority), NOT compare_at=$110 or catalog=$100
    p_41a = (eval_41a.original_price == 120.0 and eval_41a.original_line_value == 120.0)

    # Case 2: no original_unit_price; compare_at > catalog price -> compare_at is the MSRP
    li_41b = {
        "id": 412, "variant_id": 4101, "price": "75.00", "quantity": 1, "current_quantity": 1,
        "total_discount": "0.00"
    }
    var_41b = {"price": "75.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}
    eval_41b = evaluate_line_item(
        9000000041, li_41b, var_41b, {"product_type": "Apparel"},
        datetime(2026, 6, 10, tzinfo=timezone.utc), 0.0
    )
    # compare_at=$100 > catalog=$75 -> MSRP=compare_at=$100
    p_41b = (eval_41b.original_price == 100.0 and eval_41b.discount_type == "product_markdown")

    # Case 3: compare_at == catalog price -> catalog price is the MSRP (no markdown inflation)
    li_41c = {
        "id": 413, "variant_id": 4102, "price": "100.00", "quantity": 1, "current_quantity": 1,
        "total_discount": "0.00",
        "discount_allocations": [{"amount": "10.00", "code": "DISC10"}]
    }
    var_41c = {"price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "30.00"}}
    eval_41c = evaluate_line_item(
        9000000041, li_41c, var_41c, {"product_type": "Apparel"},
        datetime(2026, 6, 10, tzinfo=timezone.utc), 0.0
    )
    # compare_at == catalog -> MSRP = catalog price = $100 (not inflated)
    p_41c = (eval_41c.original_price == 100.0)

    p_41 = p_41a and p_41b and p_41c
    results.append(TestCaseResult(
        "TC-41", "MSRP Definition: explicit priority chain (original_unit_price > compare_at > catalog > price)",
        "Case A: orig_unit=$120 > compare_at=$110 > catalog=$100; Case B: compare_at=$100 > catalog=$75; Case C: compare_at=catalog=$100",
        "Case A: MSRP=120 | Case B: MSRP=100 (markdown) | Case C: MSRP=100 (no inflation)",
        "Case A: orig_price=120 | Case B: orig_price=100, type=product_markdown | Case C: orig_price=100",
        f"A: orig={eval_41a.original_price}, B: orig={eval_41b.original_price} type={eval_41b.discount_type}, C: orig={eval_41c.original_price}",
        p_41
    ))

    # TC-42: Discount Double-Counting Prevention — exhaustive reconciliation
    # Order with 2 lines sharing one cart coupon. total_discounts must exactly equal sum of line allocations.
    ord_42 = {
        "id": 9000000042, "name": "#9000000042", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "paid", "cancelled_at": None, "total_discounts": "50.00",
        "line_items": [
            {
                "id": 421, "variant_id": 4211, "sku": "SKU-DC-A", "price": "200.00",
                "quantity": 1, "current_quantity": 1, "total_discount": "0.00",
                "discount_allocations": [{"amount": "20.00", "code": "CART50"}]
            },
            {
                "id": 422, "variant_id": 4212, "sku": "SKU-DC-B", "price": "300.00",
                "quantity": 1, "current_quantity": 1, "total_discount": "0.00",
                "discount_allocations": [{"amount": "30.00", "code": "CART50"}]
            }
        ],
        "_variants": [
            {"id": 4211, "price": "200.00", "compare_at_price": "200.00", "inventory_item": {"cost": "80.00"}},
            {"id": 4212, "price": "300.00", "compare_at_price": "300.00", "inventory_item": {"cost": "120.00"}}
        ]
    }
    eval_42 = evaluate_order(ord_42)
    line_42_sum = sum(l.total_discount_amount for l in eval_42.line_items)
    # $20 + $30 = $50. Must equal order total_discounts=$50. No double counting.
    p_42 = (
        eval_42.line_items[0].total_discount_amount == 20.0 and
        eval_42.line_items[1].total_discount_amount == 30.0 and
        abs(line_42_sum - eval_42.total_discounts) < 0.01 and
        eval_42.line_items[0].line_discount_amount == 0.0 and
        eval_42.line_items[1].line_discount_amount == 0.0
    )
    results.append(TestCaseResult(
        "TC-42", "Discount double-counting prevention: sum(line discounts) == order.total_discounts",
        "2 lines sharing CART50 coupon: Line-A allocated $20, Line-B allocated $30; total_discounts=$50",
        "sum_lines=$50.00 == total_discounts=$50.00; no double-counting; line_discount != allocation",
        "line_A=$20.00, line_B=$30.00, sum=$50.00, total_discounts=$50.00, no_double_count=True",
        f"line_A=${eval_42.line_items[0].total_discount_amount:.2f}, line_B=${eval_42.line_items[1].total_discount_amount:.2f}, sum=${line_42_sum:.2f}, total_disc=${eval_42.total_discounts:.2f}",
        p_42
    ))

    # TC-43: Partial Quantity Return with Active Discount — COGS, Revenue, Leakage on active qty only
    # Order: 3 units purchased at $100 each, $30 total_discount. 1 unit physically returned.
    # Active qty = 2. Active original value = 2 * $100 = $200.
    # Active line discount = $30 * (2/3) = $20.00.
    # Net revenue = $200 - $20 = $180. Active COGS = 2 * $40 = $80.
    # Target profit (50% of $200) = $100. Actual profit = $180 - $80 = $100 -> Exact tie, not leaking.
    ord_43 = {
        "id": 9000000043, "name": "#9000000043", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "partially_refunded", "cancelled_at": None, "total_discounts": "20.00",
        "line_items": [{
            "id": 43, "variant_id": 430, "sku": "SKU-PARTRET-43",
            "price": "100.00", "quantity": 3, "current_quantity": 2,  # 1 unit returned
            "total_discount": "30.00",  # Original total discount on 3 units
        }],
        "_variants": [{"id": 430, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "40.00"}}]
    }
    cat_43 = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 40.0, "original_price": 100.0}
    eval_43 = evaluate_order(ord_43, catalog_by_variant_id={430: cat_43})
    line_43 = eval_43.line_items[0]
    # Active line value = 2 * $100 = $200; Active discount = $30 * (2/3) = $20; Net = $180; COGS = $80
    p_43 = (
        line_43.active_quantity == 2 and
        line_43.original_line_value == 200.0 and
        abs(line_43.line_discount_amount - 20.0) < 0.01 and
        abs(line_43.net_revenue - 180.0) < 0.01 and
        line_43.total_cogs == 80.0 and
        abs(line_43.actual_gross_profit - 100.0) < 0.01 and
        eval_43.f01_flagged is False
    )
    results.append(TestCaseResult(
        "TC-43", "Partial quantity return with active discount: metrics computed on active qty only",
        "Qty=3, current_qty=2 (1 returned), total_discount=$30, COGS=$40/unit, Target=50%",
        "Active: orig_val=$200, disc=$20 (2/3 of $30), net=$180, COGS=$80, actual=$100 == target=$100",
        "active_qty=2, orig_val=200, disc=20.00, net=180, cogs=80, actual=100, flagged=False",
        f"active_qty={line_43.active_quantity}, orig_val={line_43.original_line_value:.0f}, disc={line_43.line_discount_amount:.2f}, net={line_43.net_revenue:.0f}, cogs={line_43.total_cogs:.0f}, actual={line_43.actual_gross_profit:.0f}, flagged={eval_43.f01_flagged}",
        p_43
    ))

    # TC-44: Partial Cash Refund on Discounted Item — all metrics remain consistent
    # Order: 1 unit, MSRP=$100, cart discount=$10, cash refund=$20.
    # Net revenue = $100 - $10 (discount) - $20 (cash refund) = $70.
    # COGS=$40. Actual profit = $70 - $40 = $30. Target profit (50% of $100) = $50. Loss = $20.
    ord_44 = {
        "id": 9000000044, "name": "#9000000044", "created_at": "2026-06-10T12:00:00Z",
        "financial_status": "partially_refunded", "cancelled_at": None, "total_discounts": "10.00",
        "line_items": [{
            "id": 44, "variant_id": 440, "sku": "SKU-CASHREF-44",
            "price": "100.00", "quantity": 1, "current_quantity": 1,
            "total_discount": "0.00",
            "discount_allocations": [{"amount": "10.00", "code": "DISC10"}]
        }],
        "refunds": [{
            "id": 8802, "order_id": 9000000044,
            "refund_line_items": [],  # Cash-only refund, no physical return
            "transactions": [{"amount": "20.00", "status": "success"}]
        }],
        "_variants": [{"id": 440, "price": "100.00", "compare_at_price": "100.00", "inventory_item": {"cost": "40.00"}}]
    }
    cat_44 = {"product_type": "Apparel", "metafield_margin": 0.50, "true_cogs": 40.0, "original_price": 100.0}
    eval_44 = evaluate_order(ord_44, catalog_by_variant_id={440: cat_44})
    line_44 = eval_44.line_items[0]
    # original_line_value=$100; discount=$10; cash_refund=$20; net_revenue=$100-$10-$20=$70; COGS=$40
    # actual_gp=$70-$40=$30; target_profit=$100*0.50=$50; loss=$50-$30=$20
    p_44 = (
        abs(line_44.net_revenue - 70.0) < 0.01 and
        line_44.total_cogs == 40.0 and
        abs(line_44.actual_gross_profit - 30.0) < 0.01 and
        abs(line_44.target_profit - 50.0) < 0.01 and
        abs(eval_44.f01_dollar_loss - 20.0) < 0.01 and
        eval_44.f01_flagged is True
    )
    results.append(TestCaseResult(
        "TC-44", "Partial cash refund on discounted item: Revenue, COGS, Discount, Leakage all consistent",
        "MSRP=$100, cart disc=$10, cash refund=$20, COGS=$40, Target=50%",
        "Net=$100-$10-$20=$70; COGS=$40; Actual=$30; Target=$50; Loss=$20",
        "net=70.00, cogs=40.00, actual=30.00, target=50.00, loss=20.00, flagged=True",
        f"net={line_44.net_revenue:.2f}, cogs={line_44.total_cogs:.2f}, actual={line_44.actual_gross_profit:.2f}, target={line_44.target_profit:.2f}, loss={eval_44.f01_dollar_loss:.2f}, flagged={eval_44.f01_flagged}",
        p_44
    ))

    # TC-45: Configuration Constants — MIN_HISTORICAL_MARGIN_OBSERVATIONS and STOREWIDE_DEFAULT_TARGET_MARGIN
    # are declared as named production constants, not embedded magic numbers.
    from core.historical_index import MIN_HISTORICAL_MARGIN_OBSERVATIONS
    from core.fallbacks.margin import STOREWIDE_DEFAULT_TARGET_MARGIN
    from core.fallbacks.cogs import STOREWIDE_DEFAULT_MARGIN as COGS_DEFAULT_MARGIN
    p_45 = (
        MIN_HISTORICAL_MARGIN_OBSERVATIONS == 5 and
        STOREWIDE_DEFAULT_TARGET_MARGIN == 0.35 and
        COGS_DEFAULT_MARGIN == 0.35 and
        COGS_DEFAULT_MARGIN is STOREWIDE_DEFAULT_TARGET_MARGIN  # Must be the same object (imported, not duplicated)
    )
    results.append(TestCaseResult(
        "TC-45", "Configuration constants: MIN_HISTORICAL_MARGIN_OBSERVATIONS=5, STOREWIDE_DEFAULT=35%, single source of truth",
        "MIN_HISTORICAL_MARGIN_OBSERVATIONS and STOREWIDE_DEFAULT_TARGET_MARGIN declared as named constants",
        "MIN_OBS=5; DEFAULT_MARGIN=0.35 in margin.py; cogs.py imports the same object (no duplicate)",
        "MIN_OBS=5, DEFAULT_MARGIN=0.35, same_object=True",
        f"MIN_OBS={MIN_HISTORICAL_MARGIN_OBSERVATIONS}, DEFAULT_MARGIN={STOREWIDE_DEFAULT_TARGET_MARGIN}, same_object={COGS_DEFAULT_MARGIN is STOREWIDE_DEFAULT_TARGET_MARGIN}",
        p_45
    ))

    # TC-46: Line -> Order -> Store Aggregation Identity (Fix 5)
    # Use TC-25 (stacked) + TC-40 (deficit) as a 2-order batch. Verify:
    #   Σ line leakage == Σ order leakage == batch total_dollar_loss
    #   Total Shortfall == Inherent Deficit + Promotional Leakage
    batch_46 = run_f01_pipeline(
        [ord_25, ord_40],
        [],
        category_margin_table={},
        product_type_margin_table={"Apparel": 0.50}
    )
    ev_orders_46 = [o for o in batch_46.order_evaluations if o.status == "evaluated"]
    sum_line_leakage = round(sum(l.f01_dollar_loss for o in ev_orders_46 for l in o.line_items), 2)
    sum_order_leakage = round(sum(o.f01_dollar_loss for o in ev_orders_46), 2)
    batch_total = batch_46.total_dollar_loss
    shortfall_identity = abs(batch_46.total_target_shortfall - round(batch_46.total_inherent_deficit + batch_46.total_dollar_loss, 2)) < 0.01
    p_46 = (
        abs(sum_line_leakage - sum_order_leakage) < 0.01 and
        abs(sum_order_leakage - batch_total) < 0.01 and
        shortfall_identity
    )
    results.append(TestCaseResult(
        "TC-46", "Aggregation Identity: SUM(line leakage) == SUM(order leakage) == batch total; Shortfall = Deficit + Leakage",
        "Batch of 2 evaluated orders (TC-25: stacked, TC-40: deficit+leakage)",
        "sum_line == sum_order == batch_total; Total Shortfall == Inherent Deficit + Promotional Leakage",
        "line_sum == order_sum == batch_total == True, shortfall_identity == True",
        f"line_sum={sum_line_leakage:.2f}, order_sum={sum_order_leakage:.2f}, batch_total={batch_total:.2f}, shortfall_identity={shortfall_identity}",
        p_46
    ))

    return results

def main():
    print("=" * 100)
    print("FORMULA F01: COMPREHENSIVE AUTOMATED UNIT & REGRESSION TEST SUITE (TC-01 through TC-46)")
    print("=" * 100)
    results = run_f01_unit_tests()
    all_passed = True
    for r in results:
        status = "[PASS]" if r.passed else "[FAIL]"
        if not r.passed:
            all_passed = False
        print(f"{r.test_id:<7} {status} | {r.case_name}")
        if not r.passed:
            print(f"   Input:    {r.input_data}")
            print(f"   Formula:  {r.formula_steps}")
            print(f"   Expected: {r.expected_output}")
            print(f"   Actual:   {r.actual_output}")
    print("-" * 100)
    print(f"Final Test Result: {'100% PASS (46/46 Passing)' if all_passed else 'FAILURES DETECTED'}")
    print("=" * 100)
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
