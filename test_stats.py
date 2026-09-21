import json
import statistics

with open("data/synthetic_orders.json", "r", encoding="utf-8") as f:
    orders = json.load(f)
with open("data/synthetic_catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)
with open("data/historical_cost_index.json", "r", encoding="utf-8") as f:
    hist = json.load(f)

from formulas.f01_discount_leakage.runner import run_f01_pipeline
from core.historical_index import HistoricalCogsIndex

res = run_f01_pipeline(orders, catalog, HistoricalCogsIndex(hist))
eval_orders = [o for o in res.order_evaluations if o.status == "evaluated"]

order_leakages = []
line_leakages = []

for o in eval_orders:
    o_loss = 0.0
    for li in o.line_items:
        base_profit = round(li.original_line_value - li.total_cogs, 2)
        inh_def = max(0.0, round(li.target_profit - base_profit, 2))
        tot_shortfall = max(0.0, round(li.target_profit - li.actual_gross_profit, 2))
        incr_promo = max(0.0, round(tot_shortfall - inh_def, 2))
        li.f01_dollar_loss = incr_promo
        li.inherent_cogs_deficit = inh_def
        o_loss += incr_promo
        if incr_promo > 0:
            line_leakages.append(incr_promo)
    o.f01_dollar_loss = round(o_loss, 2)
    if o_loss > 0:
        order_leakages.append(o_loss)

print("ORDER-LEVEL STATS:")
print("Count of leaking orders:", len(order_leakages))
print("Total leakage:", f"{sum(order_leakages):,.2f}")
print("Mean:", f"{statistics.mean(order_leakages):,.2f}")
print("Median:", f"{statistics.median(order_leakages):,.2f}")
order_leakages.sort()
print("P90:", f"{order_leakages[int(len(order_leakages)*0.9)]:,.2f}")
print("Max:", f"{max(order_leakages):,.2f}")

print("\nLINE-LEVEL STATS:")
print("Count of leaking lines:", len(line_leakages))
print("Mean:", f"{statistics.mean(line_leakages):,.2f}")
print("Median:", f"{statistics.median(line_leakages):,.2f}")
line_leakages.sort()
print("P90:", f"{line_leakages[int(len(line_leakages)*0.9)]:,.2f}")
print("Max:", f"{max(line_leakages):,.2f}")
