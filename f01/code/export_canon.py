import json
import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from f01.code.runner import run_f01_pipeline, _find_data_file
from core.historical_index import HistoricalCogsIndex

print("Loading data...")
with open(_find_data_file("synthetic_orders.json"), "r", encoding="utf-8") as f:
    orders = json.load(f)
with open(_find_data_file("synthetic_catalog.json"), "r", encoding="utf-8") as f:
    catalog = json.load(f)
with open(_find_data_file("historical_cost_index.json"), "r", encoding="utf-8") as f:
    hist = json.load(f)

print("Running pipeline...")
res = run_f01_pipeline(orders, catalog, HistoricalCogsIndex(hist))

# Top 20 worst leaking orders
eval_orders = [o for o in res.order_evaluations if o.status == "evaluated" and o.f01_flagged]
top_20_orders = sorted(eval_orders, key=lambda x: x.f01_dollar_loss, reverse=True)[:20]

top20_rows = []
total_top20_leakage = 0.0

for rank, o in enumerate(top_20_orders, 1):
    total_top20_leakage += o.f01_dollar_loss
    is_multi = len(o.line_items) > 1
    
    for idx, li in enumerate(o.line_items):
        rank_str = str(rank) if idx == 0 else ""
        order_str = f"#{o.order_id}" if idx == 0 else "↳"
        
        top20_rows.append({
            "Rank": rank_str,
            "Order ID": order_str,
            "Line Item ID": str(li.line_item_id),
            "SKU": li.sku or "N/A",
            "Qty": str(li.active_quantity),
            "Orig Price": f"${li.original_price:,.2f}",
            "Orig Line Val": f"${li.original_line_value:,.2f}",
            "Disc Unit Price": f"${li.discounted_unit_price:,.2f}",
            "Product Disc": f"${li.line_discount_amount:,.2f}",
            "Cart Alloc": f"${li.order_discount_allocation:,.2f}",
            "Tot Disc": f"${li.total_discount_amount:,.2f}",
            "Disc %": f"{li.discount_percentage:.1f}%",
            "Code": li.discount_code or "—",
            "Net Price": f"${li.net_selling_price:,.2f}",
            "COGS/U": f"${li.cogs_used:,.2f}",
            "Tot COGS": f"${li.total_cogs:,.2f}",
            "Target %": f"{li.target_margin_used*100:.1f}%",
            "Target Profit": f"${li.target_profit:,.2f}",
            "Base Profit": f"${li.baseline_gross_profit:,.2f}",
            "Inherent Deficit": f"${li.inherent_cogs_deficit:,.2f}",
            "Actual Profit": f"${li.actual_gross_profit:,.2f}",
            "Leakage Loss": f"${li.f01_dollar_loss:,.2f}",
            "COGS Source": li.cogs_source,
            "Leakage Reason": li.leakage_reason
        })
        
    if is_multi:
        top20_rows.append({
            "Rank": "—",
            "Order ID": "Order Total",
            "Line Item ID": f"All Lines ({len(o.line_items)})",
            "SKU": "Multi",
            "Qty": str(sum(li.active_quantity for li in o.line_items)),
            "Orig Price": "—",
            "Orig Line Val": f"${o.total_original_value:,.2f}",
            "Disc Unit Price": "—",
            "Product Disc": "—",
            "Cart Alloc": "—",
            "Tot Disc": f"${o.total_discounts:,.2f}",
            "Disc %": "—",
            "Code": "—",
            "Net Price": "—",
            "COGS/U": "—",
            "Tot COGS": f"${o.total_cogs:,.2f}",
            "Target %": "—",
            "Target Profit": f"${o.target_minimum_profit:,.2f}",
            "Base Profit": f"${o.baseline_gross_profit:,.2f}",
            "Inherent Deficit": f"${o.inherent_cogs_deficit:,.2f}",
            "Actual Profit": f"${o.actual_gross_profit:,.2f}",
            "Leakage Loss": f"${o.f01_dollar_loss:,.2f}",
            "COGS Source": "—",
            "Leakage Reason": "Order Aggregation"
        })

print(f"Total Top 20 Leakage: ${total_top20_leakage:,.2f}")

# Sample 150 diverse orders for Streamlit UI
sample_pool = []
# Include all Top 20 orders
sample_pool.extend(top_20_orders)
# Include healthy orders
healthy_pool = [o for o in eval_orders if not o.f01_flagged]
sample_pool.extend(healthy_pool[:40])
# Include remaining leaking orders
other_leaking = [o for o in eval_orders if o.f01_flagged and o not in top_20_orders]
sample_pool.extend(other_leaking[:90])

sample_orders_json = []
for o in sample_pool[:150]:
    sample_orders_json.append({
        "order_id": o.order_id,
        "status": o.status,
        "is_discounted": o.is_discounted,
        "total_original_value": o.total_original_value,
        "total_net_revenue": o.total_net_revenue,
        "total_discounts": o.total_discounts,
        "total_cogs": o.total_cogs,
        "target_minimum_profit": o.target_minimum_profit,
        "baseline_gross_profit": o.baseline_gross_profit,
        "actual_gross_profit": o.actual_gross_profit,
        "inherent_cogs_deficit": o.inherent_cogs_deficit,
        "total_target_shortfall": o.total_target_shortfall,
        "f01_flagged": o.f01_flagged,
        "f01_dollar_loss": o.f01_dollar_loss,
        "negative_gross_profit": o.negative_gross_profit,
        "shipping_revenue_collected": o.shipping_revenue_collected,
        "carrier_shipping_cost": o.carrier_shipping_cost,
        "gateway_processing_fee": o.gateway_processing_fee,
        "actual_cash_contribution": o.actual_cash_contribution,
        "f03_escalation_status": o.f03_escalation_status,
        "f03_escalation_reason": o.f03_escalation_reason,
        "input_confidence": o.input_confidence,
        "line_items": [
            {
                "line_item_id": li.line_item_id,
                "sku": li.sku,
                "variant_id": li.variant_id,
                "quantity": li.quantity,
                "active_quantity": li.active_quantity,
                "original_price": li.original_price,
                "original_line_value": li.original_line_value,
                "discounted_unit_price": li.discounted_unit_price,
                "line_discount_amount": li.line_discount_amount,
                "line_discount_percentage": li.line_discount_percentage,
                "order_discount_allocation": li.order_discount_allocation,
                "total_discount_amount": li.total_discount_amount,
                "discount_percentage": li.discount_percentage,
                "discount_code": li.discount_code,
                "discount_type": li.discount_type,
                "net_selling_price": li.net_selling_price,
                "net_revenue": li.net_revenue,
                "cogs_used": li.cogs_used,
                "total_cogs": li.total_cogs,
                "cogs_source": li.cogs_source,
                "target_margin_used": li.target_margin_used,
                "target_margin_source": li.target_margin_source,
                "target_profit": li.target_profit,
                "baseline_gross_profit": li.baseline_gross_profit,
                "actual_gross_profit": li.actual_gross_profit,
                "inherent_cogs_deficit": li.inherent_cogs_deficit,
                "total_target_shortfall": li.total_target_shortfall,
                "f01_flagged": li.f01_flagged,
                "f01_dollar_loss": li.f01_dollar_loss,
                "leakage_reason": li.leakage_reason,
                "input_confidence": li.input_confidence,
                "quarantine_reason": li.quarantine_reason
            }
            for li in o.line_items
        ]
    })

summary_dict = {
    "total_orders_received": res.total_orders_received,
    "total_unique_orders": res.total_unique_orders,
    "duplicate_payloads_dropped": res.duplicate_payloads_dropped,
    "evaluated_orders": res.evaluated_orders,
    "quarantined_orders": res.quarantined_orders,
    "excluded_orders": res.excluded_orders,
    "failed_orders": res.failed_orders,
    "f01_score": res.f01_score,
    "health_band": res.health_band,
    "total_target_profit": res.total_target_profit,
    "total_baseline_profit": res.total_baseline_profit,
    "total_actual_profit": res.total_actual_profit,
    "total_inherent_deficit": res.total_inherent_deficit,
    "total_target_shortfall": res.total_target_shortfall,
    "total_dollar_loss": res.total_dollar_loss,
    "count_based_score": res.count_based_score,
    "healthy_discounted_orders": res.healthy_discounted_orders,
    "leaking_discounted_orders": res.leaking_discounted_orders,
    "negative_gross_profit_orders": res.negative_gross_profit_orders,
    "positive_gp_leaking_orders": res.positive_gp_leaking_orders,
    "confirmed_target_profit": res.confirmed_target_profit,
    "estimated_target_profit": res.estimated_target_profit,
    "confirmed_actual_profit": res.confirmed_actual_profit,
    "estimated_actual_profit": res.estimated_actual_profit,
    "confirmed_promotional_loss": res.confirmed_promotional_loss,
    "estimated_promotional_loss": res.estimated_promotional_loss,
    "order_leakage_stats": res.order_leakage_stats,
    "line_leakage_stats": res.line_leakage_stats,
    "cogs_waterfall_counts": res.cogs_waterfall_counts,
    "target_margin_source_counts": res.target_margin_source_counts,
    "confidence_counts": res.confidence_counts,
    "leakage_reason_counts": res.leakage_reason_counts,
    "f03_escalation_counts": res.f03_escalation_counts,
    "sample_orders": sample_orders_json
}

data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(data_dir, exist_ok=True)

with open(os.path.join(data_dir, "f01_evaluation_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary_dict, f)
print("Saved f01/data/f01_evaluation_summary.json successfully!")

# Load test cases
from f01.code.test_f01 import run_f01_unit_tests
tc_results = run_f01_unit_tests()
tc_data = [
    {
        "Test ID": t.test_id,
        "Test Scenario Description": t.case_name,
        "Input Conditions": t.input_data,
        "Formula Calculation Steps": t.formula_steps,
        "Expected Result": t.expected_output,
        "Actual Result": t.actual_output,
        "Status": "PASS" if t.passed else "FAIL"
    }
    for t in tc_results
]

extra_dict = {
    "top20": top20_rows,
    "test_cases": tc_data
}

with open(os.path.join(data_dir, "f01_dashboard_extra.json"), "w", encoding="utf-8") as f:
    json.dump(extra_dict, f, indent=2)
print("Saved f01/data/f01_dashboard_extra.json successfully!")
