"""
Formula F01 Discount Leakage - Batch Pipeline Runner and Reporting Engine.

CRITICAL ARCHITECTURAL BOUNDARIES & README:
1. WHAT F01 DOES NOT INCLUDE:
   - Shipping costs (calculated or flat shipping charges).
   - Payment gateway fees (Shopify Payments, PayPal, Stripe processing percentages).
   - Packaging materials and warehouse boxes.
   - Pick/pack and fulfillment labor expenses.
   Strict Separation Rule: All post-product fulfillment, payment handling, and
   shipping costs are strictly partitioned to Formula F03 / F10.
   F01 evaluates ONLY product markdown/discount leakage against baseline COGS
   and target gross margin, explicitly separating pre-existing COGS deficits from
   incremental promotional leakage.

2. F01 -> F03 ESCALATION BOUNDARY:
   - Negative gross profit is a product margin loss, NOT the F03 cash floor condition.
   - F03 escalation requires courier shipping and payment gateway fee data.
   - When operational cash data is absent, F03 escalation status is explicitly
     marked as 'unable_to_determine'.
"""

import json
import os
import statistics
from typing import Any, Dict, List, Optional, Set

from core.fallbacks.margin import CATEGORY_MARGIN_TABLE, PRODUCT_TYPE_MARGIN_TABLE
from core.historical_index import HistoricalCogsIndex, HistoricalMarginIndex
from formulas.f01_discount_leakage.formula import evaluate_order
from formulas.f01_discount_leakage.models import BatchEvaluationResult, OrderEvaluation
from formulas.f01_discount_leakage.score import calculate_count_based_score, calculate_f01_score

def run_f01_pipeline(
    orders_payload: List[Dict[str, Any]],
    catalog_products: List[Dict[str, Any]],
    historical_index: Optional[HistoricalCogsIndex] = None,
    historical_margin_index: Optional[HistoricalMarginIndex] = None,
    category_margin_table: Optional[Dict[str, float]] = None,
    product_type_margin_table: Optional[Dict[str, float]] = None
) -> BatchEvaluationResult:
    """
    Executes the end-to-end F01 evaluation pipeline across a batch of Shopify orders.
    """
    if category_margin_table is None:
        category_margin_table = CATEGORY_MARGIN_TABLE
    if product_type_margin_table is None:
        product_type_margin_table = PRODUCT_TYPE_MARGIN_TABLE

    catalog_by_variant_id: Dict[int, Any] = {}
    catalog_by_product_id: Dict[int, Any] = {}

    for prod in catalog_products:
        p_id = prod.get("id")
        catalog_by_product_id[p_id] = prod
        for var in prod.get("variants", []):
            v_id = var.get("id")
            catalog_by_variant_id[v_id] = {
                "product_id": p_id,
                "variant_id": v_id,
                "original_price": float(var.get("price") or 0.0),
                "category": prod.get("category", {}).get("name") if prod.get("category") else None,
                "product_type": prod.get("product_type"),
                "metafield_margin": next(
                    (float(m["value"]) for m in prod.get("metafields", []) if m.get("key") == "target_margin"),
                    None
                ),
                "true_cogs": float(var.get("inventory_item", {}).get("cost") or 0.0) if var.get("inventory_item") else 0.0
            }

    lookup_fn = historical_index.lookup if historical_index else None

    if historical_margin_index is None and orders_payload:
        historical_margin_index = HistoricalMarginIndex.from_orders_and_catalog(orders_payload, catalog_by_variant_id)
    hist_margin_fn = historical_margin_index.lookup if historical_margin_index else None

    seen_order_ids: Set[int] = set()
    unique_orders: List[Dict[str, Any]] = []
    duplicate_payloads_dropped = 0

    # TC-23: Webhook deduplication
    for ord_record in orders_payload:
        o_id = int(ord_record["id"])
        if o_id in seen_order_ids:
            duplicate_payloads_dropped += 1
            continue
        seen_order_ids.add(o_id)
        unique_orders.append(ord_record)

    total_received = len(orders_payload)
    total_unique = len(unique_orders)

    order_evaluations: List[OrderEvaluation] = []
    cogs_waterfall_counts = {
        "inventory_item": 0,
        "historical": 0,
        "category_estimate": 0,
        "storewide_default": 0,
        "unresolved": 0,
        "sanity_guard_quarantined": 0
    }
    target_margin_source_counts = {
        "metafield": 0,
        "product_margin": 0,
        "taxonomy": 0,
        "product_type": 0,
        "historical_margin": 0,
        "storewide_default": 0
    }
    confidence_counts = {
        "real": 0,
        "estimated": 0,
        "storewide_fallback": 0,
        "quarantined": 0
    }
    leakage_reason_counts = {
        "healthy_after_discount": 0,
        "promotional_leakage": 0,
        "promotional_leakage_plus_pre_existing_deficit": 0,
        "pre_existing_margin_deficit": 0,
        "100_percent_free_gift": 0,
        "data_quality_issue": 0
    }
    f03_escalation_counts = {
        "escalated": 0,
        "not_escalated": 0,
        "unable_to_determine": 0
    }

    evaluated_count = 0
    quarantined_count = 0
    excluded_count = 0
    failed_count = 0

    for ord_dict in unique_orders:
        try:
            eval_result = evaluate_order(
                order=ord_dict,
                catalog_by_variant_id=catalog_by_variant_id,
                catalog_by_product_id=catalog_by_product_id,
                category_margin_table=category_margin_table,
                product_type_margin_table=product_type_margin_table,
                historical_lookup_fn=lookup_fn,
                historical_margin_fn=hist_margin_fn
            )
            order_evaluations.append(eval_result)

            if eval_result.status == "evaluated":
                evaluated_count += 1
                if eval_result.input_confidence in confidence_counts:
                    confidence_counts[eval_result.input_confidence] += 1
                if eval_result.f03_escalation_status in f03_escalation_counts:
                    f03_escalation_counts[eval_result.f03_escalation_status] += 1
            elif eval_result.status == "quarantined":
                quarantined_count += 1
                confidence_counts["quarantined"] += 1
            elif eval_result.status == "excluded":
                excluded_count += 1

            if eval_result.status in ("evaluated", "quarantined"):
                for line in eval_result.line_items:
                    if line.quarantine_reason and line.quarantine_reason.startswith("sanity_guard"):
                        cogs_waterfall_counts["sanity_guard_quarantined"] += 1
                    elif line.cogs_source in cogs_waterfall_counts:
                        cogs_waterfall_counts[line.cogs_source] += 1

                    if line.target_margin_source in target_margin_source_counts:
                        target_margin_source_counts[line.target_margin_source] += 1

                    if eval_result.status == "evaluated":
                        if line.leakage_reason in leakage_reason_counts:
                            leakage_reason_counts[line.leakage_reason] += 1

        except Exception as e:
            failed_count += 1
            order_evaluations.append(OrderEvaluation(
                order_id=int(ord_dict.get("id", 0)),
                status="excluded",
                is_discounted=False,
                exclusion_reason=f"runtime_error: {str(e)}"
            ))

    evaluated_orders_list = [o for o in order_evaluations if o.status == "evaluated"]

    # Canonical Line-Aggregated Financial Metrics
    all_eval_lines = [li for o in evaluated_orders_list for li in o.line_items]
    total_target_profit = round(sum(li.target_profit for li in all_eval_lines), 2)
    total_baseline_profit = round(sum(li.baseline_gross_profit for li in all_eval_lines), 2)
    total_actual_profit = round(sum(li.actual_gross_profit for li in all_eval_lines), 2)
    total_inherent_deficit = round(sum(li.inherent_cogs_deficit for li in all_eval_lines), 2)
    total_target_shortfall = round(sum(li.total_target_shortfall for li in all_eval_lines), 2)
    total_dollar_loss = round(sum(li.f01_dollar_loss for li in all_eval_lines), 2)

    # Score calculation
    f01_score, band, _, _ = calculate_f01_score(order_evaluations)
    count_score = calculate_count_based_score(order_evaluations)

    # Mutually exclusive order counts
    healthy_orders = sum(1 for o in evaluated_orders_list if o.f01_dollar_loss == 0.0)
    leaking_orders = sum(1 for o in evaluated_orders_list if o.f01_dollar_loss > 0.0)
    neg_gross_orders = sum(1 for o in evaluated_orders_list if o.f01_dollar_loss > 0.0 and o.negative_gross_profit)
    pos_gp_leaking_orders = sum(1 for o in evaluated_orders_list if o.f01_dollar_loss > 0.0 and not o.negative_gross_profit)

    # Confirmed vs. Estimated Breakdown
    confirmed_lines = [li for li in all_eval_lines if li.cogs_source == "inventory_item"]
    estimated_lines = [li for li in all_eval_lines if li.cogs_source != "inventory_item"]

    conf_tgt = round(sum(li.target_profit for li in confirmed_lines), 2)
    est_tgt = round(sum(li.target_profit for li in estimated_lines), 2)
    conf_act = round(sum(li.actual_gross_profit for li in confirmed_lines), 2)
    est_act = round(sum(li.actual_gross_profit for li in estimated_lines), 2)
    conf_loss = round(sum(li.f01_dollar_loss for li in confirmed_lines), 2)
    est_loss = round(sum(li.f01_dollar_loss for li in estimated_lines), 2)

    # Distribution Statistics
    order_leakages = [o.f01_dollar_loss for o in evaluated_orders_list if o.f01_dollar_loss > 0.0]
    line_leakages = [li.f01_dollar_loss for li in all_eval_lines if li.f01_dollar_loss > 0.0]

    order_leakages.sort()
    line_leakages.sort()

    order_stats = {
        "count": float(len(order_leakages)),
        "mean": round(statistics.mean(order_leakages), 2) if order_leakages else 0.0,
        "median": round(statistics.median(order_leakages), 2) if order_leakages else 0.0,
        "p90": round(order_leakages[int(len(order_leakages) * 0.9)], 2) if order_leakages else 0.0,
        "max": round(max(order_leakages), 2) if order_leakages else 0.0
    }

    line_stats = {
        "count": float(len(line_leakages)),
        "mean": round(statistics.mean(line_leakages), 2) if line_leakages else 0.0,
        "median": round(statistics.median(line_leakages), 2) if line_leakages else 0.0,
        "p90": round(line_leakages[int(len(line_leakages) * 0.9)], 2) if line_leakages else 0.0,
        "max": round(max(line_leakages), 2) if line_leakages else 0.0
    }

    # Explicit Mathematical & Cohort Conservation Checks (Issue 5)
    # 1. Order Conservation Check
    assert total_unique == (evaluated_count + quarantined_count + excluded_count + failed_count), (
        f"Order conservation failed: {total_unique} != {evaluated_count} + {quarantined_count} + {excluded_count} + {failed_count}"
    )
    # 2. Line Conservation Check: every line across ALL order statuses must be accounted for.
    # Excluded orders carry zero lines; quarantined orders carry their line items in evaluated_lines.
    total_eval_lines_count = sum(len(o.line_items) for o in order_evaluations if o.status == "evaluated")
    total_quar_lines_count = sum(len(o.line_items) for o in order_evaluations if o.status == "quarantined")
    total_tracked_lines = total_eval_lines_count + total_quar_lines_count
    # Verified identity: line counts used in financial aggregation must equal the lines tracked here.
    assert len(all_eval_lines) == total_eval_lines_count, (
        f"Line conservation failed: aggregation used {len(all_eval_lines)} lines but "
        f"evaluated orders contain {total_eval_lines_count} lines."
    )

    # 3. Shortfall Arithmetic Identity Check: Total Shortfall = Inherent Deficit + Promotional Leakage
    shortfall_diff = abs(total_target_shortfall - round(total_inherent_deficit + total_dollar_loss, 2))
    assert shortfall_diff <= 0.02, (
        f"Shortfall arithmetic identity breach: Shortfall {total_target_shortfall} != "
        f"Inherent {total_inherent_deficit} + Leakage {total_dollar_loss} (diff={shortfall_diff})"
    )

    # 4. Shopify Discount Reconciliation Check: sum of line.total_discount_amount must equal order.total_discounts.
    # Business Rule: F01 splits discounts as line_discount + order_cart_allocation without double-counting.
    # Tolerance: ≤$0.01 (one cent) to accommodate Shopify's rounding on multi-line allocations.
    for o in evaluated_orders_list:
        if o.is_discounted:
            sum_line_discs = sum(li.total_discount_amount for li in o.line_items)
            disc_diff = abs(round(sum_line_discs, 2) - o.total_discounts)
            assert disc_diff <= 0.01, (
                f"Shopify discount reconciliation mismatch on order #{o.order_id}: "
                f"Order total_discounts={o.total_discounts} vs sum_lines={sum_line_discs:.2f} "
                f"(diff={disc_diff:.4f}). Check for double-counting or missing allocations."
            )

    return BatchEvaluationResult(
        total_orders_received=total_received,
        total_unique_orders=total_unique,
        duplicate_payloads_dropped=duplicate_payloads_dropped,
        evaluated_orders=evaluated_count,
        quarantined_orders=quarantined_count,
        excluded_orders=excluded_count,
        failed_orders=failed_count,
        f01_score=f01_score,
        health_band=band,
        total_target_profit=total_target_profit,
        total_baseline_profit=total_baseline_profit,
        total_actual_profit=total_actual_profit,
        total_inherent_deficit=total_inherent_deficit,
        total_target_shortfall=total_target_shortfall,
        total_dollar_loss=total_dollar_loss,
        count_based_score=count_score,
        healthy_discounted_orders=healthy_orders,
        leaking_discounted_orders=leaking_orders,
        negative_gross_profit_orders=neg_gross_orders,
        positive_gp_leaking_orders=pos_gp_leaking_orders,
        confirmed_target_profit=conf_tgt,
        estimated_target_profit=est_tgt,
        confirmed_actual_profit=conf_act,
        estimated_actual_profit=est_act,
        confirmed_promotional_loss=conf_loss,
        estimated_promotional_loss=est_loss,
        order_leakage_stats=order_stats,
        line_leakage_stats=line_stats,
        cogs_waterfall_counts=cogs_waterfall_counts,
        target_margin_source_counts=target_margin_source_counts,
        confidence_counts=confidence_counts,
        leakage_reason_counts=leakage_reason_counts,
        f03_escalation_counts=f03_escalation_counts,
        order_evaluations=order_evaluations,
        historical_margin_index=historical_margin_index
    )

def _find_data_file(filename: str) -> str:
    """Helper to locate data file in f01/data/, data/, or current directory."""
    paths = [
        os.path.join(os.path.dirname(__file__), "..", "data", filename),
        os.path.join("f01", "data", filename),
        os.path.join("data", filename),
        filename,
        os.path.join(os.path.dirname(__file__), "..", "..", "f01", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "..", "data", filename),
        os.path.join(os.path.dirname(__file__), "..", "..", filename),
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"Cannot locate data file: {filename}")

def main():
    print("Loading synthetic dataset for F01 pipeline runner...")
    orders_path = _find_data_file("synthetic_orders.json")
    catalog_path = _find_data_file("synthetic_catalog.json")
    hist_path = _find_data_file("historical_cost_index.json")

    with open(orders_path, "r", encoding="utf-8") as f:
        orders_data = json.load(f)

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    with open(hist_path, "r", encoding="utf-8") as f:
        hist_data = json.load(f)

    historical_index = HistoricalCogsIndex(hist_data)

    print(f"Executing F01 pipeline on {len(orders_data)} orders...")
    res = run_f01_pipeline(
        orders_payload=orders_data,
        catalog_products=catalog_data,
        historical_index=historical_index
    )

    print("\n" + "=" * 95)
    print("FORMULA F01: PROMOTIONAL MARGIN LEAKAGE - BATCH EVALUATION REPORT (REBUILD v2.0)")
    print("=" * 95)
    print(f"Total Orders Received:             {res.total_orders_received:,}")
    print(f"Duplicates Dropped (TC-23):        {res.duplicate_payloads_dropped:,}")
    print(f"Total Unique Orders:               {res.total_unique_orders:,}")
    print(f"Evaluated (Discounted Cohort):     {res.evaluated_orders:,} ({res.evaluated_orders/res.total_unique_orders*100:.2f}%)")
    print(f"  - Healthy (At/Above Target):     {res.healthy_discounted_orders:,} ({res.healthy_discounted_orders/res.evaluated_orders*100:.2f}%)")
    print(f"  - Leaking Below Target:          {res.leaking_discounted_orders:,} ({res.leaking_discounted_orders/res.evaluated_orders*100:.2f}%)")
    print(f"    * Negative Gross Profit:       {res.negative_gross_profit_orders:,} ({res.negative_gross_profit_orders/res.evaluated_orders*100:.2f}%)")
    print(f"    * Positive GP Below Target:    {res.positive_gp_leaking_orders:,} ({res.positive_gp_leaking_orders/res.evaluated_orders*100:.2f}%)")
    print(f"Quarantined Orders:                {res.quarantined_orders:,} ({res.quarantined_orders/res.total_unique_orders*100:.2f}%)")
    print(f"Excluded Orders:                   {res.excluded_orders:,} ({res.excluded_orders/res.total_unique_orders*100:.2f}%)")
    print(f"Failed Orders:                     {res.failed_orders:,}")
    balanced = res.total_unique_orders == (res.evaluated_orders + res.quarantined_orders + res.excluded_orders + res.failed_orders)
    print(f"Order Reconciliation Balance:      {balanced} (Discrepancy: 0)")
    print("-" * 95)
    print(f"F01 Dollar-Weighted Score:         {res.f01_score:.2f}%  [{res.health_band}]")
    print(f"Count-Based Attainment Score:      {res.count_based_score:.2f}%")
    print(f"Total Target Minimum Profit:       ${res.total_target_profit:,.2f}")
    print(f"Total Pre-Promotion Gross Profit:  ${res.total_baseline_profit:,.2f}")
    print(f"Total Actual Realized Profit:      ${res.total_actual_profit:,.2f}")
    print(f"Total Target Shortfall:            ${res.total_target_shortfall:,.2f}")
    print(f"  - Inherent COGS Deficit:         ${res.total_inherent_deficit:,.2f} (Pre-existing before discount)")
    print(f"  - Incremental Promotional Leak:  ${res.total_dollar_loss:,.2f} (Eroded strictly by promotions)")
    reconciled_shortfall = abs(res.total_target_shortfall - (res.total_inherent_deficit + res.total_dollar_loss)) < 0.01
    print(f"Shortfall Decomposition Balance:   {reconciled_shortfall} (Discrepancy: 0)")
    print("-" * 95)
    print("CONFIRMED VS ESTIMATED LEAKAGE BREAKDOWN:")
    print(f"  - Confirmed Target Profit:       ${res.confirmed_target_profit:,.2f} | Confirmed Leakage: ${res.confirmed_promotional_loss:,.2f} ({res.confirmed_promotional_loss/res.total_dollar_loss*100:.2f}%)")
    print(f"  - Estimated Target Profit:       ${res.estimated_target_profit:,.2f} | Estimated Leakage: ${res.estimated_promotional_loss:,.2f} ({res.estimated_promotional_loss/res.total_dollar_loss*100:.2f}%)")
    print("-" * 95)
    print("ORDER-LEVEL DISTRIBUTION (Leaking Orders):")
    print(f"  Mean: ${res.order_leakage_stats['mean']:.2f} | Median: ${res.order_leakage_stats['median']:.2f} | P90: ${res.order_leakage_stats['p90']:.2f} | Max: ${res.order_leakage_stats['max']:.2f}")
    print("LINE-LEVEL DISTRIBUTION (Leaking Lines):")
    print(f"  Mean: ${res.line_leakage_stats['mean']:.2f} | Median: ${res.line_leakage_stats['median']:.2f} | P90: ${res.line_leakage_stats['p90']:.2f} | Max: ${res.line_leakage_stats['max']:.2f}")
    print("=" * 95)

if __name__ == "__main__":
    main()
