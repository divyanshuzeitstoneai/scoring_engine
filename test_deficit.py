import json
from formulas.f01_discount_leakage.runner import run_f01_pipeline
from core.historical_index import HistoricalCogsIndex

with open("data/synthetic_orders.json", "r", encoding="utf-8") as f:
    orders = json.load(f)
with open("data/synthetic_catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)
with open("data/historical_cost_index.json", "r", encoding="utf-8") as f:
    hist = json.load(f)

res = run_f01_pipeline(orders, catalog, HistoricalCogsIndex(hist))
eval_orders = [o for o in res.order_evaluations if o.status == "evaluated"]

total_inherent_deficit = 0.0
total_target_shortfall = 0.0
total_incremental_promo_leakage = 0.0
lines_with_inherent_deficit = 0

for o in eval_orders:
    for li in o.line_items:
        base_profit = round(li.original_line_value - li.total_cogs, 2)
        inh_def = max(0.0, round(li.target_profit - base_profit, 2))
        tot_shortfall = max(0.0, round(li.target_profit - li.actual_gross_profit, 2))
        incr_promo = max(0.0, round(tot_shortfall - inh_def, 2))
        
        total_inherent_deficit += inh_def
        total_target_shortfall += tot_shortfall
        total_incremental_promo_leakage += incr_promo
        if inh_def > 0:
            lines_with_inherent_deficit += 1

print("Evaluated lines:", sum(len(o.line_items) for o in eval_orders))
print("Lines with inherent COGS deficit:", lines_with_inherent_deficit)
print("Total Target Shortfall: {:.2f}".format(total_target_shortfall))
print("Total Inherent COGS Deficit: {:.2f}".format(total_inherent_deficit))
print("Total Incremental Promotional Leakage: {:.2f}".format(total_incremental_promo_leakage))
diff = total_target_shortfall - (total_inherent_deficit + total_incremental_promo_leakage)
print("Reconciliation Diff: {:.4f}".format(diff))
